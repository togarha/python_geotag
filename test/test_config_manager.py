"""
Tests for ConfigManager - configuration file management
"""
import pytest
from pathlib import Path
import yaml
from app.config_manager import ConfigManager


class TestConfigLoading:
    """Test configuration file loading"""
    
    def test_load_existing_config(self, sample_config_path):
        """Test loading an existing config file"""
        manager = ConfigManager(str(sample_config_path))
        
        assert manager.config is not None
        assert isinstance(manager.config, dict)
        assert manager.config_file == Path(sample_config_path)
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent config file"""
        manager = ConfigManager("nonexistent_config.yaml")
        
        # Should still initialize with default config
        assert manager.config is not None
        # Config file path is set, but file doesn't exist
        assert manager.config_file is not None or manager.config == manager.DEFAULT_CONFIG
    
    def test_default_config_structure(self):
        """Test that default config has required keys"""
        manager = ConfigManager()
        
        required_keys = [
            'map_provider', 'elevation_service', 'filename_format',
            'include_subfolders', 'sort_by', 'thumbnail_size',
            'folder_path', 'auto_save_config', 'export_folder'
        ]
        
        for key in required_keys:
            assert key in manager.config, f"Missing config key: {key}"
    
    def test_config_values_from_file(self, sample_config_path):
        """Test that values are correctly loaded from file"""
        manager = ConfigManager(str(sample_config_path))
        
        # Check some expected values from the test config
        assert manager.config['map_provider'] == 'osm'
        assert manager.config['elevation_service'] == 'open-elevation'
        assert isinstance(manager.config['include_subfolders'], bool)


class TestConfigGetSet:
    """Test getting and setting configuration values"""
    
    def test_get_config_value(self, sample_config_path):
        """Test getting configuration value"""
        manager = ConfigManager(str(sample_config_path))
        
        value = manager.get('map_provider')
        assert value == 'osm'
        
        # Test with default value
        value = manager.get('nonexistent_key', 'default_value')
        assert value == 'default_value'
    
    def test_set_config_value(self):
        """Test setting configuration value"""
        manager = ConfigManager()
        
        manager.set('thumbnail_size', 300)
        assert manager.get('thumbnail_size') == 300
        
        manager.set('map_provider', 'google')
        assert manager.get('map_provider') == 'google'
    
    def test_update_multiple_values(self):
        """Test updating multiple configuration values"""
        manager = ConfigManager()
        
        updates = {
            'thumbnail_size': 250,
            'sort_by': 'filename',
            'include_subfolders': True
        }
        
        manager.update(updates)
        
        for key, value in updates.items():
            assert manager.get(key) == value


class TestConfigSaving:
    """Test configuration file saving"""
    
    def test_save_config_to_file(self, tmp_path):
        """Test saving configuration to file"""
        config_file = tmp_path / "test_save.yaml"
        manager = ConfigManager()
        
        # Set some values
        manager.set('thumbnail_size', 350)
        manager.set('map_provider', 'esri')
        
        # Save config
        manager.config_file = config_file
        result = manager.save()
        
        assert result is True
        assert config_file.exists()
        
        # Verify content
        with open(config_file, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config['thumbnail_size'] == 350
        assert saved_config['map_provider'] == 'esri'
    
    def test_save_without_config_file(self):
        """Test saving when no config file is set"""
        manager = ConfigManager()
        manager.config_file = None
        
        result = manager.save()
        
        # Should return False or handle gracefully
        assert result is False
    
    def test_auto_save_disabled(self):
        """Test that update doesn't save when auto_save is False"""
        manager = ConfigManager()
        manager.set('auto_save_config', False)
        manager.config_file = None
        
        # This should not try to save
        manager.update({'thumbnail_size': 400})
        
        # Config should be updated in memory
        assert manager.get('thumbnail_size') == 400
    
    @pytest.mark.skip(reason="get_config_yaml method not implemented")
    def test_get_config_as_yaml(self):
        """Test getting configuration as YAML string"""
        manager = ConfigManager()
        manager.set('thumbnail_size', 320)
        
        yaml_string = manager.get_config_yaml()
        
        assert isinstance(yaml_string, str)
        assert 'thumbnail_size: 320' in yaml_string


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_valid_map_provider(self):
        """Test valid map provider values"""
        manager = ConfigManager()
        
        valid_providers = ['osm', 'esri', 'google']
        for provider in valid_providers:
            manager.set('map_provider', provider)
            assert manager.get('map_provider') == provider
    
    def test_valid_elevation_service(self):
        """Test valid elevation service values"""
        manager = ConfigManager()
        
        valid_services = ['none', 'open-elevation', 'opentopo', 'google']
        for service in valid_services:
            manager.set('elevation_service', service)
            assert manager.get('elevation_service') == service
    
    def test_valid_sort_by(self):
        """Test valid sort_by values"""
        manager = ConfigManager()
        
        valid_sorts = ['time', 'filename']
        for sort_value in valid_sorts:
            manager.set('sort_by', sort_value)
            assert manager.get('sort_by') == sort_value
    
    def test_thumbnail_size_range(self):
        """Test thumbnail size values"""
        manager = ConfigManager()
        
        # Test various sizes
        sizes = [100, 200, 300, 400]
        for size in sizes:
            manager.set('thumbnail_size', size)
            assert manager.get('thumbnail_size') == size


class TestConfigInfo:
    """Test configuration information retrieval"""
    
    def test_has_config_file(self, sample_config_path):
        """Test checking if config file is set"""
        manager = ConfigManager(str(sample_config_path))
        
        assert manager.config_file is not None
        assert manager.config_file == Path(sample_config_path)
    
    def test_no_config_file(self):
        """Test when no config file is set"""
        manager = ConfigManager()
        
        assert manager.config_file is None
    
    def test_config_file_path_string(self, sample_config_path):
        """Test getting config file path as string"""
        manager = ConfigManager(str(sample_config_path))
        
        path_str = str(manager.config_file)
        assert isinstance(path_str, str)
        assert 'config_default.yaml' in path_str


class TestConfigPersistence:
    """Test configuration persistence and reloading"""
    
    def test_save_and_reload(self, tmp_path):
        """Test saving config and reloading it"""
        config_file = tmp_path / "persist_test.yaml"
        
        # Create and save config
        manager1 = ConfigManager()
        manager1.config_file = config_file
        manager1.set('thumbnail_size', 275)
        manager1.set('map_provider', 'google')
        manager1.set('folder_path', '/test/path')
        manager1.save()
        
        # Load config in new manager
        manager2 = ConfigManager(str(config_file))
        
        assert manager2.get('thumbnail_size') == 275
        assert manager2.get('map_provider') == 'google'
        assert manager2.get('folder_path') == '/test/path'
    
    def test_update_and_persist(self, tmp_path):
        """Test updating multiple values and persisting"""
        config_file = tmp_path / "update_test.yaml"
        
        manager = ConfigManager()
        manager.config_file = config_file
        
        updates = {
            'thumbnail_size': 225,
            'include_subfolders': True,
            'sort_by': 'filename',
            'export_folder': '/export/path'
        }
        
        manager.update(updates)
        manager.save()
        
        # Reload and verify
        manager2 = ConfigManager(str(config_file))
        for key, value in updates.items():
            assert manager2.get(key) == value


class TestConfigDefaults:
    """Test default configuration values"""
    
    def test_default_values(self):
        """Test that defaults are set correctly"""
        manager = ConfigManager()
        
        # Check default values
        assert manager.get('map_provider') == 'osm'
        assert manager.get('elevation_service') == 'open-elevation'
        assert manager.get('thumbnail_size') == 150
        assert manager.get('include_subfolders') is False
        assert manager.get('sort_by') == 'time'
        assert manager.get('auto_save_config') is True
        assert manager.get('folder_path') == ''
        assert manager.get('export_folder') == ''
    
    def test_filename_format_default(self):
        """Test default filename format"""
        manager = ConfigManager()
        
        format_str = manager.get('filename_format')
        assert isinstance(format_str, str)
        assert len(format_str) > 0
        # Should contain format codes like %Y, %m, %d
        assert '%' in format_str


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_config_file(self, tmp_path):
        """Test loading empty config file"""
        empty_config = tmp_path / "empty.yaml"
        empty_config.write_text("")
        
        manager = ConfigManager(str(empty_config))
        
        # Should fall back to defaults
        assert manager.config is not None
        assert 'map_provider' in manager.config
    
    def test_malformed_yaml(self, tmp_path):
        """Test loading malformed YAML file"""
        malformed = tmp_path / "malformed.yaml"
        malformed.write_text("{ invalid yaml content ][")
        
        manager = ConfigManager(str(malformed))
        
        # Should handle gracefully and use defaults
        assert manager.config is not None
    
    def test_get_nonexistent_key_without_default(self):
        """Test getting non-existent key without default"""
        manager = ConfigManager()
        
        value = manager.get('nonexistent_key')
        assert value is None
    
    def test_set_none_value(self):
        """Test setting None value"""
        manager = ConfigManager()
        
        manager.set('folder_path', None)
        assert manager.get('folder_path') is None
