"""Release versioning and failure ordering without builds or remote writes."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('release_cloud', ROOT / 'release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
spec = importlib.util.spec_from_file_location('publish_cloud', ROOT / 'tools/publish.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class ReleaseTests(unittest.TestCase):
    def test_magic_release_never_builds_or_syncs_other_projects(self):
        with patch.object(sys, 'argv', ['release.py', 'magic']), \
             patch.object(release, 'git', side_effect=['main', '', '0', 'index.json', 'commit-id']), \
             patch.object(release, 'network_git'), patch.object(release, 'run'), \
             patch.object(release, 'bump_versions') as bump, \
             patch.object(release, 'command') as build, \
             patch.object(release, 'sync_files', return_value=(0x26111309, ['index.json'])) as sync:
            release.main()
        bump.assert_not_called()
        self.assertTrue(build.call_args_list)
        self.assertTrue(all(call.args[0] == 'magic' for call in build.call_args_list))
        self.assertEqual(sync.call_args.args[2], ['magic'])

    def test_catalog_keeps_other_modules_and_targets(self):
        loader = dict(version=10, face_id='913211305', sha256='a')
        music = dict(id='bluetooth_audio', version=90, sha256='music')
        magic = dict(id='com.chem.magic', version=7, sha256='magic')
        other = dict(target='another-device', modules=[])
        original = dict(schema=1, targets=[dict(target='band9', loader=loader, modules=[music, magic]), other])
        target = dict(target='band9', loader=loader, modules=[dict(music, version=91, sha256='new')])
        result = publisher.merge_target(original, target)
        self.assertEqual(result['targets'][1], other)
        self.assertEqual(result['targets'][0]['modules'], [target['modules'][0], magic])
        self.assertEqual(original['targets'][0]['modules'], [music, magic])

    def test_catalog_rejects_reused_versions_and_face_ids(self):
        loader = dict(version=10, face_id='913211305', sha256='a')
        module = dict(id='com.chem.magic', version=7, sha256='magic')
        original = dict(schema=1, targets=[dict(target='band9', loader=loader, modules=[module])])
        for updated_loader, updated_module in [
            (dict(loader, version=11, sha256='b'), module),
            (loader, dict(module, sha256='changed')),
            (loader, dict(module, version=6)),
        ]:
            with self.assertRaises(ValueError):
                publisher.merge_target(original, dict(target='band9', loader=updated_loader, modules=[updated_module]))

    def test_network_retry_uses_system_proxy_and_timeout(self):
        errors = [subprocess.CalledProcessError(128, 'git'),
                  subprocess.TimeoutExpired('git', 60), None]
        with patch.object(release.urllib.request, 'getproxies', return_value={'https': 'http://127.0.0.1:7897'}), \
             patch.object(release, 'run', side_effect=errors) as run:
            release.network_git(ROOT, 'fetch', 'origin')
        self.assertEqual(run.call_count, 3)
        for call in run.call_args_list:
            self.assertEqual(call.kwargs['env']['https_proxy'], 'http://127.0.0.1:7897')
            self.assertEqual(call.kwargs['timeout'], 60)

    def test_network_failure_stops_after_three_attempts(self):
        with patch.object(release.urllib.request, 'getproxies', return_value={}), \
             patch.object(release, 'run', side_effect=subprocess.CalledProcessError(128, 'git')) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                release.network_git(ROOT, 'push', 'origin', 'main')
        self.assertEqual(run.call_count, 3)

    def test_changed_artifact_requires_newer_version(self):
        old = dict(version=10, sha256='a')
        release.check_version(dict(version=10, sha256='a'), old)
        release.check_version(dict(version=11, sha256='b'), old)
        for new in (dict(version=9, sha256='a'), dict(version=10, sha256='b')):
            with self.assertRaises(ValueError):
                release.check_version(new, old)

    def test_versions_advance_past_source_and_published_values(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manager = root / 'manager.c'
            manager.write_text('#define CHEM_BAND9_MANAGER_BUILD_ID UINT32_C(0x26111301)\n')
            (root / 'build.toml').write_text('target="band9"\nwatchface_id = "913211301"\n')
            (root / 'index.json').write_text(json.dumps({'targets': [{'target': 'band9',
                'loader': {'version': 0x29111305, 'face_id': '913211305'}}]}))
            with patch.object(release, 'CHEM', root), patch.object(release, 'MANAGER', manager):
                release.bump_versions(root)
            self.assertIn('0x29111306', manager.read_text())
            self.assertIn('913211306', (root / 'build.toml').read_text())

    def test_build_failure_prevents_sync_commit_and_push(self):
        commands = []

        def run(*command, **kwargs):
            commands.append(command)
            if 'face' in command:
                raise subprocess.CalledProcessError(1, command)

        with patch.object(sys, 'argv', ['release.py', 'chem']), \
             patch.object(release, 'git', side_effect=['main', '', '0']), \
             patch.object(release, 'run', side_effect=run), \
             patch.object(release, 'bump_versions'), \
             patch.object(release, 'command', side_effect=subprocess.CalledProcessError(1, 'build')), \
             patch.object(release, 'sync_files') as sync:
            with self.assertRaises(subprocess.CalledProcessError):
                release.main()
        sync.assert_not_called()
        self.assertFalse(any('push' in command or 'commit' in command for command in commands))


if __name__ == '__main__':
    unittest.main()
