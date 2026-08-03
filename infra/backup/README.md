# Backup schedule

Run `scripts/backup.py` from a host timer (cron or systemd timer). Store the
result outside the application host and encrypt it with the operator-approved
backup system. The encryption key must not live beside the backup.

Recommended small deployment policy:

- daily database backup;
- 7 daily, 4 weekly and 6 monthly copies;
- backup before every application upgrade;
- quarterly restore rehearsal into a new, empty database;
- document deletion remains present in offline backups until the retention
  period expires.

The repository does not choose a backup-encryption product or store its key.
