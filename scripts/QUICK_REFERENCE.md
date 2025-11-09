# Quick Reference - Backup & Maintenance Scripts

## Backup Scripts

| Command | Purpose | Output | Frequency |
|---------|---------|--------|-----------|
| `python scripts/backup_database.py` | Backup database | `.bak` file | Daily |
| `python scripts/backup_files.py` | Backup files | `.zip` file | Weekly |
| `python scripts/backup_all.py` | Complete backup | Both above | Weekly |

## Cleanup Scripts

| Command | Purpose | Dry Run | Frequency |
|---------|---------|---------|-----------|
| `python scripts/cleanup_trash.py` | Delete old trash | `--dry-run` | Daily |
| `python scripts/cleanup_tokens.py` | Remove expired tokens | `--dry-run` | Daily |
| `python scripts/cleanup_audit_logs.py` | Archive old logs | `--dry-run` | Monthly |
| `python scripts/cleanup_all.py` | Complete cleanup | `--dry-run` | Weekly |

## Configuration (.env)

```bash
# Backup
BACKUP_DIR=backups
DATABASE_RETENTION_DAYS=90
FILES_RETENTION_DAYS=90
COMPRESS_FILE_BACKUPS=True

# Cleanup
TRASH_RETENTION_DAYS=30
AUDIT_LOG_RETENTION_DAYS=365
```

## Cron Schedule (Linux)

```bash
# Backups
0 2 * * * python /path/to/scripts/backup_database.py
0 3 * * 0 python /path/to/scripts/backup_files.py

# Cleanup
0 3 * * * python /path/to/scripts/cleanup_trash.py
30 3 * * * python /path/to/scripts/cleanup_tokens.py
0 4 1 * * python /path/to/scripts/cleanup_audit_logs.py
```

## Common Tasks

### Test Before Running
```bash
python scripts/cleanup_all.py --dry-run
```

### Check Backup Status
```bash
ls -lh backups/database/
ls -lh backups/files/
```

### View Logs
```bash
tail -f /var/log/ged_backup.log
tail -f /var/log/ged_cleanup.log
```

### Manual Backup
```bash
python scripts/backup_all.py
```

### Manual Cleanup
```bash
python scripts/cleanup_all.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | Check file/directory permissions |
| Database connection failed | Verify credentials in `.env` |
| Disk space full | Free space or reduce retention |
| Script timeout | Run during low-usage period |

## Documentation

- **README.md** - Overview and quick start
- **BACKUP_SCHEDULING.md** - Detailed backup scheduling
- **MAINTENANCE_GUIDE.md** - Detailed maintenance guide
