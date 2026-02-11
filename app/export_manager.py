"""
Photo export functionality with EXIF and file attribute updates
"""
import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import contextmanager
import piexif
from iptcinfo3 import IPTCInfo

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


@contextmanager
def suppress_stderr():
    """Context manager to temporarily suppress stderr output"""
    original_stderr = sys.stderr
    try:
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        sys.stderr.close()
        sys.stderr = original_stderr


class ExportManager:
    """Manages photo export with metadata updates"""
    
    @staticmethod
    def export_photo(source_path: str, dest_folder: str, new_filename: str,
                    final_lat: Optional[float] = None, final_lon: Optional[float] = None, 
                    final_alt: Optional[float] = None,
                    new_time: Optional[datetime] = None,
                    title: Optional[str] = None,
                    keywords: Optional[str] = None,
                    city: Optional[str] = None, sublocation: Optional[str] = None,
                    state: Optional[str] = None, country: Optional[str] = None,
                    gps_datestamp: Optional[str] = None, gps_timestamp: Optional[str] = None,
                    offset_time: Optional[str] = None) -> bool:
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
            title: Photo title for XMP metadata
            keywords: Photo keywords for IPTC/XMP metadata
            city: City for IPTC/XMP metadata
            sublocation: Sub-location for IPTC/XMP metadata
            state: State/Province for IPTC/XMP metadata
            country: Country for IPTC/XMP metadata
            gps_datestamp: GPS date stamp (YYYY:MM:DD)
            gps_timestamp: GPS time stamp (HH:MM:SS)
            offset_time: Timezone offset (+HH:MM or -HH:MM)
            
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
            ExportManager._update_exif(str(dest_file), final_lat, final_lon, final_alt, new_time,
                                      title, keywords, city, sublocation, state, country,
                                      gps_datestamp, gps_timestamp, offset_time)
            
            # Update file timestamps AFTER EXIF update (if new_time is provided)
            if new_time:
                ExportManager._set_file_times(dest_file, new_time)
            
            return True
            
        except Exception as e:
            print(f"Error exporting photo {source_path}: {e}")
            return False
    
    @staticmethod
    def _update_exif(file_path: str, latitude: Optional[float], longitude: Optional[float], 
                    altitude: Optional[float], capture_time: Optional[datetime],
                    title: Optional[str] = None,
                    keywords: Optional[str] = None,
                    city: Optional[str] = None, sublocation: Optional[str] = None,
                    state: Optional[str] = None, country: Optional[str] = None,
                    gps_datestamp: Optional[str] = None, gps_timestamp: Optional[str] = None,
                    offset_time: Optional[str] = None):
        """
        Update EXIF data, IPTC location metadata, and XMP metadata in the exported photo without recompressing the image
        """
        try:
            # Load existing EXIF directly from file
            try:
                exif_dict = piexif.load(file_path)
            except:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
            
            # Clean up problematic EXIF tags that may have wrong types
            # Tag 41729 (ComponentsConfiguration) and similar tags can cause issues
            if "Exif" in exif_dict:
                exif_ifd = exif_dict["Exif"]
                # Remove tags that commonly have type issues
                problematic_tags = [41729, 41730]  # ComponentsConfiguration, ComponentsConfiguration
                for tag in problematic_tags:
                    if tag in exif_ifd:
                        # Check if it's the wrong type and fix or remove it
                        if isinstance(exif_ifd[tag], int):
                            del exif_ifd[tag]
            
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
                
                # Add GPS date/time stamps if provided
                if gps_datestamp:
                    gps_ifd[piexif.GPSIFD.GPSDateStamp] = gps_datestamp.encode('ascii')
                
                if gps_timestamp:
                    # Parse HH:MM:SS and convert to rational tuple format
                    try:
                        parts = gps_timestamp.split(':')
                        if len(parts) == 3:
                            hours = (int(parts[0]), 1)
                            minutes = (int(parts[1]), 1)
                            seconds = (int(parts[2]), 1)
                            gps_ifd[piexif.GPSIFD.GPSTimeStamp] = (hours, minutes, seconds)
                    except Exception as e:
                        print(f"Warning: Error parsing GPS timestamp: {e}")
                
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
            
            # Note: OffsetTime tags (36880, 36881, 36882) are not supported by piexif
            # They will be written separately using exiftool after main EXIF is complete
            
            # Insert updated EXIF into the file without recompressing the image
            try:
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, file_path)
            except Exception as dump_error:
                # If dump fails, try fallback with minimal EXIF
                print(f"Warning: EXIF dump failed ({dump_error}), trying fallback")
                
                try:
                    # Try removing problematic EXIF tags
                    exif_bytes = piexif.dump(exif_dict)
                    piexif.insert(exif_bytes, file_path)
                except Exception as second_error:
                    # If still failing, rebuild from scratch
                    print(f"Warning: EXIF dump still failed ({second_error}), rebuilding EXIF from scratch")
                    piexif.remove(file_path)
                    
                    # Create minimal EXIF dict with all important fields
                    minimal_exif = {"0th": {}, "Exif": {}, "GPS": {}}
                    
                    # Copy ALL GPS data (including date/time stamps)
                    if latitude is not None and longitude is not None and latitude != -360 and longitude != -360:
                        minimal_exif["GPS"] = exif_dict.get("GPS", {})
                    
                    # Copy datetime fields (but NOT offset time)
                    if capture_time:
                        exif_ifd = exif_dict.get("Exif", {})
                        minimal_exif["Exif"] = {
                            k: v for k, v in exif_ifd.items() 
                            if k in [piexif.ExifIFD.DateTimeOriginal, piexif.ExifIFD.DateTimeDigitized]
                        }
                        
                        zeroth_ifd = exif_dict.get("0th", {})
                        minimal_exif["0th"] = {
                            k: v for k, v in zeroth_ifd.items() 
                            if k in [piexif.ImageIFD.DateTime]
                        }
                    
                    # Insert the minimal EXIF
                    exif_bytes = piexif.dump(minimal_exif)
                    piexif.insert(exif_bytes, file_path)
            
            # Update IPTC location metadata if any location field is provided
            if any([keywords, city, sublocation, state, country]):
                try:
                    # Try to load existing IPTC data first
                    try:
                        with suppress_stderr():
                            iptc = IPTCInfo(file_path, force=False)
                            
                            # Set keywords
                            if keywords and keywords.strip():
                                # Keywords can be comma-separated
                                keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
                                iptc['keywords'] = keyword_list
                            
                            # Set location fields
                            if city and city.strip():
                                iptc['city'] = city
                            if sublocation and sublocation.strip():
                                iptc['sub-location'] = sublocation
                            if state and state.strip():
                                iptc['province/state'] = state
                            if country and country.strip():
                                iptc['country/primary location name'] = country
                            
                            # Try to save - this may fail if IPTC data is corrupt
                            iptc.save(['overwrite'])
                    except:
                        # If loading or saving fails (corrupt IPTC data), rebuild from scratch
                        with suppress_stderr():
                            iptc = IPTCInfo(file_path, force=True)
                            
                            # Set keywords
                            if keywords and keywords.strip():
                                keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
                                iptc['keywords'] = keyword_list
                            
                            # Set location fields again
                            if city and city.strip():
                                iptc['city'] = city
                            if sublocation and sublocation.strip():
                                iptc['sub-location'] = sublocation
                            if state and state.strip():
                                iptc['province/state'] = state
                            if country and country.strip():
                                iptc['country/primary location name'] = country
                            
                            # Save with fresh IPTC data
                            iptc.save(['overwrite'])
                except Exception as iptc_error:
                    # IPTC writing is optional - don't fail the entire export if it doesn't work
                    pass
            
            # Write XMP metadata and OffsetTime using exiftool (piexif doesn't support these)
            ExportManager._write_exiftool_metadata(file_path, title, keywords, city, sublocation, state, country, offset_time)
            
        except Exception as e:
            print(f"Error updating EXIF for {file_path}: {e}")
    
    @staticmethod
    def _write_exiftool_metadata(file_path: str, title: Optional[str] = None,
                                 keywords: Optional[str] = None,
                                 city: Optional[str] = None, sublocation: Optional[str] = None,
                                 state: Optional[str] = None, country: Optional[str] = None,
                                 offset_time: Optional[str] = None):
        """
        Write XMP metadata and OffsetTime EXIF tags using exiftool
        (piexif doesn't support XMP or OffsetTime tags)
        Falls back gracefully if exiftool is not available
        
        XMP Tags written:
        - dc:title (Dublin Core title)
        - dc:subject (Dublin Core keywords, multi-valued)
        - pdf:Keywords (Adobe PDF keywords, comma-separated string)
        - iptc4xmpCore:Location (IPTC Extension sublocation)
        - photoshop:City (Adobe Photoshop city)
        - photoshop:State (Adobe Photoshop state)
        - photoshop:Country (Adobe Photoshop country)
        """
        try:
            # Check if exiftool is available
            result = subprocess.run(
                ['exiftool', '-ver'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode != 0:
                return  # exiftool not available, skip silently
            
            # Build command with all metadata to write
            # -overwrite_original avoids creating backup files
            cmd = ['exiftool', '-overwrite_original']
            
            # Add OffsetTime tags if provided
            if offset_time:
                cmd.extend([
                    f'-OffsetTime={offset_time}',
                    f'-OffsetTimeOriginal={offset_time}',
                    f'-OffsetTimeDigitized={offset_time}'
                ])
            
            # Add XMP title (Dublin Core)
            if title and title.strip():
                cmd.append(f'-XMP:Title={title}')
            
            # Add XMP keywords (Dublin Core subject)
            if keywords and keywords.strip():
                # Keywords can be comma-separated
                keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
                for keyword in keyword_list:
                    cmd.append(f'-XMP:Subject+={keyword}')
                
                # Also add to PDF namespace Keywords field (single comma-separated string)
                cmd.append(f'-XMP-pdf:Keywords={keywords.strip()}')
            
            # Add XMP location metadata (IPTC4XMP and Photoshop namespaces)
            if sublocation and sublocation.strip():
                cmd.append(f'-XMP:Location={sublocation}')
            if city and city.strip():
                cmd.append(f'-XMP:City={city}')
            if state and state.strip():
                cmd.append(f'-XMP:State={state}')
            if country and country.strip():
                cmd.append(f'-XMP:Country={country}')
            
            # Add the file path
            cmd.append(file_path)
            
            # Only run exiftool if we have metadata to write
            if len(cmd) > 3:  # More than just 'exiftool -overwrite_original filepath'
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                # Only report errors, not success
                if result.returncode != 0:
                    print(f"Warning: exiftool failed: {result.stderr}")
                    
        except FileNotFoundError:
            # exiftool not installed, skip silently
            pass
        except subprocess.TimeoutExpired:
            print(f"Warning: exiftool timed out")
        except Exception as e:
            print(f"Warning: Error writing exiftool metadata: {e}")
    
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
