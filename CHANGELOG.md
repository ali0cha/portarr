# Changelog

All notable changes to Portarr are listed here. The version number is `__version__` in `app/__init__.py`;
a release is a `vX.Y.Z` git tag, which also publishes the Docker image `ghcr.io/ali0cha/portarr:X.Y.Z`.

## 0.1.0 - 2026-10-28

First release.

- Export and import of the quality configuration of Radarr, Sonarr, Lidarr, Whisparr and Prowlarr: custom
  formats, quality profiles and sizes, naming, media management, Lidarr metadata profiles, Prowlarr sync
  profiles, indexers and indexer proxies. Everything is referenced by name, so a bundle moves between
  instances whose IDs differ.
- Import of TRaSH Guides quality profiles (Radarr and Sonarr), from the catalogue or from pasted JSON, with
  their mandatory formats, optional groups and scores, and of their quality sizes and naming schemes, alone or
  together with a profile.
- Full backup and restore of a whole instance: Portarr triggers the application's own backup, downloads it and keeps it
  with a JSON export of the configuration. A full restore sends the zip back and waits for the restart, after backing
  up the target the same way; a selective restore opens the import with the JSON loaded.
- Scheduled full backups (every N days at a time, for the instances you choose, keeping the last few of each; only the
  scheduled ones are ever rotated out), an option to remove the copy the application keeps, and a way to bring in
  the application's own backups or a zip from another machine.
- A preview of every change before anything is written, an automatic backup of the target, and nothing is
  ever deleted. Exports never contain an API key or a password.
- Step-by-step web interface in English and French (light and dark theme), with the version and build in the
  sidebar and a notice when a newer version exists.
- Docker image for amd64 and arm64, running as user 568, with a health check on `/healthz`.
