# Geotag - Photo Geotagging Application

A powerful web-based photo geotagging application built with Python and FastAPI. Organize, view, and geotag your photos using EXIF data, GPX tracks, and manual location assignment with dual map provider support.

## Features

### 📷 Photo Management
- **Folder Scanning**: Select folders via file picker or drag-and-drop
- **Recursive Search**: Include photos from subfolders
- **Smart Sorting**: Sort by capture time or filename with synchronized grid and list views
- **Filtering**: View all, tagged, or untagged photos with correct index tracking
- **Dual View**: List and grid thumbnail views synchronized in real-time
- **Adjustable Thumbnails**: Slide control for thumbnail size (100-400px)
- **Cache-Busting**: Automatic thumbnail and image refresh with timestamp parameters
- **Cross-Platform**: Works on Windows, Mac, and Linux with proper EXIF handling

### 🗺️ GPS & Geotagging
- **Dual Map Providers**: Switch between OpenStreetMap and Google Maps
- **EXIF GPS Extraction**: Automatically reads GPS coordinates from photo metadata (supports Fraction objects on Mac)
- **GPX Track Integration**: Load multiple GPX files with smart duplicate detection
- **Time Offset System**: Compensate timezone differences between GPX (UTC) and camera times
  - Main offset control applies to all tracks
  - Individual offset per track for fine-tuning
  - Format: ±hh:mm:ss (e.g., +02:00:00 for UTC+2)
- **Automatic Matching**: Photos matched to GPX tracks within ±5 minutes
- **GPX Track Management**: 
  - Files displayed as chips/pills with point count
  - Individual remove buttons for each track
  - Backend maintains track state across operations
- **Manual Geotagging**: Click on map to set custom locations with draggable markers
- **Four Coordinate Sources**:
  - 🔴 EXIF coordinates (from camera GPS)
  - 🔵 GPX matched coordinates (from track logs)
  - 🟡 Manual coordinates (user-defined, draggable)
  - 🟢 Final coordinates (cascade: Manual → GPX → EXIF)
- **Smart Coordinate Cascade**: Final location automatically updates based on priority
- **Zoom Preservation**: Map maintains zoom level when navigating photos or placing markers
- **Visual Marker Hierarchy**: Larger, semi-transparent final marker shows around smaller manual marker

### 🖼️ Photo Viewer
- **Large Photo View**: Full-size photo display with navigation
- **Keyboard Controls**: Arrow keys for navigation, Space to open, Escape to close
- **Tag Management**: Quick tagging with checkboxes (labels removed for cleaner UI)
- **EXIF Display**: Comprehensive metadata viewing
- **Interactive Map**: View and edit photo locations with dual map provider support
- **Real-time Updates**: Coordinate display updates immediately when placing or deleting markers
- **Marker Management**: Delete manual markers with automatic fallback to GPX or EXIF coordinates

### 🎨 User Interface
- **Expandable Menu**: Auto-expands on hover or click
- **Responsive Design**: Works on desktop and mobile
- **Modern UI**: Clean, intuitive interface with smooth animations
- **Three Main Views**:
  1. Photo Thumbnails View (with dual map provider)
  2. GPX View (with dual map provider)
  3. Large Photo View (modal with dual map provider)
- **Clean Checkboxes**: Tag checkboxes without distracting labels
- **Emoji Markers**: Proper UTF-8 emoji support (🔴 🔵 🟡 🟢) in legend

## Technology Stack

- **Backend**: FastAPI (Python web framework)
- **Data Management**: Pandas DataFrames with 14 columns including final coordinates
- **Image Processing**: Pillow (PIL) with RGB conversion and thumbnail caching
- **GPX Parsing**: gpxpy
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Maps**: 
  - OpenStreetMap via Leaflet 1.9.4
  - Google Maps JavaScript API
- **Package Manager**: uv (fast Python package manager)

## Installation

### Prerequisites
- Python 3.11 or higher
- uv package manager ([installation instructions](https://github.com/astral-sh/uv))
- Google Maps API key

### Setup Steps

1. **Clone or navigate to the project directory**:
   ```powershell
   cd c:\devel\geotag
   ```

2. **Install dependencies using uv**:
   ```powershell
   uv sync
   ```

3. **Configure Map Providers**:
   
   **For OpenStreetMap (Default)**:
   - No API key required - works out of the box!
   
   **For Google Maps (Optional)**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Maps JavaScript API
   - Create credentials (API Key)
   - Copy the API key
   - Open `templates\index.html` and replace `YOUR_GOOGLE_MAPS_API_KEY`:
     ```html
     <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_ACTUAL_API_KEY"></script>
     ```

**Note**: The application defaults to OpenStreetMap, which requires no API key. You only need a Google Maps API key if you want to use Google Maps as an alternative provider.

## Running the Application

### Start the server:
```powershell
uv run python main.py
```

The server will start at `http://127.0.0.1:8000`

### Access the application:
Open your web browser and navigate to:
```
http://127.0.0.1:8000
```

## Usage Guide

### Photo Thumbnails View

1. **Select a Folder**:
   - Click "📁 Select Folder" button, or
   - Drag and drop a folder onto the drop zone

2. **Configure Options**:
   - Check "Include subfolders" for recursive scanning
   - Select sort order (Capture Time or Name) - both grid and list update automatically
   - Choose filter (All Photos, Tagged Only, Untagged Only) - maintains correct photo indices
   - Adjust thumbnail size with the slider
   - Choose map provider (OpenStreetMap or Google Maps)

3. **Interact with Photos**:
   - Single click: Select a photo
   - Double click: Open in Large Photo View
   - Press Space: Open selected photo in Large Photo View
   - Click checkbox: Toggle tagged status (checkboxes update immediately across all views)

### GPX View

1. **Select GPX Files**:
   - Click "📂 Select GPX Files"
   - Choose one or more .gpx files
   - Duplicate files are automatically detected and skipped

2. **Configure Time Offset**:
   - Use main "Time Offset" control to set offset for all tracks (±hh:mm:ss format)
   - Click ✓ button to apply main offset to all loaded tracks
   - Or set individual offset per track using the control in each track chip

3. **Manage Loaded Tracks**:
   - View all loaded tracks in the "Loaded Tracks" panel below the map
   - Each track displays as a colored chip showing:
     - Track name
     - Point count
     - Individual time offset control
     - Remove button (×)
   - Remove individual tracks by clicking their × button

4. **View Tracks on Map**:
   - All tracks are displayed on the map in red
   - Map automatically centers to fit all tracks
   - Tracks update when offsets change or tracks are added/removed

5. **Switch Map Provider**:
   - Use the "Map:" dropdown to switch between OpenStreetMap and Google Maps
   - Tracks are redrawn automatically on the new map

### Large Photo View

1. **Navigation**:
   - Click ‹ / › buttons or use arrow keys
   - Photos maintain sort order from thumbnail view
   - Map preserves zoom level when navigating between photos

2. **Viewing Information**:
   - Left side: Full-size photo
   - Top right: EXIF metadata
   - Bottom right: Interactive location map with coordinate legend

3. **Map Provider Selection**:
   - Use the "Map:" dropdown to switch between OpenStreetMap and Google Maps
   - Current zoom and center position are maintained

4. **Coordinate Legend**:
   - 🔴 EXIF: GPS coordinates from camera
   - 🔵 GPX: Coordinates matched from GPX tracks
   - 🟡 Manual: User-set coordinates (draggable)
   - 🟢 Final: Active coordinates (follows cascade logic)

5. **Geotagging**:
   - View existing coordinates from all sources
   - Click anywhere on map to set manual location
   - Drag yellow marker to adjust position
   - Manual marker appears with green final marker ring around it
   - Click "🗑️ Delete Manual Marker" to remove manual location
   - Final coordinates automatically fall back to GPX or EXIF when manual is deleted

6. **Automatic GPX Matching**:
   - When a photo opens, if no GPX coordinates exist
   - System searches GPX tracks for points within ±5 minutes of capture time
   - Closest match is automatically assigned
   - Final coordinates update accordingly

## Data Structure

### pd_photo_info DataFrame
Stores all photo information with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| filename | string | Photo filename without path |
| full_path | string | Complete file path |
| exif_capture_time | datetime | Capture time from EXIF |
| creation_time | datetime | File creation time |
| exif_latitude | float | GPS latitude from EXIF (-360 if none) |
| exif_longitude | float | GPS longitude from EXIF (-360 if none) |
| gpx_latitude | float | Matched GPS latitude from GPX (-360 if none) |
| gpx_longitude | float | Matched GPS longitude from GPX (-360 if none) |
| manual_latitude | float | User-set GPS latitude (-360 if none) |
| manual_longitude | float | User-set GPS longitude (-360 if none) |
| final_latitude | float | **Active GPS latitude (cascade logic)** |
| final_longitude | float | **Active GPS longitude (cascade logic)** |
| new_name | string | Placeholder for renaming feature |
| tagged | boolean | Tag status for filtering |
| original_index | int | Original index before filtering (frontend) |

**Final Coordinates Cascade Logic**:
1. If manual coordinates exist → use manual
2. Else if GPX coordinates exist → use GPX
3. Else → use EXIF
4. Final coordinates update automatically when any source changes

### pd_gpx_info DataFrame
Stores GPX track point information with time offset support:

| Column | Type | Description |
|--------|------|-------------|
| latitude | float | Point latitude |
| longitude | float | Point longitude |
| elevation | float | Point elevation |
| time | datetime | **Adjusted** timestamp (original + offset) |
| original_time | datetime | Original timestamp from GPX file |
| track_name | string | Name of parent track |

**Time Offset Handling**:
- Original GPX timestamps preserved in `original_time` column
- `time` column contains adjusted timestamps based on track offset
- Offsets applied to compensate timezone differences (GPX usually UTC)
- Each track maintains its own `offset_seconds` value

## API Endpoints

### Photo Management
- `GET /` - Serve main HTML page
- `POST /api/scan-folder` - Scan folder for photos (returns photos with original_index)
- `GET /api/photos` - Get photos with filtering (maintains original_index)
- `GET /api/photos/{index}` - Get specific photo details with GPX matching
- `POST /api/photos/{index}/tag` - Toggle photo tag status
- `GET /api/photo-thumbnail/{index}` - Get photo thumbnail (with cache-busting)
- `GET /api/photo-image/{index}` - Get full-size image (with cache-busting)
- `POST /api/sort` - Set photo sort order (appends to existing, skips duplicates)
- `POST /api/gpx/remove` - Remove specific GPX tracks by indices
- `POST /api/gpx/clear` - Clear all GPX tracks
- `POST /api/gpx/set-main-offset` - Set time offset for all tracks
- `POST /api/gpx/set-track-offset` - Set time offset for specific track
- `GET /api/gpx/tracks` - Get all GPX tracks with offset info
### GPS & Geotagging
- `POST /api/photos/{index}/manual-location` - Set manual GPS (returns complete photo data with final coords)
- `DELETE /api/photos/{index}/manual-location` - Delete manual GPS (returns updated photo data with fallback coords)

### GPX Management
- `POST /api/gpx/upload` - Load GPX files
- `GET /api/gpx/tracks` - Get all GPX tracks

## Project Structure

```
geotag/
├── app/
│   ├── __init__.py
│   ├── server.py          # FastAPI server and routes
│   ├── photo_manager.py   # Photo scanning and EXIF extraction
│   └── gpx_manager.py     # GPX file parsing and matching
├── static/
│   ├── styles.css         # Application styling
│   └── app.js             # Frontend JavaScript
├── templates/
│   └── index.html         # Main HTML template
├── pyproject.toml         # Project dependencies
├── main.py                # Application entry point
└── README.md              # This file
```

## Keyboard Shortcuts

- **Space**: Open selected photo in Large Photo View
- **Escape**: Close Large Photo View
- **Arrow Left**: Previous photo (in Large Photo View)
- **Arrow Right**: Next photo (in Large Photo View)

## Troubleshooting

### Photos not loading
- Ensure the folder path is correct
- Check file permissions
- Verify image file extensions are supported (jpg, jpeg, png, gif, bmp, tiff, heic)

### Mac-specific: Fraction object error
- Fixed in latest version - GPS coordinates from Mac EXIF are now properly converted
- Ensure you're running the latest code

### Photos showing wrong thumbnails after sorting/filtering
- Fixed with cache-busting - thumbnails now include timestamp parameters
- Clear browser cache if issues persist (Ctrl+Shift+R or Cmd+Shift+R)

### Markers not visible on map
- If manual and final markers overlap, final marker (green) appears as a larger ring around manual marker (yellow)
- Zoom in to see individual markers more clearly
- Check console (F12) for any JavaScript errors

### GPX tracks not matching photos
- Check if GPX files are loaded (visible in "Loaded Tracks" panel)
- Verify time offset is correct (GPX usually UTC, camera may use local time)
- Try adjusting the time offset: calculate timezone difference (e.g., +02:00:00 for UTC+2)
- Apply main offset to all tracks or individual offset for specific tracks
- Photos match within ±5 minutes of adjusted GPX timestamps
- Check timezone awareness: system handles both timezone-aware and naive datetimes

### Duplicate GPX tracks
- The application automatically detects and skips duplicate track names
- If you need to reload a track, remove it first then upload again

### Map not displaying
- **OpenStreetMap**: Should work without any configuration
- **Google Maps**: 
  - Verify API key is correctly set in `templates\index.html`
  - Check that Maps JavaScript API is enabled in Google Cloud Console
  - Ensure API key has no restrictions blocking localhost
- Try switching to the other map provider using the dropdown

### Server errors
- Check Python version (3.11+ required)
- Ensure all dependencies are installed: `uv sync`
- Check console output for specific error messages
- For Mac users: Ensure Pillow is properly installed for EXIF reading

## Development

### Install in development mode:
```powershell
uv sync --dev
```

### Run with auto-reload:
```powershell
uv run uvicorn app.server:app --reload --host 127.0.0.1 --port 8000
```

## Future Enhancements

- [ ] Batch EXIF writing (save final GPS coordinates back to photos)
- [ ] Photo renaming based on capture time/location
- [ ] Export tagged photos to new folder
- [ ] Support for RAW image formats
- [ ] Multi-language support
- [ ] Database persistence (SQLite)
- [ ] User authentication for multi-user scenarios
- [ ] Advanced filtering and search
- [ ] Photo editing tools
- [ ] Timeline view
- [ ] Offline map tiles caching
- [ ] Custom map marker styles
- [ ] Photo clustering on map
- [ ] Heatmap view for photo locations

## Recent Updates (v1.1)

### Map Providers
- ✅ Added OpenStreetMap support via Leaflet 1.9.4
- ✅ Added dual map provider support to all views
- ✅ Default to OpenStreetMap (no API key required)

### Coordinate System
- ✅ Implemented final coordinates with cascade logic (Manual → GPX → EXIF)
- ✅ Added 🟢 Final marker display (green, larger, semi-transparent)
- ✅ Real-time coordinate updates in legend

### UI/UX Improvements
- ✅ Fixed yellow emoji (🟡) display in legend
- ✅ Removed "Tag" labels from checkboxes for cleaner UI
- ✅ Fixed sorting synchronization between grid and list
- ✅ Implemented cache-busting for thumbnails and images
- ✅ Fixed filtered view index tracking with original_index

### Map Behavior
- ✅ Preserve zoom level when navigating photos
- ✅ Preserve zoom when placing/deleting markers
- ✅ Pan to center instead of fitBounds for consistent zoom
- ✅ Visual marker hierarchy (final marker larger than manual marker)

### Cross-Platform
- ✅ Fixed Mac EXIF GPS coordinate reading (Fraction objects)
- ✅ Proper handling of different EXIF data formats

### Bug Fixes
- ✅ Fixed marker overlap visibility (final marker ring around manual marker)
- ✅ Fixed tag status synchronization across views
- ✅ Fixed browser caching issues with timestamp parameters
- ✅ Fixed GPX view map provider support

## License

This project is provided as-is for personal and educational use.

## Author

Created with GitHub Copilot

## Support

For issues, questions, or contributions, please refer to the project repository.

---

**Note**: The application uses OpenStreetMap by default, which requires no API key. Google Maps is available as an optional alternative - remember to keep your API key secure and never commit it to public repositories if you choose to use it!
