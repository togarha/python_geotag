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

from .photo_manager import PhotoManager
from .gpx_manager import GPXManager

app = FastAPI(title="Geotag Application")

# Request models
class ScanFolderRequest(BaseModel):
    folder_path: str
    recursive: bool = False

class TagUpdateRequest(BaseModel):
    tagged: bool

class LocationUpdateRequest(BaseModel):
    latitude: float
    longitude: float

class SortRequest(BaseModel):
    sort_by: str = "time"

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
        return {
            "success": True,
            "folder": request.folder_path,
            "count": len(df),
            "data": df_with_index.to_dict(orient="records")
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
        return {
            "success": True,
            "count": len(df),
            "data": df_with_index.to_dict(orient="records")
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
        photo_manager.update_manual_location(index, request.latitude, request.longitude)
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
