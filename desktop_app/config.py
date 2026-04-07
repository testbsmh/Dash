import json
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('WS1Config')


class Config:
    """Configuration manager for API credentials."""
    
    def __init__(self):
        logger.info("Initializing Config manager...")
        
        # Store paths as STRINGS (not Path objects) to avoid pywebview serialization issues
        try:
            if os.name == 'nt':  # Windows
                appdata = os.environ.get('APPDATA', '')
                self._config_dir = os.path.join(appdata, 'WS1AppIntelligence')
                logger.debug(f"Windows detected. APPDATA: {appdata}")
            else:  # macOS/Linux
                home = os.path.expanduser('~')
                self._config_dir = os.path.join(home, '.ws1appintelligence')
                logger.debug(f"Unix-like OS detected. HOME: {home}")
            
            self._config_file = os.path.join(self._config_dir, 'config.json')
            logger.info(f"Config directory: {self._config_dir}")
            logger.info(f"Config file: {self._config_file}")
            
        except Exception as e:
            logger.error(f"Error setting up config paths: {e}", exc_info=True)
            # Fallback to current directory
            self._config_dir = os.path.join(os.getcwd(), '.ws1config')
            self._config_file = os.path.join(self._config_dir, 'config.json')
            logger.warning(f"Using fallback config path: {self._config_file}")
        
        # Load configuration
        self.config = self._load_config()
        logger.info("Config initialization complete")
    
    def _load_config(self):
        """Load configuration from file."""
        logger.info("Loading configuration...")
        
        default_config = {
            'tokenUrl': 'https://auth.na1.data.vmwservices.com/oauth/token',
            'clientId': '',
            'clientSecret': '',
            'intelBase': 'https://api.na1.data.workspaceone.com',
            'uemHost': '',
            'awKey': '',
            'og': '',
            'user': '',
            'pass': ''
        }
        
        try:
            if os.path.exists(self._config_file):
                logger.info(f"Config file exists at {self._config_file}, loading...")
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    logger.debug(f"Loaded config keys: {list(saved_config.keys())}")
                    default_config.update(saved_config)
                    logger.info("Configuration loaded successfully from file")
            else:
                logger.info("No existing config file found, using defaults")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in config file: {e}", exc_info=True)
        except IOError as e:
            logger.error(f"IO error reading config file: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}", exc_info=True)
        
        return default_config
    
    def save(self, config_data):
        """Save configuration to file."""
        logger.info("Saving configuration...")
        logger.debug(f"Config data to save: {list(config_data.keys())}")
        
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(self._config_dir):
                logger.info(f"Creating config directory: {self._config_dir}")
                os.makedirs(self._config_dir, exist_ok=True)
            
            # Update config
            self.config.update(config_data)
            
            # Write to file
            logger.debug(f"Writing config to: {self._config_file}")
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info("Configuration saved successfully")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission denied saving config: {e}", exc_info=True)
            return False
        except IOError as e:
            logger.error(f"IO error saving config: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving config: {e}", exc_info=True)
            return False
    
    def get(self, key, default=None):
        """Get a configuration value."""
        value = self.config.get(key, default)
        logger.debug(f"Config get '{key}': {'[SET]' if value else '[EMPTY]'}")
        return value
    
    def get_all(self):
        """Get all configuration values."""
        logger.debug("Getting all config values")
        return self.config.copy()
