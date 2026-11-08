import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.parse

from curseforge import Client, NoRedirect, game_version, load_key, save_key
import test_core as fixtures
from test_core import archive


def mod(mid=42, **extra):
    return dict(id=mid, gameId=1, classId=1, name='Example', summary='Test addon',
                authors=[{'name': 'Author'}], isAvailable=True, allowModDistribution=True,
                links={'websiteUrl': 'https://www.curseforge.com/wow/addons/example'}, **extra)


def release(fid=100, version='1.60.1', payload=None, date='2026-11-08T12:00:00Z'):
    payload = archive() if payload is None else payload
    return {'id': fid, 'modId': 42, 'gameId': 1, 'gameVersions': [version], 'fileName': 'Example.zip',
            'isAvailable': True, 'fileStatus': 4, 'releaseType': 1, 'displayName': 'Example v' + str(fid),
            'fileDate': date, 'fileLength': len(payload), 'downloadUrl': 'https://cdn.example/addon.zip',
            'hashes': [{'algo': 1, 'value': hashlib.sha1(payload).hexdigest()}], 'dependencies': []}


class Api(unittest.TestCase):
    def test_key_local_permissions_and_deletion(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'CURSEFORGE_API_KEY': ''}):
            path = Path(tmp) / 'config/curseforge.key'
            save_key('example-key', path)
            self.assertEqual(load_key(path), 'example-key')
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            save_key('new-key', path)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            save_key('', path)
            self.assertEqual(load_key(path), '')

    def test_missing_key_does_not_make_network_request(self):
        with patch('urllib.request.build_opener') as opener:
            with self.assertRaisesRegex(ValueError, 'nastav vlastní'):
                Client(16001, key='').search()
            opener.assert_not_called()

    def test_request_filters_and_pagination(self):
        client = Client(16001, key='test-only')
        response = {'data': [mod()], 'pagination': {'resultCount': 20, 'totalCount': 60}}
        stream = io.BytesIO(json.dumps(response).encode())
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = stream
            result = client.search('unit frames', index=20, sort=3)
            req = opener.return_value.open.call_args.args[0]
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(req.full_url).query)
            self.assertEqual(query['gameVersion'], ['1.60.1'])
            self.assertEqual(query['gameId'], ['1'])
            self.assertEqual(query['classId'], ['1'])
            self.assertEqual(query['index'], ['20'])
            self.assertEqual(query['searchFilter'], ['unit frames'])
            self.assertEqual(result['rows'][0]['authors'], 'Author')
            self.assertTrue(result['has_next'])
            self.assertEqual(result['index'], 20)

    def test_empty_results_and_last_page(self):
        with patch.object(Client, 'request', return_value={'data': [], 'pagination': {'totalCount': 0, 'resultCount': 0}}):
            result = Client(16001, key='test').search('missing')
        self.assertFalse(result['has_next'])
        self.assertEqual(result['rows'], [])

    def test_id_search_validates_version(self):
        with patch.object(Client, 'request', return_value={'data': mod()}), patch.object(Client, 'latest_file') as latest:
            result = Client(16001, key='test').search('42')
        latest.assert_called_once_with(42)
        self.assertEqual(result['rows'][0]['id'], 42)

    def test_file_filter_and_chronological_selection(self):
        stable = release()
        beta = dict(release(102), releaseType=2)
        wrong = release(103, version='12.0.1')
        bad = dict(release(104), fileStatus=6)
        old = release(98, date='2026-10-01T00:00:00Z')
        with patch.object(Client, 'request', return_value={'data': [old, wrong, beta, stable, bad]}):
            self.assertEqual(Client(16001, key='test').latest_file(42)['id'], 100)
        with patch.object(Client, 'request', return_value={'data': [wrong, beta, bad]}):
            with self.assertRaisesRegex(ValueError, 'stabilní ZIP'):
                Client(16001, key='test').latest_file(42)

    def test_distribution_disallowed(self):
        value = mod()
        value['allowModDistribution'] = False
        with patch.object(Client, 'request', return_value={'data': value}):
            with self.assertRaisesRegex(ValueError, 'Autor nepovoluje'):
                Client(16001, key='test').mod(42)

    def test_download_checks_hash_and_length(self):
        payload = archive()
        file = release(payload=payload)
        with patch('core.fetch', return_value=payload) as fetch:
            self.assertEqual(Client(16001, key='test').download(file), payload)
            fetch.assert_called_once_with('https://cdn.example/addon.zip')
        file['hashes'][0]['value'] = '0' * 40
        with patch('core.fetch', return_value=payload):
            with self.assertRaisesRegex(ValueError, 'kontrolní součet'):
                Client(16001, key='test').download(file)
        with patch('core.fetch', return_value=b'bad'):
            with self.assertRaisesRegex(ValueError, 'velikost'):
                Client(16001, key='test').download(file)

    def test_missing_download_url_no_fabricated_cdn(self):
        file = release()
        file['downloadUrl'] = None
        with patch.object(Client, 'request', return_value={'data': None}), patch('core.fetch') as fetch:
            with self.assertRaisesRegex(ValueError, 'neposkytuje stažení'):
                Client(16001, key='test').download(file)
            fetch.assert_not_called()

    def test_api_errors_do_not_echo_key(self):
        client = Client(16001, key='test-secret-never-log')
        for status in [401, 403, 404, 429, 500]:
            error = urllib.error.HTTPError('https://api.curseforge.com/', status, 'bad', {}, None)
            with patch('urllib.request.build_opener') as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaises(ValueError) as caught:
                    client.search()
                self.assertNotIn(client.key, str(caught.exception))

    def test_redirect_never_forwards_key(self):
        with self.assertRaisesRegex(ValueError, 'přesměrování'):
            NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.test')


class Integration(unittest.TestCase):
    setUp = fixtures.Packages.setUp
    tearDown = fixtures.Packages.tearDown

    def test_install_check_update_integrity_and_restore(self):
        payload = archive()
        current = release(payload=payload)
        def request(client, endpoint, **params):
            if endpoint.endswith('/files'):
                return {'data': [current]}
            return {'data': mod()}
        with patch.object(Client, 'request', request), patch('core.fetch', side_effect=lambda url: payload):
            self.m.curseforge(42)
            self.assertIn('aktuální', self.m.updates())
            self.assertEqual(self.m.inventory()[0]['status'], 'V pořádku')
            payload = archive('2')
            current = release(101, payload=payload, date='2026-11-09T12:00:00Z')
            self.assertIn('dostupný', self.m.updates())
            self.m.updates(True)
            self.assertEqual(self.m.inventory()[0]['version'], '2')
            self.m.restore()
            self.assertEqual(self.m.inventory()[0]['version'], '1')

    def test_no_downgrade(self):
        source = {'provider': 'curseforge', 'mod_id': 42, 'file_id': 101, 'file_date': '2026-11-09T00:00:00Z'}
        self.m.install(archive('2'), 'curseforge:42', '2', source)
        with patch.object(Client, 'mod', return_value=mod()), patch.object(Client, 'latest_file', return_value=release()), patch.object(Client, 'download') as download:
            self.assertIn('verzi nesnižuji', self.m.updates(True))
            download.assert_not_called()
        self.assertEqual(self.m.inventory()[0]['version'], '2')

    def test_bad_archive_interface_never_changes_game(self):
        payload = archive(interface='120000')
        with patch.object(Client, 'mod', return_value=mod()), patch.object(Client, 'latest_file', return_value=release(payload=payload)), patch('core.fetch', return_value=payload):
            with self.assertRaisesRegex(ValueError, 'Interface 16001'):
                self.m.curseforge(42)
        self.assertEqual(self.m.inventory(), [])

    def test_required_dependency_reported_without_download(self):
        file = release()
        file['dependencies'] = [{'modId': 99, 'relationType': 3}]
        with patch.object(Client, 'mod', return_value=mod()), patch.object(Client, 'latest_file', return_value=file), patch.object(Client, 'request', return_value={'data': {'name': 'Library'}}), patch.object(Client, 'download') as download:
            with self.assertRaisesRegex(ValueError, 'Library.*99'):
                self.m.curseforge(42)
            download.assert_not_called()
        self.assertEqual(self.m.inventory(), [])


if __name__ == '__main__':
    unittest.main()
