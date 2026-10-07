# Light deployment for 2 cores / 1 GB RAM / 40 GB disk

This profile runs one FastAPI worker and durable SQLite metadata. It does not start
PostgreSQL, Redis, HTR, translation models or LLMs. The standard deployment remains available
for the PostgreSQL/pgvector/Redis upgrade path; not every legacy prototype has been migrated
to durable adapters yet. Avoid multiple workers until source metadata locking is upgraded.

Before launch set a strong AUTH_SECRET (at least 32 characters) and CORS_ORIGINS to the exact
HTTPS website origin. Run from infra:

```
docker compose -f docker-compose.light.yml up -d --build
```

The API binds to localhost:8000, uses a non-root user, drops capabilities, uses a read-only
container filesystem, and persists metadata/objects in named volumes. Limit: 384 MiB, 1.25 CPU,
128 processes, 24 concurrent requests, 32 MiB temporary directory. Logs rotate at 5 MiB × 3.
These are configured limits, not a measured production load guarantee. /health is checked every
30 seconds. Use an existing Caddy or Nginx TLS front end; configure only the deployed domain,
compress textual responses, and reject external plaintext access to the API. Configure trusted
proxy IP handling explicitly before relying on forwarded client rate limits.

API metadata POST/PUT/PATCH bodies are bounded to 2 MiB even without Content-Length;
HTTP 413 occurs before request processing. Security response headers prevent MIME sniffing,
framing and referrer leakage. The default light rate limit is 90 requests/minute per observed
client/process. Store scientific originals externally when permitted; the API does not mirror
IIIF image collections. Android local imports retain their own on-device size policy.

StorageProvider allows later S3-compatible/R2/MinIO adapters. LocalObjectStore streams at
64 KiB, atomically publishes content-addressed objects, removes failed temporary writes and
enforces per-object 128 MiB and local total 5 GiB defaults. This limit is a provider default,
not a claim that every legacy upload endpoint has been migrated. Use object storage for scale.
After a crash, expire orphan .pending-* processing files older than 24 hours in the object
volume; never delete source objects by cache eviction. No full archive fits into 40 GB.

Reserve at least 10 GB for OS, logs and update headroom. Monitor disk/RAM before importing.
An optional 1 GB swap file can absorb spikes; it is not an inference engine or extra sustained
RAM. Configure OS swap/firewall only with actual server access; none was changed remotely here.

## Backup / restore

Daily backups must cover all metadata databases, source objects, required configuration and
a secure copy of AUTH_SECRET. Keep at least one encrypted off-server backup. Pause scientific
writes for a corpus-wide snapshot; per-database SQLite backup is internally consistent but cannot
atomically snapshot relationships across several databases while writers continue.

```
python infra/backup_light.py /path/to/metadata /path/to/new-backup-directory
```

The tool refuses to overwrite an existing backup, checks each SQLite snapshot integrity and
writes a SHA-256 manifest. Back up objects separately with original ownership/permissions.
Restore into a new directory, verify every manifest hash and PRAGMA integrity_check, start an
isolated API against restored paths and check source/layer/exercise relations. Stop the active
service before replacing volumes. Never run the old PostgreSQL-only backup script as the sole
backup for this profile. Backup/restore of a real VPS remains unverified without server access.
