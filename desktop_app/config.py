import json
import os
import logging

logger = logging.getLogger('WS1Config')


class Config:
    """Configuration manager for API credentials - uses plain strings, no Path objects."""
    
    def __init__(self):
        logger.info("Initializing Config manager...")
        
        # Determine config directory (use strings, NOT pathlib)
        try:
            if os.name == 'nt':  # Windows
                appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
                self._config_dir = os.path.join(appdata, 'WS1AppIntelligence')
            else:  # macOS/Linux
                self._config_dir = os.path.join(os.path.expanduser('~'), '.ws1appintelligence')
            
            self._config_file = os.path.join(self._config_dir, 'config.json')
            
            logger.info(f"Config directory: {self._config_dir}")
            logger.info(f"Config file: {self._config_file}")
            
        except Exception as e:
            logger.error(f"Error setting config paths: {e}")
            self._config_dir = os.path.join(os.getcwd(), '.ws1config')
            self._config_file = os.path.join(self._config_dir, 'config.json')
        
        # Load config
        self._data = self._load()
        logger.info(f"Config loaded with keys: {list(self._data.keys())}")
    
    def _get_defaults(self):
        """Get default configuration values."""
        return {
            'tokenUrl': 'https://auth.na1.data.vmwservices.com/oauth/token',
            'clientId': '',
            'clientSecret': '',
            'intelBase': 'https://api.na1.data.workspaceone.com',
            'uemHost': '',
            'awKey': '',
            'og': '',
            'user': '',
            'pass': '',
            'maxRecords': 100000,  # Limit records to fetch (0 = unlimited)
            'pageSize': 10000     # Records per API call
        }
    
    def _load(self):
        """Load configuration from file."""
        config = self._get_defaults()
        
        try:
            if os.path.exists(self._config_file):
                logger.info(f"Loading config from: {self._config_file}")
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    config.update(saved)
                    logger.info(f"Loaded {len(saved)} saved config values")
            else:
                logger.info("No config file found, using defaults")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
        
        return config
    
    def save(self, data):
        """Save configuration to file."""
        logger.info("Saving configuration...")
        
        try:
            # Create directory if needed
            if not os.path.exists(self._config_dir):
                logger.info(f"Creating config directory: {self._config_dir}")
                os.makedirs(self._config_dir, exist_ok=True)
            
            # Update internal data
            self._data.update(data)
            
            # Write to file
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2)
            
            logger.info(f"Config saved to: {self._config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a single config value."""
        return self._data.get(key, default)
    
    def get_all(self):
        """Get all config values as a plain dict."""
        return dict(self._data)  # Return a copy
