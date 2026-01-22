"""
Photo Manager - Handles photo scanning, EXIF extraction, and DataFrame management
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import tempfile
import os
from typing import Optional, Dict, Any


class PhotoManager:
    def __init__(self):
        self.pd_photo_info: Optional[pd.DataFrame] = None
        self.current_folder: Optional[str] = None
        self.sort_by: str = "time"  # 'time' or 'name'
        self.thumbnail_cache = {}
        
    def scan_folder(self, folder_path: str, recursive: bool = False) -> pd.DataFrame:
        """Scan folder for photos and create pd_photo_info DataFrame"""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.heic'}
        
        if recursive:
            image_files = [f for f in folder.rglob('*') if f.suffix.lower() in image_extensions]
        else:
            image_files = [f for f in folder.glob('*') if f.suffix.lower() in image_extensions]
        
        # Create DataFrame
        photo_data = []
        for img_file in image_files:
            photo_info = self._extract_photo_info(img_file)
            photo_data.append(photo_info)
        
        self.pd_photo_info = pd.DataFrame(photo_data)
        self.current_folder = folder_path
        self._apply_sort()
        
        return self.pd_photo_info
    
    def _extract_photo_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract photo information including EXIF data"""
        info = {
            'filename': file_path.name,
            'full_path': str(file_path),
            'exif_capture_time': None,
            'creation_time': datetime.fromtimestamp(file_path.stat().st_ctime),
            'exif_latitude': -360.0,
            'exif_longitude': -360.0,
            'gpx_latitude': -360.0,
            'gpx_longitude': -360.0,
            'manual_latitude': -360.0,
            'manual_longitude': -360.0,
            'final_latitude': -360.0,
            'final_longitude': -360.0,
            'new_name': '',
            'tagged': False
        }
        
        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    # Extract capture time
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        if tag == 'DateTimeOriginal' or tag == 'DateTime':
                            try:
                                info['exif_capture_time'] = datetime.strptime(
                                    value, '%Y:%m:%d %H:%M:%S'
                                )
                            except:
                                pass
                        
                        # Extract GPS data
                        if tag == 'GPSInfo':
                            gps_data = {}
                            for gps_tag_id in value:
                                gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                gps_data[gps_tag] = value[gps_tag_id]
                            
                            # Convert GPS coordinates
                            lat = self._get_decimal_coordinates(
                                gps_data.get('GPSLatitude'),
                                gps_data.get('GPSLatitudeRef')
                            )
                            lon = self._get_decimal_coordinates(
                                gps_data.get('GPSLongitude'),
                                gps_data.get('GPSLongitudeRef')
                            )
                            
                            if lat is not None:
                                info['exif_latitude'] = lat
                            if lon is not None:
                                info['exif_longitude'] = lon
        except Exception as e:
            print(f"Error reading EXIF from {file_path}: {e}")
        
        # Use creation time if no EXIF capture time
        if info['exif_capture_time'] is None:
            info['exif_capture_time'] = info['creation_time']
        
        # Initialize final coordinates with EXIF values
        info['final_latitude'] = info['exif_latitude']
        info['final_longitude'] = info['exif_longitude']
        
        return info
    
    def _get_decimal_coordinates(self, coords, ref):
        """Convert GPS coordinates to decimal format"""
        if coords is None or ref is None:
            return None
        
        try:
            # Handle Fraction objects (common on Mac) by converting to float
            degrees = float(coords[0])
            minutes = float(coords[1])
            seconds = float(coords[2])
            
            decimal = degrees + minutes / 60 + seconds / 3600
            if ref in ['S', 'W']:
                decimal = -decimal
            return decimal
        except Exception as e:
            print(f"Error converting GPS coordinates: {e}")
            return None
    
    def get_photos(self, filter_type: str = "all") -> pd.DataFrame:
        """Get photos with optional filtering, maintaining current sort order"""
        if self.pd_photo_info is None or self.pd_photo_info.empty:
            return pd.DataFrame()
        
        df = self.pd_photo_info.copy()
        
        if filter_type == "tagged":
            df = df[df['tagged'] == True]
        elif filter_type == "untagged":
            df = df[df['tagged'] == False]
        
        return df
    
    def get_photo_by_index(self, index: int) -> Dict[str, Any]:
        """Get a specific photo by index"""
        if self.pd_photo_info is None or index >= len(self.pd_photo_info):
            raise ValueError("Invalid photo index")
        
        photo = self.pd_photo_info.iloc[index].to_dict()
        # Convert datetime to string for JSON serialization
        for key in ['exif_capture_time', 'creation_time']:
            if pd.notna(photo[key]):
                photo[key] = photo[key].isoformat()
        
        return photo
    
    def update_tag(self, index: int, tagged: bool):
        """Update the tagged status of a photo"""
        if self.pd_photo_info is None or index >= len(self.pd_photo_info):
            raise ValueError("Invalid photo index")
        
        self.pd_photo_info.at[index, 'tagged'] = tagged
    
    def update_manual_location(self, index: int, latitude: float, longitude: float):
        """Update manual GPS coordinates"""
        if self.pd_photo_info is None or index >= len(self.pd_photo_info):
            raise ValueError("Invalid photo index")
        
        self.pd_photo_info.at[index, 'manual_latitude'] = latitude
        self.pd_photo_info.at[index, 'manual_longitude'] = longitude
        # Update final coordinates to manual values
        self.pd_photo_info.at[index, 'final_latitude'] = latitude
        self.pd_photo_info.at[index, 'final_longitude'] = longitude
    
    def delete_manual_location(self, index: int):
        """Delete manual GPS coordinates"""
        if self.pd_photo_info is None or index >= len(self.pd_photo_info):
            raise ValueError("Invalid photo index")
        
        self.pd_photo_info.at[index, 'manual_latitude'] = -360.0
        self.pd_photo_info.at[index, 'manual_longitude'] = -360.0
        
        # Update final coordinates: fallback to GPX if exists, otherwise EXIF
        gpx_lat = self.pd_photo_info.at[index, 'gpx_latitude']
        gpx_lon = self.pd_photo_info.at[index, 'gpx_longitude']
        
        if gpx_lat != -360.0 and gpx_lon != -360.0:
            self.pd_photo_info.at[index, 'final_latitude'] = gpx_lat
            self.pd_photo_info.at[index, 'final_longitude'] = gpx_lon
        else:
            self.pd_photo_info.at[index, 'final_latitude'] = self.pd_photo_info.at[index, 'exif_latitude']
            self.pd_photo_info.at[index, 'final_longitude'] = self.pd_photo_info.at[index, 'exif_longitude']
    
    def update_gpx_location(self, index: int, latitude: float, longitude: float):
        """Update GPX-matched coordinates"""
        if self.pd_photo_info is None or index >= len(self.pd_photo_info):
            raise ValueError("Invalid photo index")
        
        self.pd_photo_info.at[index, 'gpx_latitude'] = latitude
        self.pd_photo_info.at[index, 'gpx_longitude'] = longitude
        
        # Update final coordinates to GPX values (only if no manual override)
        manual_lat = self.pd_photo_info.at[index, 'manual_latitude']
        if manual_lat == -360.0:  # No manual override
            self.pd_photo_info.at[index, 'final_latitude'] = latitude
            self.pd_photo_info.at[index, 'final_longitude'] = longitude
    
    def set_sort_order(self, sort_by: str):
        """Set the sort order and re-sort the DataFrame"""
        self.sort_by = sort_by
        # Clear thumbnail cache since indices will change after sorting
        self.thumbnail_cache.clear()
        self._apply_sort()
    
    def _apply_sort(self):
        """Apply the current sort order to the DataFrame"""
        if self.pd_photo_info is None or self.pd_photo_info.empty:
            return
        
        if self.sort_by == "name":
            self.pd_photo_info = self.pd_photo_info.sort_values('filename').reset_index(drop=True)
        else:  # time
            self.pd_photo_info = self.pd_photo_info.sort_values(
                ['exif_capture_time', 'creation_time']
            ).reset_index(drop=True)
    
    def get_thumbnail(self, index: int, size: int = 200) -> str:
        """Generate or retrieve cached thumbnail"""
        cache_key = f"{index}_{size}"
        
        if cache_key in self.thumbnail_cache:
            return self.thumbnail_cache[cache_key]
        
        photo = self.get_photo_by_index(index)
        img_path = Path(photo['full_path'])
        
        if not img_path.exists():
            raise ValueError(f"Image file not found: {img_path}")
        
        try:
            # Create thumbnail
            with Image.open(img_path) as img:
                # Convert to RGB if necessary (handles PNG, RGBA, etc.)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                
                # Save to temp file
                temp_dir = Path(tempfile.gettempdir()) / "geotag_thumbs"
                temp_dir.mkdir(exist_ok=True)
                
                thumb_path = temp_dir / f"{cache_key}_{img_path.stem}.jpg"
                img.save(thumb_path, "JPEG", quality=85)
                
                self.thumbnail_cache[cache_key] = str(thumb_path)
                return str(thumb_path)
        except Exception as e:
            print(f"Error creating thumbnail for {img_path}: {e}")
            raise ValueError(f"Failed to create thumbnail: {str(e)}")
    
    def match_all_photos_with_gpx(self, gpx_manager):
        """Match all photos with GPX data and update DataFrame"""
        if self.pd_photo_info is None or len(self.pd_photo_info) == 0:
            return
        
        if not gpx_manager.has_data():
            return
        
        for index in range(len(self.pd_photo_info)):
            capture_time = self.pd_photo_info.at[index, 'exif_capture_time']
            
            # Only try to match if photo has capture time and doesn't have manual position
            if capture_time is not None and pd.notna(capture_time):
                closest_point = gpx_manager.find_closest_point(capture_time)
                
                if closest_point:
                    self.pd_photo_info.at[index, 'gpx_latitude'] = closest_point['latitude']
                    self.pd_photo_info.at[index, 'gpx_longitude'] = closest_point['longitude']
                    
                    # Update final coordinates if no manual position exists
                    manual_lat = self.pd_photo_info.at[index, 'manual_latitude']
                    if manual_lat == -360.0:
                        # Priority: manual > gpx > exif
                        self.pd_photo_info.at[index, 'final_latitude'] = closest_point['latitude']
                        self.pd_photo_info.at[index, 'final_longitude'] = closest_point['longitude']
                else:
                    # Clear GPX coordinates if no match found
                    self.pd_photo_info.at[index, 'gpx_latitude'] = -360.0
                    self.pd_photo_info.at[index, 'gpx_longitude'] = -360.0
                    
                    # Update final coordinates if no manual position
                    manual_lat = self.pd_photo_info.at[index, 'manual_latitude']
                    if manual_lat == -360.0:
                        # Fall back to EXIF
                        exif_lat = self.pd_photo_info.at[index, 'exif_latitude']
                        if exif_lat != -360.0:
                            self.pd_photo_info.at[index, 'final_latitude'] = exif_lat
                            self.pd_photo_info.at[index, 'final_longitude'] = self.pd_photo_info.at[index, 'exif_longitude']
                        else:
                            self.pd_photo_info.at[index, 'final_latitude'] = -360.0
                            self.pd_photo_info.at[index, 'final_longitude'] = -360.0
