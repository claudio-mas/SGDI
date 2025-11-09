# Backup Scheduling Guide

This guide explains how to schedule automated backups for Sistema GED.

## Backup Scripts

### Available Scripts

1. **backup_database.py** - Database backup only
2. **backup_files.py** - File storage backup only
3. **backup_all.py** - Complete system backup (database + files)

### Configuration

Backup settings can be configured via environment variables in `.env`:

```bash
# Backup directory (default: ./backups)
BACKUP_DIR=/path/to/backups

# Retention period in days (default: 90)
DATABASE_RETENTION_DAYS=90
FILES_RETENTION_DAYS=90

# Backup options
COMPRESS_FILE_BACKUPS=True
VERIFY_BACKUPS=True

# Notifications (optional)
SEND_BACKUP_NOTIFICATIONS=False
BACKUP_NOTIFICATION_EMAIL=admin@example.com
```

## Scheduling on Linux/Unix

### Using Cron

1. Open crontab editor:
```bash
crontab -e
```

2. Add backup schedules:

```bash
# Daily database backup at 2:00 AM
0 2 * * * cd /path/to/sistema-ged && /path/to/python scripts/backup_database.py >> /var/log/ged_backup.log 2>&1

# Weekly file storage backup on Sunday at 3:00 AM
0 3 * * 0 cd /path/to/sistema-ged && /path/to/python scripts/backup_files.py >> /var/log/ged_backup.log 2>&1

# Weekly complete backup on Sunday at 2:00 AM (alternative)
0 2 * * 0 cd /path/to/sistema-ged && /path/to/python scripts/backup_all.py >> /var/log/ged_backup.log 2>&1
```

### Cron Schedule Format

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Common Schedules

- Daily at 2 AM: `0 2 * * *`
- Weekly on Sunday at 3 AM: `0 3 * * 0`
- Every 6 hours: `0 */6 * * *`
- First day of month at midnight: `0 0 1 * *`

## Scheduling on Windows

### Using Task Scheduler

1. Open Task Scheduler (`taskschd.msc`)

2. Create a new task:
   - **General Tab:**
     - Name: "Sistema GED - Daily Database Backup"
     - Description: "Automated daily database backup"
     - Run whether user is logged on or not
     - Run with highest privileges

   - **Triggers Tab:**
     - New trigger
     - Begin the task: On a schedule
     - Daily at 2:00 AM
     - Enabled

   - **Actions Tab:**
     - Action: Start a program
     - Program: `C:\Python\python.exe`
     - Arguments: `C:\path\to\sistema-ged\scripts\backup_database.py`
     - Start in: `C:\path\to\sistema-ged`

   - **Conditions Tab:**
     - Start only if computer is on AC power (optional)
     - Wake computer to run this task (optional)

   - **Settings Tab:**
     - Allow task to be run on demand
     - If task fails, restart every 10 minutes
     - Stop task if it runs longer than 3 hours

### PowerShell Script for Task Creation

```powershell
# Create daily database backup task
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\path\to\sistema-ged\scripts\backup_database.py" -WorkingDirectory "C:\path\to\sistema-ged"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "GED_Database_Backup" -Action $action -Trigger $trigger -Principal $principal -Settings $settings

# Create weekly file backup task
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\path\to\sistema-ged\scripts\backup_files.py" -WorkingDirectory "C:\path\to\sistema-ged"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "GED_Files_Backup" -Action $action -Trigger $trigger -Principal $principal -Settings $settings
```

## Recommended Backup Strategy

### Production Environment

1. **Database Backups:**
   - Frequency: Daily
   - Time: 2:00 AM (low usage period)
   - Retention: 90 days
   - Script: `backup_database.py`

2. **File Storage Backups:**
   - Frequency: Weekly (Sunday)
   - Time: 3:00 AM
   - Retention: 90 days
   - Compression: Enabled
   - Script: `backup_files.py`

3. **Complete Backups:**
   - Frequency: Weekly (Sunday)
   - Time: 2:00 AM
   - Alternative to separate database + file backups
   - Script: `backup_all.py`

### Development/Testing Environment

1. **Database Backups:**
   - Frequency: Weekly
   - Retention: 30 days

2. **File Storage Backups:**
   - Frequency: Monthly
   - Retention: 30 days

## Manual Backup Execution

### Run Backups Manually

```bash
# Database backup
python scripts/backup_database.py

# File storage backup
python scripts/backup_files.py

# Complete backup
python scripts/backup_all.py
```

### Windows

```cmd
cd C:\path\to\sistema-ged
python scripts\backup_database.py
python scripts\backup_files.py
python scripts\backup_all.py
```

## Backup Verification

All backup scripts include automatic verification:

- **Database backups:** Verified by SQL Server during backup process
- **File backups:** ZIP integrity check performed after backup

To manually verify a backup:

```python
from scripts.backup_files import FileStorageBackup

backup = FileStorageBackup()
backup.verify_backup('/path/to/backup.zip')
```

## Monitoring and Alerts

### Log Files

Backup scripts output to stdout/stderr. Redirect to log files:

```bash
python scripts/backup_all.py >> /var/log/ged_backup.log 2>&1
```

### Email Notifications

Configure email notifications in `.env`:

```bash
SEND_BACKUP_NOTIFICATIONS=True
BACKUP_NOTIFICATION_EMAIL=admin@example.com
```

### Monitoring Checklist

- [ ] Verify backup scripts run successfully
- [ ] Check backup file sizes are reasonable
- [ ] Confirm old backups are being cleaned up
- [ ] Test backup restoration periodically
- [ ] Monitor disk space in backup directory

## Backup Restoration

### Database Restoration

```sql
-- Restore database from backup
RESTORE DATABASE [sistema_ged]
FROM DISK = N'C:\backups\database\sistema_ged_backup_20240101_020000.bak'
WITH REPLACE, RECOVERY
```

### File Storage Restoration

```bash
# Extract ZIP backup
unzip files_backup_20240101_030000.zip -d /path/to/uploads/

# Or copy uncompressed backup
cp -r files_backup_20240101_030000/* /path/to/uploads/
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure backup directory has write permissions
   - Run with appropriate user privileges

2. **Disk Space Full**
   - Check available disk space
   - Reduce retention period
   - Enable compression for file backups

3. **Backup Takes Too Long**
   - Schedule during low-usage periods
   - Consider incremental backups
   - Optimize database before backup

4. **SQL Server Connection Failed**
   - Verify database credentials
   - Check SQL Server is running
   - Ensure sqlcmd is installed

### Getting Help

Check backup logs for detailed error messages:
```bash
tail -f /var/log/ged_backup.log
```

## Security Considerations

1. **Backup Storage:**
   - Store backups on separate physical disk/server
   - Use encrypted storage for sensitive data
   - Restrict access to backup directory

2. **Credentials:**
   - Never hardcode database passwords
   - Use environment variables or secure vaults
   - Rotate backup user credentials regularly

3. **Offsite Backups:**
   - Copy backups to remote location
   - Use cloud storage (S3, Azure Blob)
   - Implement 3-2-1 backup strategy

## Best Practices

1. **Test Restorations:** Regularly test backup restoration process
2. **Monitor Backup Size:** Track backup size trends
3. **Document Procedures:** Keep restoration procedures documented
4. **Automate Verification:** Schedule backup verification tests
5. **Maintain Logs:** Keep backup logs for audit purposes
