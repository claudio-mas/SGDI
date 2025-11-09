# Sistema GED - Windows Server Deployment Guide

This guide provides instructions for deploying Sistema GED on Windows Server.

## Prerequisites

### System Requirements

- Windows Server 2019 or later
- IIS 10.0 or later
- Python 3.8 or higher
- SQL Server 2019 or later
- 4 CPU cores minimum
- 8GB RAM minimum
- 100GB disk space for application, 2TB+ for file storage

### Software Requirements

- Python 3.8+ (from python.org)
- pip (included with Python)
- SQL Server with SQL Server Management Studio (SSMS)
- IIS with URL Rewrite and Application Request Routing modules
- Visual C++ Redistributable (for Python packages)

## Installation Steps

### 1. Install Python

1. Download Python 3.8+ from https://www.python.org/downloads/windows/
2. Run installer with "Add Python to PATH" checked
3. Verify installation:
```powershell
python --version
pip --version
```

### 2. Install IIS and Required Modules

```powershell
# Open PowerShell as Administrator

# Install IIS
Install-WindowsFeature -name Web-Server -IncludeManagementTools

# Install URL Rewrite Module
# Download from: https://www.iis.net/downloads/microsoft/url-rewrite

# Install Application Request Routing (ARR)
# Download from: https://www.iis.net/downloads/microsoft/application-request-routing
```

### 3. Database Setup

1. Open SQL Server Management Studio (SSMS)
2. Connect to your SQL Server instance
3. Run the following SQL:

```sql
-- Create database
CREATE DATABASE sistema_ged;
GO

-- Create login
CREATE LOGIN ged_app_user WITH PASSWORD = 'YourStrongPassword123!';
GO

-- Create user
USE sistema_ged;
GO

CREATE USER ged_app_user FOR LOGIN ged_app_user;
GO

-- Grant permissions
ALTER ROLE db_owner ADD MEMBER ged_app_user;
GO
```

### 4. Application Setup

```powershell
# Create application directory
New-Item -Path "C:\inetpub\sistema_ged" -ItemType Directory

# Navigate to directory
cd C:\inetpub\sistema_ged

# Copy application files here
# (copy your application files to this directory)

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install additional packages for Windows
pip install waitress
```

### 5. Configure Environment Variables

Create a `.env` file in `C:\inetpub\sistema_ged`:

```
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_SERVER=localhost
DATABASE_NAME=sistema_ged
DATABASE_USER=ged_app_user
DATABASE_PASSWORD=YourStrongPassword123!
DATABASE_DRIVER=ODBC Driver 17 for SQL Server
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800
ALLOWED_EXTENSIONS=pdf,doc,docx,xls,xlsx,jpg,png,tif
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
SESSION_COOKIE_SECURE=True
```

### 6. Create Required Directories

```powershell
# Create directories
New-Item -Path "uploads" -ItemType Directory
New-Item -Path "logs" -ItemType Directory
New-Item -Path "backups" -ItemType Directory

# Set permissions (allow IIS_IUSRS to write)
icacls "uploads" /grant "IIS_IUSRS:(OI)(CI)M"
icacls "logs" /grant "IIS_IUSRS:(OI)(CI)M"
icacls "backups" /grant "IIS_IUSRS:(OI)(CI)M"
```

### 7. Initialize Database

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Initialize database
python init_db.py

# Create seed data
python seed_data.py
```

## Option A: Deploy with Waitress (Recommended for Windows)

### 1. Create Waitress Server Script

Create `run_waitress.py`:

```python
"""
Waitress WSGI server for Windows deployment
"""
import os
from waitress import serve
from app import create_app

app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    # Serve on all interfaces, port 8000
    # Adjust threads and connection limits as needed
    serve(
        app,
        host='0.0.0.0',
        port=8000,
        threads=4,
        connection_limit=1000,
        channel_timeout=120,
        cleanup_interval=30,
        url_scheme='http'
    )
```

### 2. Create Windows Service

Install NSSM (Non-Sucking Service Manager):

```powershell
# Download NSSM from https://nssm.cc/download
# Extract to C:\nssm

# Install service
C:\nssm\nssm.exe install SistemaGED "C:\inetpub\sistema_ged\venv\Scripts\python.exe" "C:\inetpub\sistema_ged\run_waitress.py"

# Configure service
C:\nssm\nssm.exe set SistemaGED AppDirectory "C:\inetpub\sistema_ged"
C:\nssm\nssm.exe set SistemaGED AppEnvironmentExtra "FLASK_ENV=production"
C:\nssm\nssm.exe set SistemaGED DisplayName "Sistema GED Application"
C:\nssm\nssm.exe set SistemaGED Description "Electronic Document Management System"
C:\nssm\nssm.exe set SistemaGED Start SERVICE_AUTO_START

# Set stdout/stderr logging
C:\nssm\nssm.exe set SistemaGED AppStdout "C:\inetpub\sistema_ged\logs\service_stdout.log"
C:\nssm\nssm.exe set SistemaGED AppStderr "C:\inetpub\sistema_ged\logs\service_stderr.log"

# Start service
Start-Service SistemaGED

# Check status
Get-Service SistemaGED
```

### 3. Configure IIS as Reverse Proxy

1. Open IIS Manager
2. Select your server or site
3. Double-click "URL Rewrite"
4. Click "Add Rule(s)..." → "Reverse Proxy"
5. Enter: `localhost:8000`
6. Click OK

Or create `web.config` in `C:\inetpub\wwwroot`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="Sistema GED Reverse Proxy" stopProcessing="true">
                    <match url="(.*)" />
                    <action type="Rewrite" url="http://localhost:8000/{R:1}" />
                    <serverVariables>
                        <set name="HTTP_X_FORWARDED_PROTO" value="https" />
                    </serverVariables>
                </rule>
            </rules>
        </rewrite>
        <httpProtocol>
            <customHeaders>
                <add name="X-Frame-Options" value="SAMEORIGIN" />
                <add name="X-Content-Type-Options" value="nosniff" />
                <add name="X-XSS-Protection" value="1; mode=block" />
                <add name="Strict-Transport-Security" value="max-age=31536000; includeSubDomains" />
            </customHeaders>
        </httpProtocol>
    </system.webServer>
</configuration>
```

## Option B: Deploy with IIS and HttpPlatformHandler

### 1. Install HttpPlatformHandler

Download and install from:
https://www.iis.net/downloads/microsoft/httpplatformhandler

### 2. Create web.config

Create `web.config` in `C:\inetpub\sistema_ged`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="httpPlatformHandler" path="*" verb="*" 
           modules="httpPlatformHandler" resourceType="Unspecified" />
    </handlers>
    <httpPlatform processPath="C:\inetpub\sistema_ged\venv\Scripts\python.exe"
                  arguments="C:\inetpub\sistema_ged\run_waitress.py"
                  startupTimeLimit="60"
                  startupRetryCount="3"
                  stdoutLogEnabled="true"
                  stdoutLogFile="C:\inetpub\sistema_ged\logs\httpplatform.log">
      <environmentVariables>
        <environmentVariable name="FLASK_ENV" value="production" />
        <environmentVariable name="PORT" value="%HTTP_PLATFORM_PORT%" />
      </environmentVariables>
    </httpPlatform>
    <httpProtocol>
      <customHeaders>
        <add name="X-Frame-Options" value="SAMEORIGIN" />
        <add name="X-Content-Type-Options" value="nosniff" />
      </customHeaders>
    </httpProtocol>
  </system.webServer>
</configuration>
```

### 3. Create IIS Site

```powershell
# Import IIS module
Import-Module WebAdministration

# Create application pool
New-WebAppPool -Name "SistemaGEDAppPool"
Set-ItemProperty IIS:\AppPools\SistemaGEDAppPool -Name managedRuntimeVersion -Value ""

# Create website
New-Website -Name "SistemaGED" -Port 80 -PhysicalPath "C:\inetpub\sistema_ged" -ApplicationPool "SistemaGEDAppPool"

# Start website
Start-Website -Name "SistemaGED"
```

## SSL/TLS Configuration

### Option 1: Using IIS SSL Certificate

1. Open IIS Manager
2. Select your server
3. Double-click "Server Certificates"
4. Click "Create Self-Signed Certificate" (for testing) or "Complete Certificate Request" (for production)
5. Select your site → Bindings → Add
6. Type: https, Port: 443, SSL Certificate: (select your certificate)

### Option 2: Using Let's Encrypt

Install win-acme:

```powershell
# Download win-acme from https://www.win-acme.com/
# Extract to C:\win-acme

# Run win-acme
cd C:\win-acme
.\wacs.exe

# Follow prompts to create certificate for your domain
```

## Scheduled Tasks (Backups and Cleanup)

```powershell
# Create scheduled task for database backup
$action = New-ScheduledTaskAction -Execute "C:\inetpub\sistema_ged\venv\Scripts\python.exe" -Argument "C:\inetpub\sistema_ged\scripts\backup_database.py" -WorkingDirectory "C:\inetpub\sistema_ged"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "SistemaGED-DatabaseBackup" -Action $action -Trigger $trigger -Principal $principal

# Create scheduled task for file backup (weekly)
$action = New-ScheduledTaskAction -Execute "C:\inetpub\sistema_ged\venv\Scripts\python.exe" -Argument "C:\inetpub\sistema_ged\scripts\backup_files.py" -WorkingDirectory "C:\inetpub\sistema_ged"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am
Register-ScheduledTask -TaskName "SistemaGED-FileBackup" -Action $action -Trigger $trigger -Principal $principal

# Create scheduled task for cleanup (daily)
$action = New-ScheduledTaskAction -Execute "C:\inetpub\sistema_ged\venv\Scripts\python.exe" -Argument "C:\inetpub\sistema_ged\scripts\cleanup_all.py" -WorkingDirectory "C:\inetpub\sistema_ged"
$trigger = New-ScheduledTaskTrigger -Daily -At 4am
Register-ScheduledTask -TaskName "SistemaGED-Cleanup" -Action $action -Trigger $trigger -Principal $principal
```

## Firewall Configuration

```powershell
# Allow HTTP
New-NetFirewallRule -DisplayName "Sistema GED HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow

# Allow HTTPS
New-NetFirewallRule -DisplayName "Sistema GED HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
```

## Troubleshooting

### Check Service Status

```powershell
# Check Windows Service
Get-Service SistemaGED

# View service logs
Get-Content C:\inetpub\sistema_ged\logs\service_stdout.log -Tail 50

# Check IIS site
Get-Website -Name "SistemaGED"
```

### Test Application

```powershell
# Test local endpoint
Invoke-WebRequest -Uri "http://localhost:8000/health"

# Test through IIS
Invoke-WebRequest -Uri "http://localhost/health"
```

### Common Issues

**Service won't start:**
- Check Python path in NSSM configuration
- Verify virtual environment is activated
- Check logs in `logs\service_stderr.log`

**Database connection error:**
- Verify SQL Server is running
- Check connection string in .env
- Ensure SQL Server allows TCP/IP connections
- Check firewall rules

**Permission errors:**
- Grant IIS_IUSRS permissions to uploads, logs, backups folders
- Check .env file permissions

**502 errors:**
- Ensure Waitress service is running
- Check port 8000 is not blocked
- Verify URL Rewrite is configured correctly

## Monitoring

### Event Viewer

Monitor application logs in Event Viewer:
- Windows Logs → Application
- Filter by source: "SistemaGED"

### Performance Monitor

Monitor system performance:
```powershell
# Open Performance Monitor
perfmon
```

Add counters:
- Processor → % Processor Time
- Memory → Available MBytes
- Network Interface → Bytes Total/sec
- Process → Working Set (python.exe)

## Maintenance

### Update Application

```powershell
# Stop service
Stop-Service SistemaGED

# Backup current version
Compress-Archive -Path "C:\inetpub\sistema_ged" -DestinationPath "C:\backups\sistema_ged_backup_$(Get-Date -Format 'yyyyMMdd').zip"

# Update files
# (copy new files)

# Activate virtual environment
cd C:\inetpub\sistema_ged
.\venv\Scripts\Activate.ps1

# Update dependencies
pip install -r requirements.txt

# Run migrations
python -m flask db upgrade

# Start service
Start-Service SistemaGED
```

### View Logs

```powershell
# Application logs
Get-Content C:\inetpub\sistema_ged\logs\ged_system.log -Tail 50 -Wait

# Service logs
Get-Content C:\inetpub\sistema_ged\logs\service_stdout.log -Tail 50 -Wait

# IIS logs
Get-Content C:\inetpub\logs\LogFiles\W3SVC1\*.log -Tail 50 -Wait
```

## Security Best Practices

1. Use strong passwords for database and admin accounts
2. Enable Windows Firewall
3. Keep Windows Server and SQL Server updated
4. Use SSL/TLS certificates from trusted CA
5. Restrict file permissions (remove unnecessary access)
6. Enable Windows Defender or antivirus
7. Regular security audits
8. Monitor Event Viewer for suspicious activity
9. Implement backup and disaster recovery plan
10. Use separate service account with minimal privileges

## Additional Resources

- [IIS Documentation](https://docs.microsoft.com/en-us/iis/)
- [SQL Server Documentation](https://docs.microsoft.com/en-us/sql/)
- [Python on Windows](https://docs.python.org/3/using/windows.html)
- [Waitress Documentation](https://docs.pylonsproject.org/projects/waitress/)
- [NSSM Documentation](https://nssm.cc/usage)
