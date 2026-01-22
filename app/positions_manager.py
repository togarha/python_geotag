"""
Positions Manager - Handles predefined positions from YAML files
"""
import yaml
from typing import Optional, Dict, Any, List


class PositionsManager:
    def __init__(self):
        self.positions: List[Dict[str, Any]] = []
    
    def load_yaml(self, yaml_content: str, filename: str) -> Dict[str, Any]:
        """Load and parse a YAML file with predefined positions"""
        try:
            data = yaml.safe_load(yaml_content)
            
            if not isinstance(data, list):
                raise ValueError("YAML file must contain a list of positions")
            
            loaded_positions = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                # Validate required fields
                if 'name' not in item or 'latitude' not in item or 'longitude' not in item:
                    continue
                
                position = {
                    'name': str(item['name']),
                    'latitude': float(item['latitude']),
                    'longitude': float(item['longitude']),
                    'altitude': float(item['altitude']) if 'altitude' in item and item['altitude'] is not None else None,
                    'source_file': filename
                }
                
                # Validate coordinates
                if position['latitude'] < -90 or position['latitude'] > 90:
                    continue
                if position['longitude'] < -180 or position['longitude'] > 180:
                    continue
                
                loaded_positions.append(position)
            
            # Add to positions list
            self.positions.extend(loaded_positions)
            
            return {
                'filename': filename,
                'count': len(loaded_positions),
                'positions': loaded_positions
            }
        
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing positions: {str(e)}")
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all loaded positions"""
        return self.positions
    
    def remove_positions_by_file(self, filename: str):
        """Remove all positions from a specific file"""
        self.positions = [p for p in self.positions if p['source_file'] != filename]
    
    def clear_all(self):
        """Clear all loaded positions"""
        self.positions = []
    
    def get_positions_by_file(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group positions by source file"""
        result = {}
        for pos in self.positions:
            filename = pos['source_file']
            if filename not in result:
                result[filename] = []
            result[filename].append(pos)
        return result
    
    def has_data(self) -> bool:
        """Check if any positions are loaded"""
        return len(self.positions) > 0
