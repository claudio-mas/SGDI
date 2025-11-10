# Sistema SGDI - Troubleshooting Guide

This guide provides solutions to common issues encountered during deployment and operation of Sistema SGDI.

## Table of Contents

1. [Application Issues](#application-issues)
2. [Database Issues](#database-issues)
3. [Web Server Issues](#web-server-issues)
4. [File Upload Issues](#file-upload-issues)
5. [Authentication Issues](#authentication-issues)
6. [Performance Issues](#performance-issues)
7. [Email Issues](#email-issues)
8. [SSL/TLS Issues](#ssl-tls-issues)
9. [Backup Issues](#backup-issues)
10. [Diagnostic Commands](#diagnostic-commands)

## Application Issues

### Application Won't Start

**Symptoms:**
- Gunicorn/Waitress service fails to start
- 502 Bad Gateway error
- Service crashes immediately after starting

**Diagnosis:**
```bash
# Linux - Check service status
sudo systemctl status sistema_ged
sudo supervisorctl status sistema_ged

# View error logs
tail -f /opt/sistema_ged/logs/gunicorn_error.log
sudo journalctl -u sistema_ged -n 100

# Windows - Check service status
Get-Service SistemaGED
Get-Content C:\inetpub\sistema_ged\logs\service_stderr.log -Tail 50
```

**Common Causes and Solutions:**

1. **Import Error - Missing Dependencies**
   ```bash
   # Activate virtual environment
   source venv/bin/activate  # Linux
   .\venv\Scripts\Activate.ps1  # Windows
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

2. **Database Connection Error**
   ```bash
   # Test database connection
   python -c "from app import create_app, db; \
   app = create_app('production'); \
   with app.app_context(): \
       db.engine.connect(); \
       print('Database connection successful')"
   ```
   - Check DATABASE_* variables in .env
   - Verify SQL Server is running
   - Check network connectivity

3. **Permission Error**
   ```bash
   # Linux - Fix permissions
   sudo chown -R geduser:www-data /opt/sistema_ged
   chmod 755 /opt/sistema_ged/uploads
   chmod 755 /opt/sistema_ged/logs
   chmod 600 /opt/sistema_ged/.env
   
   # Windows - Fix permissions
   icacls "C:\inetpub\sistema_ged\uploads" /grant "IIS_IUSRS:(OI)(CI)M"
   icacls "C:\inetpub\sistema_ged\logs" /grant "IIS_IUSRS:(OI)(CI)M"
   ```

4. **Port Already in Use**
   ```bash
   # Linux - Check what's using port 8000
   sudo netstat -tlnp | grep 8000
   sudo lsof -i :8000
   
   # Kill process or change port in gunicorn_config.py
   
   # Windows - Check port
   netstat -ano | findstr :8000
   ```

5. **Environment Variables Not Loaded**
   - Verify .env file exists and is readable
   - Check file encoding (should be UTF-8)
   - Ensure no syntax errors in .env
   - Restart service after changing .env

### Application Crashes Randomly

**Symptoms:**
- Service stops unexpectedly
- Workers dying and restarting
- Memory errors in logs

**Diagnosis:**
```bash
# Check memory usage
free -h  # Linux
Get-Counter '\Memory\Available MBytes'  # Windows

# Check for memory leaks
ps aux | grep gunicorn  # Linux
Get-Process python  # Windows

# Review error logs
grep -i "memory\|killed\|oom" /opt/sistema_ged/logs/*.log
```

**Solutions:**

1. **Insufficient Memory**
   - Increase server RAM
   - Reduce number of Gunicorn workers
   - Enable swap space (Linux)

2. **Memory Leak**
   - Update to latest version
   - Check for unclosed database connections
   - Review custom code for memory leaks

3. **Worker Timeout**
   - Increase timeout in gunicorn_config.py:
     ```python
     timeout = 300  # Increase from 120
     ```

## Database Issues

### Cannot Connect to Database

**Symptoms:**
- "Unable to connect to database" error
- "Login failed for user" error
- Connection timeout

**Diagnosis:**
```bash
# Test SQL Server connectivity
# Linux
telnet your-db-server 1433

# Windows
Test-NetConnection -ComputerName your-db-server -Port 1433

# Test ODBC connection
python -c "import pyodbc; \
print(pyodbc.drivers()); \
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=your-server;DATABASE=sistema_ged;UID=user;PWD=pass'); \
print('Connected')"
```

**Solutions:**

1. **ODBC Driver Not Found**
   ```bash
   # Linux - Install ODBC driver
   sudo ACCEPT_EULA=Y apt install -y msodbcsql17
   
   # Verify installation
   odbcinst -q -d
   
   # Windows - Download and install from Microsoft
   ```

2. **SQL Server Not Accepting Remote Connections**
   - Open SQL Server Configuration Manager
   - Enable TCP/IP protocol
   - Restart SQL Server service
   - Check firewall allows port 1433

3. **Authentication Failed**
   - Verify username and password in .env
   - Check SQL Server authentication mode (mixed mode)
   - Ensure user has proper permissions
   - Check if account is locked

4. **Connection String Error**
   - Verify DATABASE_DRIVER matches installed driver
   - Check server name format (server\instance or server,port)
   - Ensure no special characters need escaping

### Slow Database Queries

**Symptoms:**
- Pages load slowly
- Search takes too long
- Timeout errors

**Diagnosis:**
```sql
-- Check for missing indexes
SELECT 
    OBJECT_NAME(s.object_id) AS TableName,
    i.name AS IndexName,
    s.user_seeks, s.user_scans, s.user_lookups
FROM sys.dm_db_index_usage_stats s
INNER JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
WHERE database_id = DB_ID('sistema_ged')
ORDER BY s.user_seeks + s.user_scans + s.user_lookups DESC;

-- Check for slow queries
SELECT TOP 10
    qs.execution_count,
    qs.total_elapsed_time / 1000000 AS total_elapsed_time_sec,
    qs.total_elapsed_time / qs.execution_count / 1000000 AS avg_elapsed_time_sec,
    SUBSTRING(qt.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(qt.text)
            ELSE qs.statement_end_offset
        END - qs.statement_start_offset)/2)+1) AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
WHERE qt.dbid = DB_ID('sistema_ged')
ORDER BY qs.total_elapsed_time DESC;
```

**Solutions:**

1. **Missing Indexes**
   - Review index recommendations
   - Add indexes on frequently queried columns
   - Update statistics: `UPDATE STATISTICS`

2. **Database Fragmentation**
   ```sql
   -- Rebuild indexes
   ALTER INDEX ALL ON documentos REBUILD;
   ALTER INDEX ALL ON usuarios REBUILD;
   ```

3. **Outdated Statistics**
   ```sql
   -- Update statistics
   UPDATE STATISTICS documentos WITH FULLSCAN;
   UPDATE STATISTICS usuarios WITH FULLSCAN;
   ```

4. **Connection Pool Exhausted**
   - Increase SQLALCHEMY_POOL_SIZE in config.py
   - Check for connection leaks in code

## Web Server Issues

### 502 Bad Gateway (NGINX)

**Symptoms:**
- NGINX returns 502 error
- "Connection refused" in NGINX error log

**Diagnosis:**
```bash
# Check if Gunicorn is running
ps aux | grep gunicorn
sudo netstat -tlnp | grep 8000

# Check NGINX error log
sudo tail -f /var/log/nginx/sistema_ged_error.log

# Test upstream
curl http://localhost:8000/health
```

**Solutions:**

1. **Gunicorn Not Running**
   ```bash
   sudo supervisorctl start sistema_ged
   # or
   sudo systemctl start sistema_ged
   ```

2. **Wrong Upstream Address**
   - Check upstream configuration in NGINX config
   - Verify Gunicorn is listening on correct port
   - Update nginx_sistema_ged.conf if needed

3. **Firewall Blocking**
   ```bash
   # Allow local connections
   sudo ufw allow from 127.0.0.1 to any port 8000
   ```

### 413 Request Entity Too Large

**Symptoms:**
- File upload fails with 413 error
- Large files cannot be uploaded

**Solutions:**

1. **Increase NGINX Limit**
   ```nginx
   # In nginx_sistema_ged.conf
   client_max_body_size 50M;  # Or higher
   ```
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

2. **Increase Flask Limit**
   ```python
   # In .env
   MAX_CONTENT_LENGTH=52428800  # 50MB in bytes
   ```

### 504 Gateway Timeout

**Symptoms:**
- Long-running requests timeout
- File upload timeout for large files

**Solutions:**

1. **Increase NGINX Timeouts**
   ```nginx
   # In nginx_sistema_ged.conf
   proxy_connect_timeout 300s;
   proxy_send_timeout 300s;
   proxy_read_timeout 300s;
   ```

2. **Increase Gunicorn Timeout**
   ```python
   # In gunicorn_config.py
   timeout = 300
   ```

## File Upload Issues

### File Upload Fails

**Symptoms:**
- Upload button doesn't work
- Files don't appear after upload
- Error message during upload

**Diagnosis:**
```bash
# Check upload directory exists and is writable
ls -la /opt/sistema_ged/uploads
# Should show: drwxr-xr-x geduser www-data

# Check disk space
df -h /opt/sistema_ged

# Check application logs
tail -f /opt/sistema_ged/logs/ged_system.log
```

**Solutions:**

1. **Permission Denied**
   ```bash
   sudo chown -R geduser:www-data /opt/sistema_ged/uploads
   chmod 755 /opt/sistema_ged/uploads
   ```

2. **Disk Full**
   ```bash
   # Check disk usage
   du -sh /opt/sistema_ged/uploads/*
   
   # Clean up old files if needed
   python scripts/cleanup_trash.py
   ```

3. **File Type Not Allowed**
   - Check ALLOWED_EXTENSIONS in .env
   - Verify file extension is in allowed list
   - Check MIME type validation

4. **File Too Large**
   - Check MAX_CONTENT_LENGTH in .env
   - Increase if needed (in bytes)
   - Also check NGINX client_max_body_size

### Duplicate File Detection Not Working

**Symptoms:**
- Same file can be uploaded multiple times
- Hash calculation fails

**Diagnosis:**
```python
# Test hash calculation
from app.services.storage_service import StorageService
from werkzeug.datastructures import FileStorage

# Test with a file
with open('test.pdf', 'rb') as f:
    file_storage = FileStorage(f)
    hash_value = StorageService._calculate_hash(file_storage)
    print(f"Hash: {hash_value}")
```

**Solutions:**

1. **Hash Column Not Indexed**
   ```sql
   CREATE INDEX idx_documentos_hash ON documentos(hash_arquivo);
   ```

2. **Hash Calculation Error**
   - Check if file is being read correctly
   - Verify hashlib is available
   - Review StorageService code

## Authentication Issues

### Cannot Login

**Symptoms:**
- Valid credentials rejected
- "Invalid username or password" error
- Account locked

**Diagnosis:**
```python
# Check user exists and is active
from app import create_app, db
from app.models import User

app = create_app('production')
with app.app_context():
    user = User.query.filter_by(email='admin@example.com').first()
    if user:
        print(f"User found: {user.nome}")
        print(f"Active: {user.ativo}")
        print(f"Locked until: {user.bloqueado_ate}")
        print(f"Login attempts: {user.tentativas_login}")
    else:
        print("User not found")
```

**Solutions:**

1. **Account Locked**
   ```python
   # Unlock account
   from app import create_app, db
   from app.models import User
   
   app = create_app('production')
   with app.app_context():
       user = User.query.filter_by(email='admin@example.com').first()
       user.tentativas_login = 0
       user.bloqueado_ate = None
       db.session.commit()
       print("Account unlocked")
   ```

2. **Account Inactive**
   ```python
   # Activate account
   user.ativo = True
   db.session.commit()
   ```

3. **Wrong Password**
   ```python
   # Reset password
   user.set_password('NewPassword123!')
   db.session.commit()
   ```

### Session Expires Too Quickly

**Symptoms:**
- Users logged out frequently
- "Please login" message appears often

**Solutions:**

1. **Increase Session Lifetime**
   ```python
   # In .env
   PERMANENT_SESSION_LIFETIME=7200  # 2 hours in seconds
   ```

2. **Enable Remember Me**
   - Ensure "Remember Me" checkbox works
   - Check Flask-Login configuration

## Performance Issues

### Slow Page Load

**Diagnosis:**
```bash
# Check server load
top
htop

# Check database performance
# See "Slow Database Queries" section

# Check network latency
ping your-db-server

# Profile application
# Add Flask-DebugToolbar in development
```

**Solutions:**

1. **Enable Caching**
   ```python
   # In config.py
   CACHE_TYPE = 'RedisCache'  # Or 'SimpleCache'
   CACHE_DEFAULT_TIMEOUT = 300
   ```

2. **Optimize Database Queries**
   - Use eager loading for relationships
   - Add pagination to large result sets
   - Cache frequently accessed data

3. **Optimize Static Files**
   - Enable NGINX caching
   - Use CDN for libraries
   - Minify CSS/JS files

4. **Increase Resources**
   - Add more Gunicorn workers
   - Increase server RAM/CPU
   - Use database connection pooling

### High Memory Usage

**Diagnosis:**
```bash
# Check memory usage by process
ps aux --sort=-%mem | head

# Monitor memory over time
watch -n 5 free -h
```

**Solutions:**

1. **Reduce Gunicorn Workers**
   ```python
   # In gunicorn_config.py
   workers = 2  # Reduce from 4
   ```

2. **Enable Garbage Collection**
   ```python
   # In wsgi.py
   import gc
   gc.enable()
   ```

3. **Fix Memory Leaks**
   - Close database sessions properly
   - Clear large objects from memory
   - Use generators for large datasets

## Email Issues

### Emails Not Sending

**Symptoms:**
- No notification emails received
- SMTP errors in logs

**Diagnosis:**
```python
# Test email configuration
from app import create_app, mail
from flask_mail import Message

app = create_app('production')
with app.app_context():
    msg = Message(
        'Test Email',
        recipients=['test@example.com'],
        body='This is a test email'
    )
    try:
        mail.send(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error: {e}")
```

**Solutions:**

1. **SMTP Configuration Error**
   - Verify MAIL_SERVER, MAIL_PORT in .env
   - Check MAIL_USE_TLS setting
   - Verify credentials (MAIL_USERNAME, MAIL_PASSWORD)

2. **Gmail App Password Required**
   - Enable 2-factor authentication
   - Generate app-specific password
   - Use app password in MAIL_PASSWORD

3. **Firewall Blocking SMTP**
   ```bash
   # Test SMTP connection
   telnet smtp.gmail.com 587
   ```

4. **Email Provider Blocking**
   - Check spam folder
   - Verify sender email is not blacklisted
   - Check email provider logs

## SSL/TLS Issues

### SSL Certificate Error

**Symptoms:**
- "Your connection is not private" warning
- Certificate expired error
- Certificate name mismatch

**Diagnosis:**
```bash
# Check certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check certificate expiration
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

**Solutions:**

1. **Certificate Expired**
   ```bash
   # Renew Let's Encrypt certificate
   sudo certbot renew
   sudo systemctl reload nginx
   ```

2. **Certificate Name Mismatch**
   - Ensure certificate matches domain name
   - Include www subdomain in certificate
   - Use wildcard certificate if needed

3. **Incomplete Certificate Chain**
   - Include intermediate certificates
   - Update ssl_certificate path in NGINX config

### Mixed Content Warning

**Symptoms:**
- Browser shows "Not Secure" despite HTTPS
- Some resources load over HTTP

**Solutions:**

1. **Update Resource URLs**
   - Change http:// to https:// in templates
   - Use protocol-relative URLs: //cdn.example.com
   - Use Flask url_for() with _external=True

2. **Add Content Security Policy**
   ```nginx
   # In NGINX config
   add_header Content-Security-Policy "upgrade-insecure-requests";
   ```

## Backup Issues

### Backup Fails

**Symptoms:**
- Backup script errors
- Backup files not created
- Incomplete backups

**Diagnosis:**
```bash
# Run backup manually
cd /opt/sistema_ged
source venv/bin/activate
python scripts/backup_database.py
python scripts/backup_files.py

# Check backup directory
ls -lh backups/
```

**Solutions:**

1. **Permission Error**
   ```bash
   chmod 755 backups/
   chown geduser:www-data backups/
   ```

2. **Disk Space Full**
   ```bash
   df -h
   # Clean old backups
   find backups/ -name "*.zip" -mtime +90 -delete
   ```

3. **Database Backup Error**
   - Check SQL Server permissions
   - Verify backup path is accessible
   - Check SQL Server error log

## Diagnostic Commands

### Linux

```bash
# System information
uname -a
lsb_release -a

# Check running processes
ps aux | grep -E '(gunicorn|python|nginx)'

# Check ports
sudo netstat -tlnp
sudo ss -tlnp

# Check logs
tail -f /opt/sistema_ged/logs/*.log
sudo journalctl -u sistema_ged -f
sudo tail -f /var/log/nginx/*.log

# Check disk usage
df -h
du -sh /opt/sistema_ged/*

# Check memory
free -h
vmstat 1

# Check CPU
top
mpstat 1

# Test database connection
python -c "from app import create_app, db; app = create_app('production'); with app.app_context(): db.engine.connect(); print('OK')"

# Check Python packages
pip list
pip show flask sqlalchemy

# Check environment variables
cat .env
printenv | grep -E '(FLASK|DATABASE|MAIL)'
```

### Windows

```powershell
# System information
Get-ComputerInfo

# Check running processes
Get-Process | Where-Object {$_.Name -like "*python*"}
Get-Service SistemaGED

# Check ports
netstat -ano | findstr :8000
Get-NetTCPConnection -LocalPort 8000

# Check logs
Get-Content C:\inetpub\sistema_ged\logs\ged_system.log -Tail 50 -Wait

# Check disk usage
Get-PSDrive C

# Check memory
Get-Counter '\Memory\Available MBytes'

# Test database connection
python -c "from app import create_app, db; app = create_app('production'); with app.app_context(): db.engine.connect(); print('OK')"

# Check Python packages
pip list

# Check environment variables
Get-Content .env
Get-ChildItem Env: | Where-Object {$_.Name -like "*FLASK*"}
```

## Getting Help

If you cannot resolve the issue:

1. **Collect Information:**
   - Error messages from logs
   - Steps to reproduce
   - System information
   - Recent changes

2. **Check Documentation:**
   - DEPLOYMENT_GUIDE.md
   - README.md
   - Flask documentation
   - SQL Server documentation

3. **Contact Support:**
   - Include all collected information
   - Provide log excerpts
   - Describe troubleshooting steps already taken

## Prevention

### Regular Maintenance

- Monitor disk space weekly
- Review logs daily
- Test backups monthly
- Update dependencies quarterly
- Review security settings monthly
- Performance testing quarterly

### Monitoring Setup

- Set up log aggregation
- Configure alerting for errors
- Monitor resource usage
- Track application metrics
- Set up uptime monitoring

### Documentation

- Document all configuration changes
- Keep runbook updated
- Maintain change log
- Document custom modifications
- Update troubleshooting guide with new issues
