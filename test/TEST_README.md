# Geotag Application Test Suite

Comprehensive test suite for the geotag photo geotagging application.

## Test Statistics

- **Total Tests**: 129 (128 passing, 1 skipped)
- **Test Files**: 8 modules
- **Code Coverage**: All core functionality
- **External Dependencies**: Fully mocked (no network calls)

## Test Structure

```
test/
├── conftest.py                  # Pytest configuration and shared fixtures
├── test_photo_manager.py        # Photo scanning, EXIF extraction, metadata
├── test_gpx_manager.py          # GPX parsing, matching, time offsets
├── test_export_manager.py       # Photo export with metadata
├── test_config_manager.py       # Configuration management
├── test_positions_manager.py    # Predefined position loading
├── test_services.py             # Elevation & geocoding services (mocked)
├── resources/                   # Test data files
│   ├── Camera.jpeg              # Test photo with EXIF
│   ├── Phone.jpg                # Test photo
│   ├── Vert1.jpg                # Test photo
│   ├── outbound.gpx             # Test GPX track
│   ├── return.gpx               # Test GPX track
│   ├── sample_positions.yaml    # Test positions file
│   ├── minimal_positions.yaml   # Minimal positions file
│   └── config_default.yaml      # Test configuration
└── output/                      # Temporary test output files
```

## Running Tests

### Install Test Dependencies

```powershell
uv sync --dev
```

This installs:
- pytest >= 8.0.0
- pytest-asyncio >= 0.23.0
- pytest-mock >= 3.12.0

### Run All Tests

```powershell
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest test/test_photo_manager.py

# Run specific test class
uv run pytest test/test_photo_manager.py::TestPhotoScanning

# Run specific test
uv run pytest test/test_photo_manager.py::TestPhotoScanning::test_scan_folder_basic
```

### Run Tests by Category

```powershell
# Photo management tests
uv run pytest test/test_photo_manager.py -v

# GPX functionality tests
uv run pytest test/test_gpx_manager.py -v

# Export functionality tests
uv run pytest test/test_export_manager.py -v

# Configuration management tests
uv run pytest test/test_config_manager.py -v

# Position management tests
uv run pytest test/test_positions_manager.py -v

# Service tests (mocked APIs)
uv run pytest test/test_services.py -v
```

### Useful Pytest Options

```powershell
# Stop on first failure
uv run pytest -x

# Show local variables in tracebacks
uv run pytest -l

# Run tests matching keyword
uv run pytest -k "export"

# Show print statements
uv run pytest -s

# Run failed tests from last run
uv run pytest --lf

# Parallel execution (requires pytest-xdist)
uv run pytest -n auto
```

## Test Coverage

### PhotoManager Tests (test_photo_manager.py)
- ✅ Photo scanning (basic & recursive)
- ✅ Dataframe structure validation
- ✅ EXIF extraction (GPS, timestamps, location, keywords)
- ✅ Coordinate cascade logic (manual → GPX → EXIF)
- ✅ Manual location operations (set, delete)
- ✅ Metadata operations (title, keywords, location)
- ✅ Photo tagging (individual & bulk)
- ✅ Bulk operations (bulk_tag for multiple photos)
- ✅ Photo renaming with deduplication (apply_filename_format)
- ✅ Sorting (by time, by filename)
- **Total**: 19 tests

### GPXManager Tests (test_gpx_manager.py)
- ✅ GPX file loading (single & multiple, content-based API)
- ✅ Dataframe structure validation
- ✅ Duplicate detection
- ✅ Time offset handling (main & per-track)
- ✅ Offset format parsing (±HH:MM:SS)
- ✅ GPS point matching with time windows
- ✅ Elevation data handling
- ✅ Track management (remove by indices, clear all)
- ✅ Edge cases & error handling
- **Total**: 16 tests

### ExportManager Tests (test_export_manager.py)
- ✅ Basic photo export
- ✅ File renaming during export
- ✅ GPS coordinate export to EXIF
- ✅ Altitude export
- ✅ Metadata export (title, keywords, location)
- ✅ IPTC & XMP keywords export (dc:subject, pdf:Keywords)
- ✅ Timestamp export (capture time, GPS time, offset)
- ✅ File operations (folder creation, extensions)
- ✅ Complex multi-field export scenarios
- **Total**: 18 tests

### ConfigManager Tests (test_config_manager.py)
- ✅ Configuration loading from file
- ✅ Default configuration structure
- ✅ Get/Set operations
- ✅ Configuration saving (save method)
- ✅ Auto-save functionality
- ✅ Configuration validation
- ✅ Persistence and reloading
- ✅ Edge cases (empty, malformed files)
- **Total**: 44 tests (43 passed, 1 skipped)

### PositionsManager Tests (test_positions_manager.py)
- ✅ Position file loading (single & multiple, content-based API)
- ✅ Position data structure validation
- ✅ Altitude handling (with & without)
- ✅ Coordinate range validation
- ✅ Position retrieval (all, grouped by file)
- ✅ Position management (remove by file, clear all)
- ✅ Duplicate handling
- ✅ YAML parsing edge cases
- ✅ Source file tracking
- **Total**: 24 tests

### Services Tests (test_services.py)
- ✅ ElevationService initialization (no parameters, service passed to get_elevation)
- ✅ Multiple elevation providers (Open-Elevation, OpenTopoData, Google)
- ✅ GeocodingService with provider fallback (Nominatim → Photon)
- ✅ Mocked HTTP requests (no real API calls)
- ✅ Error handling (timeouts, connection errors, invalid responses)
- ✅ Invalid JSON response handling
- ✅ Rate limiting validation
- ✅ Service integration scenarios
- ✅ SSL verification configuration
- **Total**: 24 tests

## Test Data

The `test/resources/` directory contains:
- **Photos**: Camera.jpeg, Phone.jpg, Vert1.jpg (with various EXIF data)
- **GPX tracks**: outbound.gpx, return.gpx (with elevation data)
- **Position files**: sample_positions.yaml (comprehensive), minimal_positions.yaml (basic)
- **Config files**: config_default.yaml, config_satellite.yaml, config_google_maps.yaml

## Output Files

Test output files are written to `test/output/`:
- Exported photos with updated metadata
- Generated CSV metadata files
- Temporary configuration files
- Test-generated thumbnails

**Note**: Output files are preserved after tests for inspection. Clean manually if needed.

## Mocking Strategy

### External API Tests
Services that call external APIs (elevation, geocoding) are fully mocked:
- No real HTTP requests during tests
- Fast test execution
- Predictable test results
- No API rate limits or network issues

### File System Tests
File operations use temporary directories or the dedicated `test/output/` folder:
- Safe isolated testing
- No interference with production data
- Easy cleanup

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- All dependencies in `pyproject.toml`
- No external API calls (mocked)
- Test data included in repository
- Consistent results across environments

### Example CI Configuration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --dev
      - name: Run tests
        run: uv run pytest -v
```

## Writing New Tests

### Test Structure
```python
class TestFeatureName:
    """Test description"""
    
    def test_specific_behavior(self, fixture_name):
        """Test what this does"""
        # Arrange
        manager = SomeManager()
        
        # Act
        result = manager.some_method()
        
        # Assert
        assert result is not None
```

### Using Fixtures
```python
def test_with_photos(self, sample_photo_paths):
    """Use pre-defined fixtures from conftest.py"""
    photo_path = sample_photo_paths["camera"]
    assert photo_path.exists()
```

### Mocking External Calls
```python
@patch('app.some_module.requests.get')
def test_api_call(self, mock_get):
    """Mock HTTP requests"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'key': 'value'}
    mock_get.return_value = mock_response
    
    # Test code that makes API call
```

## Troubleshooting

### Tests Fail Due to Missing Resources
```powershell
# Ensure you're in the project root
cd c:\devel\geotag

# Verify test resources exist
ls test/resources/
```

### Import Errors
```powershell
# Reinstall dependencies
uv sync --dev

# Run from project root
cd c:\devel\geotag
uv run pytest
```

### Slow Tests
```powershell
# Run only fast tests (skip slow integration tests)
uv run pytest -m "not slow"

# Use parallel execution
pip install pytest-xdist
uv run pytest -n auto
```

### Permission Errors on Windows
- Run PowerShell as Administrator
- Check that test/output/ is writable
- Close any open files from previous test runs

## Contributing

When adding new features:
1. Write tests for new functionality
2. Ensure all existing tests pass
3. Aim for >80% code coverage
4. Use mocks for external services
5. Add test data to `test/resources/` if needed

## License

Tests are part of the geotag application and follow the same license.
