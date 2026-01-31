"""
Photo export functionality with EXIF and file attribute updates
"""
import os
import shutil
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional
import piexif

# Windows-specific imports for setting creation time
if platform.system() == 'Windows':
    try:
        import pywintypes
        import win32file
        import win32con
        WINDOWS_TIMESTAMP_SUPPORT = True
    except ImportError:
        WINDOWS_TIMESTAMP_SUPPORT = False
else:
    WINDOWS_TIMESTAMP_SUPPORT = False


class ExportManager:
    """Manages photo export with metadata updates"""
    
    @staticmethod
    def export_photo(source_path: str, dest_folder: str, new_filename: str,
                    final_lat: Optional[float] = None, final_lon: Optional[float] = None, 
                    final_alt: Optional[float] = None,
                    new_time: Optional[datetime] = None) -> bool:
        """
        Export a photo with updated EXIF and file attributes
        
        Args:
            source_path: Original photo path
            dest_folder: Destination folder
            new_filename: New filename (without path)
            final_lat: Final latitude (or None to keep original)
            final_lon: Final longitude (or None to keep original)
            final_alt: Final altitude (or None to keep original)
            new_time: New capture time (or None to keep original)
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Create destination folder if it doesn't exist
            dest_path = Path(dest_folder)
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Full destination path
            dest_file = dest_path / new_filename
            
            # Copy the file (use copy instead of copy2 to avoid preserving metadata)
            shutil.copy(source_path, dest_file)
            
            # Update EXIF data (this will re-save the file, potentially resetting timestamps)
            ExportManager._update_exif(str(dest_file), final_lat, final_lon, final_alt, new_time)
            
            # Update file timestamps AFTER EXIF update (if new_time is provided)
            if new_time:
                ExportManager._set_file_times(dest_file, new_time)
            
            return True
            
        except Exception as e:
            print(f"Error exporting photo {source_path}: {e}")
            return False
    
    @staticmethod
    def _update_exif(file_path: str, latitude: Optional[float], longitude: Optional[float], 
                    altitude: Optional[float], capture_time: Optional[datetime]):
        """Update EXIF data in the exported photo without recompressing the image"""
        try:
            # Load existing EXIF directly from file
            try:
                exif_dict = piexif.load(file_path)
            except:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
            
            # Update GPS coordinates if provided
            if latitude is not None and longitude is not None and latitude != -360 and longitude != -360:
                gps_ifd = exif_dict.get("GPS", {})
                
                # Convert latitude
                lat_deg = int(abs(latitude))
                lat_min = int((abs(latitude) - lat_deg) * 60)
                lat_sec = int(((abs(latitude) - lat_deg) * 60 - lat_min) * 60 * 100)
                gps_ifd[piexif.GPSIFD.GPSLatitude] = ((lat_deg, 1), (lat_min, 1), (lat_sec, 100))
                gps_ifd[piexif.GPSIFD.GPSLatitudeRef] = 'N' if latitude >= 0 else 'S'
                
                # Convert longitude
                lon_deg = int(abs(longitude))
                lon_min = int((abs(longitude) - lon_deg) * 60)
                lon_sec = int(((abs(longitude) - lon_deg) * 60 - lon_min) * 60 * 100)
                gps_ifd[piexif.GPSIFD.GPSLongitude] = ((lon_deg, 1), (lon_min, 1), (lon_sec, 100))
                gps_ifd[piexif.GPSIFD.GPSLongitudeRef] = 'E' if longitude >= 0 else 'W'
                
                # Update altitude if provided
                if altitude is not None:
                    alt_rational = (int(abs(altitude) * 100), 100)
                    gps_ifd[piexif.GPSIFD.GPSAltitude] = alt_rational
                    gps_ifd[piexif.GPSIFD.GPSAltitudeRef] = 0 if altitude >= 0 else 1
                
                exif_dict["GPS"] = gps_ifd
            
            # Update capture time if provided
            if capture_time:
                exif_ifd = exif_dict.get("Exif", {})
                time_str = capture_time.strftime("%Y:%m:%d %H:%M:%S")
                exif_ifd[piexif.ExifIFD.DateTimeOriginal] = time_str.encode('utf-8')
                exif_ifd[piexif.ExifIFD.DateTimeDigitized] = time_str.encode('utf-8')
                exif_dict["Exif"] = exif_ifd
                
                # Also update the main DateTime
                zeroth_ifd = exif_dict.get("0th", {})
                zeroth_ifd[piexif.ImageIFD.DateTime] = time_str.encode('utf-8')
                exif_dict["0th"] = zeroth_ifd
            
            # Insert updated EXIF into the file without recompressing the image
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, file_path)
            
        except Exception as e:
            print(f"Error updating EXIF for {file_path}: {e}")
    
    @staticmethod
    def _set_file_times(file_path: Path, timestamp: datetime):
        """Set file creation, modification, and access times on all platforms"""
        try:
            ts = timestamp.timestamp()
            system = platform.system()
            
            # Platform-specific handling
            if system == 'Windows' and WINDOWS_TIMESTAMP_SUPPORT:
                # On Windows, set all three timestamps using Windows API
                ExportManager._set_all_times_windows(file_path, timestamp)
            elif system == 'Darwin':  # macOS
                ExportManager._set_creation_time_macos(file_path, timestamp)
                # Also set modification and access time
                os.utime(file_path, (ts, ts))
            else:  # Linux and fallback
                # Linux doesn't support setting creation time (birthtime) on most filesystems
                # Just set modification and access time
                os.utime(file_path, (ts, ts))
            
        except Exception as e:
            print(f"Error setting file times for {file_path}: {e}")
    
    @staticmethod
    def _set_all_times_windows(file_path: Path, timestamp: datetime):
        """Set creation, access, and modification times on Windows"""
        try:
            # Convert pandas Timestamp to Python datetime if necessary
            if hasattr(timestamp, 'to_pydatetime'):
                timestamp = timestamp.to_pydatetime()
            
            # Convert to Windows FILETIME format
            wintime = pywintypes.Time(timestamp)
            
            # Open the file handle with appropriate permissions
            handle = win32file.CreateFile(
                str(file_path),
                win32con.GENERIC_WRITE,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL,
                None
            )
            
            # Set all three times: creation, access, and modification
            # SetFileTime(handle, creation_time, access_time, modification_time)
            win32file.SetFileTime(handle, wintime, wintime, wintime)
            
            handle.close()
            
        except Exception as e:
            print(f"Warning: Could not set timestamps on Windows: {e}")
    

    
    @staticmethod
    def _set_creation_time_macos(file_path: Path, timestamp: datetime):
        """Set creation time on macOS using SetFile command"""
        try:
            # Format timestamp for SetFile command (MM/DD/YYYY HH:MM:SS)
            time_str = timestamp.strftime("%m/%d/%Y %H:%M:%S")
            
            # Try using SetFile command (part of Xcode command line tools)
            try:
                subprocess.run(
                    ['SetFile', '-d', time_str, str(file_path)],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # SetFile not available, try touch with -t flag as fallback
                # Format: [[CC]YY]MMDDhhmm[.SS]
                touch_time = timestamp.strftime("%Y%m%d%H%M.%S")
                try:
                    subprocess.run(
                        ['touch', '-t', touch_time, str(file_path)],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                except subprocess.CalledProcessError:
                    pass
                
        except Exception as e:
            print(f"Warning: Could not set creation time on macOS: {e}")
