"""
FastAPI server with all endpoints for the geotagging application
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response, StreamingResponse
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
from .config_manager import ConfigManager
from .export_manager import ExportManager

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
    new_offset_time: Optional[str] = None

class TimeOffsetRequest(BaseModel):
    offset: str
    mode: str = 'all'  # 'all', 'tagged', or 'not_updated'

class SettingsUpdate(BaseModel):
    map_provider: Optional[str] = None
    elevation_service: Optional[str] = None
    filename_format: Optional[str] = None
    include_subfolders: Optional[bool] = None
    sort_by: Optional[str] = None
    thumbnail_size: Optional[int] = None
    folder_path: Optional[str] = None
    export_folder: Optional[str] = None
    auto_save_config: Optional[bool] = None

class ConfigSaveAsRequest(BaseModel):
    file_path: str

class ExportRequest(BaseModel):
    export_type: str  # 'all' or 'tagged'

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

# Configuration manager (initialized from main.py)
config_manager: ConfigManager = ConfigManager()

def set_config_manager(cm: ConfigManager):
    """Set the config manager instance (called from main.py)"""
    global config_manager
    config_manager = cm
    
    # Apply initial settings from config to photo_manager
    filename_format = config_manager.get('filename_format')
    if filename_format:
        photo_manager.set_filename_format(filename_format)
    
    sort_by = config_manager.get('sort_by')
    if sort_by:
        photo_manager.sort_by = sort_by

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
        for col in ['exif_capture_time', 'creation_time', 'new_time']:
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


class BulkTagRequest(BaseModel):
    indices: list[int]
    tagged: bool


@app.post("/api/photos/bulk-tag")
async def bulk_tag(request: BulkTagRequest):
    """Tag multiple photos at once"""
    try:
        for index in request.indices:
            photo_manager.update_tag(index, request.tagged)
        return {"success": True, "count": len(request.indices), "tagged": request.tagged}
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

@app.post("/api/apply-time-offset")
async def apply_time_offset(request: TimeOffsetRequest):
    """
    Apply a time offset to all, tagged, or not-updated photos
    """
    try:
        if photo_manager.pd_photo_info is None or len(photo_manager.pd_photo_info) == 0:
            return {"success": False, "detail": "No photos loaded"}
        
        count = photo_manager.apply_time_offset(request.offset, request.mode, gpx_manager)
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/apply-timezone-offset")
async def apply_timezone_offset(request: TimeOffsetRequest):
    """
    Apply a timezone offset to all or tagged photos and calculate GPS timestamps
    """
    try:
        if photo_manager.pd_photo_info is None or len(photo_manager.pd_photo_info) == 0:
            return {"success": False, "detail": "No photos loaded"}
        
        count = photo_manager.apply_timezone_offset(request.offset, request.mode)
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/photos/{index}/metadata")
async def update_photo_metadata(index: int, request: PhotoMetadataUpdate):
    """
    Update new_time, new_title, and/or new_offset_time for a specific photo
    """
    try:
        if photo_manager.pd_photo_info is None or index >= len(photo_manager.pd_photo_info):
            return {"success": False, "detail": "Invalid photo index"}
        
        photo_manager.update_photo_metadata(index, request.new_time, request.new_title, gpx_manager, request.new_offset_time)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/settings")
async def get_settings():
    """
    Get current application settings
    """
    return config_manager.get_all()

@app.post("/api/settings")
async def update_settings(request: SettingsUpdate):
    """
    Update application settings and persist to config file if auto_save is enabled
    """
    try:
        updates = {}
        
        if request.map_provider is not None:
            updates["map_provider"] = request.map_provider
        if request.elevation_service is not None:
            updates["elevation_service"] = request.elevation_service
        if request.filename_format is not None:
            updates["filename_format"] = request.filename_format
            photo_manager.set_filename_format(request.filename_format)
        if request.include_subfolders is not None:
            updates["include_subfolders"] = request.include_subfolders
        if request.sort_by is not None:
            updates["sort_by"] = request.sort_by
        if request.thumbnail_size is not None:
            updates["thumbnail_size"] = request.thumbnail_size
        if request.folder_path is not None:
            updates["folder_path"] = request.folder_path
        if request.export_folder is not None:
            updates["export_folder"] = request.export_folder
        if request.auto_save_config is not None:
            updates["auto_save_config"] = request.auto_save_config
        
        # Update config
        config_manager.update(updates)
        
        # Save to file if auto_save is enabled and config file is set
        if config_manager.get('auto_save_config', True):
            config_manager.save()
        
        return {"success": True, "settings": config_manager.get_all()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/config/save")
async def save_config():
    """
    Manually save configuration to current config file
    """
    try:
        if not config_manager.config_file:
            return {"success": False, "detail": "No config file specified"}
        
        success = config_manager.save()
        return {
            "success": success,
            "file_path": str(config_manager.config_file) if success else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/config/save-as")
async def save_config_as(request: ConfigSaveAsRequest):
    """
    Save configuration to a new file
    """
    try:
        success = config_manager.save_as(request.file_path)
        return {
            "success": success,
            "file_path": str(config_manager.config_file) if success else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/config/download")
async def download_config():
    """
    Download current configuration as YAML file
    """
    try:
        import yaml
        from io import BytesIO
        
        # Get current config
        config_data = config_manager.get_all()
        
        # Convert to YAML
        yaml_content = yaml.dump(config_data, default_flow_style=False, sort_keys=False)
        
        # Return as downloadable file
        return Response(
            content=yaml_content,
            media_type="application/x-yaml",
            headers={
                "Content-Disposition": "attachment; filename=config.yaml"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/config/info")
async def get_config_info():
    """
    Get information about the current config file
    """
    return {
        "has_config_file": config_manager.config_file is not None,
        "config_file_path": str(config_manager.config_file) if config_manager.config_file else None,
        "auto_save_enabled": config_manager.get('auto_save_config', True)
    }



@app.post("/api/export")
async def export_photos(request: ExportRequest):
    """
    Export photos with updated metadata - streaming progress updates
    """
    import json
    import asyncio
    
    async def generate():
        try:
            # Get export folder from config
            export_folder = config_manager.get('export_folder', '')
            
            if not export_folder:
                data = {"error": "Export folder not configured"}
                yield f"data: {json.dumps(data)}\n\n"
                return
            
            # Get photos to export
            if request.export_type == 'tagged':
                photos_df = photo_manager.get_photos('tagged')
            else:  # 'all'
                photos_df = photo_manager.get_photos('all')
            
            if photos_df.empty:
                data = {"progress": 100, "current": 0, "total": 0, "message": "No photos to export", "done": True}
                yield f"data: {json.dumps(data)}\n\n"
                return
            
            total_photos = len(photos_df)
            
            # Check for filename conflicts before starting export
            export_path = Path(export_folder)
            conflicts = []
            
            for idx, row in photos_df.iterrows():
                photo = row.to_dict()
                new_filename = photo.get('new_name') or photo.get('filename')
                dest_file = export_path / new_filename
                
                if dest_file.exists():
                    conflicts.append(new_filename)
            
            # If there are conflicts, report error and don't export anything
            if conflicts:
                conflict_list = ", ".join(conflicts[:5])  # Show first 5
                if len(conflicts) > 5:
                    conflict_list += f" and {len(conflicts) - 5} more"
                error_msg = f"Export cancelled: {len(conflicts)} file(s) already exist in destination folder: {conflict_list}"
                data = {"error": error_msg}
                yield f"data: {json.dumps(data)}\n\n"
                return
            
            # Export each photo
            exported_count = 0
            failed_photos = []
            
            for idx, row in photos_df.iterrows():
                photo = row.to_dict()
                # Get the new filename or use original
                new_filename = photo.get('new_name') or photo.get('filename')
                
                # Send progress update
                progress = int((exported_count / total_photos) * 100)
                data = {"progress": progress, "current": exported_count + 1, "total": total_photos, "filename": new_filename}
                yield f"data: {json.dumps(data)}\n\n"
                
                # Get the new time or use original
                new_time = None
                if photo.get('new_time') and pd.notna(photo['new_time']):
                    new_time = photo['new_time']
                elif photo.get('exif_capture_time') and pd.notna(photo['exif_capture_time']):
                    new_time = photo['exif_capture_time']
                
                # Get final GPS coordinates
                final_lat = photo.get('final_latitude', -360)
                final_lon = photo.get('final_longitude', -360)
                final_alt = photo.get('final_altitude')
                
                # Only pass valid GPS coordinates
                if final_lat == -360 or final_lon == -360:
                    final_lat = None
                    final_lon = None
                    final_alt = None
                
                # Export the photo
                success = ExportManager.export_photo(
                    source_path=photo['full_path'],
                    dest_folder=export_folder,
                    new_filename=new_filename,
                    final_lat=final_lat,
                    final_lon=final_lon,
                    final_alt=final_alt,
                    new_time=new_time
                )
                
                if success:
                    exported_count += 1
                else:
                    failed_photos.append(photo['filename'])
                
                # Small delay to ensure progress updates are sent
                await asyncio.sleep(0.01)
            
            # Send final completion message
            message = f"Exported {exported_count} photos"
            if failed_photos:
                message += f". Failed: {len(failed_photos)} photos"
            
            data = {"progress": 100, "current": total_photos, "total": total_photos, "message": message, "done": True, "count": exported_count, "failed": len(failed_photos)}
            yield f"data: {json.dumps(data)}\n\n"
            
        except Exception as e:
            data = {"error": str(e)}
            yield f"data: {json.dumps(data)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
