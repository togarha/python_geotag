"""
Pytest configuration and shared fixtures for geotag tests
"""
import pytest
import shutil
from pathlib import Path
import tempfile


# Test directory paths
TEST_DIR = Path(__file__).parent
RESOURCES_DIR = TEST_DIR / "resources"
OUTPUT_DIR = TEST_DIR / "output"


@pytest.fixture(scope="session", autouse=True)
def setup_output_dir():
    """Ensure output directory exists and is clean"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    yield
    # Clean up after all tests (optional - keep files for inspection)
    # for file in OUTPUT_DIR.glob("*"):
    #     if file.is_file():
    #         file.unlink()


@pytest.fixture
def test_resources_dir():
    """Path to test resources directory"""
    return RESOURCES_DIR


@pytest.fixture
def test_output_dir():
    """Path to test output directory"""
    return OUTPUT_DIR


@pytest.fixture
def sample_photo_paths():
    """Paths to sample test photos"""
    return {
        "camera": RESOURCES_DIR / "Camera.jpeg",
        "phone": RESOURCES_DIR / "Phone.jpg",
        "vert": RESOURCES_DIR / "Vert1.jpg",
        "subfolder": RESOURCES_DIR / "subfolder"
    }


@pytest.fixture
def sample_gpx_paths():
    """Paths to sample GPX files"""
    return {
        "outbound": RESOURCES_DIR / "outbound.gpx",
        "return": RESOURCES_DIR / "return.gpx"
    }


@pytest.fixture
def sample_config_path():
    """Path to sample config file"""
    return RESOURCES_DIR / "config_default.yaml"


@pytest.fixture
def sample_positions_paths():
    """Paths to sample position files"""
    return {
        "sample": RESOURCES_DIR / "sample_positions.yaml",
        "minimal": RESOURCES_DIR / "minimal_positions.yaml"
    }


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing"""
    config_path = tmp_path / "test_config.yaml"
    config_content = """map_provider: osm
elevation_service: open-elevation
filename_format: '%Y%m%d_%H%M%S'
include_subfolders: false
sort_by: time
thumbnail_size: 200
folder_path: ''
auto_save_config: false
export_folder: ''
"""
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def temp_output_file(tmp_path):
    """Generate a unique temporary output file path"""
    return tmp_path / "test_output.jpg"


@pytest.fixture
def clean_output_dir():
    """Fixture that cleans output directory before each test"""
    # Clean before test
    if OUTPUT_DIR.exists():
        for file in OUTPUT_DIR.glob("*"):
            if file.is_file():
                file.unlink()
    OUTPUT_DIR.mkdir(exist_ok=True)
    yield OUTPUT_DIR
    # Optional: clean after test
    # for file in OUTPUT_DIR.glob("*"):
    #     if file.is_file():
    #         file.unlink()


@pytest.fixture
def load_gpx_content():
    """Helper function to load GPX file content"""
    def _loader(gpx_path):
        with open(gpx_path, 'r', encoding='utf-8') as f:
            return f.read()
    return _loader


@pytest.fixture
def load_positions_content():
    """Helper function to load positions YAML file content"""
    def _loader(positions_path):
        with open(positions_path, 'r', encoding='utf-8') as f:
            return f.read()
    return _loader
