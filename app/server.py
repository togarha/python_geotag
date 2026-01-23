"""
FastAPI server with all endpoints for the geotagging application
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
import json
import math

from .photo_manager import PhotoManager
from .gpx_manager import GPXManager
from .elevation_service import ElevationService
from .positions_manager import PositionsManager

app = FastAPI(title="Geotag Application")

# Helper function to clean NaN values for JSON serialization
def clean_nan_values(obj):
    """Recursively replace NaN and inf values with None for JSON serialization"""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    return obj

# Request models
class ScanFolderRequest(BaseModel):
    folder_path: str
    recursive: bool = False

class TagUpdateRequest(BaseModel):
    tagged: bool

class LocationUpdateRequest(BaseModel):
    latitude: float
    longitude: float
    altitude: Optional[float] = None

class SortRequest(BaseModel):
    sort_by: str = "time"

class ElevationRequest(BaseModel):
    latitude: float
    longitude: float
    service: str = "open-elevation"

class FilenameFormatRequest(BaseModel):
    format: str

class PhotoTitleRequest(BaseModel):
    title: str

class PhotoMetadataUpdate(BaseModel):
    new_time: Optional[str] = None
    new_title: Optional[str] = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage (in production, use proper state management)
photo_manager = PhotoManager()
gpx_manager = GPXManager()
elevation_service = ElevationService()
positions_manager = PositionsManager()

# Serve static files
static_path = Path(__file__).parent.parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Serve templates
templates_path = Path(__file__).parent.parent / "templates"
templates_path.mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    index_file = templates_path / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding='utf-8'), status_code=200)
    return HTMLResponse(content="<h1>Welcome to Geotag App</h1><p>Templates not found.</p>")


@app.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon to prevent 404 errors"""
    return Response(status_code=204)


@app.post("/api/elevation")
async def get_elevation(request: ElevationRequest):
    """Fetch elevation for given coordinates using specified service"""
    try:
        elevation = elevation_service.get_elevation(
            request.latitude,
            request.longitude,
            request.service
        )
        
        return {
            "success": True,
            "elevation": elevation,
            "service": request.service
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/scan-folder")
async def scan_folder(request: ScanFolderRequest):
    """
    Scan a folder for photos and create pd_photo_info DataFrame
    """
    try:
        df = photo_manager.scan_folder(request.folder_path, request.recursive)
        
        # Match with GPX if available
        if gpx_manager.has_data():
            photo_manager.match_all_photos_with_gpx(gpx_manager)
            df = photo_manager.pd_photo_info
        
        # Reset index and add original index as a column
        df_with_index = df.reset_index()
        df_with_index.rename(columns={'index': 'original_index'}, inplace=True)
        
        # Convert datetime columns to string for JSON serialization
        for col in ['exif_capture_time', 'creation_time']:
            if col in df_with_index.columns:
                df_with_index[col] = df_with_index[col].apply(
                    lambda x: x.isoformat() if pd.notna(x) else None
                )
        
        # Convert to dict and clean NaN values
        df_dict = df_with_index.to_dict(orient="records")
        df_dict = clean_nan_values(df_dict)
        
        return {
            "success": True,
            "folder": request.folder_path,
            "count": len(df),
            "data": df_dict
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/photos")
async def get_photos(filter_type: str = "all"):
    """
    Get photos from pd_photo_info with optional filtering
    filter_type: 'all', 'tagged', 'untagged'
    """
    try:
        df = photo_manager.get_photos(filter_type)
        # Reset index and add original index as a column
        df_with_index = df.reset_index()
        df_with_index.rename(columns={'index': 'original_index'}, inplace=True)
        
        # Convert datetime columns to string for JSON serialization
        for col in ['exif_capture_time', 'creation_time']:
            if col in df_with_index.columns:
                df_with_index[col] = df_with_index[col].apply(
                    lambda x: x.isoformat() if pd.notna(x) else None
                )
        
        # Convert to dict and clean NaN values
        df_dict = df_with_index.to_dict(orient="records")
        df_dict = clean_nan_values(df_dict)
        
        return {
            "success": True,
            "count": len(df),
            "data": df_dict
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/photos/{index}/tag")
async def toggle_tag(index: int, request: TagUpdateRequest):
    """Toggle the tagged status of a photo"""
    try:
        photo_manager.update_tag(index, request.tagged)
        return {"success": True, "index": index, "tagged": request.tagged}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/photos/{index}/manual-location")
async def update_manual_location(index: int, request: LocationUpdateRequest):
    """Update manual GPS coordinates for a photo"""
    try:
        photo_manager.update_manual_location(index, request.latitude, request.longitude, request.altitude)
        photo = photo_manager.get_photo_by_index(index)
        return {"success": True, "photo": photo}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/photos/{index}/manual-location")
async def delete_manual_location(index: int):
    """Delete manual GPS coordinates for a photo"""
    try:
        photo_manager.delete_manual_location(index)
        photo = photo_manager.get_photo_by_index(index)
        return {"success": True, "photo": photo}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/photos/{index}")
async def get_photo_details(index: int):
    """Get detailed information about a specific photo"""
    try:
        photo = photo_manager.get_photo_by_index(index)
        
        # GPX matching is now done upfront when photos/GPX are loaded
        # or when GPX data changes, so just return the photo data
        
        return {"success": True, "photo": photo}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/photo-thumbnail/{index}")
async def get_photo_thumbnail(index: int, size: int = 200):
    """Get a thumbnail of a photo"""
    try:
        thumbnail_path = photo_manager.get_thumbnail(index, size)
        return FileResponse(thumbnail_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/photo-image/{index}")
async def get_photo_image(index: int):
    """Get the full-size image"""
    try:
        photo = photo_manager.get_photo_by_index(index)
        return FileResponse(photo['full_path'])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/gpx/upload")
async def upload_gpx(files: List[UploadFile] = File(...)):
    """Load and parse one or more GPX files"""
    try:
        # Don't clear - append new tracks to existing ones
        results = []
        for file in files:
            content = await file.read()
            result = gpx_manager.load_gpx(content.decode('utf-8'), file.filename)
            results.append(result)
        
        # Match all photos with updated GPX data
        if photo_manager.pd_photo_info is not None:
            photo_manager.match_all_photos_with_gpx(gpx_manager)
        
        return {
            "success": True,
            "files_loaded": len(results),
            "tracks": gpx_manager.get_all_tracks()  # Return ALL tracks
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/gpx/remove")
async def remove_gpx_tracks(request: dict):
    """Remove specific GPX tracks by indices"""
    try:
        indices = request.get('indices', [])
        
        gpx_manager.remove_tracks_by_indices(indices)
        
        # Re-match all photos with remaining GPX data
        if photo_manager.pd_photo_info is not None:
            photo_manager.match_all_photos_with_gpx(gpx_manager)
        
        return {
            "success": True,
            "tracks": gpx_manager.get_all_tracks()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/gpx/clear")
async def clear_gpx_tracks():
    """Clear all GPX tracks"""
    try:
        gpx_manager.clear_tracks()
        
        return {
            "success": True,
            "tracks": []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/gpx/set-main-offset")
async def set_main_gpx_offset(request: dict):
    """Set main time offset for all GPX tracks"""
    try:
        offset_str = request.get('offset', '+00:00:00')
        offset_seconds = gpx_manager.parse_offset_string(offset_str)
        gpx_manager.set_main_offset(offset_seconds)
        
        # Re-match all photos with updated GPX times
        if photo_manager.pd_photo_info is not None:
            photo_manager.match_all_photos_with_gpx(gpx_manager)
        
        return {
            "success": True,
            "tracks": gpx_manager.get_all_tracks()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/gpx/set-track-offset")
async def set_track_gpx_offset(request: dict):
    """Set time offset for a specific GPX track"""
    try:
        track_index = request.get('track_index')
        offset_str = request.get('offset', '+00:00:00')
        
        if track_index is None:
            raise HTTPException(status_code=400, detail="track_index is required")
        
        offset_seconds = gpx_manager.parse_offset_string(offset_str)
        gpx_manager.set_track_offset(track_index, offset_seconds)
        
        # Re-match all photos with updated GPX times
        if photo_manager.pd_photo_info is not None:
            photo_manager.match_all_photos_with_gpx(gpx_manager)
        
        return {
            "success": True,
            "tracks": gpx_manager.get_all_tracks()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/gpx/tracks")
async def get_gpx_tracks():
    """Get all loaded GPX tracks"""
    try:
        tracks = gpx_manager.get_all_tracks()
        return {"success": True, "tracks": tracks}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/positions/upload")
async def upload_positions(files: List[UploadFile] = File(...)):
    """Load and parse one or more YAML files with predefined positions"""
    try:
        results = []
        for file in files:
            content = await file.read()
            result = positions_manager.load_yaml(content.decode('utf-8'), file.filename)
            results.append(result)
        
        return {
            "success": True,
            "files_loaded": len(results),
            "positions": positions_manager.get_all_positions()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/positions/remove")
async def remove_positions(request: dict):
    """Remove positions from a specific file"""
    try:
        filename = request.get('filename')
        if not filename:
            raise HTTPException(status_code=400, detail="filename is required")
        
        positions_manager.remove_positions_by_file(filename)
        
        return {
            "success": True,
            "positions": positions_manager.get_all_positions()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/positions")
async def get_positions():
    """Get all loaded predefined positions"""
    try:
        positions = positions_manager.get_all_positions()
        positions_by_file = positions_manager.get_positions_by_file()
        return {
            "success": True,
            "positions": positions,
            "by_file": positions_by_file
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sort")
async def set_sort_order(request: SortRequest):
    """
    Set the sort order for photos
    sort_by: 'time' or 'name'
    """
    try:
        photo_manager.set_sort_order(request.sort_by)
        return {"success": True, "sort_by": request.sort_by}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/preview-rename")
async def preview_rename(request: FilenameFormatRequest):
    """
    Preview what photo filenames would look like with the given format
    Returns first 20 photos as preview
    """
    try:
        if photo_manager.pd_photo_info is None or len(photo_manager.pd_photo_info) == 0:
            return {"success": False, "detail": "No photos loaded"}
        
        previews = photo_manager.preview_rename_format(request.format, max_count=20)
        return {"success": True, "previews": previews}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/apply-rename-format")
async def apply_rename_format(request: FilenameFormatRequest):
    """
    Apply the filename format to all photos (updates new_name column)
    """
    try:
        if photo_manager.pd_photo_info is None or len(photo_manager.pd_photo_info) == 0:
            return {"success": False, "detail": "No photos loaded"}
        
        count = photo_manager.apply_rename_format(request.format)
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/filename-format")
async def get_filename_format():
    """
    Get the current filename format
    """
    try:
        format_str = photo_manager.get_filename_format()
        return {"success": True, "format": format_str}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/apply-photo-title")
async def apply_photo_title(request: PhotoTitleRequest):
    """
    Apply a title to all photos (updates new_title column)
    """
    try:
        if photo_manager.pd_photo_info is None or len(photo_manager.pd_photo_info) == 0:
            return {"success": False, "detail": "No photos loaded"}
        
        count = photo_manager.apply_photo_title(request.title)
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/clear-photo-titles")
async def clear_photo_titles():
    """
    Clear all new_title values
    """
    try:
        if photo_manager.pd_photo_info is None or len(photo_manager.pd_photo_info) == 0:
            return {"success": False, "detail": "No photos loaded"}
        
        count = photo_manager.clear_photo_titles()
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/apply-photo-title-tagged")
async def apply_photo_title_tagged(request: PhotoTitleRequest):
    """
    Apply a title to tagged photos only (updates new_title column)
    """
    try:
        if photo_manager.pd_photo_info is None or len(photo_manager.pd_photo_info) == 0:
            return {"success": False, "detail": "No photos loaded"}
        
        count = photo_manager.apply_photo_title_tagged(request.title)
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/photos/{index}/metadata")
async def update_photo_metadata(index: int, request: PhotoMetadataUpdate):
    """
    Update new_time and/or new_title for a specific photo
    """
    try:
        if photo_manager.pd_photo_info is None or index >= len(photo_manager.pd_photo_info):
            return {"success": False, "detail": "Invalid photo index"}
        
        photo_manager.update_photo_metadata(index, request.new_time, request.new_title)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
