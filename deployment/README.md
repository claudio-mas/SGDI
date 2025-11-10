# Sistema SGDI - Deployment Files

This directory contains all files and documentation needed to deploy Sistema SGDI in production environments.

## Contents

### Configuration Files

- **`nginx_sistema_ged.conf`** - NGINX reverse proxy configuration for production (with SSL)
- **`nginx_sistema_ged_dev.conf`** - NGINX configuration for development/testing (without SSL)
- **`supervisor_sistema_ged.conf`** - Supervisor process manager configuration
- **`sistema_ged.service`** - systemd service file (alternative to Supervisor)
- **`gunicorn_config.py`** - Gunicorn WSGI server configuration (in project root)
- **`wsgi.py`** - WSGI entry point (in project root)

### Documentation

- **`DEPLOYMENT_GUIDE.md`** - Complete deployment guide with detailed instructions
- **`QUICK_START.md`** - Quick reference for experienced administrators
- **`WINDOWS_DEPLOYMENT.md`** - Windows Server specific deployment guide
- **`TROUBLESHOOTING.md`** - Common issues and solutions

## Quick Links

### For First-Time Deployment

1. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete instructions
2. Follow platform-specific guide:
   - Linux: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
   - Windows: [WINDOWS_DEPLOYMENT.md](WINDOWS_DEPLOYMENT.md)
3. Refer to [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues

### For Experienced Administrators

- Use [QUICK_START.md](QUICK_START.md) for rapid deployment
- Reference [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

## Deployment Options

### Linux Deployment

**Process Manager Options:**
- **Supervisor** (Recommended for simplicity)
  - Use `supervisor_sistema_ged.conf`
  - Easy to configure and manage
  - Good for single-server deployments

- **systemd** (Recommended for production)
  - Use `sistema_ged.service`
  - Native to modern Linux distributions
  - Better integration with system services

**Web Server:**
- **NGINX** (Recommended)
  - Use `nginx_sistema_ged.conf` for production
  - Use `nginx_sistema_ged_dev.conf` for development
  - Handles SSL/TLS termination
  - Serves static files efficiently

### Windows Deployment

**Process Manager:**
- **NSSM** (Non-Sucking Service Manager)
  - Creates Windows service from Python application
  - Easy to configure
  - Automatic restart on failure

**Web Server:**
- **IIS** (Internet Information Services)
  - Native to Windows Server
  - Use with HttpPlatformHandler or as reverse proxy
  - Handles SSL/TLS certificates

**Application Server:**
- **Waitress** (Recommended for Windows)
  - Pure Python WSGI server
  - Better Windows compatibility than Gunicorn
  - Production-ready

## Configuration Steps Overview

### 1. Prepare Server

- Install required software (Python, database, web server)
- Create application user
- Set up firewall rules

### 2. Deploy Application

- Copy application files
- Create virtual environment
- Install dependencies
- Configure environment variables

### 3. Configure Database

- Create database and user
- Run migrations
- Create seed data

### 4. Configure Web Server

- Copy appropriate NGINX/IIS configuration
- Update paths and domain names
- Enable site

### 5. Configure Process Manager

- Copy Supervisor/systemd/NSSM configuration
- Update paths and settings
- Start service

### 6. Configure SSL/TLS

- Obtain SSL certificate (Let's Encrypt recommended)
- Configure web server with certificate
- Test HTTPS access

### 7. Set Up Backups

- Configure automated database backups
- Configure file backups
- Set up cleanup tasks

### 8. Verify Deployment

- Test application access
- Verify all features work
- Check logs for errors
- Test backup/restore

## File Locations

### Linux (Default Paths)

```
/opt/sistema_ged/                    # Application directory
├── app/                             # Application code
├── static/                          # Static files
├── uploads/                         # Uploaded documents
├── logs/                            # Application logs
├── backups/                         # Backup files
├── venv/                            # Virtual environment
├── .env                             # Environment variables
├── wsgi.py                          # WSGI entry point
└── gunicorn_config.py               # Gunicorn configuration

/etc/nginx/sites-available/          # NGINX configurations
/etc/supervisor/conf.d/              # Supervisor configurations
/etc/systemd/system/                 # systemd service files
/var/log/nginx/                      # NGINX logs
/var/log/supervisor/                 # Supervisor logs
```

### Windows (Default Paths)

```
C:\inetpub\sistema_ged\              # Application directory
├── app\                             # Application code
├── static\                          # Static files
├── uploads\                         # Uploaded documents
├── logs\                            # Application logs
├── backups\                         # Backup files
├── venv\                            # Virtual environment
├── .env                             # Environment variables
├── wsgi.py                          # WSGI entry point
└── run_waitress.py                  # Waitress server script

C:\inetpub\wwwroot\                  # IIS root (if using IIS)
C:\Windows\System32\inetsrv\config\  # IIS configuration
```

## Environment Variables

Key environment variables that must be configured in `.env`:

```bash
# Required
FLASK_ENV=production
SECRET_KEY=<generate-strong-key>
DATABASE_SERVER=<your-db-server>
DATABASE_NAME=sistema_ged
DATABASE_USER=<db-username>
DATABASE_PASSWORD=<db-password>

# Optional (with defaults)
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
SESSION_COOKIE_SECURE=True
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#environment-variables) for complete list.

## Security Checklist

Before going to production, ensure:

- [ ] Strong SECRET_KEY generated
- [ ] Database uses strong password
- [ ] SSL/TLS certificate installed
- [ ] Firewall configured
- [ ] File permissions set correctly
- [ ] .env file has restricted permissions
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Backups configured and tested
- [ ] Default admin password changed
- [ ] All dependencies updated
- [ ] Security audit performed

## Common Commands

### Linux

```bash
# Start/stop application
sudo supervisorctl start sistema_ged
sudo supervisorctl stop sistema_ged
sudo systemctl start sistema_ged
sudo systemctl stop sistema_ged

# Reload NGINX
sudo nginx -t
sudo systemctl reload nginx

# View logs
tail -f /opt/sistema_ged/logs/gunicorn_error.log
sudo journalctl -u sistema_ged -f

# Run backups
cd /opt/sistema_ged && source venv/bin/activate
python scripts/backup_database.py
python scripts/backup_files.py
```

### Windows

```powershell
# Start/stop service
Start-Service SistemaGED
Stop-Service SistemaGED
Restart-Service SistemaGED

# View logs
Get-Content C:\inetpub\sistema_ged\logs\service_stdout.log -Tail 50 -Wait

# Run backups
cd C:\inetpub\sistema_ged
.\venv\Scripts\Activate.ps1
python scripts\backup_database.py
python scripts\backup_files.py
```

## Support and Resources

### Documentation

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [NGINX Documentation](https://nginx.org/en/docs/)
- [Supervisor Documentation](http://supervisord.org/)
- [SQL Server Documentation](https://docs.microsoft.com/en-us/sql/)

### Getting Help

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review application logs
3. Check web server logs
4. Verify configuration files
5. Contact system administrator

## Maintenance

### Regular Tasks

- **Daily**: Monitor logs, check disk space
- **Weekly**: Review error logs, check backups
- **Monthly**: Test backup restoration, review security
- **Quarterly**: Update dependencies, performance testing

### Updates

To update the application:

1. Stop the service
2. Backup current version
3. Deploy new version
4. Run database migrations
5. Restart service
6. Verify functionality

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#updating-the-application) for detailed steps.

## License

[Your License Here]

## Contact

For deployment support, contact: [Your Contact Information]
