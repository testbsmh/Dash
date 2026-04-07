import requests
import time
from base64 import b64encode

class WS1API:
    """WorkspaceONE API client."""
    
    def __init__(self, config):
        self.config = config
        self.access_token = None
        self.token_expiry = 0
    
    def get_token(self):
        """Get OAuth2 access token."""
        if self.access_token and time.time() < self.token_expiry - 30:
            return self.access_token
        
        token_url = self.config.get('tokenUrl')
        client_id = self.config.get('clientId')
        client_secret = self.config.get('clientSecret')
        
        if not client_id or not client_secret:
            raise Exception('Client ID and Secret are required')
        
        response = requests.post(token_url, data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        })
        
        if response.status_code != 200:
            raise Exception(f'Token request failed: {response.status_code}')
        
        data = response.json()
        self.access_token = data['access_token']
        self.token_expiry = time.time() + data.get('expires_in', 3600)
        return self.access_token
    
    def fetch_intelligence_data(self, app_type_filter=''):
        """Fetch application data from Intelligence GraphQL API."""
        token = self.get_token()
        intel_base = self.config.get('intelBase')
        
        filter_str = f"airwatch.application.app_type IN ('{app_type_filter}')" if app_type_filter else ''
        
        all_results = []
        offset = 0
        page_size = 5000
        
        while True:
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
            
            response = requests.post(
                f'{intel_base}/graphql',
                json=payload,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise Exception(f'Intelligence API error: {response.status_code}')
            
            data = response.json()
            preview = data.get('data', {}).get('previewReport')
            
            if not preview:
                raise Exception('Unexpected response from Intelligence API')
            
            all_results.extend(preview.get('results', []))
            total = preview.get('paged_response', {}).get('total_count', 0)
            offset += page_size
            
            if offset >= total:
                break
        
        return all_results
    
    def fetch_assignments(self, uem_app_id, app_type):
        """Fetch assignment groups from UEM API."""
        uem_host = self.config.get('uemHost')
        aw_key = self.config.get('awKey')
        user = self.config.get('user')
        password = self.config.get('pass')
        
        if not uem_host or not aw_key:
            return []
        
        auth_string = b64encode(f'{user}:{password}'.encode()).decode()
        
        path = f'/api/mam/apps/purchased/{uem_app_id}/assignment' if app_type == 'Purchased' else f'/api/mam/apps/{uem_app_id}/assignment'
        
        try:
            response = requests.get(
                f'{uem_host}{path}',
                headers={
                    'Accept': 'application/json',
                    'aw-tenant-code': aw_key,
                    'Authorization': f'Basic {auth_string}'
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return data.get('AssignmentDetail') or data.get('Assignments') or data.get('Value') or []
        except Exception:
            return []
