import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from core import Manager, unpack


def archive(version='1', interface='16001', extra=None):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        z.writestr('Example/Example.toc', f'## Interface: {interface}\n## Version: {version}\nmain.lua\n')
        z.writestr('Example/main.lua', 'print("' + version + '")')
        for name, value in (extra or {}).items():
            z.writestr(name, value)
    return out.getvalue()


class Packages(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        game = self.root / '_forever_'
        (game / 'WTF').mkdir(parents=True)
        (game / 'Wow.exe').touch()
        (game / 'WTF/Config.wtf').write_text('SET engineSurveyPatch "16001"')
        self.m = Manager(game, self.root / 'data')

    def tearDown(self):
        self.temp.cleanup()

    def install(self, version='1'):
        return self.m.install(archive(version), 'test', version)

    def test_install_update_restore_and_settings(self):
        self.install()
        self.assertEqual(self.m.inventory()[0]['status'], 'V pořádku')
        self.install('2')
        self.assertEqual(self.m.inventory()[0]['version'], '2')
        self.m.restore()
        self.assertEqual(self.m.inventory()[0]['version'], '1')
        self.assertEqual((self.m.game / 'WTF/Config.wtf').read_text(), 'SET engineSurveyPatch "16001"')

    def test_remove_and_restore(self):
        self.install()
        self.m.remove('test')
        self.assertEqual(self.m.inventory(), [])
        self.m.restore()
        self.assertEqual(self.m.inventory()[0]['status'], 'V pořádku')

    def test_game_running_blocks_changes(self):
        fake = self.root / 'cmdline'
        fake.write_bytes(b'wine\x00C:\\WoW\\Wow.exe\x00')
        with patch('core.Path.glob', return_value=[fake]):
            with self.assertRaisesRegex(ValueError, 'ukonči WoW'):
                self.m.idle()

    def test_local_changes_block_update(self):
        self.install()
        p = self.m.addons / 'Example/main.lua'
        p.write_text('user edit')
        with self.assertRaisesRegex(ValueError, 'Lokální změna'):
            self.install('2')
        self.assertEqual(p.read_text(), 'user edit')

    def test_missing_and_extra_files_detected(self):
        self.install()
        (self.m.addons / 'Example/extra.lua').touch()
        self.assertNotEqual(self.m.inventory()[0]['status'], 'V pořádku')
        (self.m.addons / 'Example/main.lua').unlink()
        with self.assertRaises(ValueError):
            self.install('2')

    def test_incompatible_and_zip_escape_rejected(self):
        for payload in [archive(interface='11508'), archive(extra={'../escape': 'bad'}), archive(extra={'Example/evil.exe': 'bad'})]:
            with self.assertRaises(ValueError):
                self.m.install(payload, 'test', '1')
        self.assertEqual(self.m.inventory(), [])
        self.assertFalse((self.root / 'escape').exists())

    def test_symlink_not_followed(self):
        self.install()
        target = self.root / 'important'
        target.write_text('keep')
        p = self.m.addons / 'Example/main.lua'
        p.unlink()
        p.symlink_to(target)
        with self.assertRaises(ValueError):
            self.install('2')
        self.assertEqual(target.read_text(), 'keep')

    def test_unmanaged_conflict(self):
        (self.m.addons / 'Example').mkdir()
        with self.assertRaisesRegex(ValueError, 'již existuje'):
            self.install()

    def test_missing_dependency(self):
        payload = archive(extra={'Example/Example_Forever.toc': '## Interface: 16001\n## Dependencies: Missing\n'})
        with self.assertRaisesRegex(ValueError, 'chybí závislost'):
            self.m.install(payload, 'test', '1')

    def test_rollback_on_copy_failure(self):
        self.install()
        import shutil
        real = shutil.copytree
        failed = False
        def copy(src, dst, *args, **kwargs):
            nonlocal failed
            if str(src).startswith('/tmp/forever-stage-') and not failed:
                failed = True
                raise OSError('simulated disk failure')
            return real(src, dst, *args, **kwargs)
        with patch('core.shutil.copytree', side_effect=copy):
            with self.assertRaises(OSError):
                self.install('2')
        self.assertEqual(self.m.inventory()[0]['version'], '1')
        self.assertEqual(self.m.inventory()[0]['status'], 'V pořádku')

    def test_github_compatible_asset_selection(self):
        releases = [{'draft': False, 'prerelease': False, 'tag_name': 'v2', 'assets': [
            {'name': 'addon.zip', 'size': 100, 'browser_download_url': 'https://test/retail'},
            {'name': 'addon-forever.zip', 'size': 100, 'browser_download_url': 'https://test/forever'}]}]
        def fake(url, *args):
            if 'api.github.com' in url:
                return json.dumps(releases).encode()
            return archive('2', '16001' if url.endswith('forever') else '120000')
        with patch('core.fetch', side_effect=fake):
            self.m.github('example/addon')
        self.assertEqual(self.m.inventory()[0]['version'], '2')
        self.assertIn('aktuální', self.check_with_fake(fake))

    def check_with_fake(self, fake):
        with patch('core.fetch', side_effect=fake):
            return self.m.updates()


if __name__ == '__main__':
    unittest.main()
