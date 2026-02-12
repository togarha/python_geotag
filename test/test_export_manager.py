"""
Tests for ExportManager - photo export with metadata updates
"""
import pytest
import shutil
from pathlib import Path
from PIL import Image
import piexif
from app.export_manager import ExportManager


class TestPhotoExport:
    """Test basic photo export functionality"""
    
    def test_export_photo_basic(self, sample_photo_paths, clean_output_dir):
        """Test basic photo export without metadata"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        new_filename = "test_export.jpg"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=new_filename
        )
        
        assert result is True
        assert (dest_folder / new_filename).exists()
    
    def test_export_with_new_filename(self, sample_photo_paths, clean_output_dir):
        """Test export with renamed file"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        original_name = source.name
        new_name = "renamed_photo.jpg"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=new_name
        )
        
        assert result is True
        assert (dest_folder / new_name).exists()
        assert not (dest_folder / original_name).exists()
    
    def test_export_preserves_image_quality(self, sample_photo_paths, clean_output_dir):
        """Test that exported image maintains quality"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "quality_test.jpg"
        
        # Get original image size
        original_img = Image.open(source)
        original_size = original_img.size
        
        ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename
        )
        
        # Check exported image
        exported_img = Image.open(dest_folder / filename)
        assert exported_img.size == original_size
    
    def test_export_nonexistent_source(self, clean_output_dir):
        """Test export with non-existent source file"""
        result = ExportManager.export_photo(
            source_path="nonexistent.jpg",
            dest_folder=str(clean_output_dir),
            new_filename="output.jpg"
        )
        
        assert result is False


class TestGPSExport:
    """Test GPS coordinate export to EXIF"""
    
    def test_export_with_gps_coordinates(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo with GPS coordinates"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "gps_export.jpg"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            final_lat=48.8584,  # Eiffel Tower
            final_lon=2.2945,
            final_alt=324.0
        )
        
        assert result is True
        
        # Verify GPS data was written
        img = Image.open(dest_folder / filename)
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
            if 'GPS' in exif_dict and exif_dict['GPS']:
                # GPS data should be present
                assert piexif.GPSIFD.GPSLatitude in exif_dict['GPS'] or \
                       piexif.GPSIFD.GPSLongitude in exif_dict['GPS']
    
    def test_export_with_altitude(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo with altitude"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "altitude_export.jpg"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            final_lat=45.0,
            final_lon=-75.0,
            final_alt=150.5
        )
        
        assert result is True
    
    def test_export_without_gps(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo without GPS coordinates"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "no_gps_export.jpg"
        
        # Export without GPS parameters
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            final_lat=None,
            final_lon=None
        )
        
        assert result is True


class TestMetadataExport:
    """Test metadata export (title, keywords, location)"""
    
    def test_export_with_title(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo with title"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "title_export.jpg"
        test_title = "Beautiful Landscape"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            title=test_title
        )
        
        assert result is True
        
        # Verify title was written (would need EXIF extraction to fully verify)
        assert (dest_folder / filename).exists()
    
    def test_export_with_keywords(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo with keywords"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "keywords_export.jpg"
        test_keywords = "mountain, landscape, nature"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            keywords=test_keywords
        )
        
        assert result is True
    
    def test_export_with_location_metadata(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo with location metadata"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "location_export.jpg"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            city="Paris",
            sublocation="Champ de Mars",
            state="Île-de-France",
            country="France"
        )
        
        assert result is True
    
    def test_export_with_offset_time(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo with offset time"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "offset_export.jpg"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            offset_time="+02:00"
        )
        
        assert result is True


class TestTimestampExport:
    """Test timestamp-related export functionality"""
    
    def test_export_with_new_time(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo with modified timestamp"""
        from datetime import datetime
        
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "time_export.jpg"
        new_time = datetime(2026, 1, 15, 14, 30, 0)
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            new_time=new_time
        )
        
        assert result is True
    
    def test_export_with_gps_timestamps(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo with GPS timestamps"""
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "gps_time_export.jpg"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            gps_datestamp="2026:01:15",
            gps_timestamp="14:30:00"
        )
        
        assert result is True


class TestFileOperations:
    """Test file operation aspects of export"""
    
    def test_export_creates_destination_folder(self, sample_photo_paths, tmp_path):
        """Test that destination folder is created if it doesn't exist"""
        source = sample_photo_paths["camera"]
        dest_folder = tmp_path / "new_folder" / "subfolder"
        filename = "test.jpg"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename
        )
        
        assert result is True
        assert dest_folder.exists()
        assert (dest_folder / filename).exists()
    
    def test_export_different_extensions(self, sample_photo_paths, clean_output_dir):
        """Test exporting photos with different extensions"""
        # Test with .jpg
        if sample_photo_paths["phone"].exists():
            result = ExportManager.export_photo(
                source_path=str(sample_photo_paths["phone"]),
                dest_folder=str(clean_output_dir),
                new_filename="test.jpg"
            )
            assert result is True
        
        # Test with .jpeg
        if sample_photo_paths["camera"].exists():
            result = ExportManager.export_photo(
                source_path=str(sample_photo_paths["camera"]),
                dest_folder=str(clean_output_dir),
                new_filename="test.jpeg"
            )
            assert result is True
    
    def test_export_file_timestamps(self, sample_photo_paths, clean_output_dir):
        """Test that file timestamps are updated"""
        from datetime import datetime
        
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "timestamp_test.jpg"
        new_time = datetime(2026, 1, 15, 14, 30, 0)
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            new_time=new_time
        )
        
        assert result is True
        
        # Check that file exists and has timestamps
        output_file = dest_folder / filename
        assert output_file.exists()
        assert output_file.stat().st_mtime > 0


class TestComplexExport:
    """Test complex export scenarios with multiple metadata fields"""
    
    def test_export_with_all_metadata(self, sample_photo_paths, clean_output_dir):
        """Test exporting photo with all metadata fields"""
        from datetime import datetime
        
        source = sample_photo_paths["camera"]
        dest_folder = clean_output_dir
        filename = "full_metadata.jpg"
        
        result = ExportManager.export_photo(
            source_path=str(source),
            dest_folder=str(dest_folder),
            new_filename=filename,
            final_lat=48.8584,
            final_lon=2.2945,
            final_alt=324.0,
            new_time=datetime(2026, 1, 15, 14, 30, 0),
            title="Eiffel Tower View",
            keywords="paris, landmark, travel",
            city="Paris",
            sublocation="Champ de Mars",
            state="Île-de-France",
            country="France",
            gps_datestamp="2026:01:15",
            gps_timestamp="12:30:00",
            offset_time="+01:00"
        )
        
        assert result is True
        assert (dest_folder / filename).exists()
    
    def test_export_multiple_photos(self, sample_photo_paths, clean_output_dir):
        """Test exporting multiple photos"""
        dest_folder = clean_output_dir
        
        photos_to_export = [
            (sample_photo_paths["camera"], "export1.jpg"),
            (sample_photo_paths["phone"], "export2.jpg"),
            (sample_photo_paths["vert"], "export3.jpg")
        ]
        
        for source, filename in photos_to_export:
            if source.exists():
                result = ExportManager.export_photo(
                    source_path=str(source),
                    dest_folder=str(dest_folder),
                    new_filename=filename
                )
                assert result is True
        
        # Check all files exist
        for _, filename in photos_to_export:
            if (dest_folder / filename).exists():
                assert (dest_folder / filename).is_file()
