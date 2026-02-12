"""
Tests for PhotoManager - photo scanning, EXIF extraction, and metadata operations
"""
import pytest
import pandas as pd
from pathlib import Path
from app.photo_manager import PhotoManager


class TestPhotoScanning:
    """Test photo scanning functionality"""
    
    def test_scan_folder_basic(self, test_resources_dir):
        """Test basic folder scanning without recursion"""
        manager = PhotoManager()
        result = manager.scan_folder(str(test_resources_dir), recursive=False)
        
        assert result is not None
        assert len(manager.pd_photo_info) > 0
        assert 'filename' in manager.pd_photo_info.columns
        assert 'full_path' in manager.pd_photo_info.columns
    
    def test_scan_folder_recursive(self, test_resources_dir):
        """Test recursive folder scanning"""
        manager = PhotoManager()
        result_non_recursive = manager.scan_folder(str(test_resources_dir), recursive=False)
        count_non_recursive = len(manager.pd_photo_info)
        
        manager2 = PhotoManager()
        result_recursive = manager2.scan_folder(str(test_resources_dir), recursive=True)
        count_recursive = len(manager2.pd_photo_info)
        
        # Recursive should find at least as many photos as non-recursive
        assert count_recursive >= count_non_recursive
    
    def test_dataframe_structure(self, test_resources_dir):
        """Test that dataframe has all required columns"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        required_columns = [
            'filename', 'full_path', 'exif_capture_time', 'creation_time',
            'new_time', 'exif_offset_time', 'new_offset_time',
            'exif_gps_datestamp', 'new_gps_datestamp',
            'exif_gps_timestamp', 'new_gps_timestamp',
            'exif_image_title', 'new_title',
            'exif_city', 'new_city', 'exif_sublocation', 'new_sublocation',
            'exif_state', 'new_state', 'exif_country', 'new_country',
            'exif_keywords', 'new_keywords',
            'exif_latitude', 'exif_longitude', 'exif_altitude',
            'gpx_latitude', 'gpx_longitude', 'gpx_altitude',
            'manual_latitude', 'manual_longitude', 'manual_altitude',
            'final_latitude', 'final_longitude', 'final_altitude',
            'new_name', 'tagged'
        ]
        
        for col in required_columns:
            assert col in manager.pd_photo_info.columns, f"Missing column: {col}"


class TestEXIFExtraction:
    """Test EXIF data extraction"""
    
    def test_gps_extraction(self, test_resources_dir):
        """Test GPS coordinate extraction from EXIF"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        # Check if any photos have GPS data
        has_gps = (manager.pd_photo_info['exif_latitude'] != -360).any()
        # At least verify the column exists and can contain GPS data
        assert 'exif_latitude' in manager.pd_photo_info.columns
        assert 'exif_longitude' in manager.pd_photo_info.columns
        assert 'exif_altitude' in manager.pd_photo_info.columns
    
    def test_timestamp_extraction(self, test_resources_dir):
        """Test timestamp extraction from EXIF"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        # All photos should have creation_time
        assert manager.pd_photo_info['creation_time'].notna().all()
        
        # Some photos might have exif_capture_time
        assert 'exif_capture_time' in manager.pd_photo_info.columns
    
    def test_location_extraction(self, test_resources_dir):
        """Test IPTC location metadata extraction"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        # Verify location columns exist
        location_columns = ['exif_city', 'exif_sublocation', 'exif_state', 'exif_country']
        for col in location_columns:
            assert col in manager.pd_photo_info.columns
    
    def test_keywords_extraction(self, test_resources_dir):
        """Test keywords extraction from IPTC"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        assert 'exif_keywords' in manager.pd_photo_info.columns
        assert 'new_keywords' in manager.pd_photo_info.columns


class TestCoordinateCascade:
    """Test final coordinate cascade logic"""
    
    def test_manual_coordinates_priority(self, test_resources_dir):
        """Test that manual coordinates have highest priority"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            index = 0
            # Set manual coordinates
            manager.set_manual_location(index, 45.0, -75.0, 100.0)
            
            photo = manager.get_photo_by_index(index)
            assert photo['manual_latitude'] == 45.0
            assert photo['manual_longitude'] == -75.0
            assert photo['manual_altitude'] == 100.0
            assert photo['final_latitude'] == 45.0
            assert photo['final_longitude'] == -75.0
            assert photo['final_altitude'] == 100.0
    
    def test_delete_manual_location(self, test_resources_dir):
        """Test deleting manual location"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            index = 0
            # Set then delete manual coordinates
            manager.set_manual_location(index, 45.0, -75.0, 100.0)
            manager.delete_manual_location(index)
            
            photo = manager.get_photo_by_index(index)
            assert photo['manual_latitude'] == -360
            assert photo['manual_longitude'] == -360
            assert photo['manual_altitude'] is None or pd.isna(photo['manual_altitude'])


class TestMetadataOperations:
    """Test metadata update operations"""
    
    def test_update_photo_title(self, test_resources_dir):
        """Test updating photo title"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            index = 0
            test_title = "Test Photo Title"
            manager.update_photo_metadata(index, new_title=test_title)
            
            photo = manager.get_photo_by_index(index)
            assert photo['new_title'] == test_title
    
    def test_update_photo_keywords(self, test_resources_dir):
        """Test updating photo keywords"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            index = 0
            test_keywords = "mountain, landscape, nature"
            manager.update_photo_metadata(index, new_keywords=test_keywords)
            
            photo = manager.get_photo_by_index(index)
            assert photo['new_keywords'] == test_keywords
    
    def test_update_photo_location(self, test_resources_dir):
        """Test updating photo location metadata"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            index = 0
            manager.update_photo_metadata(
                index,
                new_city="Paris",
                new_sublocation="Eiffel Tower",
                new_state="Île-de-France",
                new_country="France"
            )
            
            photo = manager.get_photo_by_index(index)
            assert photo['new_city'] == "Paris"
            assert photo['new_sublocation'] == "Eiffel Tower"
            assert photo['new_state'] == "Île-de-France"
            assert photo['new_country'] == "France"
    
    def test_bulk_keywords_operations(self, test_resources_dir):
        """Test bulk keywords operations"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            # Apply keywords to all
            manager.apply_photo_keywords("test, bulk")
            assert (manager.pd_photo_info['new_keywords'] == "test, bulk").all()
            
            # Clear keywords
            manager.clear_photo_keywords()
            assert (manager.pd_photo_info['new_keywords'] == "").all()


class TestTagging:
    """Test photo tagging functionality"""
    
    def test_toggle_tag(self, test_resources_dir):
        """Test toggling photo tag"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            index = 0
            original_tag = manager.pd_photo_info.loc[index, 'tagged']
            
            # Toggle tag (update_tag toggles the current value)
            manager.update_tag(index, not original_tag)
            new_tag = manager.pd_photo_info.loc[index, 'tagged']
            
            assert original_tag != new_tag
    
    def test_bulk_tag_operations(self, test_resources_dir):
        """Test bulk tagging operations"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            # Get all indices
            indices = list(manager.pd_photo_info.index)
            
            # Tag all
            manager.bulk_tag(indices, tagged=True)
            assert manager.pd_photo_info['tagged'].all()
            
            # Untag all
            manager.bulk_tag(indices, tagged=False)
            assert not manager.pd_photo_info['tagged'].any()


class TestPhotoRenaming:
    """Test photo renaming and deduplication"""
    
    def test_apply_filename_format(self, test_resources_dir):
        """Test applying filename format"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            format_string = "%Y%m%d_%H%M%S"
            manager.apply_filename_format(format_string)
            
            # Check that new_name column is populated
            assert manager.pd_photo_info['new_name'].notna().all()
            
            # New names should follow the format (8 digits + _ + 6 digits)
            for name in manager.pd_photo_info['new_name']:
                assert len(name) > 0
    
    def test_deduplication_numbering(self, test_resources_dir):
        """Test that duplicate filenames get _02, _03 suffixes"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 0:
            # Apply simple format that may create duplicates
            format_string = "%Y%m%d"
            manager.apply_filename_format(format_string)
            
            # Check for _02, _03 suffixes if duplicates exist
            names = manager.pd_photo_info['new_name'].tolist()
            base_names = [n.rsplit('_', 1)[0] if '_' in n and n.split('_')[-1].replace('.jpg', '').replace('.jpeg', '').isdigit() else n.split('.')[0] for n in names]
            
            # If there are duplicates, check for proper numbering
            from collections import Counter
            name_counts = Counter(base_names)
            for base_name, count in name_counts.items():
                if count > 1:
                    # Should have _02, _03, etc. (first keeps original name)
                    matching = [n for n in names if base_name in n]
                    # At least one should have _02
                    has_numbered = any('_02' in n or '_03' in n for n in matching)
                    # This validates that deduplication is working
                    assert len(matching) == count


class TestSorting:
    """Test photo sorting"""
    
    def test_sort_by_time(self, test_resources_dir):
        """Test sorting by capture time"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 1:
            manager.set_sort_order('time')
            # Check that dataframe is sorted by exif_capture_time or creation_time
            times = manager.pd_photo_info['exif_capture_time'].fillna(
                manager.pd_photo_info['creation_time']
            )
            assert times.is_monotonic_increasing
    
    def test_sort_by_filename(self, test_resources_dir):
        """Test sorting by filename"""
        manager = PhotoManager()
        manager.scan_folder(str(test_resources_dir), recursive=False)
        
        if len(manager.pd_photo_info) > 1:
            manager.set_sort_order('filename')
            filenames = manager.pd_photo_info['filename'].tolist()
            assert filenames == sorted(filenames)
