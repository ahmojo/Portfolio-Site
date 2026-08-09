# Project working rules

## Production VM deployment safety

- Treat production content, the SQLite database, uploads, `.env` files, and generated metrics as authoritative data. Never overwrite them from a local checkout.
- Before a deployment, inspect the VM worktree status and diff, and make a recoverable backup of each code file that will be touched.
- For code-only deployments, prefer reviewed Git patch hunks or small code-region edits on the VM. Do not copy an entire repository, website directory, or whole file from the local workspace when a narrower patch is possible.
- Never replace production `data/`, database, upload, secret, environment, or editable content files as part of a code deployment.
- Preserve unrelated VM changes. After applying the patch, review the resulting diff, restart only the required services, and verify health plus the affected UI on production.
