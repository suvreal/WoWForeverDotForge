---
name: wow-forever-addons
description: Manage WoW Forever addons in Faugus on Linux using the local Forever Addons application. Use for addon installation, updates, integrity checks, and CurseForge catalog searches.
---

Run commands using the system Python 3 from the project root (`python3 app.py ...`). The user's local installation may be in `~/Applications/ForeverAddons`. Write all project content, code, interface text, and documentation in English.

- `list`: inventory of addon folders, versions, and package sources.
- `verify`: compare files against the installation SHA-256 manifest; return a nonzero status for changes. Unmanaged addons have no trusted reference manifest.
- `curse-search "query" [--index 20]`: search the CurseForge catalog for the client version by name, author, or numeric ID. An empty query lists popular addons.
- `install-curseforge ID`: install the latest available stable release for the client. Missing required dependencies are reported by name and ID; install them first.
- `check`: check compatible stable GitHub and CurseForge releases.
- `update`: update managed GitHub and CurseForge packages.
- `install-github OWNER/REPO`: install a distribution ZIP from a stable GitHub release.
- `install-zip /absolute/path.zip`: import a selected distribution ZIP; import newer versions the same way.
- `remove KEY`: remove a managed package after backing it up; obtain the key from `list`.
- `restore`: undo the latest package operation from its backup. This replaces later local edits to affected addons; explain that consequence before using it.
- `startup check|update|off`: configure behavior when opening the application, not at system login.
- `gui`: open the desktop application.

The default game path is `~/Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_`; `FOREVER_GAME_DIR` can override it. Only target `Interface/AddOns`; do not overwrite WTF, the client, Battle.net, or `_classic_beta_`. Read Interface from `WTF/Config.wtf`. Do not bypass compatibility checks by editing TOC files. A TOC declaration does not establish in-game API compatibility. State and backups are shared per Linux user; changing the game path does not create a separate profile.

Check inventory and integrity first. Report local modifications instead of bypassing overwrite protection. Do not change addons while WoW is running. Do not delete manifests or backups in `~/.local/share/forever-addons` without a request. Run `verify` after installation and report its result. Integrity compares files against the installed package; it does not scan for malicious code.

CurseForge uses the official API. Users enter their own key in the application or interactively through `curse-key`; never request it in chat, print its contents, or commit it. The file `~/.config/forever-addons/curseforge.key` has permissions 0600; `CURSEFORGE_API_KEY` takes precedence. Without a key, report that catalog access is unconfigured; never present simulated results as live responses. Respect distribution restrictions and missing download URLs. The application supports one active API key per process, not website account synchronization or independent addon sets by account.

GitHub uses the public Releases API without a token and examines the latest 15 releases. Prereleases and source ZIPs without a distribution layout are not accepted. When networking is unavailable, do not establish update status from local inventory alone. Install specific addons according to the user's selection or request.
