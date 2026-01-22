"""
Elevation Service - Fetches elevation data from various APIs
"""
import requests
import urllib3
from typing import Optional, Dict

# Disable SSL warnings for APIs with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ElevationService:
    def __init__(self):
        self.services = {
            'open-elevation': self._open_elevation,
            'opentopodata': self._opentopodata,
            'google': self._google_elevation
        }
    
    def get_elevation(self, latitude: float, longitude: float, service: str = 'open-elevation') -> Optional[float]:
        """
        Get elevation for given coordinates using specified service
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            service: Service name ('open-elevation', 'opentopodata', 'google')
        
        Returns:
            Elevation in meters or None if failed
        """
        if service not in self.services:
            raise ValueError(f"Unknown elevation service: {service}")
        
        try:
            return self.services[service](latitude, longitude)
        except Exception as e:
            print(f"Error fetching elevation from {service}: {e}")
            return None
    
    def _open_elevation(self, latitude: float, longitude: float) -> Optional[float]:
        """Fetch elevation from Open-Elevation API"""
        url = "https://api.open-elevation.com/api/v1/lookup"
        params = {
            "locations": f"{latitude},{longitude}"
        }
        
        # Disable SSL verification for open-elevation due to certificate issues
        response = requests.get(url, params=params, timeout=10, verify=False)
        response.raise_for_status()
        
        data = response.json()
        if data.get('results') and len(data['results']) > 0:
            return float(data['results'][0]['elevation'])
        
        return None
    
    def _opentopodata(self, latitude: float, longitude: float) -> Optional[float]:
        """Fetch elevation from OpenTopoData API"""
        # Using SRTM 90m dataset (global coverage)
        url = f"https://api.opentopodata.org/v1/srtm90m"
        params = {
            "locations": f"{latitude},{longitude}"
        }
        
        # Disable SSL verification for opentopodata due to certificate issues
        response = requests.get(url, params=params, timeout=10, verify=False)
        response.raise_for_status()
        
        data = response.json()
        if data.get('results') and len(data['results']) > 0:
            elevation = data['results'][0].get('elevation')
            if elevation is not None:
                return float(elevation)
        
        return None
    
    def _google_elevation(self, latitude: float, longitude: float, api_key: Optional[str] = None) -> Optional[float]:
        """
        Fetch elevation from Google Maps Elevation API
        Note: Requires API key. This is a placeholder implementation.
        """
        if not api_key:
            # Google requires API key, return None if not provided
            return None
        
        url = "https://maps.googleapis.com/maps/api/elevation/json"
        params = {
            "locations": f"{latitude},{longitude}",
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == 'OK' and data.get('results'):
            return float(data['results'][0]['elevation'])
        
        return None
