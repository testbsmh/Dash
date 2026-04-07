import requests
import time
import logging
from base64 import b64encode

# Setup logging
logger = logging.getLogger('WS1API')


class WS1API:
    """WorkspaceONE API client."""
    
    def __init__(self, config):
        logger.info("Initializing WS1 API client...")
        self._token_url = config.get('tokenUrl', '')
        self._client_id = config.get('clientId', '')
        self._client_secret = config.get('clientSecret', '')
        self._intel_base = config.get('intelBase', '')
        self._uem_host = config.get('uemHost', '')
        self._aw_key = config.get('awKey', '')
        self._uem_user = config.get('user', '')
        self._uem_pass = config.get('pass', '')
        
        self._access_token = None
        self._token_expiry = 0
        
        logger.debug(f"Token URL: {self._token_url}")
        logger.debug(f"Intel Base: {self._intel_base}")
        logger.debug(f"UEM Host: {self._uem_host}")
        logger.debug(f"Client ID configured: {bool(self._client_id)}")
        logger.debug(f"Client Secret configured: {bool(self._client_secret)}")
        logger.info("WS1 API client initialized")
    
    def get_token(self):
        """Get OAuth2 access token."""
        logger.info("Getting OAuth2 access token...")
        
        # Check if existing token is still valid
        if self._access_token and time.time() < self._token_expiry - 30:
            logger.debug("Using cached token (still valid)")
            return self._access_token
        
        if not self._client_id or not self._client_secret:
            logger.error("Client ID and Secret are required but not configured")
            raise Exception('Client ID and Secret are required')
        
        logger.debug(f"Requesting new token from: {self._token_url}")
        
        try:
            response = requests.post(
                self._token_url, 
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self._client_id,
                    'client_secret': self._client_secret
                },
                timeout=30
            )
            
            logger.debug(f"Token response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Token request failed with status {response.status_code}")
                logger.error(f"Response body: {response.text[:500]}")
                raise Exception(f'Token request failed: {response.status_code}')
            
            data = response.json()
            self._access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            self._token_expiry = time.time() + expires_in
            
            logger.info(f"Token obtained successfully, expires in {expires_in}s")
            return self._access_token
            
        except requests.exceptions.Timeout:
            logger.error("Token request timed out")
            raise Exception('Token request timed out')
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during token request: {e}")
            raise Exception(f'Connection error: {e}')
        except Exception as e:
            logger.error(f"Unexpected error getting token: {e}", exc_info=True)
            raise
    
    def fetch_intelligence_data(self, app_type_filter=''):
        """Fetch application data from Intelligence GraphQL API."""
        logger.info("Fetching Intelligence data...")
        logger.debug(f"App type filter: '{app_type_filter}'")
        
        token = self.get_token()
        
        filter_str = f"airwatch.application.app_type IN ('{app_type_filter}')" if app_type_filter else ''
        
        all_results = []
        offset = 0
        page_size = 5000
        page_num = 0
        
        while True:
            page_num += 1
            logger.info(f"Fetching page {page_num} (offset: {offset}, page_size: {page_size})")
            
            payload = {
                'operationName': 'ReportPreview',
                'variables': {
                    'genericSearchRequestInput': {
                        'offset': offset,
                        'page_size': page_size,
                        'fields': [
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
                            'airwatch.device.device_organization_group_name',
                            'airwatch.device.device_enrollment_email_address',
                            'airwatch.device.device_last_seen',
                        ],
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
                logger.debug(f"Sending GraphQL request to: {self._intel_base}/graphql")
                
                response = requests.post(
                    f'{self._intel_base}/graphql',
                    json=payload,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=60
                )
                
                logger.debug(f"GraphQL response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"Intelligence API error: {response.status_code}")
                    logger.error(f"Response: {response.text[:500]}")
                    raise Exception(f'Intelligence API error: {response.status_code}')
                
                data = response.json()
                
                # Check for GraphQL errors
                if 'errors' in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    raise Exception(f"GraphQL error: {data['errors']}")
                
                preview = data.get('data', {}).get('previewReport')
                
                if not preview:
                    logger.error(f"Unexpected response structure: {list(data.keys())}")
                    raise Exception('Unexpected response from Intelligence API')
                
                results = preview.get('results', [])
                all_results.extend(results)
                
                paged_response = preview.get('paged_response', {})
                total = paged_response.get('total_count', 0)
                
                logger.info(f"Page {page_num}: Retrieved {len(results)} records (total so far: {len(all_results)} of {total})")
                
                offset += page_size
                
                if offset >= total:
                    logger.info(f"Finished fetching all data: {len(all_results)} total records")
                    break
                    
            except requests.exceptions.Timeout:
                logger.error("GraphQL request timed out")
                raise Exception('API request timed out')
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
                raise Exception(f'Connection error: {e}')
            except Exception as e:
                logger.error(f"Error fetching Intelligence data: {e}", exc_info=True)
                raise
        
        return all_results
    
    def fetch_assignments(self, uem_app_id, app_type):
        """Fetch assignment groups from UEM API."""
        logger.info(f"Fetching assignments for app: {uem_app_id} (type: {app_type})")
        
        if not self._uem_host or not self._aw_key:
            logger.warning("UEM Host or API Key not configured, skipping assignments")
            return []
        
        auth_string = b64encode(f'{self._uem_user}:{self._uem_pass}'.encode()).decode()
        
        path = f'/api/mam/apps/purchased/{uem_app_id}/assignment' if app_type == 'Purchased' else f'/api/mam/apps/{uem_app_id}/assignment'
        url = f'{self._uem_host}{path}'
        
        logger.debug(f"UEM API URL: {url}")
        
        try:
            response = requests.get(
                url,
                headers={
                    'Accept': 'application/json',
                    'aw-tenant-code': self._aw_key,
                    'Authorization': f'Basic {auth_string}'
                },
                timeout=30
            )
            
            logger.debug(f"UEM API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"UEM API returned {response.status_code}")
                return []
            
            data = response.json()
            assignments = data.get('AssignmentDetail') or data.get('Assignments') or data.get('Value') or []
            
            logger.info(f"Retrieved {len(assignments)} assignments")
            return assignments
            
        except requests.exceptions.Timeout:
            logger.error("UEM API request timed out")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"UEM API connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching assignments: {e}", exc_info=True)
            return []
