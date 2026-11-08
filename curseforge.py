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
        raise ValueError('The API key must be a single line.')
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
        raise ValueError('The CurseForge API returned an unexpected redirect.')


class Client:
    def __init__(self, interface, key=None):
        self.version = game_version(interface)
        self.key = load_key() if key is None else key

    def request(self, endpoint, **params):
        if not self.key:
            raise ValueError('Set your own CurseForge API key in the catalog first.')
        if any(c in self.key for c in '\r\n'):
            raise ValueError('The configured CurseForge API key has an invalid format.')
        url = API + endpoint
        if params:
            url += '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            'x-api-key': self.key, 'Accept': 'application/json', 'User-Agent': 'WoWForeverDotForge/1.1'})
        try:
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=25) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('The catalog response is too large.')
            return json.loads(raw)
        except urllib.error.HTTPError as error:
            messages = {401: 'Invalid CurseForge API key.',
                        403: 'CurseForge denied access. Check your API key and permissions.',
                        404: 'The addon or file is no longer in the catalog.',
                        429: 'CurseForge rate limit reached. Try again later.'}
            raise ValueError(messages.get(error.code, f'CurseForge API: HTTP {error.code}.')) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ValueError('CurseForge is unavailable. Check your internet connection.') from None

    def search(self, query='', index=0, sort=2):
        if index < 0 or index + PAGE_SIZE > 10000:
            raise ValueError('The requested page is outside the catalog range.')
        query = query.strip()
        if query.isdecimal():
            if index:
                raise ValueError('Searching by ID has only one page.')
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
            raise ValueError('Invalid addon ID.')
        mod = self.request(f'mods/{mod_id}')['data']
        if mod.get('id') != mod_id or mod.get('gameId') != 1 or mod.get('classId') != 1:
            raise ValueError('The project is not a WoW addon.')
        if not mod.get('isAvailable', True):
            raise ValueError('The addon is no longer available.')
        if mod.get('allowModDistribution') is False:
            raise ValueError('The author does not allow third-party distribution. Use the addon website and import its ZIP.')
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
                raise ValueError('The project has too many files. Select a specific ZIP on its website.')
        compatible = [f for f in files if f.get('modId') == int(mod_id) and f.get('gameId') == 1
                      and self.version in f.get('gameVersions', [])
                      and f.get('releaseType') == 1 and f.get('isAvailable')
                      and f.get('fileStatus') in {4, 10}
                      and not f.get('isEarlyAccessContent')
                      and f.get('fileName', '').lower().endswith('.zip')]
        if not compatible:
            raise ValueError(f'The addon has no available stable ZIP for WoW {self.version}.')
        return max(compatible, key=lambda f: (f.get('fileDate', ''), f['id']))

    def download(self, file):
        from core import LIMIT, fetch
        if not 0 < file.get('fileLength', 0) <= LIMIT:
            raise ValueError('The file exceeds 100 MB or has an invalid size.')
        url = file.get('downloadUrl')
        if not url:
            url = self.request(f"mods/{file['modId']}/files/{file['id']}/download-url").get('data')
        if not url:
            raise ValueError('CurseForge does not provide an API download. Use the website and import the ZIP.')
        # No API headers, no fabricated CDN URL when the author disallows downloading.
        payload = fetch(url)
        if len(payload) != file['fileLength']:
            raise ValueError('The downloaded ZIP size does not match.')
        verified = False
        for checksum in file.get('hashes', []):
            algo = {1: 'sha1', 2: 'md5'}.get(checksum['algo'])
            if algo:
                if hashlib.new(algo, payload).hexdigest().lower() != checksum['value'].lower():
                    raise ValueError('The CurseForge ZIP checksum does not match.')
                verified = True
        if not verified:
            raise ValueError('CurseForge did not provide a supported file checksum.')
        return payload
