# WoWForeverDotForge

**Forever Addons** is a local Linux addon manager for World of Warcraft Forever installed through Faugus. It provides a native GTK 4 interface, a CurseForge catalog, installation from GitHub Releases and ZIP packages, updates, file integrity checks, and backups. It is not affiliated with Blizzard or CurseForge.

All project code, interface text, documentation, comments, and contribution messages are written in English.

## Requirements

- Linux with Python 3.10 or later. The graphical interface also requires PyGObject, GTK 4, and an active desktop session.
- A WoW Forever installation that you have started and exited normally at least once. It must contain `_forever_/Wow.exe` and `_forever_/WTF/Config.wtf` with an `engineSurveyPatch` setting.
- Write access to `Interface/AddOns` and enough free disk space for downloads, extraction, and backups. Run the manager as your normal Linux user.
- An internet connection for catalog searches and updates. Local inventory, integrity checks, importing an existing ZIP, and restoring backups work offline.
- Your own approved CurseForge API key for the built-in catalog. GitHub installation and manual ZIP imports do not require that key.

Battle.net and Faugus do not need to be running while you manage addons. Exit the game before installing, updating, removing, or restoring packages, and do not start it while an operation is in progress.

## 1. Install the application

### Pop!_OS 22.04, Ubuntu, and Debian

```bash
sudo apt update
sudo apt install git python3 python3-gi gir1.2-gtk-4.0 xdg-user-dirs
mkdir -p "$HOME/Applications"
git clone https://github.com/suvreal/WoWForeverDotForge.git "$HOME/Applications/WoWForeverDotForge"
cd "$HOME/Applications/WoWForeverDotForge"
/usr/bin/python3 --version
/usr/bin/python3 -c 'import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk; print("GTK 4 is available")'
/usr/bin/python3 install.py --desktop
/usr/bin/python3 app.py
```

On other distributions, install the packages that provide Python 3.10+, the `gi` module, GTK 4 introspection data, and `xdg-user-dir`. Run the remaining commands from the directory containing `app.py`. The application does not require `pip install`, Wine, or the Windows CurseForge client. Use the system Python: a virtual environment usually cannot see the distribution's `python3-gi` package.

If your existing installation is in `~/Applications/ForeverAddons`, work in that directory instead. You do not need a second copy. Do not clone into an existing nonempty directory.

The installer registers the application at its current location. It creates `~/.local/share/applications/forever-addons.desktop`; `--desktop` also creates `Forever Addons.desktop` in the folder returned by `xdg-user-dir DESKTOP`. It does not copy the application source elsewhere. Run the installer again after moving the project. If your desktop requires confirmation, right-click the shortcut and select **Allow Launching**. If no desktop folder is configured, use `python3 install.py` without `--desktop` and launch from the application menu.

## 2. Configure the game installation

The default game directory is:

```text
~/Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_
```

Check the `Interface/AddOns` path and the client's Interface number in the application header. The manager only targets a folder named `_forever_`; it does not support `_classic_beta_`, Classic Era, or Retail. Do not edit TOC files or client settings to bypass compatibility checks.

### A different disk or Wine prefix

Set `FOREVER_GAME_DIR` to the full path of the `_forever_` directory, rather than `Interface/AddOns`. For a single launch:

```bash
FOREVER_GAME_DIR='/mnt/games/Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_' /usr/bin/python3 app.py
```

Use the same variable with `list`, `verify`, `check`, and other commands for that installation. The application does not save the game path in its settings.

To preserve the path when launching from an icon, edit the `Exec=` line in the corresponding `.desktop` file. For example:

```ini
Exec=/usr/bin/env "FOREVER_GAME_DIR=/mnt/games/Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_" /usr/bin/python3 "/home/YOUR_USER/Applications/WoWForeverDotForge/app.py"
```

Replace both paths with your actual absolute paths. Desktop entries do not expand `~` or `$HOME`. Update both the application-menu entry and the desktop copy if you use both. Running `FOREVER_GAME_DIR=… python3 install.py` alone does not save that setting in the launcher. Running the installer again overwrites a customized `Exec=` line.

**Multiple game installations:** the current application uses one package registry and backup directory per Linux user. Changing `FOREVER_GAME_DIR` does not create an independent profile. Use one managed installation per Linux user; use separate Linux accounts for independent environments. There is no built-in game-profile switcher yet.

## 3. CurseForge accounts and API access

### Which account or key do you need?

| Access type | How this application uses it |
| --- | --- |
| Regular CurseForge website account | Sign in through your browser. The application does not inherit that session or its API permissions. |
| Approved third-party CurseForge API access | Its API key enables built-in searches, direct installation, and updates. |
| Game publisher account in CurseForge for Studios | Intended for publishers of their own games. Do not create a new game to manage WoW addons. |
| Battle.net account | Used by the game; never entered into this manager. |
| GitHub account | Not required to download public GitHub Releases. Required separately to push changes to this project. |

The client supports **one active API key per process**. It does not provide OAuth sign-in, a list of CurseForge accounts, cloud synchronization, importing favorites, or separate addon sets for website accounts. Signing into another account in your browser does not change the application's active API key.

### Request your own API key

1. Open the [official CurseForge API key application guide](https://support.curseforge.com/support/solutions/articles/9000208346-about-the-curseforge-api-and-how-to-apply-for-a-key).
2. Follow its application link for third-party developers. Describe your actual project, its GitHub URL, and your intended use for searching and downloading WoW addons.
3. Complete the required terms and approval process. A regular website account does not automatically grant API access; availability and approval are controlled by CurseForge.
4. Once approved, use the key assigned to your access. Follow its terms, including any restriction to a particular application.

The [API documentation](https://docs.curseforge.com/rest-api/) distinguishes game publishers from third-party applications. Do not obtain another manager's key from its source code. Your account password, browser cookie, and Battle.net token are not API keys.

### Configure the key in the application

1. Open **Browse CurseForge → Set API key**.
2. Paste your key into the hidden field and click **Save**.
3. Leave the search empty and click **Search**, or enter an addon name.
4. A successful connection returns actual catalog results or a valid empty response. The message that a key is configured only confirms that a key is present; it does not verify its validity.

The key is stored unencrypted in `~/.config/forever-addons/curseforge.key` with permissions `0600`. The file is outside the repository, package registry, and backups. Do not display it using `cat`, or paste it into chat, tickets, desktop entries, or Git commits. Revoke a compromised key through its API provider, then configure a replacement.

Alternatively, configure it from a terminal using a hidden input prompt:

```bash
/usr/bin/python3 app.py curse-key
/usr/bin/python3 app.py curse-search ""
```

### Switch to another API account or access grant

**Replace the saved key:** close the application. If launching from a terminal, run `unset CURSEFORGE_API_KEY`, open the application from that terminal, and save the other access grant's key in the settings dialog. This replaces the saved key, but preserves installed addons and backups. Replacing the local file does not revoke the previous key at CurseForge.

**Forget the saved key:** select **Forget the saved key** in the dialog and save. In the CLI, submit an empty value to `curse-key`. An empty field in the graphical dialog instead preserves the existing key.

**Environment variable precedence:** a nonempty `CURSEFORGE_API_KEY` overrides the saved file. Deleting the file or changing the key in the dialog does not change an existing process's environment variable. To return to the saved-file configuration, close the application, unset the variable in the environment you launch it from, and start a new process. Starting a second instance while a window is open may simply activate the original window with its original environment.

### Keep multiple keys under one Linux account

Named profiles are not built in yet. If you are authorized to use multiple API keys, you can keep them in separate files outside the project and pass the selected one to the process. These commands use **Bash** and do not place the key value in command history:

```bash
(
    umask 077
    mkdir -p "$HOME/.config/forever-addons/accounts"
    read -r -s -p 'API key for account A: ' cf_profile_key
    printf '\n'
    printf '%s' "$cf_profile_key" > "$HOME/.config/forever-addons/accounts/account-a.key"
    chmod 600 "$HOME/.config/forever-addons/accounts/account-a.key"
    unset cf_profile_key
)
```

Repeat the storage step using `account-b.key` for another access grant. Close every application window before switching keys. From the project directory, launch with:

```bash
CURSEFORGE_API_KEY="$(< "$HOME/.config/forever-addons/accounts/account-a.key")" /usr/bin/python3 app.py
```

Use the other file for account B. The key is passed through the environment rather than a command-line argument, and is not copied into the shared saved-key file. Do not share your process environment or diagnostic dumps. You manage these files yourself: **Forget the saved key** does not delete them.

This only switches API access. The same Linux user still uses **the same installed addons, manifests, backups, and startup settings**. For two people with independent data, use separate Linux accounts and configure each person's own installation and authorized API key. Each user also needs appropriate access to their game directory.

### Use the manager without an API key

An addon's website button opens its browser page, where you can download a compatible ZIP and use **Import ZIP**. Without a connected catalog, open the [CurseForge website search](https://www.curseforge.com/wow/search?class=addons) directly. GitHub Releases and local file checks also remain available. Manually imported ZIPs are not automatically associated with a CurseForge project and must be updated by importing another ZIP.

## 4. Install and manage addons

### From the CurseForge catalog

1. In **Browse CurseForge**, search by addon name, author, or numeric project ID. An empty query browses popular results. Select a sort order and use **Previous / Next** to browse pages.
2. Click **Install**. File selection accepts available stable releases for the exact client version, then validates download size, the API-provided checksum, and the TOC Interface inside the ZIP. Beta, alpha, and early-access files are not installed automatically. A search result therefore does not guarantee an installable stable release.
3. If the application lists a required dependency by name and ID, install that dependency first, then retry the original addon. Dependencies are not downloaded automatically. A manually installed or GitHub-installed library may not be recognized as satisfying a specific CurseForge project's API dependency.
4. If the author disables third-party distribution or the API does not provide a download, use the addon website and import a ZIP manually. The manager does not bypass those restrictions.
5. After installation, open **Installed addons → Verify files**. Start WoW only after all operations finish, then verify that the addon loads in the game.

The version filter and TOC are author declarations; they do not guarantee that the addon works correctly with the current game API.

### From GitHub Releases

Enter `OWNER/REPOSITORY` or the repository's main URL in the GitHub field. The manager examines the latest 15 releases for a compatible distribution ZIP in a stable release. It ignores prereleases and `nolib` packages. The automatically generated **Source code (zip)** usually lacks the correct distribution structure and is not a substitute for a packaged addon release.

### From a local ZIP

Click **Import ZIP** and select the archive. Expected structure:

```text
Addon.zip
└── AddonName/
    ├── AddonName.toc
    └── ...addon files...
```

An archive may contain multiple addons, but each must provide a valid TOC for the current Interface. Unsafe paths, symlinks, and executable files are rejected. Downloaded or imported ZIPs are limited to 100 MB; extracted archives are limited to 400 MB and 25,000 entries.

Existing unmanaged folders are displayed but are not automatically adopted or overwritten. Do not delete them just to bypass a collision warning. Plan any migration with your own backup and source verification.

### Updates and startup checks

- **Check for updates** looks for compatible releases.
- **Update all** updates managed GitHub and CurseForge packages unless compatibility checks, missing dependencies, network errors, or local changes prevent it.
- Update a manually imported ZIP by importing a newer distribution package with the same addon folders.
- **When the application starts** offers checks, automatic updates, or no action. This applies when opening the manager; it does not create a background service or start the application at Linux login.

Read the full output after a batch operation. Packages are processed independently: one failure does not mean every package failed. CLI `check` and `update` can return exit code 0 while reporting individual package failures in their output. Automation must not rely on the exit code alone.

## 5. Integrity, backups, and recovery

**Verify files** compares each file's SHA-256 digest with the manifest created during installation. It detects modified, added, and missing files. It is not a malware scanner or independent verification of an author's trustworthiness. Unmanaged addons have no reference manifest, and **Unmanaged** does not mean their integrity has been verified.

Before installation, update, or removal, the manager backs up affected addons. If a write fails, it attempts to restore the previous state. An interrupted process may leave `pending.json`; further changes are blocked until recovery.

**Restore latest backup** restores the state before the latest package operation. It replaces the current contents of affected folders, including any later local edits. After updating multiple packages, it restores the last individual operation rather than the whole batch. Repeated restores do not automatically step through older backups. Local changes block updates and removal: preserve your edits before deciding whether to keep them or restore a previous state. There is currently no repair button that reinstalls the exact currently installed archive.

| Location | Contents |
| --- | --- |
| `~/.config/forever-addons/curseforge.key` | Saved API key; permissions 0600, unencrypted. |
| `~/.local/share/forever-addons/state.json` | Package sources, versions, manifests, and startup mode. |
| `~/.local/share/forever-addons/backups/` | Backups taken before changes; never pruned automatically. |
| `~/.local/share/forever-addons/pending.json` | Unfinished operation record, when present. |
| `_forever_/Interface/AddOns/` | Installed addon files. |
| `_forever_/WTF/` | Client, character, and addon settings; neither overwritten nor backed up by the manager. |

When migrating, preserve both your addons and the manager's entire data directory. Do not delete `state.json` to resolve an integrity error: doing so loses package tracking and reference manifests. Back up WTF settings separately as needed.

## 6. Verify a working installation and troubleshoot

From the project root:

```bash
/usr/bin/python3 app.py list
/usr/bin/python3 app.py verify
/usr/bin/python3 app.py curse-search ""
/usr/bin/python3 app.py check
```

`list` reports actual local folders; `[]` is normal for an empty installation. `verify` returns 1 for modified or missing managed files and 0 otherwise; exit code 0 does not verify unmanaged folders. `curse-search` must return a real API response without a connection error. After installing your first chosen addon, verify its files and then confirm it loads in the game. Automated tests alone do not establish that your API key, network connection, or graphical session works.

| Problem | What to check |
| --- | --- |
| `No module named gi` / GTK unavailable | Install the packages from section 1 and use `/usr/bin/python3` outside a virtual environment. |
| No graphical session | Launch from your logged-in desktop terminal without `sudo`. Use CLI commands over SSH without a graphical session. |
| Not a `_forever_` installation | The directory must end in `_forever_` and contain `Wow.exe`. Check `FOREVER_GAME_DIR` and the shortcut's `Exec=` line. |
| Unable to detect Interface | Start the correct game version and exit it. Check its `WTF/Config.wtf`; do not invent an Interface value. |
| A key is configured but the catalog reports 401/403 | Check that your API access is approved and valid, and whether `CURSEFORGE_API_KEY` overrides the saved key. Website sign-in is insufficient. |
| Replacing/deleting the key did not help | Close the existing window, unset the environment variable, and launch a new process. |
| Empty catalog or no stable ZIP | Try another query or ID, and check whether the author publishes a stable package for your exact client version. Do not bypass checks by editing TOC files. |
| Missing dependency | Search for and install the reported project ID, then retry the original addon. |
| Distribution disabled / missing download URL | Use the project's website and its permitted manual download, then import the ZIP. |
| HTTP 429 | Wait and retry later; changing accounts is not a remedy. |
| Network unavailable / `Could not resolve host` | Run `getent hosts api.curseforge.com github.com` in a normal terminal. Agent network restrictions are separate from your desktop's connection. |
| WoW or another operation is running | Exit the game and wait for the other manager operation to finish. |
| Local changes / unfinished operation | Preserve your changes and restore a backup where appropriate. Do not delete recovery records just to unblock writes. |
| Permission denied | Check ownership of the specific game folder. Do not run the entire manager with `sudo`. |
| Double-clicking the icon shows nothing | Run `/usr/bin/python3 app.py` in a terminal to see the error and check the absolute `Exec=` path. Rerun the installer after moving the project. |

## 7. Command-line reference

```bash
/usr/bin/python3 app.py --help
/usr/bin/python3 app.py list
/usr/bin/python3 app.py verify
/usr/bin/python3 app.py curse-key
/usr/bin/python3 app.py curse-search "unit frames"
/usr/bin/python3 app.py curse-search "" --index 20
/usr/bin/python3 app.py install-curseforge PROJECT_ID
/usr/bin/python3 app.py install-github OWNER/REPOSITORY
/usr/bin/python3 app.py install-zip /path/to/addon.zip
/usr/bin/python3 app.py check
/usr/bin/python3 app.py update
/usr/bin/python3 app.py remove curseforge:PROJECT_ID
/usr/bin/python3 app.py restore
/usr/bin/python3 app.py startup check
```

`PROJECT_ID`, `OWNER/REPOSITORY`, and paths are placeholders. Find the package key for `remove` in the `source` field of `list`; it may also start with `github:` or `zip:`. Startup modes are `check`, `update`, and `off`. Individual batch-operation errors do not necessarily produce a nonzero exit code; read the output.

## 8. Update or uninstall the manager

Close the application before updating it, then run from the project directory:

```bash
git status --short
git pull --ff-only
/usr/bin/python3 -m unittest discover -v
/usr/bin/python3 app.py
```

Resolve local code changes or diverging history before updating; do not overwrite them forcibly. `git pull` requires a published upstream history. Updating in the same directory does not require reinstalling shortcuts.

To uninstall, close the application and remove its application-menu entry, desktop shortcut, and optionally the source directory. This does not automatically remove installed addons, manager data, or API keys. Keep backups until you no longer need them. Deleting a local key file does not revoke that key with CurseForge.

## 9. Development, GitHub access, and publishing

Use a GitHub account with write access to `suvreal/WoWForeverDotForge`. GitHub access is independent of CurseForge API keys and Battle.net accounts.

### Sign in from your own Linux terminal

If GitHub CLI is missing, install it with `sudo apt install gh` on systems providing that package. Check connectivity, then sign in interactively through your browser:

```bash
getent hosts github.com
gh auth login --hostname github.com --git-protocol https --web --scopes workflow
gh auth setup-git
gh auth status
```

Complete sign-in in your browser using an account with project access. The additional `workflow` scope is needed to push this project's `.github/workflows/tests.yml` with OAuth credentials. Never paste a password or token into chat. If several accounts are configured, select the correct one with `gh auth switch --hostname github.com --user suvreal`; switching does not renew an invalid token. See the [GitHub CLI login guide](https://cli.github.com/manual/gh_auth_login).

If you use your own fine-grained token instead, restrict it to this repository and grant **Contents: Read and write**, **Workflows: Read and write** for the workflow file, and **Pull requests: Read and write** to create PRs. Respect expiration and any organization approval requirements. Follow the [GitHub token documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) for secure authentication; do not place tokens in the `origin` URL or project files.

### First push to an empty repository

For an existing local Git history, after reviewing the committed files:

```bash
git status --short
git log -3 --oneline
git remote get-url origin
git ls-remote origin
git push -u origin main
```

The expected remote is `https://github.com/suvreal/WoWForeverDotForge.git`. Empty output from `git ls-remote origin` with exit code 0 means no refs were returned; a network or authentication error does not establish that the repository is empty. If remote commits have appeared, fetch and review the history first. Do not use `--force` to fix authentication problems or diverging history.

### Subsequent changes through a pull request

```bash
git switch -c docs/setup-and-accounts
# Edit files and review the diff; stage only the intended files.
git add README.md
git commit -m 'BEL: Document installation and account setup'
git push -u origin HEAD
gh pr create --base main --title 'BEL: Document installation and account setup' --body 'BEL: Add installation, configuration, account switching and verification instructions.'
```

PR titles and messages use **`BEL: {MESSAGE}`**. The initial publication to an empty repository must establish the default branch first; a PR cannot target a nonexistent `main` branch.

### Connector or agent environment prevents publishing

GitHub API error **403 `Resource not accessible by integration`** indicates insufficient integration-token permissions for the operation. Repository ownership alone does not establish that the integration can write. Check the relevant GitHub App in [GitHub application settings](https://github.com/settings/installations), its repository access, and any pending permission approval. If the app does not offer the required permission, use your own GitHub CLI authentication. GitHub Actions workflow permissions do not repair an external connector's token. See [GitHub REST API troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api#resource-not-accessible).

An invalid-token report from `gh auth status` in an environment without working networking is not conclusive evidence that GitHub revoked the token. Verify it from a normal terminal with internet access. Renewing CLI authentication does not renew a separate connector's token. A completed push must confirm the remote branch update; a local commit or passing tests is insufficient.

## 10. Tests and verification limits

```bash
/usr/bin/python3 -m unittest discover -v
/usr/bin/python3 -m py_compile app.py catalog.py core.py curseforge.py install.py
```

Tests use isolated fake installations and simulated API responses, without API keys or changes to your actual game. They cover installation, updates, restores, local changes, unsafe ZIP rejection, version selection, and CurseForge checksums. They do not open the graphical interface or download real addons. End-to-end verification requires a desktop session, internet access, your own approved API key, and a selected compatible addon; follow section 6.

The project includes the `wow-forever-addons` skill in `skill/`, linked from `.agents/skills/`. Open the project in Codex to use it. The skill uses the same CLI and protections as the application.
