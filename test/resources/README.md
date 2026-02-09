# Test Configuration Files

This folder contains sample configuration files for testing the application's config file management feature.

## Usage

Start the application with a config file:

```bash
uv run python main.py --config test/resources/config_default.yaml
```

Or with short option:

```bash
uv run python main.py -c test/resources/config_google_maps.yaml
```

## Configuration Files

### config_default.yaml
Default configuration using OpenStreetMap and Open-Elevation (free services):
- Map Provider: OpenStreetMap
- Elevation Service: Open-Elevation
- Filename Format: `%Y%m%d_%H%M%S_{title}`
- Include Subfolders: No
- Sort By: Time
- Thumbnail Size: 150px
- Folder Path: `C:\Users\Photos\Vacation2024`

### config_google_maps.yaml
Configuration using Google Maps services (requires API key):
- Map Provider: Google Maps
- Elevation Service: Google Maps Elevation API
- Filename Format: `%Y-%m-%d_%H%M_{title}`
- Include Subfolders: Yes
- Sort By: Name
- Thumbnail Size: 200px
- Folder Path: `D:\Photography\Events\Wedding2025`

## Configuration Fields

All configuration files support the following fields:

| Field | Type | Options | Description |
|-------|------|---------|-------------|
| `map_provider` | string | `"osm"`, `"esri"`, `"google"` | Map provider for displaying locations |
| `elevation_service` | string | `"none"`, `"open-elevation"`, `"opentopodata"`, `"google"` | Elevation API service |
| `filename_format` | string | strftime format + `{title}` | Format for renaming photos |
| `include_subfolders` | boolean | `true`, `false` | Whether to scan subfolders recursively |
| `sort_by` | string | `"time"`, `"name"` | Default sorting method for photos |
| `thumbnail_size` | integer | 50-300 | Thumbnail size in pixels |
| `folder_path` | string | Any valid path | Last used or default folder path |
| `auto_save_config` | boolean | `true`, `false` | Auto-save config file on changes |

## Creating Your Own Config

Create a YAML file with the desired settings:

```yaml
map_provider: osm
elevation_service: open-elevation
filename_format: '%Y%m%d_%H%M%S_{title}'
include_subfolders: false
sort_by: time
thumbnail_size: 150
folder_path: ''
auto_save_config: true
```

All fields are optional - missing fields will use default values.

## Auto-Save Configuration

When `auto_save_config` is set to `true`, any changes made through the UI are automatically saved back to the config file. If set to `false`, you need to manually save using the "Save Config" button in the Settings view.

You can also use "Save Config As..." to save the current configuration to a new file.

## Command Line Options

```
usage: main.py [-h] [--config CONFIG] [--host HOST] [--port PORT]
               [--folder-path FOLDER_PATH] [--export-folder EXPORT_FOLDER]

Photo Geotagging Application

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to configuration file (YAML)
  --host HOST           Host to bind to (default: 127.0.0.1)
  --port PORT           Port to bind to (default: 8000)
  --folder-path FOLDER_PATH
                        Photo folder path (overrides config file)
  --export-folder EXPORT_FOLDER
                        Export folder path (overrides config file)
```

**Priority**: Command-line arguments take priority over config file values. This allows you to temporarily override folder paths without modifying the config file.

## Auto-Save

When running with a config file and `auto_save_config: true`, any changes made through the UI (map provider, elevation service, filename format, etc.) are automatically saved back to the config file.

When `auto_save_config: false`, changes are kept in memory and you must use the "Save Config" button in Settings to persist them.

If no config file is specified, settings are stored in memory only and will be lost when the application restarts.
