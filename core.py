"""Forever Addons: local package manager; no third-party Python dependencies."""
import contextlib
import copy
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import time
import urllib.request
import zipfile

GAME = Path(os.environ.get('FOREVER_GAME_DIR', str(Path.home() / 'Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_'))).expanduser()
DATA = Path.home() / '.local/share/forever-addons'
LIMIT = 100 * 1024 * 1024


def read_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save_json(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    os.replace(tmp, path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root):
    result = {}
    if root.is_symlink():
        raise ValueError('Symlink v cestě addonu: ' + str(root))
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError('Symlink v addonu: ' + str(p))
        if p.is_file():
            result[p.relative_to(root).as_posix()] = digest(p)
    return result


def metadata(folder):
    tocs = sorted(folder.glob('*.toc'))
    specific = [p for p in tocs if p.stem.lower().endswith(('_forever', '_camelot'))]
    generic = [p for p in tocs if p.stem.lower() == folder.name.lower()]
    chosen = specific or generic
    fields = {}
    for toc in chosen:
        for line in toc.read_text(encoding='utf-8-sig', errors='replace').splitlines():
            m = re.match(r'##\s*([^:]+):\s*(.*)', line)
            if m:
                key, value = m.groups()
                fields.setdefault(key.lower(), []).append(value)
    return {k: ', '.join(v) for k, v in fields.items()}


def fetch(url, limit=LIMIT):
    if not url.startswith('https://'):
        raise ValueError('Stahování vyžaduje HTTPS.')
    req = urllib.request.Request(url, headers={'User-Agent': 'ForeverAddons/1.0', 'Accept': 'application/vnd.github+json' if 'api.github.com/' in url else 'application/octet-stream'})
    with urllib.request.urlopen(req, timeout=25) as response:
        if not response.url.startswith('https://'):
            raise ValueError('Nezabezpečené přesměrování.')
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Soubor překročil velikostní limit.')
    return data


def unpack(data, destination, interface):
    """Validate every ZIP entry before extracting; accept only addon root folders."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        entries = z.infolist()
        if len(entries) > 25000 or sum(i.file_size for i in entries) > 400 * 1024 * 1024:
            raise ValueError('Příliš velký archiv.')
        seen = set()
        for i in entries:
            p = PurePosixPath(i.filename)
            mode = i.external_attr >> 16
            if (p.is_absolute() or '..' in p.parts or '\\' in i.filename or ':' in i.filename
                    or not p.parts or any(c in i.filename for c in '\x00\n\r')
                    or stat.S_ISLNK(mode)):
                raise ValueError('Nebezpečná cesta v ZIPu: ' + i.filename)
            key = str(p).casefold()
            if key in seen:
                raise ValueError('Duplicitní cesta v ZIPu.')
            seen.add(key)
        z.extractall(destination)
    roots = [d for d in destination.iterdir() if d.is_dir() and list(d.glob('*.toc'))]
    if not roots:
        raise ValueError('ZIP musí obsahovat složky addonů s .toc přímo uvnitř (distribuční balíček).')
    for folder in roots:
        if not re.fullmatch(r'[A-Za-z0-9_+.-]+', folder.name) or folder.name.startswith('.'):
            raise ValueError('Nepodporovaný název složky addonu.')
        info = metadata(folder)
        versions = re.findall(r'\d+', info.get('interface', ''))
        if str(interface) not in versions:
            raise ValueError(f'{folder.name}: chybí deklarace Interface {interface}.')
        for p in folder.rglob('*'):
            if p.suffix.lower() in {'.exe', '.dll', '.so', '.bat', '.cmd', '.ps1', '.sh'}:
                raise ValueError('Spustitelný soubor v balíčku: ' + p.name)
    return roots


class Manager:
    def __init__(self, game=GAME, data=DATA):
        self.game, self.data = Path(game), Path(data)
        if self.game.name != '_forever_' or not (self.game / 'Wow.exe').exists():
            raise ValueError('Není to instalace _forever_ s Wow.exe: ' + str(self.game))
        self.addons = self.game / 'Interface/AddOns'
        if any(p.is_symlink() for p in [self.game, self.game / 'Interface', self.addons]):
            raise ValueError('Cílová cesta nesmí být symlink.')
        self.data.mkdir(parents=True, exist_ok=True)
        self.addons.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data / 'state.json'
        self.state = read_json(self.state_file, {'packages': {}, 'startup': 'check'})
        config = self.game / 'WTF/Config.wtf'
        m = re.search(r'SET engineSurveyPatch "(\d+)"', config.read_text() if config.exists() else '')
        if not m:
            raise ValueError('Nelze zjistit Interface z WTF/Config.wtf; spusť hru a ukonči ji.')
        self.interface = int(m.group(1))

    @contextlib.contextmanager
    def lock(self):
        with (self.data / 'lock').open('w') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('Jiná operace správce právě běží.')
            self.state = read_json(self.state_file, self.state)
            yield

    def idle(self):
        for cmdline in Path('/proc').glob('[0-9]*/cmdline'):
            try:
                args = cmdline.read_bytes().decode(errors='replace').split('\x00')
                if any(arg.replace('\\', '/').rsplit('/', 1)[-1].lower() in {'wow.exe', 'wowb.exe'} for arg in args):
                    raise ValueError('Nejdřív ukonči WoW; za běhu hry neměním addony.')
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                pass
        if (self.data / 'pending.json').exists():
            raise ValueError('Nedokončená operace. Použij obnovu poslední zálohy.')

    def inventory(self):
        owners = {name: key for key, p in self.state['packages'].items() for name in p['folders']}
        names = set(owners) | {p.name for p in self.addons.iterdir() if p.is_dir()}
        rows = []
        for name in sorted(names, key=str.lower):
            folder = self.addons / name
            key = owners.get(name)
            info = metadata(folder) if folder.exists() else {}
            status = 'Nespravovaný'
            if key:
                expected = self.state['packages'][key]['hashes'][name]
                try:
                    actual = manifest(folder) if folder.exists() else {}
                    status = 'V pořádku' if actual == expected else 'Změněný / chybí soubory'
                except ValueError:
                    status = 'Symlink – zablokováno'
            rows.append({'folder': name, 'title': info.get('title', name), 'version': info.get('version', '—'),
                         'status': status, 'source': key or 'Ruční instalace',
                         'interface': info.get('interface', '—')})
        return rows

    def backup(self, names):
        target = self.data / 'backups' / (time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns()))
        target.mkdir(parents=True)
        for name in names:
            src = self.addons / name
            if src.exists():
                manifest(src)
                shutil.copytree(src, target / name)
        save_json(target / 'record.json', {'names': names, 'state': copy.deepcopy(self.state)})
        save_json(self.data / 'pending.json', {'backup': str(target)})
        return target

    def restore(self):
        with self.lock():
            # A restore is also forbidden while the game is running.
            pending = self.data / 'pending.json'
            record_pending = read_json(pending, None)
            if record_pending:
                pending.unlink()
            try:
                self.idle()
            finally:
                if record_pending:
                    save_json(pending, record_pending)
            backups = sorted((self.data / 'backups').glob('*'))
            if not backups:
                raise ValueError('Žádná záloha k obnově.')
            target = Path(record_pending['backup']) if record_pending else backups[-1]
            self._restore(target)
            return 'Obnovena záloha ' + target.name

    def _restore(self, target):
        record = read_json(target / 'record.json', {})
        for name in record['names']:
            dst = self.addons / name
            if dst.is_symlink():
                raise ValueError('Cílový addon je symlink; obnova zastavena.')
            if dst.exists():
                shutil.rmtree(dst)
            if (target / name).exists():
                shutil.copytree(target / name, dst)
        self.state = record['state']
        save_json(self.state_file, self.state)
        (self.data / 'pending.json').unlink(missing_ok=True)

    def install(self, data, key, version, source=None):
        with self.lock(), tempfile.TemporaryDirectory(prefix='forever-stage-') as temp:
            self.idle()
            roots = unpack(data, Path(temp), self.interface)
            names = [p.name for p in roots]
            old = self.state['packages'].get(key)
            for name in names:
                for other, package in self.state['packages'].items():
                    if other != key and name.casefold() in [n.casefold() for n in package['folders']]:
                        raise ValueError('Složku vlastní jiný balíček: ' + name)
                if (self.addons / name).exists() and (not old or name not in old['folders']):
                    raise ValueError('Složka již existuje mimo tento balíček: ' + name)
                if any(p.name.casefold() == name.casefold() and p.name != name for p in self.addons.iterdir()):
                    raise ValueError('Kolize velikosti písmen: ' + name)
            if old:
                for name in old['folders']:
                    path = self.addons / name
                    if (manifest(path) if path.exists() else {}) != old['hashes'][name]:
                        raise ValueError('Lokální změna nebo poškození; nejdřív obnov zálohu nebo vyřeš soubory: ' + name)
            # Required dependencies must exist now or be included in the same package.
            removed = set(old['folders'] if old else []) - set(names)
            for root in roots:
                info = metadata(root)
                for dep in re.split(r'[,\s]+', info.get('dependencies', info.get('requireddeps', ''))):
                    if dep and dep not in names and (dep in removed or not (self.addons / dep).is_dir()):
                        raise ValueError(f'{root.name}: chybí závislost {dep}; nainstaluj ji nejdřív.')
            touched = sorted(set(names) | set(old['folders'] if old else []))
            backup = self.backup(touched)
            try:
                for name in touched:
                    dst = self.addons / name
                    if dst.exists():
                        shutil.rmtree(dst)
                for root in roots:
                    shutil.copytree(root, self.addons / root.name)
                self.state['packages'][key] = {'version': version, 'source': source, 'folders': names,
                    'hashes': {name: manifest(self.addons / name) for name in names},
                    'archive_sha256': hashlib.sha256(data).hexdigest()}
                save_json(self.state_file, self.state)
                (self.data / 'pending.json').unlink()
            except Exception:
                self._restore(backup)
                raise
            return 'Nainstalováno: ' + ', '.join(names) + ' • ' + version

    def remove(self, key):
        with self.lock():
            self.idle()
            package = self.state['packages'].get(key)
            if not package:
                raise ValueError('Odstraňovat lze pouze spravovaný balíček.')
            for name in package['folders']:
                path = self.addons / name
                if (manifest(path) if path.exists() else {}) != package['hashes'][name]:
                    raise ValueError('Addon má lokální změny; odstranění zastaveno: ' + name)
            backup = self.backup(package['folders'])
            try:
                for name in package['folders']:
                    shutil.rmtree(self.addons / name)
                del self.state['packages'][key]
                save_json(self.state_file, self.state)
                (self.data / 'pending.json').unlink()
            except Exception:
                self._restore(backup)
                raise
            return 'Odstraněno se zálohou: ' + key

    def install_zip(self, path):
        path = Path(path).expanduser()
        if path.stat().st_size > LIMIT:
            raise ValueError('ZIP je větší než 100 MB.')
        payload = path.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            roots = unpack(payload, Path(temp), self.interface)
            key = 'zip:' + sorted(p.name for p in roots)[0]
        return self.install(payload, key, path.name)

    def candidate(self, repository):
        repository = repository.strip().removeprefix('https://github.com/').rstrip('/').removesuffix('.git')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('Zadej GitHub vlastník/repozitář nebo odkaz na repozitář.')
        releases = json.loads(fetch('https://api.github.com/repos/' + repository + '/releases?per_page=15', 8 * 1024 * 1024))
        for release in releases:
            if release['draft'] or release['prerelease']:
                continue
            assets = sorted(release['assets'], key=lambda a: ('forever' not in a['name'].lower() and 'camelot' not in a['name'].lower(), a['name']))
            for asset in assets:
                if not asset['name'].lower().endswith('.zip') or 'nolib' in asset['name'].lower():
                    continue
                if asset['size'] > LIMIT:
                    continue
                payload = fetch(asset['browser_download_url'])
                checksum = asset.get('digest')
                if checksum and checksum.startswith('sha256:') and hashlib.sha256(payload).hexdigest() != checksum[7:]:
                    raise ValueError('Nesouhlasí SHA-256 staženého balíčku.')
                try:
                    with tempfile.TemporaryDirectory() as temp:
                        unpack(payload, Path(temp), self.interface)
                except (ValueError, zipfile.BadZipFile):
                    continue
                return repository, release['tag_name'], payload
        raise ValueError('V posledních 15 vydáních není stabilní distribuční ZIP pro Interface ' + str(self.interface))

    def github(self, repository):
        repo, version, payload = self.candidate(repository)
        return self.install(payload, 'github:' + repo.lower(), version, repo)

    def curse_search(self, query='', index=0, sort=2):
        from curseforge import Client
        return Client(self.interface).search(query, index, sort)

    def curseforge(self, mod_id):
        from curseforge import Client
        client = Client(self.interface)
        mod = client.mod(mod_id)
        file = client.latest_file(mod['id'])
        return self._install_curse_file(client, mod, file)

    def _install_curse_file(self, client, mod, file):
        # TOC validation in install() also checks required folder dependencies.
        # API-only dependencies may have no TOC entry, so report those explicitly.
        missing = [d['modId'] for d in file.get('dependencies', [])
                   if d.get('relationType') == 3 and 'curseforge:' + str(d['modId']) not in self.state['packages']]
        if missing:
            descriptions = []
            for mod_id in missing:
                dependency = client.request(f'mods/{int(mod_id)}')['data']
                descriptions.append(f"{dependency['name']} (ID {mod_id})")
            raise ValueError('Nejdřív nainstaluj povinné závislosti z katalogu: ' + ', '.join(descriptions))
        payload = client.download(file)
        source = {'provider': 'curseforge', 'mod_id': mod['id'], 'file_id': file['id'],
                  'file_date': file.get('fileDate', ''), 'name': mod['name']}
        return self.install(payload, 'curseforge:' + str(mod['id']), file['displayName'], source)

    def updates(self, apply=False):
        messages = []
        for key, package in list(self.state['packages'].items()):
            if not package.get('source'):
                messages.append(key + ': ruční ZIP – aktualizace importem nového ZIPu')
                continue
            try:
                if isinstance(package['source'], dict):
                    from curseforge import Client
                    source = package['source']
                    if source.get('provider') != 'curseforge':
                        raise ValueError('Neznámý zdroj balíčku.')
                    client = Client(self.interface)
                    mod = client.mod(source['mod_id'])
                    file = client.latest_file(mod['id'])
                    name = mod['name']
                    if file['id'] == source['file_id']:
                        messages.append(name + ': aktuální')
                    elif file.get('fileDate', '') < source.get('file_date', ''):
                        messages.append(name + ': katalog nabízí starší soubor; verzi nesnižuji')
                    elif apply:
                        messages.append(self._install_curse_file(client, mod, file))
                    else:
                        messages.append(name + ': dostupný kompatibilní balíček ' + file['displayName'])
                    continue
                repo, version, payload = self.candidate(package['source'])
                sha = hashlib.sha256(payload).hexdigest()
                if sha == package['archive_sha256']:
                    messages.append(repo + ': aktuální')
                elif apply:
                    messages.append(self.install(payload, key, version, repo))
                else:
                    messages.append(repo + ': dostupný kompatibilní balíček ' + version)
            except Exception as e:
                messages.append(key + ': ' + str(e))
        return '\n'.join(messages) or 'Žádné spravované addony. Přidej GitHub repozitář nebo ZIP.'

    def startup(self, mode):
        if mode not in {'off', 'check', 'update'}:
            raise ValueError('Neplatný režim.')
        with self.lock():
            self.state['startup'] = mode
            save_json(self.state_file, self.state)
