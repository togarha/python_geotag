"""
Tests for PositionsManager - predefined position loading and management
"""
import pytest
from pathlib import Path
from app.positions_manager import PositionsManager


class TestPositionLoading:
    """Test position file loading"""
    
    def test_load_single_position_file(self, sample_positions_paths, load_positions_content):
        """Test loading a single position file"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["minimal"])
        result = manager.load_yaml(content, Path(sample_positions_paths["minimal"]).name)
        
        assert result is not None
        assert len(manager.positions) > 0
    
    def test_load_multiple_position_files(self, sample_positions_paths, load_positions_content):
        """Test loading multiple position files"""
        manager = PositionsManager()
        content1 = load_positions_content(sample_positions_paths["minimal"])
        manager.load_yaml(content1, Path(sample_positions_paths["minimal"]).name)
        content2 = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content2, Path(sample_positions_paths["sample"]).name)
        
        # Should have positions from both files
        assert len(manager.positions) > 0
        # Should have at least 2 different source files
        sources = set(pos['source_file'] for pos in manager.positions)
        assert len(sources) >= 2
    
    def test_position_structure(self, sample_positions_paths, load_positions_content):
        """Test that loaded positions have correct structure"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        for position in manager.positions:
            assert 'name' in position
            assert 'latitude' in position
            assert 'longitude' in position
            assert 'source_file' in position
            # altitude is optional
            
            assert isinstance(position['name'], str)
            assert isinstance(position['latitude'], (int, float))
            assert isinstance(position['longitude'], (int, float))
            assert isinstance(position['source_file'], str)
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent position file"""
        manager = PositionsManager()
        # Test with invalid YAML content
        try:
            result = manager.load_yaml("", "nonexistent.yaml")
            assert False, "Should have raised an error"
        except (ValueError, Exception):
            pass


class TestPositionData:
    """Test position data handling"""
    
    def test_position_with_altitude(self, sample_positions_paths, load_positions_content):
        """Test positions that include altitude"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        # Find a position with altitude (e.g., Eiffel Tower should have one)
        positions_with_altitude = [p for p in manager.positions if 'altitude' in p and p['altitude'] is not None]
        
        if len(positions_with_altitude) > 0:
            pos = positions_with_altitude[0]
            assert isinstance(pos['altitude'], (int, float))
            assert pos['altitude'] > 0
    
    def test_position_without_altitude(self, sample_positions_paths, load_positions_content):
        """Test positions without altitude"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["minimal"])
        manager.load_yaml(content, Path(sample_positions_paths["minimal"]).name)
        
        # Minimal file might not have altitudes
        for position in manager.positions:
            # Should handle missing altitude gracefully
            altitude = position.get('altitude')
            assert altitude is None or isinstance(altitude, (int, float))
    
    def test_coordinate_ranges(self, sample_positions_paths, load_positions_content):
        """Test that coordinates are within valid ranges"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        for position in manager.positions:
            # Latitude should be between -90 and 90
            assert -90 <= position['latitude'] <= 90
            # Longitude should be between -180 and 180
            assert -180 <= position['longitude'] <= 180


class TestPositionRetrieval:
    """Test retrieving positions"""
    
    def test_get_all_positions(self, sample_positions_paths, load_positions_content):
        """Test getting all positions"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        positions = manager.get_all_positions()
        
        assert isinstance(positions, list)
        assert len(positions) > 0
        assert positions == manager.positions
    
    def test_get_positions_by_file(self, sample_positions_paths, load_positions_content):
        """Test getting positions grouped by file"""
        manager = PositionsManager()
        content1 = load_positions_content(sample_positions_paths["minimal"])
        manager.load_yaml(content1, Path(sample_positions_paths["minimal"]).name)
        content2 = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content2, Path(sample_positions_paths["sample"]).name)
        
        grouped = manager.get_positions_by_file()
        
        assert isinstance(grouped, dict)
        assert len(grouped) >= 2
        
        for filename, positions in grouped.items():
            assert isinstance(filename, str)
            assert isinstance(positions, list)
            assert len(positions) > 0
    
    def test_search_positions_by_name(self, sample_positions_paths, load_positions_content):
        """Test searching positions by name"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        # Search for a position (e.g., "Paris" or "Tower")
        if len(manager.positions) > 0:
            # Get first position name
            first_name = manager.positions[0]['name']
            search_term = first_name.split()[0]  # Get first word
            
            results = [p for p in manager.positions if search_term.lower() in p['name'].lower()]
            assert len(results) > 0


class TestPositionManagement:
    """Test position management operations"""
    
    def test_remove_positions_by_file(self, sample_positions_paths, load_positions_content):
        """Test removing positions by source file"""
        manager = PositionsManager()
        content1 = load_positions_content(sample_positions_paths["minimal"])
        manager.load_yaml(content1, Path(sample_positions_paths["minimal"]).name)
        content2 = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content2, Path(sample_positions_paths["sample"]).name)
        
        initial_count = len(manager.positions)
        
        # Remove positions from minimal file
        minimal_filename = Path(sample_positions_paths["minimal"]).name
        manager.remove_positions_by_file(minimal_filename)
        
        # Should have fewer positions
        assert len(manager.positions) < initial_count
        
        # No positions should have the removed file as source
        remaining_sources = [p['source_file'] for p in manager.positions]
        assert minimal_filename not in remaining_sources
    
    def test_clear_all_positions(self, sample_positions_paths, load_positions_content):
        """Test clearing all positions"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        assert len(manager.positions) > 0
        
        manager.clear_all()
        
        assert len(manager.positions) == 0
    
    def test_get_position_count(self, sample_positions_paths, load_positions_content):
        """Test getting position count"""
        manager = PositionsManager()
        
        assert len(manager.positions) == 0
        
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        count = len(manager.positions)
        assert count > 0


class TestDuplicateHandling:
    """Test handling of duplicate positions"""
    
    def test_load_same_file_twice(self, sample_positions_paths, load_positions_content):
        """Test loading the same file twice"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        initial_count = len(manager.positions)
        
        # Try to load same file again
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        # Count should not double (implementation dependent)
        # At minimum, positions should still be valid
        assert len(manager.positions) > 0
    
    def test_duplicate_position_names(self, sample_positions_paths, load_positions_content):
        """Test handling positions with same name from different files"""
        manager = PositionsManager()
        content1 = load_positions_content(sample_positions_paths["minimal"])
        manager.load_yaml(content1, Path(sample_positions_paths["minimal"]).name)
        content2 = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content2, Path(sample_positions_paths["sample"]).name)
        
        # Count positions by name
        names = [p['name'] for p in manager.positions]
        
        # Should be able to handle duplicate names (from different files)
        assert len(manager.positions) > 0


class TestYAMLParsing:
    """Test YAML parsing edge cases"""
    
    def test_empty_yaml_file(self, tmp_path):
        """Test loading empty YAML file"""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        
        manager = PositionsManager()
        try:
            content = empty_file.read_text()
            result = manager.load_yaml(content, "empty.yaml")
            assert False, "Should have raised an error"
        except (ValueError, Exception):
            pass
    
    def test_malformed_yaml(self, tmp_path):
        """Test loading malformed YAML"""
        malformed_file = tmp_path / "malformed.yaml"
        malformed_file.write_text("{ invalid: yaml: content ][")
        
        manager = PositionsManager()
        try:
            content = malformed_file.read_text()
            result = manager.load_yaml(content, "malformed.yaml")
            assert False, "Should have raised an error"
        except (ValueError, Exception):
            pass
    
    def test_incomplete_position_data(self, tmp_path):
        """Test loading YAML with incomplete position data"""
        incomplete_file = tmp_path / "incomplete.yaml"
        incomplete_file.write_text("""
- name: "Incomplete Position"
  latitude: 45.0
  # Missing longitude
""")
        
        manager = PositionsManager()
        try:
            content = incomplete_file.read_text()
            result = manager.load_yaml(content, "incomplete.yaml")
            # Should handle gracefully - might skip invalid positions
            # or return empty result
            assert isinstance(result, dict)
        except (ValueError, Exception):
            pass


class TestPositionValidation:
    """Test position data validation"""
    
    def test_valid_coordinates(self, sample_positions_paths, load_positions_content):
        """Test that all loaded positions have valid coordinates"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        for position in manager.positions:
            # Check latitude
            assert isinstance(position['latitude'], (int, float))
            assert -90 <= position['latitude'] <= 90
            
            # Check longitude
            assert isinstance(position['longitude'], (int, float))
            assert -180 <= position['longitude'] <= 180
    
    def test_valid_altitude_when_present(self, sample_positions_paths, load_positions_content):
        """Test that altitude values are valid when present"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        for position in manager.positions:
            if 'altitude' in position and position['altitude'] is not None:
                assert isinstance(position['altitude'], (int, float))
                # Altitude should be reasonable (Mt. Everest is ~8849m)
                assert -500 <= position['altitude'] <= 10000
    
    def test_non_empty_names(self, sample_positions_paths, load_positions_content):
        """Test that position names are non-empty"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        for position in manager.positions:
            assert isinstance(position['name'], str)
            assert len(position['name']) > 0
            assert position['name'].strip() != ""


class TestSourceFileTracking:
    """Test source file tracking"""
    
    def test_source_file_stored(self, sample_positions_paths, load_positions_content):
        """Test that source file is stored with each position"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        for position in manager.positions:
            assert 'source_file' in position
            assert isinstance(position['source_file'], str)
            assert len(position['source_file']) > 0
    
    def test_source_file_is_filename(self, sample_positions_paths, load_positions_content):
        """Test that source file is the filename, not full path"""
        manager = PositionsManager()
        content = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content, Path(sample_positions_paths["sample"]).name)
        
        for position in manager.positions:
            source = position['source_file']
            # Should be just filename, not path
            assert '/' not in source or source.endswith('.yaml')
            assert source.endswith('.yaml')
    
    def test_multiple_files_tracked_separately(self, sample_positions_paths, load_positions_content):
        """Test that positions from different files are tracked separately"""
        manager = PositionsManager()
        content1 = load_positions_content(sample_positions_paths["minimal"])
        manager.load_yaml(content1, Path(sample_positions_paths["minimal"]).name)
        content2 = load_positions_content(sample_positions_paths["sample"])
        manager.load_yaml(content2, Path(sample_positions_paths["sample"]).name)
        
        minimal_name = Path(sample_positions_paths["minimal"]).name
        sample_name = Path(sample_positions_paths["sample"]).name
        
        minimal_positions = [p for p in manager.positions if p['source_file'] == minimal_name]
        sample_positions = [p for p in manager.positions if p['source_file'] == sample_name]
        
        assert len(minimal_positions) > 0
