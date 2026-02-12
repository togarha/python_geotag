"""
Geocoding Service - Provides reverse geocoding from GPS coordinates
Supports multiple providers with fallback
"""
import requests
from typing import Optional, Dict, Any
from time import sleep
import urllib3

# Disable SSL warnings when certificate verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GeocodingService:
    def __init__(self):
        self.providers = ['nominatim', 'photon']
        self.current_provider_index = 0
        
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, str]]:
        """
        Reverse geocode GPS coordinates to location information
        Returns dict with city, sublocation, state, country or None if failed
        """
        if latitude == -360.0 or longitude == -360.0:
            return None
        
        # Try each provider in order
        for _ in range(len(self.providers)):
            provider = self.providers[self.current_provider_index]
            
            try:
                if provider == 'nominatim':
                    result = self._reverse_geocode_nominatim(latitude, longitude)
                elif provider == 'photon':
                    result = self._reverse_geocode_photon(latitude, longitude)
                else:
                    continue
                
                if result:
                    return result
                    
                # Provider returned None, try next provider
                self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)
                    
            except Exception as e:
                print(f"Error with {provider}: {e}")
                # Try next provider
                self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)
        
        return None
    
    def _reverse_geocode_nominatim(self, latitude: float, longitude: float) -> Optional[Dict[str, str]]:
        """
        Use OpenStreetMap Nominatim for reverse geocoding
        Free, but requires rate limiting (1 request per second)
        """
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 18
        }
        headers = {
            'User-Agent': 'GeotagPhotoApp/1.0'
        }
        
        # Note: verify=False disables SSL certificate verification
        # This is necessary in some corporate environments with proxy/firewall
        response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            
            # Extract location components
            # City can be city, town, village, etc.
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('municipality') or 
                   address.get('hamlet'))
            
            # SubLocation could be suburb, neighbourhood, etc.
            sublocation = (address.get('suburb') or 
                          address.get('neighbourhood') or 
                          address.get('quarter'))
            
            # State
            state = (address.get('state') or 
                    address.get('province') or 
                    address.get('region'))
            
            # Country
            country = address.get('country')
            
            # Rate limiting - sleep 1 second between requests
            sleep(1)
            
            return {
                'city': city,
                'sublocation': sublocation,
                'state': state,
                'country': country
            }
        
        return None
    
    def _reverse_geocode_photon(self, latitude: float, longitude: float) -> Optional[Dict[str, str]]:
        """
        Use Photon (OpenStreetMap-based) for reverse geocoding
        Faster than Nominatim, no strict rate limits
        """
        url = "https://photon.komoot.io/reverse"
        params = {
            'lat': latitude,
            'lon': longitude
        }
        
        # Note: verify=False disables SSL certificate verification
        # This is necessary in some corporate environments with proxy/firewall
        response = requests.get(url, params=params, timeout=10, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'features' in data and len(data['features']) > 0:
                properties = data['features'][0].get('properties', {})
                
                # Extract location components
                city = (properties.get('city') or 
                       properties.get('town') or 
                       properties.get('village'))
                
                sublocation = (properties.get('suburb') or 
                              properties.get('neighbourhood') or 
                              properties.get('district'))
                
                state = (properties.get('state') or 
                        properties.get('county'))
                
                country = properties.get('country')
                
                return {
                    'city': city,
                    'sublocation': sublocation,
                    'state': state,
                    'country': country
                }
        
        return None
    
    def get_current_provider(self) -> str:
        """Get the name of the currently selected provider"""
        return self.providers[self.current_provider_index]
    
    def set_provider(self, provider: str):
        """Set the geocoding provider"""
        if provider in self.providers:
            self.current_provider_index = self.providers.index(provider)
