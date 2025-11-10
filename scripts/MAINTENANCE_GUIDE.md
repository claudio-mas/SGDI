# Maintenance Scripts Guide

This guide explains the maintenance and cleanup scripts for Sistema SGDI.

## Overview

Sistema SGDI includes automated maintenance scripts to keep the system clean and performant:

1. **Trash Cleanup** - Permanently delete documents in trash for 30+ days
2. **Token Cleanup** - Remove expired password reset tokens
3. **Audit Log Cleanup** - Archive and clean old audit logs

## Cleanup Scripts

### 1. Trash Cleanup (`cleanup_trash.py`)

Permanently deletes documents that have been in the trash for longer than the retention period (default: 30 days).

**Usage:**
```bash
# Normal execution
python scripts/cleanup_trash.py

# Dry run (preview without making changes)
python scripts/cleanup_trash.py --dry-run
```

**What it does:**
- Finds documents with status='excluido' older than retention period
- Deletes physical files from storage
- Deletes version files
- Removes database records

**Configuration:**
```bash
# In .env file
TRASH_RETENTION_DAYS=30  # Default: 30 days
```

### 2. Token Cleanup (`cleanup_tokens.py`)

Removes expired and used password reset tokens from the database.

**Usage:**
```bash
# Normal execution (removes expired and used tokens)
python scripts/cleanup_tokens.py

# Dry run
python scripts/cleanup_tokens.py --dry-run

# Only remove expired tokens (keep used ones)
python scripts/cleanup_tokens.py --no-include-used
```

**What it does:**
- Finds expired password reset tokens
- Optionally finds used tokens
- Deletes tokens from database

### 3. Audit Log Cleanup (`cleanup_audit_logs.py`)

Archives old audit logs to JSON files and optionally removes them from the database.

**Usage:**
```bash
# Normal execution (archive and delete)
python scripts/cleanup_audit_logs.py

# Dry run
python scripts/cleanup_audit_logs.py --dry-run

# Delete without archiving (not recommended)
python scripts/cleanup_audit_logs.py --no-archive
```

**What it does:**
- Finds audit logs older than retention period
- Archives logs to JSON file
- Provides statistics about archived logs
- Deletes logs from database

**Configuration:**
```bash
# In .env file
AUDIT_LOG_RETENTION_DAYS=365  # Default: 1 year
```

### 4. Complete Cleanup (`cleanup_all.py`)

Runs all cleanup tasks in sequence.

**Usage:**
```bash
# Normal execution
python scripts/cleanup_all.py

# Dry run
python scripts/cleanup_all.py --dry-run
```

**What it does:**
- Executes trash cleanup
- Executes token cleanup
- Executes audit log cleanup
- Provides summary of all operations

## Scheduling Maintenance Tasks

### Recommended Schedule

**Production Environment:**

1. **Trash Cleanup:**
   - Frequency: Daily
   - Time: 3:00 AM
   - Command: `python scripts/cleanup_trash.py`

2. **Token Cleanup:**
   - Frequency: Daily
   - Time: 3:30 AM
   - Command: `python scripts/cleanup_tokens.py`

3. **Audit Log Cleanup:**
   - Frequency: Monthly (first day of month)
   - Time: 4:00 AM
   - Command: `python scripts/cleanup_audit_logs.py`

4. **Complete Cleanup:**
   - Frequency: Weekly (Sunday)
   - Time: 3:00 AM
   - Alternative to individual scripts
   - Command: `python scripts/cleanup_all.py`

### Linux/Unix Cron

Add to crontab (`crontab -e`):

```bash
# Daily trash cleanup at 3:00 AM
0 3 * * * cd /path/to/sistema-ged && python scripts/cleanup_trash.py >> /var/log/ged_cleanup.log 2>&1

# Daily token cleanup at 3:30 AM
30 3 * * * cd /path/to/sistema-ged && python scripts/cleanup_tokens.py >> /var/log/ged_cleanup.log 2>&1

# Monthly audit log cleanup on 1st at 4:00 AM
0 4 1 * * cd /path/to/sistema-ged && python scripts/cleanup_audit_logs.py >> /var/log/ged_cleanup.log 2>&1

# Alternative: Weekly complete cleanup on Sunday at 3:00 AM
0 3 * * 0 cd /path/to/sistema-ged && python scripts/cleanup_all.py >> /var/log/ged_cleanup.log 2>&1
```

### Windows Task Scheduler

**PowerShell script to create tasks:**

```powershell
# Daily trash cleanup
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\path\to\sistema-ged\scripts\cleanup_trash.py" -WorkingDirectory "C:\path\to\sistema-ged"
$trigger = New-ScheduledTaskTrigger -Daily -At 3am
Register-ScheduledTask -TaskName "GED_Cleanup_Trash" -Action $action -Trigger $trigger

# Daily token cleanup
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\path\to\sistema-ged\scripts\cleanup_tokens.py" -WorkingDirectory "C:\path\to\sistema-ged"
$trigger = New-ScheduledTaskTrigger -Daily -At 3:30am
Register-ScheduledTask -TaskName "GED_Cleanup_Tokens" -Action $action -Trigger $trigger

# Monthly audit log cleanup
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\path\to\sistema-ged\scripts\cleanup_audit_logs.py" -WorkingDirectory "C:\path\to\sistema-ged"
$trigger = New-ScheduledTaskTrigger -Daily -At 4am
# Note: Configure to run only on 1st day of month in Task Scheduler GUI
Register-ScheduledTask -TaskName "GED_Cleanup_AuditLogs" -Action $action -Trigger $trigger
```

## Dry Run Mode

All cleanup scripts support dry-run mode to preview changes without making them:

```bash
python scripts/cleanup_trash.py --dry-run
python scripts/cleanup_tokens.py --dry-run
python scripts/cleanup_audit_logs.py --dry-run
python scripts/cleanup_all.py --dry-run
```

**Benefits:**
- Preview what will be deleted
- Verify script configuration
- Test before production deployment
- Generate reports without changes

## Monitoring and Logging

### Log Output

All scripts output detailed information:
- Items found for cleanup
- Actions taken
- Errors encountered
- Summary statistics

### Redirect to Log Files

```bash
# Append to log file
python scripts/cleanup_all.py >> /var/log/ged_cleanup.log 2>&1

# Separate log files per script
python scripts/cleanup_trash.py >> /var/log/ged_cleanup_trash.log 2>&1
python scripts/cleanup_tokens.py >> /var/log/ged_cleanup_tokens.log 2>&1
python scripts/cleanup_audit_logs.py >> /var/log/ged_cleanup_audit.log 2>&1
```

### Monitoring Checklist

- [ ] Verify cleanup scripts run successfully
- [ ] Check log files for errors
- [ ] Monitor disk space freed
- [ ] Verify archived audit logs are accessible
- [ ] Confirm database size reduction

## Archive Management

### Audit Log Archives

Archives are stored in: `backups/audit_logs/`

**Archive format:** JSON
**Naming:** `audit_logs_archive_YYYYMMDD_HHMMSS.json`

**Archive structure:**
```json
[
  {
    "id": 12345,
    "usuario_id": 1,
    "acao": "download",
    "tabela": "documentos",
    "registro_id": 100,
    "dados_json": "{...}",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "data_hora": "2024-01-01T10:30:00"
  }
]
```

### Archive Retention

Manage archive files separately:

```bash
# Find archives older than 2 years
find backups/audit_logs/ -name "*.json" -mtime +730

# Delete archives older than 2 years
find backups/audit_logs/ -name "*.json" -mtime +730 -delete

# Compress old archives
find backups/audit_logs/ -name "*.json" -mtime +365 -exec gzip {} \;
```

## Troubleshooting

### Common Issues

**1. Permission Denied**
```
Error: Permission denied when deleting files
```
**Solution:** Ensure script runs with appropriate permissions to delete files and modify database.

**2. Database Connection Failed**
```
Error: Could not connect to database
```
**Solution:** Verify database credentials in `.env` file and ensure database is running.

**3. File Not Found**
```
Warning: File not found: /path/to/file
```
**Solution:** This is normal if files were manually deleted. Script will continue and clean database records.

**4. Disk Space Issues**
```
Error: No space left on device
```
**Solution:** Free up disk space or adjust retention periods to delete more aggressively.

### Debug Mode

Run scripts with Python verbose mode:

```bash
python -v scripts/cleanup_all.py
```

### Manual Verification

Check database before and after cleanup:

```sql
-- Count documents in trash
SELECT COUNT(*) FROM documentos WHERE status = 'excluido';

-- Count expired tokens
SELECT COUNT(*) FROM password_resets WHERE expiracao < GETDATE();

-- Count old audit logs
SELECT COUNT(*) FROM log_auditoria WHERE data_hora < DATEADD(day, -365, GETDATE());
```

## Safety Features

### Built-in Safeguards

1. **Dry Run Mode:** Preview changes before execution
2. **Retention Periods:** Configurable grace periods
3. **Archive Before Delete:** Audit logs archived before deletion
4. **Transaction Rollback:** Database changes rolled back on error
5. **Detailed Logging:** Complete audit trail of cleanup operations

### Recovery Options

**Restore from Trash:**
Documents in trash can be restored before permanent deletion:
```python
from app.models.document import Documento
doc = Documento.query.get(document_id)
doc.restore()
```

**Restore Audit Logs:**
Archived audit logs can be imported back:
```python
import json
with open('audit_logs_archive_20240101_040000.json') as f:
    logs = json.load(f)
# Process and re-import logs as needed
```

## Best Practices

1. **Test First:** Always run with `--dry-run` before production
2. **Monitor Logs:** Review cleanup logs regularly
3. **Verify Archives:** Ensure audit log archives are created successfully
4. **Adjust Retention:** Tune retention periods based on requirements
5. **Schedule Wisely:** Run during low-usage periods
6. **Backup First:** Ensure backups are current before cleanup
7. **Document Changes:** Keep records of cleanup operations

## Integration with Backup Strategy

Coordinate cleanup with backup schedule:

1. **Run backups first** (2:00 AM)
2. **Then run cleanup** (3:00 AM)
3. **Verify both completed** (4:00 AM)

This ensures deleted data is backed up before permanent removal.

## Compliance Considerations

### Data Retention Policies

Adjust retention periods to meet regulatory requirements:

```bash
# LGPD/GDPR: Minimum retention for audit logs
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years

# Document retention
TRASH_RETENTION_DAYS=30  # 30 days grace period
```

### Audit Trail

All cleanup operations should be logged:
- What was deleted
- When it was deleted
- Who initiated the cleanup (system/admin)
- How many items were affected

## Support

For issues or questions:
1. Check log files for detailed error messages
2. Review this guide for troubleshooting steps
3. Run scripts in dry-run mode to diagnose issues
4. Contact system administrator
