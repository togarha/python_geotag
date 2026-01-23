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
        self.filename_format: str = "%Y%m%d_%H%M%S"  # Default format for new filenames
        
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
        self._deduplicate_filenames()
        self._apply_sort()
        
        return self.pd_photo_info
    
    def _extract_photo_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract photo information including EXIF data"""
        info = {
            'filename': file_path.name,
            'full_path': str(file_path),
            'exif_capture_time': None,
            'creation_time': datetime.fromtimestamp(file_path.stat().st_ctime),
            'new_time': None,
            'exif_image_title': None,
            'new_title': None,
            'exif_latitude': -360.0,
            'exif_longitude': -360.0,
            'exif_altitude': None,
            'gpx_latitude': -360.0,
            'gpx_longitude': -360.0,
            'gpx_altitude': None,
            'manual_latitude': -360.0,
            'manual_longitude': -360.0,
            'manual_altitude': None,
            'final_latitude': -360.0,
            'final_longitude': -360.0,
            'final_altitude': None,
            'new_name': '',
            'tagged': False
        }
        
        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    # Extract capture time and image title
                    # First pass: look for ImageDescription (highest priority)
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        if tag == 'DateTimeOriginal' or tag == 'DateTime':
                            try:
                                info['exif_capture_time'] = datetime.strptime(
                                    value, '%Y:%m:%d %H:%M:%S'
                                )
                            except:
                                pass
                        
                        # Extract image title - prioritize ImageDescription for cross-platform compatibility
                        if tag == 'ImageDescription':
                            if value and str(value).strip():
                                info['exif_image_title'] = str(value).strip()
                    
                    # If no ImageDescription found, try Windows-specific tags as fallback
                    if not info['exif_image_title']:
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)
                            
                            if tag in ['XPTitle', 'XPComment']:
                                if value:
                                    # XPTitle/XPComment are stored as bytes, need to decode
                                    if isinstance(value, bytes):
                                        try:
                                            decoded = value.decode('utf-16le').rstrip('\x00').strip()
                                            if decoded:
                                                info['exif_image_title'] = decoded
                                                break
                                        except:
                                            pass
                    
                    # Extract GPS data
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
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
                            
                            # Extract altitude
                            if 'GPSAltitude' in gps_data:
                                try:
                                    altitude = float(gps_data['GPSAltitude'])
                                    # GPSAltitudeRef: 0 = above sea level, 1 = below sea level
                                    if gps_data.get('GPSAltitudeRef', 0) == 1:
                                        altitude = -altitude
                                    info['exif_altitude'] = altitude
                                except:
                                    pass
        except Exception as e:
            print(f"Error reading EXIF from {file_path}: {e}")
        
        # Use creation time if no EXIF capture time
        if info['exif_capture_time'] is None:
            info['exif_capture_time'] = info['creation_time']
        
        # Keep new_time and new_title as None (will be set when user modifies them)
        # info['new_time'] remains None
        # info['new_title'] remains None
        
        # Initialize final coordinates with EXIF values
        info['final_latitude'] = info['exif_latitude']
        info['final_longitude'] = info['exif_longitude']
        info['final_altitude'] = info['exif_altitude']
        
        # Generate new filename based on current format
        info['new_name'] = self._generate_new_filename_from_info(info)
        
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
        for key in ['exif_capture_time', 'creation_time', 'new_time']:
            if pd.notna(photo[key]):
                photo[key] = photo[key].isoformat()
        
        # Convert nan to None for altitude fields (JSON cannot serialize nan)
        for key in ['exif_altitude', 'gpx_altitude', 'manual_altitude', 'final_altitude']:
            if pd.isna(photo.get(key)):
                photo[key] = None
        
        return photo
    
    def update_tag(self, index: int, tagged: bool):
        """Update the tagged status of a photo"""
        if self.pd_photo_info is None or index >= len(self.pd_photo_info):
            raise ValueError("Invalid photo index")
        
        self.pd_photo_info.at[index, 'tagged'] = tagged
    
    def update_manual_location(self, index: int, latitude: float, longitude: float, altitude: float = None):
        """Update manual GPS coordinates"""
        if self.pd_photo_info is None or index >= len(self.pd_photo_info):
            raise ValueError("Invalid photo index")
        
        self.pd_photo_info.at[index, 'manual_latitude'] = latitude
        self.pd_photo_info.at[index, 'manual_longitude'] = longitude
        self.pd_photo_info.at[index, 'manual_altitude'] = altitude
        # Update final coordinates to manual values
        self.pd_photo_info.at[index, 'final_latitude'] = latitude
        self.pd_photo_info.at[index, 'final_longitude'] = longitude
        self.pd_photo_info.at[index, 'final_altitude'] = altitude
    
    def delete_manual_location(self, index: int):
        """Delete manual GPS coordinates"""
        if self.pd_photo_info is None or index >= len(self.pd_photo_info):
            raise ValueError("Invalid photo index")
        
        self.pd_photo_info.at[index, 'manual_latitude'] = -360.0
        self.pd_photo_info.at[index, 'manual_longitude'] = -360.0
        self.pd_photo_info.at[index, 'manual_altitude'] = None
        
        # Update final coordinates: fallback to GPX if exists, otherwise EXIF
        gpx_lat = self.pd_photo_info.at[index, 'gpx_latitude']
        gpx_lon = self.pd_photo_info.at[index, 'gpx_longitude']
        
        if gpx_lat != -360.0 and gpx_lon != -360.0:
            self.pd_photo_info.at[index, 'final_latitude'] = gpx_lat
            self.pd_photo_info.at[index, 'final_longitude'] = gpx_lon
            self.pd_photo_info.at[index, 'final_altitude'] = self.pd_photo_info.at[index, 'gpx_altitude']
        else:
            self.pd_photo_info.at[index, 'final_latitude'] = self.pd_photo_info.at[index, 'exif_latitude']
            self.pd_photo_info.at[index, 'final_longitude'] = self.pd_photo_info.at[index, 'exif_longitude']
            self.pd_photo_info.at[index, 'final_altitude'] = self.pd_photo_info.at[index, 'exif_altitude']
    
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
                    self.pd_photo_info.at[index, 'gpx_altitude'] = closest_point.get('elevation')
                    
                    # Update final coordinates if no manual position exists
                    manual_lat = self.pd_photo_info.at[index, 'manual_latitude']
                    if manual_lat == -360.0:
                        # Priority: manual > gpx > exif
                        self.pd_photo_info.at[index, 'final_latitude'] = closest_point['latitude']
                        self.pd_photo_info.at[index, 'final_longitude'] = closest_point['longitude']
                        self.pd_photo_info.at[index, 'final_altitude'] = closest_point.get('elevation')
                else:
                    # Clear GPX coordinates if no match found
                    self.pd_photo_info.at[index, 'gpx_latitude'] = -360.0
                    self.pd_photo_info.at[index, 'gpx_longitude'] = -360.0
                    self.pd_photo_info.at[index, 'gpx_altitude'] = None
                    
                    # Update final coordinates if no manual position
                    manual_lat = self.pd_photo_info.at[index, 'manual_latitude']
                    if manual_lat == -360.0:
                        # Fall back to EXIF
                        exif_lat = self.pd_photo_info.at[index, 'exif_latitude']
                        if exif_lat != -360.0:
                            self.pd_photo_info.at[index, 'final_latitude'] = exif_lat
                            self.pd_photo_info.at[index, 'final_longitude'] = self.pd_photo_info.at[index, 'exif_longitude']
                            self.pd_photo_info.at[index, 'final_altitude'] = self.pd_photo_info.at[index, 'exif_altitude']
                        else:
                            self.pd_photo_info.at[index, 'final_latitude'] = -360.0
                            self.pd_photo_info.at[index, 'final_longitude'] = -360.0
                            self.pd_photo_info.at[index, 'final_altitude'] = None
    
    def preview_rename_format(self, format_str: str, max_count: int = 20) -> list:
        """
        Preview what filenames would look like with the given format
        Returns list of {old_name, new_name} dicts for first max_count photos
        """
        if self.pd_photo_info is None or len(self.pd_photo_info) == 0:
            return []
        
        previews = []
        count = min(max_count, len(self.pd_photo_info))
        
        for index in range(count):
            old_name = self.pd_photo_info.at[index, 'filename']
            new_name = self._generate_new_filename(index, format_str)
            
            previews.append({
                'old_name': old_name,
                'new_name': new_name
            })
        
        return previews
    
    def apply_rename_format(self, format_str: str) -> int:
        """
        Apply the filename format to all photos (updates new_name column)
        Returns count of photos updated
        """
        if self.pd_photo_info is None or len(self.pd_photo_info) == 0:
            return 0
        
        # Update the stored format
        self.filename_format = format_str
        
        for index in range(len(self.pd_photo_info)):
            new_name = self._generate_new_filename(index, format_str)
            self.pd_photo_info.at[index, 'new_name'] = new_name
        
        # Deduplicate filenames to avoid conflicts
        self._deduplicate_filenames()
        
        return len(self.pd_photo_info)
    
    def apply_photo_title(self, title: str) -> int:
        """
        Apply a title to all photos (updates new_title column)
        Returns count of photos updated
        """
        if self.pd_photo_info is None or len(self.pd_photo_info) == 0:
            return 0
        
        for index in range(len(self.pd_photo_info)):
            self.pd_photo_info.at[index, 'new_title'] = title
        
        return len(self.pd_photo_info)
    
    def apply_photo_title_tagged(self, title: str) -> int:
        """
        Apply a title to tagged photos only (updates new_title column)
        Returns count of photos updated
        """
        if self.pd_photo_info is None or len(self.pd_photo_info) == 0:
            return 0
        
        count = 0
        for index in range(len(self.pd_photo_info)):
            if self.pd_photo_info.at[index, 'tagged']:
                self.pd_photo_info.at[index, 'new_title'] = title
                count += 1
        
        return count
    
    def clear_photo_titles(self) -> int:
        """
        Clear all new_title values (set to None)
        Returns count of photos updated
        """
        if self.pd_photo_info is None or len(self.pd_photo_info) == 0:
            return 0
        
        for index in range(len(self.pd_photo_info)):
            self.pd_photo_info.at[index, 'new_title'] = None
        
        return len(self.pd_photo_info)
    
    def update_photo_metadata(self, index: int, new_time: str = None, new_title: str = None) -> bool:
        """
        Update new_time and/or new_title for a specific photo
        Args:
            index: Photo index
            new_time: ISO format datetime string or None to keep unchanged
            new_title: Title string or None to keep unchanged
        Returns:
            True if successful
        """
        if self.pd_photo_info is None or index >= len(self.pd_photo_info):
            raise ValueError("Invalid photo index")
        
        if new_time is not None:
            if new_time == "":  # Empty string means clear/set to None
                self.pd_photo_info.at[index, 'new_time'] = None
            else:
                # Parse ISO format datetime
                try:
                    dt = datetime.fromisoformat(new_time.replace('Z', '+00:00'))
                    self.pd_photo_info.at[index, 'new_time'] = dt
                except:
                    raise ValueError("Invalid datetime format")
        
        if new_title is not None:
            # Keep empty string as empty string (don't convert to None)
            self.pd_photo_info.at[index, 'new_title'] = new_title
        
        return True
    
    def get_filename_format(self) -> str:
        """Get the current filename format"""
        return self.filename_format
    
    def _deduplicate_filenames(self):
        """
        Handle duplicate filenames by appending letters (a, b, c, etc.)
        Comparison is case-insensitive for Windows compatibility
        """
        if self.pd_photo_info is None or len(self.pd_photo_info) == 0:
            return
        
        # Create a temporary column with lowercase names for grouping
        self.pd_photo_info['_temp_lower_name'] = self.pd_photo_info['new_name'].str.lower()
        
        # Group by lowercase name to find duplicates
        name_groups = self.pd_photo_info.groupby('_temp_lower_name', sort=False)
        
        for lower_name, group in name_groups:
            if len(group) > 1:
                # Multiple photos have the same name (case-insensitive)
                # Append letters a, b, c, etc. to all but the first
                for i, idx in enumerate(group.index):
                    if i > 0:  # Skip the first one (keep original name)
                        old_name = self.pd_photo_info.at[idx, 'new_name']
                        # Split name and extension
                        name_path = Path(old_name)
                        base_name = name_path.stem
                        extension = name_path.suffix
                        
                        # Append letter (a, b, c, etc.)
                        # chr(97) is 'a', chr(98) is 'b', etc.
                        letter = chr(96 + i)  # 96 + 1 = 97 = 'a'
                        new_name = f"{base_name}{letter}{extension}"
                        
                        self.pd_photo_info.at[idx, 'new_name'] = new_name
                        # Update the temporary lowercase column too
                        self.pd_photo_info.at[idx, '_temp_lower_name'] = new_name.lower()
        
        # Remove the temporary column
        self.pd_photo_info.drop(columns=['_temp_lower_name'], inplace=True)
    
    def _generate_new_filename_from_info(self, info: Dict[str, Any]) -> str:
        """
        Generate new filename from photo info dict (used during scanning)
        Uses EXIF capture time if available, otherwise file creation time
        """
        # Get the timestamp to use
        capture_time = info['exif_capture_time']
        
        if capture_time is None or pd.isna(capture_time):
            # Fall back to creation time
            capture_time = info['creation_time']
        
        # Get the original file extension
        old_filename = info['filename']
        extension = Path(old_filename).suffix
        
        # Format the timestamp according to the format string
        try:
            new_base_name = capture_time.strftime(self.filename_format)
            new_filename = f"{new_base_name}{extension}"
        except Exception as e:
            # If format is invalid, return original filename
            print(f"Error formatting filename: {e}")
            new_filename = old_filename
        
        return new_filename
    
    def _generate_new_filename(self, index: int, format_str: str) -> str:
        """
        Generate new filename for a photo based on format string
        Uses EXIF capture time if available, otherwise file creation time
        """
        # Get the timestamp to use
        capture_time = self.pd_photo_info.at[index, 'exif_capture_time']
        
        if capture_time is None or pd.isna(capture_time):
            # Fall back to creation time
            capture_time = self.pd_photo_info.at[index, 'creation_time']
        
        # Get the original file extension
        old_filename = self.pd_photo_info.at[index, 'filename']
        extension = Path(old_filename).suffix
        
        # Format the timestamp according to the format string
        try:
            new_base_name = capture_time.strftime(format_str)
            new_filename = f"{new_base_name}{extension}"
        except Exception as e:
            # If format is invalid, return original filename
            print(f"Error formatting filename: {e}")
            new_filename = old_filename
        
        return new_filename
