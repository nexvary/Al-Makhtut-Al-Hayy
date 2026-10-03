# Production Operations

## Secrets
Never commit `AUTH_SECRET`, database passwords, object-store credentials or private model URLs. Production startup rejects the development authentication secret.

## Database
Run SQL migrations in order from `services/api/migrations`. Migration 001 enables pgvector and creates provenance-first manuscript/page/region/text tables.

## Object storage
The application uses an `ObjectStore` contract. Local content-addressed storage is available for single-node deployments; an S3-compatible adapter can replace it without changing domain models.

## HTR queue
`RedisHtrQueue` persists job messages/results. Workers must use isolated job directories and pinned model checksums.

## Rate limiting
A process-local rate limiter protects a single API process. Multi-replica production should use Redis-backed counters at the proxy/application boundary.

## Backups
Back up PostgreSQL and object storage together. `infra/backup.sh` creates a timestamped PostgreSQL custom dump and object archive with 14-day local retention. Copy backups to a separate failure domain and regularly test restoration.

## Deployment
`infra/docker-compose.prod.yml` binds the API only to loopback. Put TLS/reverse proxy in front of it. Do not expose PostgreSQL or Redis publicly.

## Observability
API logs are JSON and every response receives `X-Request-ID`. Centralize stdout logs and add host/container metrics in deployment infrastructure.

## Release
A release candidate requires backend, HTR, web and Android CI to pass plus the end-to-end ingestion smoke test.
