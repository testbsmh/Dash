import requests
import time
import logging
from base64 import b64encode

logger = logging.getLogger('WS1API')


class WS1API:
    """WorkspaceONE API client - Pure Python, no browser dependencies."""
    
    def __init__(self, config):
        """
        Initialize API client.
        
        Args:
            config: Config object with get() method, or dict-like object
        """
        logger.info("Initializing WS1API client...")
        
        # Handle both Config object and dict
        if hasattr(config, 'get'):
            self._get_config = config.get
        else:
            self._get_config = lambda k, d=None: config.get(k, d)
        
        self._token_url = self._get_config('tokenUrl', '')
        self._client_id = self._get_config('clientId', '')
        self._client_secret = self._get_config('clientSecret', '')
        self._intel_base = self._get_config('intelBase', '').rstrip('/')
        self._uem_host = self._get_config('uemHost', '').rstrip('/')
        self._aw_key = self._get_config('awKey', '')
        self._uem_user = self._get_config('user', '')
        self._uem_pass = self._get_config('pass', '')
        
        self._access_token = None
        self._token_expiry = 0
        
        logger.info(f"  Token URL: {self._token_url}")
        logger.info(f"  Intel Base: {self._intel_base}")
        logger.info(f"  UEM Host: {self._uem_host or '[Not configured]'}")
        logger.info(f"  Client ID: {self._client_id[:20] + '...' if len(self._client_id) > 20 else self._client_id or '[Not set]'}")
        logger.info(f"  Client Secret: {'[SET]' if self._client_secret else '[Not set]'}")
    
    def get_token(self):
        """Get OAuth2 access token."""
        logger.info("Getting OAuth2 token...")
        
        # Return cached token if still valid
        if self._access_token and time.time() < self._token_expiry - 30:
            logger.info("Using cached token")
            return self._access_token
        
        if not self._client_id or not self._client_secret:
            raise Exception('Client ID and Client Secret are required')
        
        logger.info(f"Requesting token from: {self._token_url}")
        
        try:
            resp = requests.post(
                self._token_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self._client_id,
                    'client_secret': self._client_secret
                },
                timeout=30
            )
            
            logger.info(f"Token response status: {resp.status_code}")
            
            if resp.status_code != 200:
                logger.error(f"Token request failed: {resp.status_code}")
                logger.error(f"Response: {resp.text[:500]}")
                raise Exception(f'Token request failed with status {resp.status_code}: {resp.text[:200]}')
            
            data = resp.json()
            self._access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            self._token_expiry = time.time() + expires_in
            
            logger.info(f"Token obtained successfully (expires in {expires_in}s)")
            return self._access_token
            
        except requests.exceptions.Timeout:
            logger.error("Token request timed out")
            raise Exception('Token request timed out - check your network connection')
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise Exception(f'Cannot connect to auth server: {e}')
    
    def fetch_intelligence_data(self, app_type_filter='', max_records=0, page_size=10000):
        """
        Fetch all application data from Intelligence GraphQL API.
        
        Args:
            app_type_filter: Filter by app type (optional)
            max_records: Maximum records to fetch (0 = unlimited)
            page_size: Records per API call (default 10000)
        """
        logger.info("="*50)
        logger.info("Fetching Intelligence data...")
        logger.info(f"  Max records: {max_records if max_records > 0 else 'unlimited'}")
        logger.info(f"  Page size: {page_size}")
        logger.info("="*50)
        
        token = self.get_token()
        
        filter_str = f"airwatch.application.app_type IN ('{app_type_filter}')" if app_type_filter else ''
        
        all_results = []
        offset = 0
        
        # Updated field names as per latest API
        fields = [
            'airwatch.application.app_id',
            'airwatch.application.app_name',
            'airwatch.application.app_package_id',
            'airwatch.application.app_version',
            'airwatch.application.app_assigned_version',
            'airwatch.application.app_type',
            'airwatch.application.app_install_status',
            'airwatch.application.app_is_installed',
            'airwatch.application._device_platform',
            'airwatch.device.device_id',
            'airwatch.device.device_friendly_name',
            'airwatch.device.device_enrollment_user_name',
            'airwatch.device.device_enrollment_status',
            'airwatch.device.device_serial_number',
            'airwatch.device.device_location_group_name',
            'airwatch.device.device_enrollment_user_email',
            'airwatch.device.device_last_seen',
        ]
        
        while True:
            logger.info(f"Fetching page at offset {offset}...")
            
            payload = {
                'operationName': 'ReportPreview',
                'variables': {
                    'genericSearchRequestInput': {
                        'offset': offset,
                        'page_size': page_size,
                        'fields': fields,
                        'filter': filter_str,
                        'entity': 'application',
                        'integration': 'airwatch'
                    }
                },
                'query': '''query ReportPreview($genericSearchRequestInput: GenericSearchRequestInput!) {
                    previewReport(input: $genericSearchRequestInput) {
                        paged_response { offset page_size total_count }
                        results
                    }
                }'''
            }
            
            try:
                url = f'{self._intel_base}/graphql'
                logger.debug(f"POST {url}")
                
                resp = requests.post(
                    url,
                    json=payload,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=60
                )
                
                logger.info(f"Response status: {resp.status_code}")
                
                if resp.status_code != 200:
                    logger.error(f"API error: {resp.text[:500]}")
                    raise Exception(f'Intelligence API error: {resp.status_code}')
                
                data = resp.json()
                
                if 'errors' in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    raise Exception(f"GraphQL error: {data['errors'][0].get('message', 'Unknown error')}")
                
                preview = data.get('data', {}).get('previewReport')
                if not preview:
                    logger.error(f"Unexpected response: {data}")
                    raise Exception('Unexpected API response structure')
                
                results = preview.get('results', [])
                all_results.extend(results)
                
                paged = preview.get('paged_response', {})
                total = paged.get('total_count', 0)
                
                logger.info(f"Got {len(results)} records. Total so far: {len(all_results)} of {total}")
                
                offset += page_size
                
                # Check if we've hit the max records limit
                if max_records > 0 and len(all_results) >= max_records:
                    logger.info(f"Reached max records limit ({max_records}), stopping fetch")
                    all_results = all_results[:max_records]
                    break
                
                if offset >= total:
                    break
                    
            except requests.exceptions.Timeout:
                raise Exception('API request timed out')
            except requests.exceptions.ConnectionError as e:
                raise Exception(f'Connection error: {e}')
        
        logger.info(f"Fetch complete: {len(all_results)} total records")
        return all_results
    
    def fetch_assignments(self, uem_app_id, app_type):
        """Fetch assignment groups from UEM API."""
        logger.info(f"Fetching assignments for app {uem_app_id}")
        
        if not self._uem_host or not self._aw_key:
            logger.warning("UEM not configured, skipping assignments")
            return []
        
        auth = b64encode(f'{self._uem_user}:{self._uem_pass}'.encode()).decode()
        
        path = f'/api/mam/apps/purchased/{uem_app_id}/assignment' if app_type == 'Purchased' else f'/api/mam/apps/{uem_app_id}/assignment'
        
        try:
            resp = requests.get(
                f'{self._uem_host}{path}',
                headers={
                    'Accept': 'application/json',
                    'aw-tenant-code': self._aw_key,
                    'Authorization': f'Basic {auth}'
                },
                timeout=30
            )
            
            if resp.status_code != 200:
                logger.warning(f"UEM API returned {resp.status_code}")
                return []
            
            data = resp.json()
            return data.get('AssignmentDetail') or data.get('Assignments') or data.get('Value') or []
            
        except Exception as e:
            logger.error(f"UEM API error: {e}")
            return []
