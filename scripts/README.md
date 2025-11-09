# Sistema GED - Backup and Maintenance Scripts

This directory contains automated scripts for backup and maintenance operations.

## Directory Structure

```
scripts/
├── README.md                    # This file
├── BACKUP_SCHEDULING.md         # Backup scheduling guide
├── MAINTENANCE_GUIDE.md         # Maintenance scripts guide
├── backup_config.py             # Backup configuration
├── backup_database.py           # Database backup script
├── backup_files.py              # File storage backup script
├── backup_all.py                # Complete backup script
├── cleanup_trash.py             # Trash cleanup script
├── cleanup_tokens.py            # Token cleanup script
├── cleanup_audit_logs.py        # Audit log cleanup script
└── cleanup_all.py               # Complete cleanup script
```

## Quick Start

### Backup Operations

```bash
# Database backup
python scripts/backup_database.py

# File storage backup
python scripts/backup_files.py

# Complete system backup
python scripts/backup_all.py
```

### Maintenance Operations

```bash
# Clean old trash items
python scripts/cleanup_trash.py

# Clean expired tokens
python scripts/cleanup_tokens.py

# Archive old audit logs
python scripts/cleanup_audit_logs.py

# Complete cleanup
python scripts/cleanup_all.py
```

### Dry Run Mode

Preview changes without making them:

```bash
python scripts/cleanup_all.py --dry-run
python scripts/backup_all.py  # Backups don't have dry-run
```

## Configuration

Configure backup and maintenance settings in `.env`:

```bash
# Backup settings
BACKUP_DIR=backups
DATABASE_RETENTION_DAYS=90
FILES_RETENTION_DAYS=90
COMPRESS_FILE_BACKUPS=True
VERIFY_BACKUPS=True

# Maintenance settings
TRASH_RETENTION_DAYS=30
AUDIT_LOG_RETENTION_DAYS=365
```

## Scheduling

### Recommended Schedule

**Production:**
- Database backup: Daily at 2:00 AM
- File backup: Weekly (Sunday) at 3:00 AM
- Trash cleanup: Daily at 3:00 AM
- Token cleanup: Daily at 3:30 AM
- Audit log cleanup: Monthly at 4:00 AM

See [BACKUP_SCHEDULING.md](BACKUP_SCHEDULING.md) for detailed scheduling instructions.

## Documentation

- **[BACKUP_SCHEDULING.md](BACKUP_SCHEDULING.md)** - Complete guide for scheduling backups
- **[MAINTENANCE_GUIDE.md](MAINTENANCE_GUIDE.md)** - Complete guide for maintenance scripts

## Requirements

### System Requirements

- Python 3.8+
- SQL Server client tools (sqlcmd)
- Sufficient disk space for backups
- Write permissions to backup directory

### Python Dependencies

All dependencies are included in `requirements.txt`:
- Flask and extensions
- SQLAlchemy
- PyODBC

## Script Details

### Backup Scripts

| Script | Purpose | Frequency | Output |
|--------|---------|-----------|--------|
| `backup_database.py` | SQL Server backup | Daily | `.bak` files |
| `backup_files.py` | File storage backup | Weekly | `.zip` files |
| `backup_all.py` | Complete backup | Weekly | Both above |

### Cleanup Scripts

| Script | Purpose | Frequency | Retention |
|--------|---------|-----------|-----------|
| `cleanup_trash.py` | Delete old trash | Daily | 30 days |
| `cleanup_tokens.py` | Remove expired tokens | Daily | Immediate |
| `cleanup_audit_logs.py` | Archive old logs | Monthly | 365 days |
| `cleanup_all.py` | Complete cleanup | Weekly | Various |

## Safety Features

1. **Dry Run Mode** - Preview changes before execution
2. **Retention Periods** - Configurable grace periods
3. **Archive Before Delete** - Audit logs archived before deletion
4. **Transaction Rollback** - Database changes rolled back on error
5. **Detailed Logging** - Complete audit trail

## Monitoring

### Check Script Status

```bash
# View recent backup logs
tail -f /var/log/ged_backup.log

# View recent cleanup logs
tail -f /var/log/ged_cleanup.log
```

### Verify Backups

```bash
# List recent backups
ls -lh backups/database/
ls -lh backups/files/

# Check backup sizes
du -sh backups/
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure write permissions to backup directory
   - Run with appropriate user privileges

2. **Database Connection Failed**
   - Verify database credentials in `.env`
   - Check SQL Server is running
   - Ensure sqlcmd is installed

3. **Disk Space Full**
   - Check available disk space
   - Reduce retention periods
   - Enable compression

4. **Script Timeout**
   - Increase timeout in script
   - Schedule during low-usage periods
   - Optimize database before backup

### Getting Help

1. Run scripts with `--dry-run` to diagnose issues
2. Check log files for detailed error messages
3. Review documentation in this directory
4. Contact system administrator

## Best Practices

1. **Test First** - Always test with `--dry-run` before production
2. **Monitor Regularly** - Review logs and verify backups
3. **Schedule Wisely** - Run during low-usage periods
4. **Verify Backups** - Test restoration periodically
5. **Document Changes** - Keep records of operations
6. **Coordinate Operations** - Run backups before cleanup
7. **Maintain Security** - Protect backup files and credentials

## Integration

### With Cron (Linux)

```bash
# Edit crontab
crontab -e

# Add backup and cleanup schedules
0 2 * * * cd /path/to/sistema-ged && python scripts/backup_all.py >> /var/log/ged_backup.log 2>&1
0 3 * * * cd /path/to/sistema-ged && python scripts/cleanup_all.py >> /var/log/ged_cleanup.log 2>&1
```

### With Task Scheduler (Windows)

See [BACKUP_SCHEDULING.md](BACKUP_SCHEDULING.md) for PowerShell scripts to create scheduled tasks.

## Support

For detailed information:
- Backup operations: See [BACKUP_SCHEDULING.md](BACKUP_SCHEDULING.md)
- Maintenance operations: See [MAINTENANCE_GUIDE.md](MAINTENANCE_GUIDE.md)
- Configuration: Check `.env.example` for all options

## Version

Current version: 1.0.0

## License

Part of Sistema GED - Electronic Document Management System
