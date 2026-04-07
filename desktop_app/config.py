import json
import os
from pathlib import Path

class Config:
    """Configuration manager for API credentials."""
    
    def __init__(self):
        # Store config in user's app data directory
        if os.name == 'nt':  # Windows
            self.config_dir = Path(os.environ.get('APPDATA', '')) / 'WS1AppIntelligence'
        else:  # macOS/Linux
            self.config_dir = Path.home() / '.ws1appintelligence'
        
        self.config_file = self.config_dir / 'config.json'
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
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
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except Exception:
                pass
        
        return default_config
    
    def save(self, config_data):
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config.update(config_data)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        return True
    
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def get_all(self):
        """Get all configuration values."""
        return self.config.copy()
