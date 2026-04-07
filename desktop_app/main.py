#!/usr/bin/env python3
"""
WorkspaceONE App Intelligence Dashboard
Desktop application built with PyWebView
"""

import webview
import json
import threading
import os
import sys
from config import Config
from api import WS1API

# Get the directory where the script is located
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class API:
    """Python API exposed to JavaScript."""
    
    def __init__(self):
        self.config = Config()
        self.ws1_api = None
    
    def get_config(self):
        """Get current configuration."""
        return self.config.get_all()
    
    def save_config(self, config_data):
        """Save configuration."""
        try:
            self.config.save(config_data)
            self.ws1_api = WS1API(self.config)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fetch_data(self):
        """Fetch all application data from WorkspaceONE."""
        try:
            if not self.ws1_api:
                self.ws1_api = WS1API(self.config)
            
            client_id = self.config.get('clientId')
            client_secret = self.config.get('clientSecret')
            
            if not client_id or not client_secret:
                return {'success': False, 'demo': True, 'message': 'No credentials configured'}
            
            rows = self.ws1_api.fetch_intelligence_data()
            return {'success': True, 'data': rows, 'count': len(rows)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fetch_assignments(self, app_id, app_type):
        """Fetch assignments for a specific app."""
        try:
            if not self.ws1_api:
                self.ws1_api = WS1API(self.config)
            
            assignments = self.ws1_api.fetch_assignments(app_id, app_type)
            return {'success': True, 'data': assignments}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def load_html():
    """Load the HTML content."""
    html_path = os.path.join(BASE_DIR, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    """Main entry point."""
    api = API()
    
    # Create window with the HTML file
    html_path = os.path.join(BASE_DIR, 'index.html')
    
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
    
    # Start the webview
    webview.start(debug=False)


if __name__ == '__main__':
    main()
