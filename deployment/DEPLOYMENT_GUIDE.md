# Sistema GED - Deployment Guide

This guide provides step-by-step instructions for deploying Sistema GED in a production environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Database Setup](#database-setup)
4. [Application Installation](#application-installation)
5. [NGINX Configuration](#nginx-configuration)
6. [Process Management](#process-management)
7. [SSL/TLS Setup](#ssltls-setup)
8. [Post-Deployment](#post-deployment)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Application Server:**
- OS: Ubuntu 20.04+ or Windows Server 2019+
- CPU: 4 cores minimum
- RAM: 8GB minimum
- Disk: 100GB for application, 2TB+ for file storage

**Database Server:**
- SQL Server 2019 or later
- CPU: 4 cores minimum
- RAM: 16GB minimum
- Disk: 500GB minimum with RAID configuration

### Software Requirements

- Python 3.8 or higher
- pip (Python package manager)
- virtualenv
- NGINX 1.18+
- Gunicorn 20.0+
- Supervisor or systemd
- SQL Server with ODBC Driver 17+

## Server Setup

### 1. Update System Packages

```bash
# Ubuntu/Debian
sudo apt update
sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv nginx supervisor
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

### 2. Install SQL Server ODBC Driver

```bash
# Ubuntu 20.04
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

sudo apt update
sudo ACCEPT_EULA=Y apt install -y msodbcsql17 unixodbc-dev
```

### 3. Create Application User

```bash
# Create a dedicated user for the application
sudo useradd -m -s /bin/bash geduser
sudo usermod -aG www-data geduser
```

## Database Setup

### 1. Create Database

Connect to SQL Server and run:

```sql
-- Create database
CREATE DATABASE sistema_ged;
GO

-- Create login and user
CREATE LOGIN ged_app_user WITH PASSWORD = 'YourStrongPassword123!';
GO

USE sistema_ged;
GO

CREATE USER ged_app_user FOR LOGIN ged_app_user;
GO

-- Grant permissions
ALTER ROLE db_owner ADD MEMBER ged_app_user;
GO
```

### 2. Enable Full-Text Search (Optional)

```sql
USE sistema_ged;
GO

-- Create full-text catalog
CREATE FULLTEXT CATALOG ged_catalog AS DEFAULT;
GO

-- Full-text index will be created by migrations
```

## Application Installation

### 1. Clone or Copy Application

```bash
# Create application directory
sudo mkdir -p /opt/sistema_ged
sudo chown geduser:www-data /opt/sistema_ged

# Switch to application user
sudo su - geduser

# Navigate to application directory
cd /opt/sistema_ged

# Copy your application files here
# Or clone from repository:
# git clone https://github.com/your-org/sistema-ged.git .
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Gunicorn
pip install gunicorn
```

### 4. Configure Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

See [Environment Variables](#environment-variables) section for details.

### 5. Create Required Directories

```bash
# Create directories
mkdir -p uploads logs backups

# Set permissions
chmod 755 uploads logs backups
```

### 6. Run Database Migrations

```bash
# Initialize database
python init_db.py

# Or use Alembic migrations
flask db upgrade
```

### 7. Create Initial Data

```bash
# Run seed script to create default profiles and admin user
python seed_data.py
```

## NGINX Configuration

### 1. Copy NGINX Configuration

```bash
# Copy configuration file
sudo cp deployment/nginx_sistema_ged.conf /etc/nginx/sites-available/sistema_ged

# Update paths in the configuration file
sudo nano /etc/nginx/sites-available/sistema_ged

# Update these values:
# - server_name: your-domain.com
# - root: /opt/sistema_ged
# - alias paths for static and uploads
# - SSL certificate paths
```

### 2. Enable Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/sistema_ged /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test NGINX configuration
sudo nginx -t

# Reload NGINX
sudo systemctl reload nginx
```

## Process Management

You can use either Supervisor or systemd to manage the Gunicorn process.

### Option A: Using Supervisor

```bash
# Copy Supervisor configuration
sudo cp deployment/supervisor_sistema_ged.conf /etc/supervisor/conf.d/

# Update paths in the configuration
sudo nano /etc/supervisor/conf.d/supervisor_sistema_ged.conf

# Update these values:
# - command: /opt/sistema_ged/venv/bin/gunicorn
# - directory: /opt/sistema_ged
# - user: geduser
# - environment variables

# Reload Supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Start the application
sudo supervisorctl start sistema_ged

# Check status
sudo supervisorctl status sistema_ged
```

### Option B: Using systemd

```bash
# Copy systemd service file
sudo cp deployment/sistema_ged.service /etc/systemd/system/

# Update paths in the service file
sudo nano /etc/systemd/system/sistema_ged.service

# Update these values:
# - WorkingDirectory: /opt/sistema_ged
# - EnvironmentFile: /opt/sistema_ged/.env
# - ExecStart: /opt/sistema_ged/venv/bin/gunicorn
# - User and Group: geduser

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable sistema_ged

# Start the service
sudo systemctl start sistema_ged

# Check status
sudo systemctl status sistema_ged
```

## SSL/TLS Setup

### Option A: Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Certbot will automatically update NGINX configuration
# Test automatic renewal
sudo certbot renew --dry-run
```

### Option B: Using Self-Signed Certificate (Development Only)

```bash
# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/sistema_ged.key \
  -out /etc/ssl/certs/sistema_ged.crt

# Update NGINX configuration with certificate paths
sudo nano /etc/nginx/sites-available/sistema_ged
```

### Option C: Using Commercial Certificate

1. Purchase SSL certificate from a Certificate Authority
2. Copy certificate files to server:
   - Certificate: `/etc/ssl/certs/sistema_ged.crt`
   - Private key: `/etc/ssl/private/sistema_ged.key`
   - CA bundle (if provided): `/etc/ssl/certs/ca-bundle.crt`
3. Update NGINX configuration with certificate paths
4. Reload NGINX: `sudo systemctl reload nginx`

## Post-Deployment

### 1. Verify Installation

```bash
# Check if Gunicorn is running
ps aux | grep gunicorn

# Check if NGINX is running
sudo systemctl status nginx

# Test application
curl http://localhost:8000/health
curl https://your-domain.com/health
```

### 2. Create Admin User

```bash
# If not created by seed script, create manually
cd /opt/sistema_ged
source venv/bin/activate
python -c "from app import create_app, db; from app.models import User, Perfil; \
app = create_app('production'); \
with app.app_context(): \
    admin_perfil = Perfil.query.filter_by(nome='Administrador').first(); \
    admin = User(nome='Admin', email='admin@example.com', perfil_id=admin_perfil.id, ativo=True); \
    admin.set_password('ChangeMe123!'); \
    db.session.add(admin); \
    db.session.commit(); \
    print('Admin user created')"
```

### 3. Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Allow SSH (if not already allowed)
sudo ufw allow OpenSSH

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 4. Set Up Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/sistema_ged
```

Add the following content:

```
/opt/sistema_ged/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 geduser www-data
    sharedscripts
    postrotate
        supervisorctl restart sistema_ged > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/sistema_ged*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
```

### 5. Set Up Backup Cron Jobs

```bash
# Edit crontab for geduser
sudo su - geduser
crontab -e
```

Add the following lines:

```cron
# Daily database backup at 2 AM
0 2 * * * cd /opt/sistema_ged && /opt/sistema_ged/venv/bin/python scripts/backup_database.py

# Weekly file backup on Sunday at 3 AM
0 3 * * 0 cd /opt/sistema_ged && /opt/sistema_ged/venv/bin/python scripts/backup_files.py

# Daily cleanup at 4 AM
0 4 * * * cd /opt/sistema_ged && /opt/sistema_ged/venv/bin/python scripts/cleanup_all.py
```

### 6. Configure Monitoring (Optional)

Consider setting up monitoring tools:
- **Application Monitoring**: New Relic, Datadog, or Sentry
- **Server Monitoring**: Prometheus + Grafana, Nagios, or Zabbix
- **Log Aggregation**: ELK Stack (Elasticsearch, Logstash, Kibana)

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-very-secret-key-change-this-in-production

# Database Configuration
DATABASE_SERVER=your-db-server.database.windows.net
DATABASE_NAME=sistema_ged
DATABASE_USER=ged_app_user
DATABASE_PASSWORD=YourStrongPassword123!
DATABASE_DRIVER=ODBC Driver 17 for SQL Server

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800
ALLOWED_EXTENSIONS=pdf,doc,docx,xls,xlsx,jpg,png,tif

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@your-domain.com

# Session Configuration
SESSION_COOKIE_SECURE=True
PERMANENT_SESSION_LIFETIME=3600

# Security Settings
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION=900
PASSWORD_RESET_TOKEN_EXPIRATION=3600

# Application Settings
MAX_VERSIONS_PER_DOCUMENT=10
TRASH_RETENTION_DAYS=30

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Gunicorn Configuration
PORT=8000
GUNICORN_WORKERS=4
GUNICORN_LOG_LEVEL=info
```

**Important Security Notes:**
- Generate a strong SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
- Use strong database passwords
- Never commit `.env` file to version control
- Restrict file permissions: `chmod 600 .env`

## Troubleshooting

### Application Won't Start

**Check Gunicorn logs:**
```bash
# Supervisor
sudo tail -f /var/log/supervisor/sistema_ged_stderr.log

# systemd
sudo journalctl -u sistema_ged -f

# Application logs
tail -f /opt/sistema_ged/logs/gunicorn_error.log
```

**Common issues:**
- Database connection failed: Check DATABASE_* environment variables
- Import errors: Ensure all dependencies are installed in virtual environment
- Permission errors: Check file/directory permissions

### Database Connection Issues

**Test database connection:**
```bash
cd /opt/sistema_ged
source venv/bin/activate
python -c "from app import create_app, db; app = create_app('production'); \
with app.app_context(): db.engine.connect(); print('Database connection successful')"
```

**Common issues:**
- ODBC driver not found: Install msodbcsql17
- Authentication failed: Check username/password
- Server not found: Check DATABASE_SERVER value and network connectivity
- Firewall blocking: Ensure SQL Server port (1433) is open

### NGINX Issues

**Test NGINX configuration:**
```bash
sudo nginx -t
```

**Check NGINX logs:**
```bash
sudo tail -f /var/log/nginx/sistema_ged_error.log
```

**Common issues:**
- 502 Bad Gateway: Gunicorn not running or wrong upstream address
- 413 Request Entity Too Large: Increase client_max_body_size
- SSL certificate errors: Check certificate paths and validity

### File Upload Issues

**Check permissions:**
```bash
ls -la /opt/sistema_ged/uploads
# Should be owned by geduser:www-data with 755 permissions
```

**Check disk space:**
```bash
df -h /opt/sistema_ged
```

### Performance Issues

**Check resource usage:**
```bash
# CPU and memory
top
htop

# Disk I/O
iotop

# Network
iftop
```

**Optimize Gunicorn workers:**
- Formula: (2 x CPU cores) + 1
- Monitor memory usage per worker
- Adjust in gunicorn_config.py

**Database optimization:**
- Check slow query log
- Analyze and optimize indexes
- Update statistics: `UPDATE STATISTICS`

### SSL/TLS Issues

**Test SSL configuration:**
```bash
# Check certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Test SSL with SSL Labs
# Visit: https://www.ssllabs.com/ssltest/
```

**Common issues:**
- Certificate expired: Renew certificate
- Mixed content warnings: Ensure all resources use HTTPS
- Certificate chain incomplete: Include intermediate certificates

## Maintenance

### Regular Tasks

**Daily:**
- Monitor application logs
- Check disk space
- Verify backups completed

**Weekly:**
- Review error logs
- Check database performance
- Update security patches

**Monthly:**
- Review audit logs
- Test backup restoration
- Update dependencies (after testing)

### Updating the Application

```bash
# Stop the application
sudo supervisorctl stop sistema_ged
# or
sudo systemctl stop sistema_ged

# Backup current version
cd /opt/sistema_ged
tar -czf ../sistema_ged_backup_$(date +%Y%m%d).tar.gz .

# Pull updates
git pull origin main
# or copy new files

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Run migrations
flask db upgrade

# Start the application
sudo supervisorctl start sistema_ged
# or
sudo systemctl start sistema_ged

# Verify
curl https://your-domain.com/health
```

## Security Checklist

- [ ] Strong SECRET_KEY configured
- [ ] Database uses strong password
- [ ] SSL/TLS certificate installed and valid
- [ ] Firewall configured (only necessary ports open)
- [ ] File permissions set correctly (no world-writable files)
- [ ] .env file has restricted permissions (600)
- [ ] Security headers configured in NGINX
- [ ] Rate limiting enabled
- [ ] Backups configured and tested
- [ ] Log rotation configured
- [ ] Monitoring and alerting set up
- [ ] Default admin password changed
- [ ] CSRF protection enabled
- [ ] SQL injection protection (using ORM)
- [ ] XSS protection enabled

## Support

For issues and questions:
- Check application logs: `/opt/sistema_ged/logs/`
- Check NGINX logs: `/var/log/nginx/`
- Check system logs: `sudo journalctl -xe`
- Review this troubleshooting guide
- Contact system administrator

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [NGINX Documentation](https://nginx.org/en/docs/)
- [SQL Server Documentation](https://docs.microsoft.com/en-us/sql/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
