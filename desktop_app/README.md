# WorkspaceONE App Intelligence Dashboard

A desktop application for viewing WorkspaceONE application intelligence data.

## Features

- View all applications across iOS, Android, macOS, and Windows
- Track installation status (Installed, Pending, Assigned, Not Assigned)
- Monitor device activity and last seen dates
- Export data to CSV
- Secure local credential storage
- Demo mode when API not configured

## Requirements

- Python 3.8 or higher
- Windows 10/11, macOS 10.14+, or Linux

## Installation

### From Source

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

### Building the Executable

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Build the .exe file:
   ```bash
   python build.py
   ```

3. Find the executable in the `dist/` folder:
   - Windows: `dist/WS1AppIntelligence.exe`
   - macOS: `dist/WS1AppIntelligence` (or .app bundle)
   - Linux: `dist/WS1AppIntelligence`

## Configuration

1. Click "Configure API" in the application
2. Enter your WorkspaceONE credentials:
   - **OAuth Token URL**: Authentication endpoint
   - **Client ID**: Your OAuth client ID
   - **Client Secret**: Your OAuth client secret
   - **Intelligence API Base**: API endpoint for app data
   - **UEM API Host**: Your UEM environment URL
   - **UEM API Key**: Your aw-tenant-code
   - **UEM Credentials**: Username and password for UEM API

Credentials are stored securely in your user profile directory.

## Demo Mode

If no API credentials are configured, the application runs in demo mode with sample data to showcase all features.

## Export Options

- **Export Apps**: Download all applications as CSV
- **Export Devices**: Download device details for selected app as CSV

## License

Proprietary - Internal Use Only
