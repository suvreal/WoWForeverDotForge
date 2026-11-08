"""Official CurseForge API client. Credentials never accompany archive downloads."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.parse
import urllib.request

API = 'https://api.curseforge.com/v1/'
KEY_FILE = Path.home() / '.config/forever-addons/curseforge.key'
KEY_APPLICATION_URL = 'https://console.curseforge.com/'
PAGE_SIZE = 20


def load_key(path=KEY_FILE):
    value = os.environ.get('CURSEFORGE_API_KEY', '').strip()
    if value:
        return value
    path = Path(path)
    return path.read_text().strip() if path.exists() else ''


def save_key(value, path=KEY_FILE):
    """Atomic, owner-only local credential, deliberately outside project and backups."""
    path = Path(path)
    value = value.strip()
    if '\n' in value or '\r' in value:
        raise ValueError('API klíč musí být na jednom řádku.')
    if not value:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix='.key-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(value)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def game_version(interface):
    return f'{interface // 10000}.{interface // 100 % 100}.{interface % 100}'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an x-api-key to a different host, or silently change API host.
        raise ValueError('CurseForge API vrátilo neočekávané přesměrování.')


class Client:
    def __init__(self, interface, key=None):
        self.version = game_version(interface)
        self.key = load_key() if key is None else key

    def request(self, endpoint, **params):
        if not self.key:
            raise ValueError('Nejdřív nastav vlastní CurseForge API klíč v katalogu.')
        if any(c in self.key for c in '\r\n'):
            raise ValueError('Uložený CurseForge API klíč má neplatný formát.')
        url = API + endpoint
        if params:
            url += '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            'x-api-key': self.key, 'Accept': 'application/json', 'User-Agent': 'WoWForeverDotForge/1.1'})
        try:
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=25) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('Příliš velká odpověď katalogu.')
            return json.loads(raw)
        except urllib.error.HTTPError as error:
            messages = {401: 'Neplatný CurseForge API klíč.',
                        403: 'CurseForge odmítl přístup. Ověř klíč a oprávnění API.',
                        404: 'Addon nebo soubor už v katalogu není.',
                        429: 'CurseForge omezil počet požadavků. Zkus to později.'}
            raise ValueError(messages.get(error.code, f'CurseForge API: HTTP {error.code}.')) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ValueError('CurseForge není dostupný. Zkontroluj připojení k internetu.') from None

    def search(self, query='', index=0, sort=2):
        if index < 0 or index + PAGE_SIZE > 10000:
            raise ValueError('Požadovaná stránka je mimo rozsah katalogu.')
        query = query.strip()
        if query.isdecimal():
            if index:
                raise ValueError('Hledání podle ID má pouze jednu stránku.')
            mod = self.request(f'mods/{int(query)}')['data']
            self.latest_file(int(query))
            response = {'data': [mod], 'pagination': {'resultCount': 1, 'totalCount': 1}}
        else:
            response = self.request('mods/search', gameId=1, classId=1,
                gameVersion=self.version, searchFilter=query, sortField=sort,
                sortOrder='desc', index=index, pageSize=PAGE_SIZE)
        # The API applies the version filter. ZIP contents are validated independently.
        rows = []
        for mod in response['data']:
            if mod.get('gameId') != 1 or mod.get('classId') != 1 or not mod.get('isAvailable', True):
                continue
            rows.append({
                'id': int(mod['id']), 'name': mod['name'], 'summary': mod.get('summary', ''),
                'authors': ', '.join(a['name'] for a in mod.get('authors', [])),
                'downloads': mod.get('downloadCount', 0),
                'updated': mod.get('dateModified', '')[:10],
                'url': mod.get('links', {}).get('websiteUrl', ''),
                'allowed': mod.get('allowModDistribution') is not False,
            })
        pagination = response.get('pagination', {})
        count = pagination.get('resultCount', len(response['data']))
        total = min(pagination.get('totalCount', index + count), 10000)
        return {'rows': rows, 'index': index, 'count': count, 'total': total,
                'has_next': index + PAGE_SIZE < total, 'version': self.version}

    def mod(self, mod_id):
        mod_id = int(mod_id)
        if mod_id <= 0:
            raise ValueError('Neplatné ID addonu.')
        mod = self.request(f'mods/{mod_id}')['data']
        if mod.get('id') != mod_id or mod.get('gameId') != 1 or mod.get('classId') != 1:
            raise ValueError('Projekt není WoW addon.')
        if not mod.get('isAvailable', True):
            raise ValueError('Addon už není dostupný.')
        if mod.get('allowModDistribution') is False:
            raise ValueError('Autor nepovoluje distribuci přes jiné správce. Použij stránku addonu a import ZIPu.')
        return mod

    def latest_file(self, mod_id):
        files = []
        # Refuse an unbounded scan rather than silently selecting an older file.
        for index in range(0, 10000, 50):
            response = self.request(f'mods/{int(mod_id)}/files', gameVersion=self.version,
                                    index=index, pageSize=50)
            files.extend(response['data'])
            count = response.get('pagination', {}).get('totalCount')
            if len(response['data']) < 50 or (count is not None and index + 50 >= count):
                break
            if index >= 200:
                raise ValueError('Projekt má příliš mnoho souborů. Vyber konkrétní ZIP na webu.')
        compatible = [f for f in files if f.get('modId') == int(mod_id) and f.get('gameId') == 1
                      and self.version in f.get('gameVersions', [])
                      and f.get('releaseType') == 1 and f.get('isAvailable')
                      and f.get('fileStatus') in {4, 10}
                      and not f.get('isEarlyAccessContent')
                      and f.get('fileName', '').lower().endswith('.zip')]
        if not compatible:
            raise ValueError(f'Addon nemá dostupný stabilní ZIP pro WoW {self.version}.')
        return max(compatible, key=lambda f: (f.get('fileDate', ''), f['id']))

    def download(self, file):
        from core import LIMIT, fetch
        if not 0 < file.get('fileLength', 0) <= LIMIT:
            raise ValueError('Soubor překračuje limit 100 MB nebo má neplatnou velikost.')
        url = file.get('downloadUrl')
        if not url:
            url = self.request(f"mods/{file['modId']}/files/{file['id']}/download-url").get('data')
        if not url:
            raise ValueError('CurseForge neposkytuje stažení přes API. Použij web a import ZIPu.')
        # No API headers, no fabricated CDN URL when the author disallows downloading.
        payload = fetch(url)
        if len(payload) != file['fileLength']:
            raise ValueError('Nesouhlasí velikost staženého ZIPu.')
        verified = False
        for checksum in file.get('hashes', []):
            algo = {1: 'sha1', 2: 'md5'}.get(checksum['algo'])
            if algo:
                if hashlib.new(algo, payload).hexdigest().lower() != checksum['value'].lower():
                    raise ValueError('Nesouhlasí kontrolní součet ZIPu z CurseForge.')
                verified = True
        if not verified:
            raise ValueError('CurseForge neposkytl podporovaný kontrolní součet souboru.')
        return payload
