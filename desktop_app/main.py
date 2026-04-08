#!/usr/bin/env python3
"""
WorkspaceONE App Intelligence Dashboard
Desktop application built with PyWebView - FULLY PYTHON DRIVEN

Run with: python main.py
"""

import webview
import json
import os
import sys
import logging
import traceback
import threading
import time

# Setup logging FIRST
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

# Get the directory where the script is located
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    logger.info(f"Running as frozen executable, BASE_DIR: {BASE_DIR}")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Running as script, BASE_DIR: {BASE_DIR}")

# Import after logging setup
from config import Config
from api import WS1API


class PythonAPI:
    """
    Python API exposed to JavaScript via pywebview.
    All methods return JSON-serializable dicts.
    """
    
    def __init__(self, window=None):
        logger.info("Initializing PythonAPI...")
        self.window = window
        self._config = Config()
        self._ws1_api = None
        logger.info("PythonAPI initialized")
    
    def set_window(self, window):
        """Set the window reference after creation."""
        self.window = window
        logger.info("Window reference set")
    
    def log(self, message):
        """Log a message from JavaScript."""
        logger.info(f"[JS] {message}")
        return True
    
    def get_config(self):
        """Get current configuration."""
        logger.info("get_config() called")
        try:
            config = self._config.get_all()
            logger.info(f"Returning config with {len(config)} keys")
            # Mask secrets in log
            safe_log = {k: ('***' if 'secret' in k.lower() or 'pass' in k.lower() else v) for k, v in config.items()}
            logger.debug(f"Config values: {safe_log}")
            return {'success': True, 'data': config}
        except Exception as e:
            logger.error(f"get_config error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def save_config(self, config_data):
        """Save configuration to file."""
        logger.info("save_config() called")
        try:
            if not config_data:
                return {'success': False, 'error': 'No config data provided'}
            
            logger.debug(f"Saving config keys: {list(config_data.keys())}")
            success = self._config.save(config_data)
            
            if success:
                logger.info("Config saved successfully")
                return {'success': True}
            else:
                logger.error("Config save returned False")
                return {'success': False, 'error': 'Failed to save configuration'}
                
        except Exception as e:
            logger.error(f"save_config error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def fetch_data(self, app_type_filter='', platform_filter=''):
        """Fetch all application data from WorkspaceONE APIs."""
        logger.info("="*40)
        logger.info("fetch_data() called - Starting data fetch")
        logger.info(f"  App type filter: {app_type_filter or 'All'}")
        logger.info(f"  Platform filter: {platform_filter or 'All'}")
        logger.info("="*40)
        
        try:
            # Get fresh config
            config = self._config.get_all()
            
            client_id = config.get('clientId', '').strip()
            client_secret = config.get('clientSecret', '').strip()
            
            logger.info(f"Client ID: {'[SET: ' + client_id[:10] + '...]' if client_id else '[EMPTY]'}")
            logger.info(f"Client Secret: {'[SET]' if client_secret else '[EMPTY]'}")
            
            if not client_id or not client_secret:
                logger.warning("No credentials configured - returning demo flag")
                return {
                    'success': False,
                    'demo': True,
                    'message': 'No API credentials configured. Click Configure to add credentials, then Sync Data.'
                }
            
            # Create API client
            logger.info("Creating WS1API client...")
            self._ws1_api = WS1API(self._config)
            
            # Get fetch settings from config
            max_records = int(self._config.get('maxRecords', 10000) or 0)
            page_size = int(self._config.get('pageSize', 1000) or 1000)
            
            # Fetch data with limits
            logger.info(f"Calling fetch_intelligence_data(appType={app_type_filter}, platform={platform_filter}, max={max_records}, pageSize={page_size})...")
            rows = self._ws1_api.fetch_intelligence_data(
                app_type_filter=app_type_filter,
                platform_filter=platform_filter,
                max_records=max_records,
                page_size=page_size
            )
            
            logger.info(f"SUCCESS: Retrieved {len(rows)} records")
            return {
                'success': True,
                'data': rows,
                'count': len(rows)
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"fetch_data FAILED: {error_msg}", exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'demo': True
            }
    
    def fetch_assignments(self, app_id, app_type):
        """Fetch assignments for a specific app."""
        logger.info(f"fetch_assignments() called: app_id={app_id}, app_type={app_type}")
        
        try:
            if not self._ws1_api:
                self._ws1_api = WS1API(self._config)
            
            assignments = self._ws1_api.fetch_assignments(app_id, app_type)
            logger.info(f"Retrieved {len(assignments)} assignments")
            return {'success': True, 'data': assignments}
            
        except Exception as e:
            logger.error(f"fetch_assignments error: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'data': []}
    
    def test_connection(self):
        """Test API connection with current credentials."""
        logger.info("test_connection() called")
        
        try:
            config = self._config.get_all()
            client_id = config.get('clientId', '').strip()
            client_secret = config.get('clientSecret', '').strip()
            
            if not client_id or not client_secret:
                return {
                    'success': False,
                    'error': 'Client ID and Secret are required'
                }
            
            # Try to get a token
            api = WS1API(self._config)
            token = api.get_token()
            
            if token:
                logger.info("Connection test SUCCESS - token obtained")
                return {'success': True, 'message': 'Connection successful!'}
            else:
                return {'success': False, 'error': 'Failed to obtain token'}
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


def get_html_content():
    """Load and return the HTML content."""
    html_path = os.path.join(BASE_DIR, 'index.html')
    logger.info(f"Loading HTML from: {html_path}")
    
    if not os.path.exists(html_path):
        raise FileNotFoundError(f"index.html not found at {html_path}")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    """Main entry point."""
    logger.info("Starting main application...")
    
    try:
        # Create API instance
        api = PythonAPI()
        
        # Get HTML path
        html_path = os.path.join(BASE_DIR, 'index.html')
        
        if not os.path.exists(html_path):
            logger.error(f"HTML file not found: {html_path}")
            print(f"\nERROR: index.html not found at {html_path}")
            input("Press Enter to exit...")
            return
        
        logger.info(f"Creating window with HTML: {html_path}")
        
        # Create window
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
        
        # Set window reference in API
        api.set_window(window)
        
        logger.info("Starting webview...")
        print("\n" + "="*60)
        print("Application starting...")
        print("Check 'ws1_app.log' for detailed logs")
        print("="*60 + "\n")
        
        # Start webview (debug=False to hide Chrome DevTools)
        webview.start(debug=False)
        
        logger.info("Application closed normally")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        print(f"\nTraceback:\n{traceback.format_exc()}")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == '__main__':
    main()
