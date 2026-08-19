# systemd units

Reference copies of the two systemd units that run Karmine on the Raspberry Pi
(`/etc/systemd/system/karmine-{backend,frontend}.service`). This directory
exists for history, review, and disaster recovery — it is **not** applied
automatically. `scripts/deploy.sh` never reads these files; it only restarts
the already-installed services when relevant paths change.

If you edit a unit file here, apply it by hand on the Pi:

```bash
sudo cp systemd/karmine-backend.service /etc/systemd/system/karmine-backend.service
sudo cp systemd/karmine-frontend.service /etc/systemd/system/karmine-frontend.service
sudo systemctl daemon-reload
sudo systemctl restart karmine-backend.service karmine-frontend.service
```

Then verify the change is what you intended (`systemctl status`, hit the
relevant endpoints) before committing — same as any other change to what's
actually running in production. Conversely, if you change the live unit
directly on the Pi first (as was done to fix the frontend's SPA-fallback bug
— see `systemd/karmine-frontend.service`'s lack of a `-s` flag), copy the
result back here (`systemctl cat <service>`) and commit it, so the fix has a
record and can't silently regress if the unit is ever recreated.

Both units hardcode Pi-specific absolute paths (the Poetry virtualenv hash,
the nvm Node version) that will go stale if those are ever reinstalled or
upgraded — check `poetry env info --path` / `which node` on the Pi if a
service fails to start after such a change, and update both the live unit
and this copy together.
