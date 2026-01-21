"""
GPX Manager - Handles GPX file parsing and track management
"""
import pandas as pd
import gpxpy
import gpxpy.gpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List


class GPXManager:
    def __init__(self):
        self.pd_gpx_info: Optional[pd.DataFrame] = None
        self.tracks: List[Dict[str, Any]] = []
    
    def load_gpx(self, gpx_content: str, filename: str) -> Dict[str, Any]:
        """Load and parse a GPX file"""
        gpx = gpxpy.parse(gpx_content)
        
        points = []
        track_info = {
            'filename': filename,
            'name': '',
            'points': [],
            'bounds': None
        }
        
        for track in gpx.tracks:
            if not track_info['name']:
                track_info['name'] = track.name or filename
            
            for segment in track.segments:
                for point in segment.points:
                    point_data = {
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'elevation': point.elevation,
                        'time': point.time,
                        'track_name': track.name or filename
                    }
                    points.append(point_data)
                    track_info['points'].append({
                        'lat': point.latitude,
                        'lng': point.longitude
                    })
        
        # Calculate bounds
        if track_info['points']:
            lats = [p['lat'] for p in track_info['points']]
            lngs = [p['lng'] for p in track_info['points']]
            track_info['bounds'] = {
                'north': max(lats),
                'south': min(lats),
                'east': max(lngs),
                'west': min(lngs)
            }
        
        # Check if track with same name already exists
        existing_track_index = None
        for idx, existing_track in enumerate(self.tracks):
            if existing_track['name'] == track_info['name']:
                existing_track_index = idx
                break
        
        if existing_track_index is not None:
            return track_info  # Return but don't add
        
        # Add to tracks list
        self.tracks.append(track_info)
        
        # Create or append to DataFrame
        if points:
            new_df = pd.DataFrame(points)
            if self.pd_gpx_info is None:
                self.pd_gpx_info = new_df
            else:
                self.pd_gpx_info = pd.concat([self.pd_gpx_info, new_df], ignore_index=True)
            
            # Sort by time
            if 'time' in self.pd_gpx_info.columns:
                self.pd_gpx_info = self.pd_gpx_info.sort_values('time').reset_index(drop=True)
        
        return track_info
    
    def has_data(self) -> bool:
        """Check if any GPX data is loaded"""
        return self.pd_gpx_info is not None and not self.pd_gpx_info.empty
    
    def get_all_tracks(self) -> List[Dict[str, Any]]:
        """Get all loaded track information"""
        return self.tracks
    
    def clear_tracks(self):
        """Clear all loaded tracks"""
        self.tracks = []
        self.pd_gpx_info = None
    
    def remove_tracks_by_indices(self, indices: List[int]):
        """Remove specific tracks by their indices"""
        # Sort indices in reverse to maintain correct positions during removal
        sorted_indices = sorted(indices, reverse=True)
        
        # Collect track names to remove from DataFrame
        track_names_to_remove = []
        for idx in sorted_indices:
            if 0 <= idx < len(self.tracks):
                track_name = self.tracks[idx]['name']
                track_names_to_remove.append(track_name)
                self.tracks.pop(idx)
        
        # Remove points from DataFrame by filtering out the track names
        if self.pd_gpx_info is not None and 'track_name' in self.pd_gpx_info.columns:
            # Filter out rows where track_name is in the removal list
            self.pd_gpx_info = self.pd_gpx_info[~self.pd_gpx_info['track_name'].isin(track_names_to_remove)]
            self.pd_gpx_info = self.pd_gpx_info.reset_index(drop=True)
            
            # If no data remains, set to None
            if self.pd_gpx_info.empty:
                self.pd_gpx_info = None
    
    def find_closest_point(self, target_time: datetime, time_window_minutes: int = 5) -> Optional[Dict[str, float]]:
        """Find the closest GPX point to a given time within a time window"""
        if not self.has_data():
            return None
        
        if 'time' not in self.pd_gpx_info.columns:
            return None
        
        # Filter points within time window
        time_min = target_time - timedelta(minutes=time_window_minutes)
        time_max = target_time + timedelta(minutes=time_window_minutes)
        
        mask = (self.pd_gpx_info['time'] >= time_min) & (self.pd_gpx_info['time'] <= time_max)
        nearby_points = self.pd_gpx_info[mask]
        
        # Find closest point by time difference
        nearby_points = nearby_points.copy()
        nearby_points['time_diff'] = abs((nearby_points['time'] - target_time).dt.total_seconds())
        closest = nearby_points.loc[nearby_points['time_diff'].idxmin()]
        
        return {
            'latitude': closest['latitude'],
            'longitude': closest['longitude'],
            'elevation': closest['elevation'] if pd.notna(closest['elevation']) else None,
            'time_diff_seconds': closest['time_diff']
        }
