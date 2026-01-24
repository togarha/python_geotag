"""
Photo Geotagging Application
Main FastAPI server
"""
import argparse
import uvicorn
from app.server import app, set_config_manager
from app.config_manager import ConfigManager

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Photo Geotagging Application')
    parser.add_argument('--config', '-c', type=str, help='Path to configuration file (YAML)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    args = parser.parse_args()
    
    # Initialize config manager
    config_manager = ConfigManager(args.config)
    set_config_manager(config_manager)
    
    # Start server
    print(f"Starting server on {args.host}:{args.port}")
    if args.config:
        print(f"Using configuration file: {args.config}")
    
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

