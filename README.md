# Geotag - Photo Geotagging Application

A powerful web-based photo geotagging application built with Python and FastAPI. Organize, view, and geotag your photos using EXIF data, GPX tracks, predefined positions, and manual location assignment with dual map provider support and automatic elevation fetching.

## Features

### 📷 Photo Management
- **Folder Scanning**: Select folders via file picker or drag-and-drop
- **Recursive Search**: Include photos from subfolders
- **Smart Sorting**: Sort by capture time or filename with synchronized grid and list views
- **Advanced Filtering**: Comprehensive filter combining tag status and GPS status
  - Tag filters: All, Tagged, Untagged
  - GPS filters: With GPS, Without GPS, With EXIF, With GPX, With Manual
  - Combined filters: Tagged+With GPS, Tagged+Without GPS, Untagged+With GPS, Untagged+Without GPS
- **Search**: Real-time filename search
- **Date Range Filter**: Filter photos by capture date with from/to date pickers
- **Bulk Operations**: Tag or untag all currently visible photos with one click
- **Export Functionality**: Export photos with updated metadata to a designated folder
  - Export all photos or only tagged photos
  - Updates EXIF GPS coordinates and altitude in exported files
  - Updates EXIF capture time (DateTimeOriginal, DateTimeDigitized)
  - Sets file creation and modification timestamps (cross-platform)
  - Uses new filename if configured
  - Conflict detection prevents accidental overwrites
- **Dual View**: List and grid thumbnail views synchronized in real-time
- **Adjustable Thumbnails**: Slide control for thumbnail size (100-400px)
- **Cache-Busting**: Automatic thumbnail and image refresh with timestamp parameters
- **Cross-Platform**: Works on Windows, Mac, and Linux with proper EXIF handling
- **Photo Renaming**: Configurable filename format with EXIF capture time or file creation time fallback
- **Metadata Editing**: Edit photo title and timestamp individually with modal interface
- **Title Management**: Extract and edit ImageDescription from EXIF metadata

### 🗺️ GPS & Geotagging
- **Triple Map Providers**: Switch between OpenStreetMap, ESRI World Imagery (Satellite), and Google Maps
- **EXIF GPS Extraction**: Automatically reads GPS coordinates and altitude from photo metadata (supports Fraction objects on Mac)
- **GPX Track Integration**: Load multiple GPX files with smart duplicate detection and elevation data
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
- **Predefined Positions**: Load YAML files with named locations for quick position assignment
- **Automatic Elevation Fetching**: Get altitude automatically when clicking on map
  - Multiple free API options: Open-Elevation, OpenTopoData (SRTM 90m), Google Maps
  - Selectable elevation service via dropdown
  - SSL certificate handling for problematic APIs
- **Four Coordinate Sources with Altitude**:
  - 🔴 EXIF coordinates + altitude (from camera GPS)
  - 🔵 GPX matched coordinates + elevation (from track logs)
  - 🟡 Manual coordinates + altitude (user-defined, draggable, auto-fetched elevation)
  - 🟢 Final coordinates + altitude (cascade: Manual → GPX → EXIF)
- **Smart Coordinate Cascade**: Final location automatically updates based on priority
- **Zoom Preservation**: Map maintains zoom level when navigating photos or placing markers
- **Visual Marker Hierarchy**: Larger, semi-transparent final marker shows around smaller manual marker

### 📍 Position Management
- **Predefined Positions View**: Dedicated interface for managing named locations
- **YAML File Support**: Load multiple YAML files with positions
- **Position Selection Modal**: Beautiful modal dialog for choosing positions
- **Hover Effects**: Interactive position list with smooth animations
- **Source Tracking**: See which file each position came from
- **Altitude Support**: Optional altitude in predefined positions
- **Quick Assignment**: One-click position assignment to photos

### 🖼️ Photo Viewer
- **Large Photo View**: Full-size photo display with navigation
- **Keyboard Controls**: Arrow keys for navigation, Space to open, Escape to close
- **Tag Management**: Quick tagging with checkboxes (labels removed for cleaner UI)
- **EXIF Display**: Comprehensive metadata viewing including altitude
- **Interactive Map**: View and edit photo locations with dual map provider support
- **Real-time Updates**: Coordinate display updates immediately when placing or deleting markers
- **Marker Management**: 
  - 📋 Copy position from previous photo
  - ✏️ Set manual position via text input (latitude, longitude, optional altitude)
  - 📍 Select from predefined positions
  - 🗑️ Delete manual marker
- **Position Input Methods**:
  1. Click on map (auto-fetches elevation)
  2. Enter coordinates manually with format: `latitude, longitude (altitude)`
  3. Select from loaded predefined positions
  4. Copy from previous photo

### 🎨 User Interface
- **Expandable Menu**: Auto-expands on hover or click
- **Responsive Design**: Works on desktop and mobile
- **Modern UI**: Clean, intuitive interface with smooth animations
- **Four Main Views**:
  1. Photo Thumbnails View (with triple map provider support)
  2. GPX View (with triple map provider support and time offset controls)
  3. Positions View (YAML file management)
  4. Settings View (photo renaming, metadata configuration, and map/elevation provider selection)
  5. Large Photo View (modal with triple map provider and metadata editing)
- **Clean Checkboxes**: Tag checkboxes without distracting labels
- **Emoji Markers**: Proper UTF-8 emoji support (🔴 🔵 🟡 🟢) in legend
- **Styled Modals**: Beautiful position selection and metadata editing with hover effects

### ⚙️ Configuration Management
- **YAML Configuration Files**: Store all application settings in YAML format
- **Command-line Config Loading**: Start server with `--config` or `-c` flag to load config file
- **Auto-save Toggle**: Choose to automatically save settings changes or save manually
- **Manual Save/Download**: Save config to current file or download as new file
- **Configurable Settings**:
  - Map provider (osm, esri, google)
  - Elevation service (none, open-elevation, opentopo, google)
  - Photo renaming format
  - Include subfolders checkbox state
  - Sort by preference
  - Thumbnail size
  - Folder path
  - Auto-save configuration toggle
- **Sample Configs**: Example configuration files in `test/resources/`

## Technology Stack

- **Backend**: FastAPI (Python web framework)
- **Data Management**: Pandas DataFrames with altitude support across all coordinate types
- **Image Processing**: Pillow (PIL) with RGB conversion and thumbnail caching
- **GPX Parsing**: gpxpy with elevation data extraction
- **YAML Parsing**: PyYAML for predefined positions
- **Elevation APIs**: requests library with SSL handling
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Maps**: 
  - OpenStreetMap via Leaflet 1.9.4
  - ESRI World Imagery (Satellite) via Leaflet 1.9.4
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
   
   This will install all required packages:
   - FastAPI and Uvicorn (web server)
   - Pandas (data management)
   - Pillow (image processing)
   - gpxpy (GPX file parsing)
   - PyYAML (predefined positions)
   - requests (elevation APIs)
   - python-multipart (file uploads)
   - piexif (EXIF metadata updates)
   - pywin32 (Windows file timestamps) - Windows only

3. **Configure Services**:
   
   **Map Providers**:
   - **OpenStreetMap (Default)**: No API key required - works out of the box!
   - **ESRI World Imagery (Satellite)**: Free satellite imagery - no API key required!
   - **Google Maps (Optional)**:
     - Go to [Google Cloud Console](https://console.cloud.google.com/)
     - Create a new project or select an existing one
     - Enable the Maps JavaScript API
     - Create credentials (API Key)
     - Copy the API key
     - Open `templates\index.html` and replace `YOUR_GOOGLE_MAPS_API_KEY`:
       ```html
       <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_ACTUAL_API_KEY"></script>
       ```
   
   **Elevation Services**:
   - **None**: Disable automatic elevation fetching
   - **Open-Elevation**: Free, no API key required (default)
   - **OpenTopoData**: Free, no API key required, uses SRTM 90m dataset
   - **Google Maps Elevation API**: Requires API key (same as Maps API)

## Running the Application

### Start the server:

**Basic usage**:
```powershell
uv run python main.py
```

**With configuration file**:
```powershell
uv run python main.py --config path/to/config.yaml
# or
uv run python main.py -c path/to/config.yaml
```

**With custom host and port**:
```powershell
uv run python main.py --host 0.0.0.0 --port 8080
```

**All options combined**:
```powershell
uv run python main.py -c config.yaml --host 0.0.0.0 --port 8080
```

The server will start at `http://127.0.0.1:8000` by default

### Access the application:
Open your web browser and navigate to:
```
http://127.0.0.1:8000
```

### Configuration Files

Configuration files use YAML format and can store all application settings:

```yaml
# Example config.yaml
map_provider: esri                    # osm, esri, or google
elevation_service: open-elevation     # none, open-elevation, opentopo, or google
filename_format: "%Y%m%d_%H%M%S"     # Python strftime format
include_subfolders: true              # Recursive folder scanning
sort_by: capture_time                 # capture_time or name
thumbnail_size: 200                   # 100-400 pixels
folder_path: "C:/Photos"             # Last used folder path
auto_save_config: true               # Auto-save settings changes
export_folder: ""                    # Folder for exporting photos with metadata
```

**Sample configuration files** are available in `test/resources/`:
- `config_default.yaml` - OpenStreetMap with Open-Elevation
- `config_satellite.yaml` - ESRI satellite imagery
- `config_google_maps.yaml` - Google Maps configuration example

See `test/resources/README.md` for detailed configuration documentation.

## Usage Guide

### Photo Thumbnails View

1. **Select a Folder**:
   - Click "📁 Select Folder" button, or
   - Drag and drop a folder onto the drop zone

2. **Configure Options**:
   - Check "Include subfolders" for recursive scanning
   - Select sort order (Capture Time or Name) - both grid and list update automatically
   - **Filter dropdown** - Comprehensive filtering combining tag and GPS status:
     - Tag filters: All Photos, Tagged Only, Untagged Only
     - GPS filters: With GPS, Without GPS, With EXIF GPS, With GPX, With Manual GPS
     - Combined filters: Tagged+With GPS, Tagged+Without GPS, Untagged+With GPS, Untagged+Without GPS
   - **Search field** - Search photos by filename in real-time
   - **Date range filter (📅 button)** - Filter photos by capture date
     - Click calendar icon to show/hide date pickers
     - Select from date and/or to date
     - Clear button (✖️) to remove date filter
   - Adjust thumbnail size with the slider
   - Choose map provider (OpenStreetMap, ESRI World Imagery, or Google Maps)
   - Select elevation service (None, Open-Elevation, OpenTopoData, or Google)

3. **Bulk Operations**:
   - **Tag All Visible (🏷️ button)** - Tags all currently filtered/visible photos
   - **Untag All Visible (🚫 button)** - Untags all currently filtered/visible photos
   - **Export All (📤 button)** - Exports all visible photos with updated metadata
   - **Export Tagged (📤🏷️ button)** - Exports only tagged photos with updated metadata
   - All operations show confirmation dialog with photo count

4. **Export Photos**:
   - **Set Export Folder** in Settings view
   - **Export All Photos**: Exports all currently visible photos
   - **Export Tagged Photos**: Exports only tagged photos
   - **What gets updated**:
     - New filename (if configured via renaming format)
     - GPS coordinates and altitude in EXIF (from final_latitude, final_longitude, final_altitude)
     - Capture time in EXIF (from new_time or exif_capture_time)
     - File creation timestamp (cross-platform)
     - File modification timestamp (cross-platform)
   - **Conflict Protection**: Checks for existing files before export, cancels if conflicts found
   - **Cross-Platform**:
     - Windows: Uses Win32 API for creation time
     - macOS: Uses SetFile command or touch fallback
     - Linux: Sets modification time only (creation time not supported on most filesystems)
   - **Progress Feedback**: Shows count of exported photos and any failures

5. **Interact with Photos**:
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
   - Use the "Map:" dropdown to switch between OpenStreetMap, ESRI World Imagery, and Google Maps
   - Tracks are redrawn automatically on the new map
   - Map provider selection syncs with Settings view

### Positions View

1. **Load Predefined Positions**:
   - Click "📂 Select YAML Files"
   - Choose one or more .yaml or .yml files
   - Positions are displayed grouped by source file

2. **YAML File Format**:
   ```yaml
   # Each position requires: name, latitude, longitude
   # Altitude is optional
   
   - name: "Eiffel Tower, Paris"
     latitude: 48.8584
     longitude: 2.2945
     altitude: 324
   
   - name: "Stonehenge, UK"
     latitude: 51.1789
     longitude: -1.8262
   ```

3. **View Loaded Positions**:
   - Each file shows its filename and position count
   - Individual positions display name, coordinates, and altitude
   - Remove entire files with the "🗑️ Remove" button

4. **Use in Photos**:
   - Predefined positions become available in the Large Photo View
   - Click the 📍 button to select from loaded positions

### Settings View

1. **Export Settings**:
   - **Export Folder**: Enter the full path to folder where exported photos will be saved
   - Path is entered manually (browser folder picker not available due to security restrictions)
   - Example: `C:\Users\YourName\Pictures\Exported` or `/Users/YourName/Pictures/Exported`
   - Folder will be created automatically if it doesn't exist during export

2. **Map & Elevation Provider Configuration**:
   - **Map Provider**: Choose between OpenStreetMap, ESRI World Imagery (Satellite), or Google Maps
   - **Elevation Service**: Select None, Open-Elevation, OpenTopoData (SRTM), or Google
   - Changes sync with map provider selectors in Photo and GPX views

3. **Configuration File Management**:
   - **Auto-save Config**: Toggle to automatically save settings changes
   - **Current Config File**: Shows which config file is loaded (if any)
   - **Save Config**: Manually save settings to current config file
   - **Download Config As**: Download current settings as a new YAML file
   - All settings are persisted: map provider, elevation service, filename format, folder preferences, export folder

4. **Photo Renaming**:
   - Configure filename format using Python strftime codes
   - Default format: `%Y%m%d_%H%M%S` (e.g., `20260123_143052.jpg`)
   - Available format codes:
     - `%Y` - Year (4 digits, e.g., 2026)
     - `%m` - Month (01-12)
     - `%d` - Day (01-31)
     - `%H` - Hour 24h (00-23)
     - `%M` - Minute (00-59)
     - `%S` - Second (00-59)
     - `%I` - Hour 12h (01-12)
     - `%p` - AM/PM
   - Click "Preview Names" to see first 20 photos old → new
   - Click "Apply Format" to update new_name column for all photos
   - Falls back to file creation time if EXIF capture time not available
   - **Automatic Deduplication**: If multiple photos have same timestamp, letters (a, b, c) are appended automatically
     - Example: `20260123_143052.jpg`, `20260123_143052a.jpg`, `20260123_143052b.jpg`
     - Case-insensitive comparison for Windows compatibility

5. **Photo Title Management**:
   - Set title for all photos at once
   - Set title for tagged photos only
   - Clear all titles
   - Titles populate the new_title column
   - Uses ImageDescription EXIF field (cross-platform standard)
   - Fallback support for Windows XPTitle and XPComment tags

6. **Format Help**:
   - Collapsible help section with format codes and examples
   - Click to expand/collapse

### Large Photo View

1. **Navigation**:
   - Click ‹ / › buttons or use arrow keys
   - Photos maintain sort order from thumbnail view
   - Map preserves zoom level when navigating between photos

2. **Viewing Information**:
   - Left side: Full-size photo
   - Top right: EXIF metadata with Photo Information table
     - Shows Current Value and New Value columns
     - Displays: Filename, Image Title, File Creation Time, EXIF Capture Time, EXIF Position
     - New Value shows: new_name, new_title, new_time (if set), final coordinates
   - Bottom right: Interactive location map with coordinate legend

3. **Edit Photo Metadata (✏️ button)**:
   - Click "✏️ Edit Time & Title" button in Photo Information panel
   - Modal window opens with editable fields:
     - **Photo Title**: Text input for title (blank to clear)
     - **Photo Date/Time**: datetime-local picker with seconds
   - Each field has its own "Apply" button for independent updates
   - Changes update the new_title and new_time columns
   - Photo Information table updates immediately
   - Title states:
     - **N/A**: Not set (new_title is null)
     - **(blank)**: Intentionally cleared (new_title is empty string)
     - **value**: Custom title set

3. **Map Provider Selection**:
   - Use the "Map:" dropdown to switch between OpenStreetMap, ESRI World Imagery, and Google Maps
   - Current zoom and center position are maintained
   - Provider selection syncs with Settings and GPX views

4. **Coordinate Legend**:
   - 🔴 EXIF: GPS coordinates and altitude from camera
   - 🔵 GPX: Coordinates and elevation matched from GPX tracks
   - 🟡 Manual: User-set coordinates and altitude (draggable)
   - 🟢 Final: Active coordinates and altitude (follows cascade logic)

5. **Setting Photo Location**:
   
   **Method 1: Click on Map**
   - Click anywhere on the map
   - Altitude is automatically fetched from selected elevation service
   - Yellow manual marker appears with draggable capability
   
   **Method 2: Manual Entry (✏️ button)**
   - Click the ✏️ "Set Manual Position" button
   - Enter coordinates in format: `latitude, longitude (altitude)`
   - Altitude is optional: `43.4452, -2.7840` or `43.4452, -2.7840 (125)`
   - Coordinates are validated (lat: -90 to 90, lng: -180 to 180)
   
   **Method 3: Predefined Positions (📍 button)**
   - Click the 📍 "Set Predefined Position" button
   - Beautiful modal shows all loaded positions
   - Click any position to apply it instantly
   - Includes altitude from YAML file if specified
   
   **Method 4: Copy from Previous (📋 button)**
   - Click the 📋 "Copy position from previous image" button
   - Copies manual or final position (including altitude) from previous photo
   - Disabled for the first photo

6. **Deleting Manual Location (🗑️ button)**:
   - Click "🗑️" to remove manual location
   - Final coordinates automatically fall back to GPX or EXIF when manual is deleted
   - Altitude also falls back to GPX or EXIF altitude

7. **Automatic GPX Matching**:
   - When a photo opens, if no GPX coordinates exist
   - System searches GPX tracks for points within ±5 minutes of capture time
   - Closest match is automatically assigned with elevation data
   - Final coordinates update accordingly

8. **Automatic Elevation Fetching**:
   - When clicking on map, elevation is automatically fetched
   - Select elevation service from dropdown: Open-Elevation, OpenTopoData, or Google
   - OpenTopoData uses SRTM 90m dataset for global coverage
   - Elevation displays in meters in coordinate legend

## Data Structure

### pd_photo_info DataFrame
Stores all photo information with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| filename | string | Photo filename without path |
| full_path | string | Complete file path |
| exif_capture_time | datetime | Capture time from EXIF |
| creation_time | datetime | File creation time |
| new_time | datetime | User-modified capture time (None if not set) |
| exif_image_title | string | ImageDescription from EXIF (cross-platform) |
| new_title | string | User-modified title (None if not set, "" if cleared) |
| exif_latitude | float | GPS latitude from EXIF (-360 if none) |
| exif_longitude | float | GPS longitude from EXIF (-360 if none) |
| exif_altitude | float | GPS altitude from EXIF (None if none) |
| gpx_latitude | float | Matched GPS latitude from GPX (-360 if none) |
| gpx_longitude | float | Matched GPS longitude from GPX (-360 if none) |
| gpx_altitude | float | Matched elevation from GPX (None if none) |
| manual_latitude | float | User-set GPS latitude (-360 if none) |
| manual_longitude | float | User-set GPS longitude (-360 if none) |
| manual_altitude | float | User-set altitude (None if none) |
| final_latitude | float | **Active GPS latitude (cascade logic)** |
| final_longitude | float | **Active GPS longitude (cascade logic)** |
| final_altitude | float | **Active altitude (cascade logic)** |
| new_name | string | Generated filename based on format (auto-deduplicated) |
| tagged | boolean | Tag status for filtering |
| original_index | int | Original index before filtering (frontend) |

**Final Coordinates Cascade Logic**:
1. If manual coordinates exist → use manual (lat, lng, altitude)
2. Else if GPX coordinates exist → use GPX (lat, lng, elevation)
3. Else → use EXIF (lat, lng, altitude)
4. Final coordinates update automatically when any source changes

**Title and Time Fields**:
- `exif_image_title`: Read from EXIF ImageDescription (with fallback to XPTitle/XPComment on Windows)
- `new_title`: User-modified title (None = not set, "" = cleared, value = custom)
- `new_time`: User-modified timestamp (None = use original exif_capture_time)
- Displayed in Photo Information table with Current and New Value columns

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
- `GET /api/photos` - Get all photos (filtering done client-side)
- `GET /api/photos/{index}` - Get specific photo details with GPX matching
- `POST /api/photos/{index}/tag` - Toggle photo tag status
- `POST /api/photos/bulk-tag` - Tag or untag multiple photos at once
- `GET /api/photo-thumbnail/{index}` - Get photo thumbnail (with cache-busting)
- `GET /api/photo-image/{index}` - Get full-size image (with cache-busting)
- `POST /api/sort` - Set photo sort order

### GPS & Geotagging
- `POST /api/photos/{index}/manual-location` - Set manual GPS coordinates and altitude
- `DELETE /api/photos/{index}/manual-location` - Delete manual GPS (returns updated photo with fallback)

### GPX Management
- `POST /api/gpx/upload` - Load GPX files with elevation data
- `POST /api/gpx/remove` - Remove specific GPX tracks by indices
- `POST /api/gpx/clear` - Clear all GPX tracks
- `POST /api/gpx/set-main-offset` - Set time offset for all tracks
- `POST /api/gpx/set-track-offset` - Set time offset for specific track
- `GET /api/gpx/tracks` - Get all GPX tracks with offset info

### Predefined Positions
- `POST /api/positions/upload` - Load YAML files with positions
- `POST /api/positions/remove` - Remove positions by filename
- `GET /api/positions` - Get all loaded positions grouped by file

### Elevation Services
- `POST /api/elevation` - Fetch elevation for coordinates from selected service

### Settings & Configuration
- `GET /api/settings` - Get all application settings
- `POST /api/settings` - Update settings (conditionally saves based on auto_save_config)
- `POST /api/config/save` - Manually save current settings to config file
- `GET /api/config/download` - Download current settings as YAML file
- `GET /api/config/info` - Get current config file information

### Photo Export
- `POST /api/export` - Export photos with updated metadata
  - Request body: `{"export_type": "all" | "tagged"}`
  - Updates EXIF GPS coordinates and altitude
  - Updates EXIF capture time
  - Sets file creation and modification timestamps (cross-platform)
  - Returns count of exported photos and any failures
  - Returns 409 Conflict if destination files already exist

## Project Structure

```
geotag/
├── app/
│   ├── __init__.py
│   ├── server.py            # FastAPI server and routes
│   ├── photo_manager.py     # Photo scanning and EXIF extraction with altitude
│   ├── gpx_manager.py       # GPX file parsing and matching with elevation
│   ├── positions_manager.py # YAML positions parsing and management
│   ├── elevation_service.py # Elevation API integration (3 services)
│   ├── config_manager.py    # Configuration file management (YAML)
│   └── export_manager.py    # Photo export with EXIF and timestamp updates
├── static/
│   ├── styles.css           # Application styling with modal designs
│   └── app.js               # Frontend JavaScript with elevation and positions
├── templates/
│   └── index.html           # Main HTML template with all views
├── test/
│   └── resources/
│       ├── config_default.yaml       # Default OpenStreetMap config
│       ├── config_satellite.yaml     # ESRI satellite imagery config
│       ├── config_google_maps.yaml   # Google Maps config example
│       ├── sample_positions.yaml     # Comprehensive test positions
│       ├── minimal_positions.yaml    # Quick test positions
│       └── README.md                 # Configuration documentation
├── pyproject.toml           # Project dependencies
├── main.py                  # Application entry point with argparse
├── example_positions.yaml   # Example position file
└── README.md                # This file
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
- **ESRI World Imagery**: Free satellite imagery, should work without any configuration
- **Google Maps**: 
  - Verify API key is correctly set in `templates\index.html`
  - Check that Maps JavaScript API is enabled in Google Cloud Console
  - Ensure API key has no restrictions blocking localhost
- Try switching to another map provider using the dropdown
- If switching providers shows grey areas, navigate away and back to the view to refresh

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

- [ ] Support for RAW image formats
- [ ] Multi-language support
- [ ] Database persistence (SQLite)
- [ ] User authentication for multi-user scenarios
- [ ] Photo editing tools
- [ ] Timeline view
- [ ] Offline map tiles caching
- [ ] Custom map marker styles
- [ ] Photo clustering on map
- [ ] Heatmap view for photo locations
- [x] ~~Photo renaming based on capture time~~ ✅ Implemented in v1.3
- [x] ~~Photo metadata editing~~ ✅ Implemented in v1.3
- [x] ~~Advanced filtering and search~~ ✅ Implemented in v1.5
- [x] ~~Export photos with updated metadata~~ ✅ Implemented in v1.6

## Recent Updates

### Version 1.6 - Photo Export with Metadata Updates

**Export Functionality**:
- ✅ Export all photos or tagged photos only
- ✅ EXIF metadata updates in exported files:
  - GPS coordinates (latitude, longitude) from final position
  - GPS altitude from final altitude
  - Capture time (DateTimeOriginal, DateTimeDigitized, DateTime) from new_time or original
- ✅ File timestamp updates (cross-platform):
  - **Windows**: Creation, access, and modification times using Win32 API (pywin32)
  - **macOS**: Creation time via SetFile command with touch fallback
  - **Linux**: Modification and access times (creation time not supported on most filesystems)
- ✅ Pandas Timestamp to datetime conversion for API compatibility
- ✅ New filename support from photo renaming format
- ✅ Export folder configuration in Settings view
- ✅ Direct path input (browser folder picker not available due to security)
- ✅ File conflict detection before export
- ✅ 409 Conflict error if destination files exist (prevents overwrites)
- ✅ Export buttons in thumbnails view: 📤 (all) and 📤🏷️ (tagged)
- ✅ Progress feedback showing exported count and failures
- ✅ ExportManager class with piexif for EXIF manipulation

**Technical Details**:
- Uses `shutil.copy()` instead of `copy2()` to avoid timestamp preservation
- Updates EXIF first, then sets file timestamps after file is finalized
- Handles NaN/None values gracefully
- Preserves all non-updated EXIF data
- Quality setting: 95 for minimal quality loss

**Dependencies**:
- Added piexif>=1.1.3 for EXIF updates
- Added pywin32>=306 for Windows (platform-specific)

### Version 1.5 - Advanced Filtering & Bulk Operations

**Advanced Filtering System**:
- ✅ Comprehensive filter dropdown combining tag and GPS status
- ✅ Tag filters: All, Tagged Only, Untagged Only
- ✅ GPS filters: With GPS, Without GPS, With EXIF, With GPX, With Manual
- ✅ Combined filters: Tagged+GPS combinations (4 options)
- ✅ Real-time filename search field
- ✅ Date range filter with from/to date pickers
- ✅ Calendar button (📅) to show/hide date range controls
- ✅ Clear date filter button (✖️)
- ✅ All filters work together (compound filtering)
- ✅ Client-side filtering for instant results

**Bulk Operations**:
- ✅ Tag All Visible button (🏷️) - Icon only with tooltip
- ✅ Untag All Visible button (🚫) - Icon only with tooltip
- ✅ Bulk tag/untag API endpoint
- ✅ Confirmation dialogs showing photo count
- ✅ Works with filtered results

**Filtering Logic**:
- ✅ Uses EXIF capture time or creation time for date filtering
- ✅ Maintains photo index tracking across filters
- ✅ Updates displays in real-time
- ✅ Preserves sort order with filters

### Version 1.4 - Configuration Management & ESRI Satellite Imagery

**Configuration File System**:
- ✅ YAML-based configuration management with ConfigManager class
- ✅ Command-line arguments: `--config` (or `-c`), `--host`, `--port`
- ✅ Auto-save toggle: Choose automatic or manual config saving
- ✅ Manual save and download buttons in Settings view
- ✅ Browser-native file download for "Save Config As"
- ✅ All settings persisted: map_provider, elevation_service, filename_format, include_subfolders, sort_by, thumbnail_size, folder_path, auto_save_config
- ✅ Sample configuration files in `test/resources/`
- ✅ Complete configuration documentation

**ESRI World Imagery Support**:
- ✅ Added ESRI World Imagery as third map provider option
- ✅ Free satellite imagery via ArcGIS REST services
- ✅ No API key required
- ✅ Available in all views: Photo, GPX, and Large Photo View
- ✅ Map provider selectors synchronized across views
- ✅ Proper map initialization on visible containers only
- ✅ Smooth provider switching without grey tile areas

**Map Provider Synchronization**:
- ✅ Settings view map provider syncs with GPX view selector
- ✅ GPX view map provider syncs with Settings view selector
- ✅ Both map instances (photo and GPX) cleared when provider changes
- ✅ Maps only initialize when their containers are visible
- ✅ Proper Leaflet size recalculation with invalidateSize()

### Version 1.3 - Photo Renaming & Metadata Editing

**Photo Renaming System**:
- ✅ Settings View added as 4th main view
- ✅ Configurable filename format using Python strftime codes
- ✅ Default format: `%Y%m%d_%H%M%S` (e.g., 20260123_143052.jpg)
- ✅ Preview functionality showing first 20 photos (old → new)
- ✅ Apply format updates new_name column for all photos
- ✅ Automatic fallback to file creation time if no EXIF capture time
- ✅ Smart deduplication: letters (a, b, c) appended to duplicate filenames
- ✅ Case-insensitive comparison for Windows compatibility
- ✅ Extension preservation

**Photo Metadata Editing**:
- ✅ new_time column for user-modified capture timestamps
- ✅ new_title column for user-modified photo titles
- ✅ exif_image_title extraction from ImageDescription EXIF field
- ✅ Cross-platform EXIF title support (ImageDescription priority)
- ✅ Fallback to Windows XPTitle and XPComment tags
- ✅ Modal editor in Large Photo View with separate apply buttons
- ✅ Individual photo editing via "✏️ Edit Time & Title" button
- ✅ Datetime-local input with seconds for precise time editing
- ✅ Photo Information table shows Current and New values
- ✅ Title states: N/A (not set), (blank) (cleared), or custom value

**Bulk Title Management**:
- ✅ "Apply to All" sets title for all photos
- ✅ "Apply to Tagged" sets title for tagged photos only
- ✅ "Clear All Titles" removes all titles
- ✅ API endpoints for title management

**UI Improvements**:
- ✅ Collapsible format help section with examples
- ✅ Inline form layout with separate Apply buttons per field
- ✅ Modal window for metadata editing
- ✅ Real-time preview results display

### Version 1.2 - Altitude & Position Management

**Altitude Support**:
- ✅ Full altitude tracking across all coordinate types (EXIF, GPX, Manual, Final)
- ✅ EXIF altitude extraction with sea level reference handling
- ✅ GPX elevation data from track files
- ✅ Manual altitude entry and editing
- ✅ Altitude display in all coordinate legends with " (altitude m)" format
- ✅ NaN/inf value handling for JSON serialization

**Automatic Elevation Fetching**:
- ✅ Three free elevation APIs: Open-Elevation, OpenTopoData (SRTM 90m), Google Maps
- ✅ Selectable elevation service via dropdown
- ✅ Auto-fetch elevation when clicking on map
- ✅ SSL certificate handling for problematic APIs

**Predefined Positions System**:
- ✅ YAML file support for named locations
- ✅ Dedicated Positions View with file management
- ✅ Beautiful modal selector with hover effects
- ✅ Position grouping by source file
- ✅ Optional altitude in position definitions
- ✅ One-click position assignment to photos
- ✅ Sample YAML files in test/resources

**Enhanced Position Entry**:
- ✅ Manual coordinate entry via text input (📋 button with ✏️ icon)
- ✅ Format: `latitude, longitude (altitude)` with optional altitude
- ✅ Coordinate validation (lat: -90 to 90, lng: -180 to 180)
- ✅ Copy position from previous photo (📋 button)
- ✅ Select from predefined positions (📍 button)
- ✅ All methods include altitude support

**UI Improvements**:
- ✅ Styled position selection modal with smooth animations
- ✅ Position list with name, coordinates, altitude, and source file
- ✅ Hover effects on selectable positions
- ✅ Button tooltips without text labels for cleaner interface
- ✅ Four-button toolbar: Copy, Manual Entry, Predefined, Delete

### Version 1.1 - Map Providers & Coordinate System

**Map Providers**:
- ✅ Added OpenStreetMap support via Leaflet 1.9.4
- ✅ Added dual map provider support to all views
- ✅ Default to OpenStreetMap (no API key required)

**Coordinate System**:
- ✅ Implemented final coordinates with cascade logic (Manual → GPX → EXIF)
- ✅ Added 🟢 Final marker display (green, larger, semi-transparent)
- ✅ Real-time coordinate updates in legend

**UI/UX Improvements**:
- ✅ Fixed yellow emoji (🟡) display in legend
- ✅ Removed "Tag" labels from checkboxes for cleaner UI
- ✅ Fixed sorting synchronization between grid and list
- ✅ Implemented cache-busting for thumbnails and images
- ✅ Fixed filtered view index tracking with original_index

**Map Behavior**:
- ✅ Preserve zoom level when navigating photos
- ✅ Preserve zoom when placing/deleting markers
- ✅ Pan to center instead of fitBounds for consistent zoom
- ✅ Visual marker hierarchy (final marker larger than manual marker)

### Cross-Platform
- ✅ Fixed Mac EXIF GPS coordinate reading (Fraction objects)
- ✅ Proper handling of different EXIF data formats
- ✅ Altitude extraction with GPSAltitudeRef support

### Bug Fixes
- ✅ Fixed marker overlap visibility (final marker ring around manual marker)
- ✅ Fixed tag status synchronization across views
- ✅ Fixed browser caching issues with timestamp parameters
- ✅ Fixed GPX view map provider support
- ✅ Fixed NaN/inf JSON serialization errors
- ✅ SSL certificate verification issues with elevation APIs

## License

This project is provided as-is for personal and educational use.

## Author

Created with GitHub Copilot

## Support

For issues, questions, or contributions, please refer to the project repository.

---

**Note**: The application now supports three map providers: OpenStreetMap (default), ESRI World Imagery (free satellite), and Google Maps (requires API key). Two of three providers require no configuration! Free elevation services (Open-Elevation, OpenTopoData) are available, with an option to disable elevation fetching entirely. All settings can be saved to YAML configuration files and loaded automatically on startup.

**Example Files**: 
- Check `test/resources/` for sample YAML position files to get started with predefined positions
- Check `test/resources/` for sample configuration files (default, satellite, and Google Maps examples)
