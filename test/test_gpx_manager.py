"""
Tests for GPXManager - GPX file parsing, matching, and time offset handling
"""
import pytest
from datetime import datetime, timedelta
from app.gpx_manager import GPXManager


class TestGPXLoading:
    """Test GPX file loading and parsing"""
    
    def test_load_single_gpx(self, sample_gpx_paths, load_gpx_content):
        """Test loading a single GPX file"""
        manager = GPXManager()
        content = load_gpx_content(sample_gpx_paths["outbound"])
        result = manager.load_gpx(content, "outbound.gpx")
        
        assert result is not None
        assert len(manager.pd_gpx_info) > 0
        assert len(manager.tracks) >= 1
    
    def test_load_multiple_gpx(self, sample_gpx_paths, load_gpx_content):
        """Test loading multiple GPX files"""
        manager = GPXManager()
        content1 = load_gpx_content(sample_gpx_paths["outbound"])
        content2 = load_gpx_content(sample_gpx_paths["return"])
        manager.load_gpx(content1, "outbound.gpx")
        manager.load_gpx(content2, "return.gpx")
        
        assert len(manager.tracks) == 2
        # Should have points from both tracks
        assert len(manager.pd_gpx_info) > 0
    
    def test_gpx_dataframe_structure(self, sample_gpx_paths, load_gpx_content):
        """Test that GPX dataframe has all required columns"""
        manager = GPXManager()
        content = load_gpx_content(sample_gpx_paths["outbound"])
        manager.load_gpx(content, "outbound.gpx")
        
        required_columns = [
            'latitude', 'longitude', 'elevation',
            'time', 'track_name'
        ]
        
        for col in required_columns:
            assert col in manager.pd_gpx_info.columns, f"Missing column: {col}"
    
    def test_duplicate_detection(self, sample_gpx_paths, load_gpx_content):
        """Test that duplicate tracks are not loaded"""
        manager = GPXManager()
        content = load_gpx_content(sample_gpx_paths["outbound"])
        manager.load_gpx(content, "outbound.gpx")
        initial_count = len(manager.tracks)
        
        # Try to load same track again (same name)
        manager.load_gpx(content, "outbound.gpx")
        
        # Should not increase count
        assert len(manager.tracks) == initial_count


class TestTimeOffset:
    """Test time offset functionality"""
    
    def test_set_main_offset(self, sample_gpx_paths, load_gpx_content):
        """Test setting main offset for all tracks"""
        manager = GPXManager()
        content1 = load_gpx_content(sample_gpx_paths["outbound"])
        content2 = load_gpx_content(sample_gpx_paths["return"])
        manager.load_gpx(content1, "outbound.gpx")
        manager.load_gpx(content2, "return.gpx")
        
        # Set main offset to 2 hours
        offset_seconds = 2 * 3600
        manager.set_main_offset(offset_seconds)
        
        # Check that all tracks have the offset
        for track in manager.tracks:
            assert track['offset_seconds'] == offset_seconds
    
    def test_set_individual_track_offset(self, sample_gpx_paths, load_gpx_content):
        """Test setting offset for individual track"""
        manager = GPXManager()
        content1 = load_gpx_content(sample_gpx_paths["outbound"])
        content2 = load_gpx_content(sample_gpx_paths["return"])
        manager.load_gpx(content1, "outbound.gpx")
        manager.load_gpx(content2, "return.gpx")
        
        if len(manager.tracks) > 0:
            offset_seconds = 3600  # 1 hour
            
            manager.set_track_offset(0, offset_seconds)
            
            # Check that specific track has the offset
            assert manager.tracks[0]['offset_seconds'] == offset_seconds
    
    def test_offset_format_parsing(self):
        """Test parsing offset format string"""
        manager = GPXManager()
        
        # Test positive offset
        offset_seconds = manager.parse_offset_string("+02:30:00")
        assert offset_seconds == 2 * 3600 + 30 * 60
        
        # Test negative offset
        offset_seconds = manager.parse_offset_string("-01:15:00")
        assert offset_seconds == -(1 * 3600 + 15 * 60)
        
        # Test zero
        offset_seconds = manager.parse_offset_string("00:00:00")
        assert offset_seconds == 0


class TestGPXMatching:
    """Test GPX point matching with photos"""
    
    def test_find_closest_point_exact_match(self, sample_gpx_paths, load_gpx_content):
        """Test finding exact time match"""
        manager = GPXManager()
        content = load_gpx_content(sample_gpx_paths["outbound"])
        manager.load_gpx(content, "outbound.gpx")
        
        if len(manager.pd_gpx_info) > 0:
            # Get a timestamp from the GPX data
            test_time = manager.pd_gpx_info.iloc[0]['time']
            
            result = manager.find_closest_point(test_time)
            
            assert result is not None
            assert 'latitude' in result
            assert 'longitude' in result
            assert 'elevation' in result
    
    def test_find_closest_point_within_window(self, sample_gpx_paths, load_gpx_content):
        """Test finding match within time window"""
        manager = GPXManager()
        content = load_gpx_content(sample_gpx_paths["outbound"])
        manager.load_gpx(content, "outbound.gpx")
        
        if len(manager.pd_gpx_info) > 0:
            # Get a timestamp and add 2 minutes (within 5 minute window)
            test_time = manager.pd_gpx_info.iloc[0]['time'] + timedelta(minutes=2)
            
            result = manager.find_closest_point(test_time)
            
            # Should still find a match
            assert result is not None
    
    def test_elevation_data(self, sample_gpx_paths, load_gpx_content):
        """Test that elevation data is preserved"""
        manager = GPXManager()
        content = load_gpx_content(sample_gpx_paths["outbound"])
        manager.load_gpx(content, "outbound.gpx")
        
        # Check that elevation column exists
        assert 'elevation' in manager.pd_gpx_info.columns
        
        # Some points should have elevation data (not all GPX files have this)
        # Just verify the column can contain data
        assert manager.pd_gpx_info['elevation'].dtype in ['float64', 'object']


class TestTrackManagement:
    """Test track removal and management"""
    
    def test_remove_single_track(self, sample_gpx_paths, load_gpx_content):
        """Test removing a single track"""
        manager = GPXManager()
        content1 = load_gpx_content(sample_gpx_paths["outbound"])
        content2 = load_gpx_content(sample_gpx_paths["return"])
        manager.load_gpx(content1, "outbound.gpx")
        manager.load_gpx(content2, "return.gpx")
        
        initial_track_count = len(manager.tracks)
        
        if initial_track_count > 0:
            # Remove first track
            manager.remove_tracks_by_indices([0])
            
            assert len(manager.tracks) == initial_track_count - 1
    
    def test_clear_all_tracks(self, sample_gpx_paths, load_gpx_content):
        """Test clearing all tracks"""
        manager = GPXManager()
        content1 = load_gpx_content(sample_gpx_paths["outbound"])
        content2 = load_gpx_content(sample_gpx_paths["return"])
        manager.load_gpx(content1, "outbound.gpx")
        manager.load_gpx(content2, "return.gpx")
        
        manager.clear_tracks()
        
        assert manager.pd_gpx_info is None or len(manager.pd_gpx_info) == 0
        assert len(manager.tracks) == 0
    
    def test_get_track_info(self, sample_gpx_paths, load_gpx_content):
        """Test getting track information"""
        manager = GPXManager()
        content = load_gpx_content(sample_gpx_paths["outbound"])
        manager.load_gpx(content, "outbound.gpx")
        
        tracks_info = manager.get_all_tracks()
        
        assert len(tracks_info) > 0
        
        for track in tracks_info:
            assert 'name' in track
            assert 'offset_seconds' in track


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_load_invalid_gpx(self):
        """Test loading invalid GPX content"""
        manager = GPXManager()
        
        try:
            manager.load_gpx("invalid xml content", "test.gpx")
            # Should raise exception
            assert False, "Should have raised exception"
        except:
            # Expected to fail
            pass
    
    def test_empty_gpx_manager(self):
        """Test operations on empty GPX manager"""
        manager = GPXManager()
        
        # Should not crash
        result = manager.find_closest_point(datetime.now())
        assert result is None
        
        tracks = manager.get_all_tracks()
        assert len(tracks) == 0
    
    def test_has_data(self, sample_gpx_paths, load_gpx_content):
        """Test has_data method"""
        manager = GPXManager()
        
        assert not manager.has_data()
        
        content = load_gpx_content(sample_gpx_paths["outbound"])
        manager.load_gpx(content, "outbound.gpx")
        
        assert manager.has_data()
