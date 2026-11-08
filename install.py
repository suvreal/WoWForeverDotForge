#!/usr/bin/env python3
"""Register the application from this directory; no system-wide changes."""
import argparse
from pathlib import Path
import shutil
import subprocess


def desktop_quote(value):
    value = str(value).replace('%', '%%')
    for char in ['\\', '"', '`', '$']:
        value = value.replace(char, '\\' + char)
    return '"' + value + '"'


def main():
    parser = argparse.ArgumentParser(description='Add Forever Addons to the application menu.')
    parser.add_argument('--desktop', action='store_true', help='Also add a desktop shortcut')
    args = parser.parse_args()
    app = Path(__file__).resolve().parent / 'app.py'
    content = '\n'.join([
        '[Desktop Entry]', 'Type=Application', 'Name=Forever Addons',
        'Comment=Manage addons for World of Warcraft Forever',
        'Exec=/usr/bin/python3 ' + desktop_quote(app), 'Icon=applications-games',
        'Terminal=false', 'Categories=Game;Utility;', 'StartupNotify=true', '',
    ])
    target = Path.home() / '.local/share/applications/forever-addons.desktop'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    print('Added to the application menu:', target)
    if args.desktop:
        if not shutil.which('xdg-user-dir'):
            raise SystemExit('Unable to locate the desktop: xdg-user-dir is missing.')
        result = subprocess.run(['xdg-user-dir', 'DESKTOP'], check=True, capture_output=True, text=True)
        desktop = Path(result.stdout.strip())
        if not desktop.is_absolute() or desktop == Path.home():
            raise SystemExit('No desktop folder is configured; the launcher is still available in the application menu.')
        desktop.mkdir(parents=True, exist_ok=True)
        shortcut = desktop / 'Forever Addons.desktop'
        shortcut.write_text(content)
        shortcut.chmod(0o755)
        if shutil.which('gio'):
            subprocess.run(['gio', 'set', str(shortcut), 'metadata::trusted', 'true'], capture_output=True)
        print('Added to the desktop:', shortcut)
        print('If your desktop asks for confirmation, select Allow Launching.')


if __name__ == '__main__':
    main()
