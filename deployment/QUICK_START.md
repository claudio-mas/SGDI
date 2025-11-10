# Sistema SGDI - Quick Start Deployment

This is a condensed guide for experienced administrators. For detailed instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## Prerequisites

- Ubuntu 20.04+ or Windows Server 2019+
- Python 3.8+
- SQL Server 2019+
- NGINX 1.18+
- ODBC Driver 17+

## Quick Installation Steps

### 1. System Setup

```bash
# Install dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx supervisor
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev

# Install ODBC Driver
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt update && sudo ACCEPT_EULA=Y apt install -y msodbcsql17 unixodbc-dev

# Create user
sudo useradd -m -s /bin/bash geduser
sudo usermod -aG www-data geduser
```

### 2. Database Setup

```sql
CREATE DATABASE sistema_ged;
CREATE LOGIN ged_app_user WITH PASSWORD = 'YourPassword123!';
USE sistema_ged;
CREATE USER ged_app_user FOR LOGIN ged_app_user;
ALTER ROLE db_owner ADD MEMBER ged_app_user;
```

### 3. Application Setup

```bash
# Create directory
sudo mkdir -p /opt/sistema_ged
sudo chown geduser:www-data /opt/sistema_ged
cd /opt/sistema_ged

# Copy application files
# (copy your files here)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Create directories
mkdir -p uploads logs backups
chmod 755 uploads logs backups

# Initialize database
python init_db.py
python seed_data.py
```

### 4. NGINX Setup

```bash
# Copy and configure
sudo cp deployment/nginx_sistema_ged.conf /etc/nginx/sites-available/sistema_ged
sudo nano /etc/nginx/sites-available/sistema_ged  # Update paths and domain

# Enable site
sudo ln -s /etc/nginx/sites-available/sistema_ged /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Process Management (Choose One)

**Option A: Supervisor**
```bash
sudo cp deployment/supervisor_sistema_ged.conf /etc/supervisor/conf.d/
sudo nano /etc/supervisor/conf.d/supervisor_sistema_ged.conf  # Update paths
sudo supervisorctl reread && sudo supervisorctl update
sudo supervisorctl start sistema_ged
```

**Option B: systemd**
```bash
sudo cp deployment/sistema_ged.service /etc/systemd/system/
sudo nano /etc/systemd/system/sistema_ged.service  # Update paths
sudo systemctl daemon-reload
sudo systemctl enable sistema_ged
sudo systemctl start sistema_ged
```

### 6. SSL Setup (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 7. Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### 8. Backups (Cron)

```bash
sudo su - geduser
crontab -e
```

Add:
```cron
0 2 * * * cd /opt/sistema_ged && /opt/sistema_ged/venv/bin/python scripts/backup_database.py
0 3 * * 0 cd /opt/sistema_ged && /opt/sistema_ged/venv/bin/python scripts/backup_files.py
0 4 * * * cd /opt/sistema_ged && /opt/sistema_ged/venv/bin/python scripts/cleanup_all.py
```

## Essential Commands

### Application Control

```bash
# Supervisor
sudo supervisorctl status sistema_ged
sudo supervisorctl start sistema_ged
sudo supervisorctl stop sistema_ged
sudo supervisorctl restart sistema_ged

# systemd
sudo systemctl status sistema_ged
sudo systemctl start sistema_ged
sudo systemctl stop sistema_ged
sudo systemctl restart sistema_ged
```

### NGINX Control

```bash
sudo nginx -t                    # Test configuration
sudo systemctl reload nginx      # Reload configuration
sudo systemctl restart nginx     # Restart NGINX
```

### View Logs

```bash
# Application logs
tail -f /opt/sistema_ged/logs/gunicorn_error.log
tail -f /opt/sistema_ged/logs/ged_system.log

# Supervisor logs
sudo tail -f /var/log/supervisor/sistema_ged_stderr.log

# systemd logs
sudo journalctl -u sistema_ged -f

# NGINX logs
sudo tail -f /var/log/nginx/sistema_ged_error.log
sudo tail -f /var/log/nginx/sistema_ged_access.log
```

### Database Operations

```bash
cd /opt/sistema_ged
source venv/bin/activate

# Run migrations
flask db upgrade

# Create admin user
python seed_data.py

# Backup database
python scripts/backup_database.py
```

## Environment Variables (.env)

```bash
FLASK_ENV=production
SECRET_KEY=generate-with-secrets-token-hex-32
DATABASE_SERVER=your-server
DATABASE_NAME=sistema_ged
DATABASE_USER=ged_app_user
DATABASE_PASSWORD=YourPassword123!
DATABASE_DRIVER=ODBC Driver 17 for SQL Server
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
SESSION_COOKIE_SECURE=True
```

## Verification

```bash
# Test application
curl http://localhost:8000/health
curl https://your-domain.com/health

# Check processes
ps aux | grep gunicorn
sudo systemctl status nginx

# Check ports
sudo netstat -tlnp | grep -E '(80|443|8000)'
```

## Troubleshooting Quick Fixes

**502 Bad Gateway:**
```bash
sudo supervisorctl restart sistema_ged
# or
sudo systemctl restart sistema_ged
```

**Database connection error:**
```bash
# Test connection
cd /opt/sistema_ged && source venv/bin/activate
python -c "from app import create_app, db; app = create_app('production'); \
with app.app_context(): db.engine.connect(); print('OK')"
```

**Permission errors:**
```bash
sudo chown -R geduser:www-data /opt/sistema_ged
chmod 755 /opt/sistema_ged/uploads
chmod 600 /opt/sistema_ged/.env
```

**SSL certificate renewal:**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

## Security Checklist

- [ ] Change default admin password
- [ ] Generate strong SECRET_KEY
- [ ] Configure firewall (ufw)
- [ ] Enable SSL/TLS
- [ ] Set file permissions (chmod 600 .env)
- [ ] Configure backups
- [ ] Enable log rotation
- [ ] Update security headers in NGINX
- [ ] Test backup restoration

## Next Steps

1. Access application: `https://your-domain.com`
2. Login with admin credentials
3. Change admin password
4. Configure system settings
5. Create user accounts
6. Set up categories and folders
7. Test document upload/download
8. Configure email notifications
9. Set up monitoring
10. Review security settings

For detailed information, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).
