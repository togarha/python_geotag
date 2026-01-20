# Geotag - Photo Geotagging Application

A powerful web-based photo geotagging application built with Python and FastAPI. Organize, view, and geotag your photos using EXIF data, GPX tracks, and manual location assignment.

## Features

### 📷 Photo Management
- **Folder Scanning**: Select folders via file picker or drag-and-drop
- **Recursive Search**: Include photos from subfolders
- **Smart Sorting**: Sort by capture time or filename
- **Filtering**: View all, tagged, or untagged photos
- **Dual View**: List and grid thumbnail views simultaneously
- **Adjustable Thumbnails**: Slide control for thumbnail size (100-400px)

### 🗺️ GPS & Geotagging
- **EXIF GPS Extraction**: Automatically reads GPS coordinates from photo metadata
- **GPX Track Integration**: Load GPX files and match photos to track points
- **Automatic Matching**: Photos matched to GPX tracks within ±5 minutes
- **Manual Geotagging**: Click on map to set custom locations
- **Three Coordinate Sources**:
  - 🔴 EXIF coordinates (from camera GPS)
  - 🔵 GPX matched coordinates (from track logs)
  - 🟢 Manual coordinates (user-defined)

### 🖼️ Photo Viewer
- **Large Photo View**: Full-size photo display with navigation
- **Keyboard Controls**: Arrow keys for navigation, Space to open, Escape to close
- **Tag Management**: Quick tagging with checkboxes
- **EXIF Display**: Comprehensive metadata viewing
- **Interactive Map**: View and edit photo locations on Google Maps

### 🎨 User Interface
- **Expandable Menu**: Auto-expands on hover or click
- **Responsive Design**: Works on desktop and mobile
- **Modern UI**: Clean, intuitive interface with smooth animations
- **Three Main Views**:
  1. Photo Thumbnails View
  2. GPX View
  3. Large Photo View (modal)

## Technology Stack

- **Backend**: FastAPI (Python web framework)
- **Data Management**: Pandas DataFrames
- **Image Processing**: Pillow (PIL)
- **GPX Parsing**: gpxpy
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Maps**: Google Maps JavaScript API
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

3. **Get a Google Maps API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Maps JavaScript API
   - Create credentials (API Key)
   - Copy the API key

4. **Configure Google Maps API**:
   Open `templates\index.html` and replace `YOUR_GOOGLE_MAPS_API_KEY` with your actual API key:
   ```html
   <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_ACTUAL_API_KEY"></script>
   ```

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
   - Select sort order (Capture Time or Name)
   - Choose filter (All Photos, Tagged Only, Untagged Only)
   - Adjust thumbnail size with the slider

3. **Interact with Photos**:
   - Single click: Select a photo
   - Double click: Open in Large Photo View
   - Press Space: Open selected photo in Large Photo View
   - Click checkbox: Toggle tagged status

### GPX View

1. **Select GPX Files**:
   - Click "📂 Select GPX Files"
   - Choose one or more .gpx files

2. **View Tracks**:
   - Tracks are displayed on the map in red
   - Map automatically centers to fit all tracks
   - Track information shows below the map

### Large Photo View

1. **Navigation**:
   - Click ‹ / › buttons or use arrow keys
   - Photos maintain sort order from thumbnail view

2. **Viewing Information**:
   - Left side: Full-size photo
   - Top right: EXIF metadata
   - Bottom right: Interactive location map

3. **Geotagging**:
   - View existing coordinates (EXIF, GPX, Manual)
   - Click anywhere on map to set manual location
   - Drag green marker to adjust position
   - Click "🗑️ Delete Manual Marker" to remove manual location

4. **Automatic GPX Matching**:
   - When a photo opens, if no GPX coordinates exist
   - System searches GPX tracks for points within ±5 minutes of capture time
   - Closest match is automatically assigned

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
| new_name | string | Placeholder for renaming feature |
| tagged | boolean | Tag status for filtering |

### pd_gpx_info DataFrame
Stores GPX track point information:

| Column | Type | Description |
|--------|------|-------------|
| latitude | float | Point latitude |
| longitude | float | Point longitude |
| elevation | float | Point elevation |
| time | datetime | Timestamp of track point |
| track_name | string | Name of parent track |

## API Endpoints

- `GET /` - Serve main HTML page
- `POST /api/scan-folder` - Scan folder for photos
- `GET /api/photos` - Get photos with filtering
- `GET /api/photos/{index}` - Get specific photo details
- `POST /api/photos/{index}/tag` - Toggle photo tag
- `POST /api/photos/{index}/manual-location` - Set manual GPS
- `DELETE /api/photos/{index}/manual-location` - Delete manual GPS
- `GET /api/photo-thumbnail/{index}` - Get photo thumbnail
- `GET /api/photo-image/{index}` - Get full-size image
- `POST /api/gpx/upload` - Load GPX files
- `GET /api/gpx/tracks` - Get all GPX tracks
- `POST /api/sort` - Set photo sort order

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

### GPX not matching photos
- Verify GPX files have timestamps
- Check that photo capture times are within ±5 minutes of GPX points
- Ensure EXIF capture time exists in photos

### Google Maps not displaying
- Verify API key is correctly set in `templates\index.html`
- Check that Maps JavaScript API is enabled in Google Cloud Console
- Ensure API key has no restrictions blocking localhost

### Server errors
- Check Python version (3.11+ required)
- Ensure all dependencies are installed: `uv sync`
- Check console output for specific error messages

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

- [ ] Batch EXIF writing (save GPS coordinates back to photos)
- [ ] Photo renaming based on capture time/location
- [ ] Export tagged photos to new folder
- [ ] Support for RAW image formats
- [ ] Multi-language support
- [ ] Database persistence (SQLite)
- [ ] User authentication for multi-user scenarios
- [ ] Advanced filtering and search
- [ ] Photo editing tools
- [ ] Timeline view

## License

This project is provided as-is for personal and educational use.

## Author

Created with GitHub Copilot

## Support

For issues, questions, or contributions, please refer to the project repository.

---

**Note**: Remember to keep your Google Maps API key secure and never commit it to public repositories!
