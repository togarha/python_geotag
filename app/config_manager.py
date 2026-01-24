"""
Configuration file management for the geotagging application
"""
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigManager:
    """Manages application configuration with YAML file persistence"""
    
    DEFAULT_CONFIG = {
        "map_provider": "osm",  # 'osm', 'esri', or 'google'
        "elevation_service": "open-elevation",  # 'none', 'open-elevation', 'opentopodata', or 'google'
        "filename_format": "%Y%m%d_%H%M%S_{title}",
        "include_subfolders": False,
        "sort_by": "time",  # 'time' or 'name'
        "thumbnail_size": 150,  # pixels
        "folder_path": "",
        "auto_save_config": True  # Auto-save config file on changes
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize config manager
        
        Args:
            config_file: Path to config file. If None, uses default config.
        """
        self.config_file = Path(config_file) if config_file else None
        self.config = self.DEFAULT_CONFIG.copy()
        
        if self.config_file and self.config_file.exists():
            self.load()
    
    def load(self) -> bool:
        """
        Load configuration from file
        
        Returns:
            True if successfully loaded, False otherwise
        """
        if not self.config_file or not self.config_file.exists():
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
            
            # Merge with defaults to ensure all keys exist
            self.config = self.DEFAULT_CONFIG.copy()
            if loaded_config:
                self.config.update(loaded_config)
            
            print(f"✓ Configuration loaded from {self.config_file}")
            return True
        except Exception as e:
            print(f"✗ Error loading config file: {e}")
            return False
    
    def save(self) -> bool:
        """
        Save configuration to file
        
        Returns:
            True if successfully saved, False otherwise
        """
        if not self.config_file:
            return False
        
        try:
            # Create directory if it doesn't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            
            print(f"✓ Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"✗ Error saving config file: {e}")
            return False
    
    def save_as(self, new_path: str) -> bool:
        """
        Save configuration to a new file and update config_file path
        
        Args:
            new_path: Path to new config file
            
        Returns:
            True if successfully saved, False otherwise
        """
        self.config_file = Path(new_path)
        return self.save()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values"""
        self.config.update(updates)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config.copy()
    
    def set_config_file(self, config_file: str):
        """Set the config file path"""
        self.config_file = Path(config_file)
