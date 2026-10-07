# Managed accounts

Keep a strong AUTH_SECRET in the deployment environment and a configured HTTPS/CORS origin.
Create the first Administrator interactively on the configured metadata volume:

```sh
docker compose -f infra/docker-compose.light.yml run --rm --no-deps api python -m app.accounts bootstrap --username owner
```

Bootstrap succeeds only for an empty accounts database; passwords are entered using getpass,
not command arguments or defaults. Users sign in through the web account panel; Administrator
controls create accounts, change roles, enable/disable and reset passwords. Reader, Student,
Researcher, Reviewer, Editor and Administrator roles are available; legacy Viewer/Transcriber
roles stay compatible. The last active Administrator cannot be removed.

Passwords use per-account random salts and scrypt(16384,8,1); hashing is serialized for memory
bounds. Hashes stay in a mode-0600 SQLite file. Audit stores identities and permission changes,
never password values/hashes. Login returns a one-hour signed token tied to account ID/version.
Any role change, disable, password reset or logout revokes existing managed sessions immediately.
Logout revokes all sessions for that account. Password reset currently requires Administrator;
self-service/email reset is not implemented. There is no public signup or invented email flow.

The web retains tokens only in memory/form inputs and clears them on logout or server change.
Account login requires HTTPS outside loopback development. Other existing editorial token
inputs remain available. Legacy `issue_token` tokens do not use account versions; rotate the
AUTH_SECRET to revoke them. Do not confuse client logout with legacy-token revocation.

The accounts SQLite file lives on `/data/metadata/accounts.sqlite3`; the consistent backup
script includes it. Backups are sensitive and created in a mode-0700 directory. Stop writes
for a corpus-wide snapshot and keep AUTH_SECRET separately for disaster recovery.
