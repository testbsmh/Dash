#!/usr/bin/env python3
"""
WorkspaceONE App Intelligence Dashboard
Desktop application built with PyWebView

Run with: python main.py
"""

import webview
import json
import os
import sys
import logging
import traceback

# Setup logging FIRST - before any other imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ws1_app.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('WS1Main')
logger.info("="*60)
logger.info("WorkspaceONE App Intelligence - Starting...")
logger.info("="*60)

# Now import our modules
from config import Config
from api import WS1API

# Get the directory where the script is located
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    logger.info(f"Running as frozen executable, BASE_DIR: {BASE_DIR}")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Running as script, BASE_DIR: {BASE_DIR}")


class API:
    """
    Python API exposed to JavaScript.
    
    IMPORTANT: Only simple types (dict, list, str, int, bool, None) should be 
    returned from these methods. PyWebView serializes the entire class, so 
    avoid storing non-serializable objects as instance attributes.
    """
    
    def __init__(self):
        logger.info("Initializing Python API bridge...")
        
        # Store config as a simple dict, not the Config object
        try:
            self._config_manager = Config()
            self._config_data = self._config_manager.get_all()
            logger.info("Config manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize config: {e}", exc_info=True)
            self._config_manager = None
            self._config_data = {}
        
        self._ws1_api = None
        logger.info("Python API bridge initialized")
    
    def get_config(self):
        """Get current configuration as a simple dict."""
        logger.info("JavaScript called: get_config()")
        try:
            if self._config_manager:
                self._config_data = self._config_manager.get_all()
            result = self._config_data.copy()
            logger.debug(f"Returning config with keys: {list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"Error in get_config: {e}", exc_info=True)
            return {}
    
    def save_config(self, config_data):
        """Save configuration."""
        logger.info("JavaScript called: save_config()")
        logger.debug(f"Config data received: {list(config_data.keys()) if config_data else 'None'}")
        
        try:
            if not config_data:
                logger.error("No config data provided")
                return {'success': False, 'error': 'No config data provided'}
            
            if self._config_manager:
                success = self._config_manager.save(config_data)
                if success:
                    self._config_data = self._config_manager.get_all()
                    logger.info("Config saved successfully")
                    return {'success': True}
                else:
                    logger.error("Config manager returned False")
                    return {'success': False, 'error': 'Failed to save config'}
            else:
                logger.error("Config manager not available")
                return {'success': False, 'error': 'Config manager not initialized'}
                
        except Exception as e:
            logger.error(f"Error in save_config: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def fetch_data(self):
        """Fetch all application data from WorkspaceONE."""
        logger.info("JavaScript called: fetch_data()")
        
        try:
            # Check if credentials are configured
            client_id = self._config_data.get('clientId', '')
            client_secret = self._config_data.get('clientSecret', '')
            
            logger.debug(f"Client ID configured: {bool(client_id)}")
            logger.debug(f"Client Secret configured: {bool(client_secret)}")
            
            if not client_id or not client_secret:
                logger.info("No credentials configured, returning demo mode flag")
                return {
                    'success': False, 
                    'demo': True, 
                    'message': 'No credentials configured - using demo mode'
                }
            
            # Initialize API client with current config
            logger.info("Initializing WS1 API client...")
            
            # Create a simple config-like object for the API
            class SimpleConfig:
                def __init__(self, data):
                    self._data = data
                def get(self, key, default=None):
                    return self._data.get(key, default)
            
            simple_config = SimpleConfig(self._config_data)
            self._ws1_api = WS1API(simple_config)
            
            # Fetch data
            logger.info("Fetching Intelligence data...")
            rows = self._ws1_api.fetch_intelligence_data()
            
            logger.info(f"Successfully fetched {len(rows)} records")
            return {
                'success': True, 
                'data': rows, 
                'count': len(rows)
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in fetch_data: {error_msg}", exc_info=True)
            return {
                'success': False, 
                'error': error_msg,
                'traceback': traceback.format_exc()
            }
    
    def fetch_assignments(self, app_id, app_type):
        """Fetch assignments for a specific app."""
        logger.info(f"JavaScript called: fetch_assignments(app_id={app_id}, app_type={app_type})")
        
        try:
            if not self._ws1_api:
                logger.warning("WS1 API not initialized, initializing now...")
                
                class SimpleConfig:
                    def __init__(self, data):
                        self._data = data
                    def get(self, key, default=None):
                        return self._data.get(key, default)
                
                simple_config = SimpleConfig(self._config_data)
                self._ws1_api = WS1API(simple_config)
            
            assignments = self._ws1_api.fetch_assignments(app_id, app_type)
            
            logger.info(f"Retrieved {len(assignments)} assignments")
            return {'success': True, 'data': assignments}
            
        except Exception as e:
            logger.error(f"Error in fetch_assignments: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


def main():
    """Main entry point."""
    logger.info("Starting main application...")
    
    try:
        # Initialize API
        logger.info("Creating API instance...")
        api = API()
        
        # Get HTML file path
        html_path = os.path.join(BASE_DIR, 'index.html')
        logger.info(f"HTML file path: {html_path}")
        
        if not os.path.exists(html_path):
            logger.error(f"HTML file not found at: {html_path}")
            raise FileNotFoundError(f"index.html not found at {html_path}")
        
        # Create window
        logger.info("Creating webview window...")
        window = webview.create_window(
            'WorkspaceONE App Intelligence',
            html_path,
            js_api=api,
            width=1400,
            height=900,
            min_size=(1000, 700),
            resizable=True,
            text_select=True
        )
        
        logger.info("Starting webview...")
        logger.info("="*60)
        logger.info("Application window should appear now")
        logger.info("Check ws1_app.log for detailed logs")
        logger.info("="*60)
        
        # Start the webview
        webview.start(debug=True)  # Enable debug mode for more info
        
        logger.info("Application closed")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        print(f"\n{'='*60}")
        print(f"FATAL ERROR: {e}")
        print(f"{'='*60}")
        print(f"\nFull traceback:\n{traceback.format_exc()}")
        print(f"\nCheck ws1_app.log for more details")
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == '__main__':
    main()
