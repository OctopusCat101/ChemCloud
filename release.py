#!/usr/bin/env python3
"""Build, test and publish ChemCloud in one command."""
from datetime import datetime
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.request

from tools.projects import ROOT, projects, command

CHEM = projects()['chem']['path']
MANAGER = CHEM / 'manager/target/lvgl_v8/chem_manager_target_lvgl_v8.c'
REVISION = r'(#define CHEM_BAND9_MANAGER_BUILD_ID\s+UINT32_C\()(0x[0-9a-fA-F]+)(\))'


def run(*command, cwd=ROOT, timeout=None, env=None):
    print('+ ' + subprocess.list2cmdline([str(x) for x in command]), flush=True)
    subprocess.run([str(x) for x in command], cwd=cwd, check=True, timeout=timeout, env=env)


def network_git(repository, *args):
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GCM_INTERACTIVE'] = 'Never'
    proxy = urllib.request.getproxies().get('https')
    if proxy:
        env['https_proxy'] = proxy
    credentials = []
    if shutil.which('gh') and subprocess.run(['gh', 'auth', 'status', '--hostname', 'github.com'],
                                            capture_output=True, timeout=15).returncode == 0:
        credentials = ['-c', 'credential.https://github.com.helper=',
                       '-c', 'credential.https://github.com.helper=!gh auth git-credential']
    for attempt in range(3):
        try:
            run('git', '-c', 'http.version=HTTP/1.1', '-c', 'http.lowSpeedLimit=100',
                '-c', 'http.lowSpeedTime=20', *credentials, *args, cwd=repository, timeout=60, env=env)
            return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            if attempt == 2:
                raise
            print(f'Git network operation failed; retrying ({attempt + 2}/3)...', flush=True)


def git(repository, *args):
    return subprocess.check_output(['git', '-C', str(repository), *args], text=True).strip()


def bump_versions(repository):
    source = MANAGER.read_text(encoding='utf-8')
    config_path = CHEM / 'build.toml'
    config_text = config_path.read_text(encoding='utf-8')
    config = tomllib.loads(config_text)
    revision = re.search(REVISION, source)
    if revision is None:
        raise ValueError('Missing Chem build ID')
    catalog = json.loads((repository / 'index.json').read_text(encoding='utf-8'))
    previous = next(t for t in catalog['targets'] if t['target'] == config['target'])['loader']
    version = max(int(revision[2], 16), previous['version']) + 1
    version = max(version, int(datetime.now().strftime('%y%m%d') + '01', 16))
    face_id = str(max(int(config['watchface_id']), int(previous['face_id'])) + 1)
    if len(face_id) != 9 or version > 0xffffffff:
        raise ValueError('Release version space exhausted')
    MANAGER.write_text(re.sub(REVISION, lambda m: f'{m[1]}0x{version:08X}{m[3]}', source), encoding='utf-8')
    config_path.write_text(re.sub(r'(?m)^watchface_id\s*=\s*"[0-9]{9}"',
                                 f'watchface_id = "{face_id}"', config_text), encoding='utf-8')
    print(f'New build: 0x{version:08X}, watchface: {face_id}', flush=True)


def sync_files(repository, music, selected=('chem', 'music', 'magic')):
    from tools import publish as publisher
    with tempfile.TemporaryDirectory(prefix='chem-publish-') as folder:
        staging = Path(folder)
        if (repository / 'index.json').exists():
            shutil.copy2(repository / 'index.json', staging / 'index.json')
        publisher.publish(staging, music, selected=selected)
        catalog = json.loads((staging / 'index.json').read_text(encoding='utf-8'))
        config = tomllib.loads((CHEM / 'build.toml').read_text(encoding='utf-8'))
        target = next(t for t in catalog['targets'] if t['target'] == config['target'])
        loader = target['loader']
        previous_path = repository / 'index.json'
        if previous_path.exists():
            previous = json.loads(previous_path.read_text(encoding='utf-8'))
            old = next(t for t in previous['targets'] if t['target'] == target['target'])
            check_version(loader, old['loader'])
            if loader['sha256'] != old['loader']['sha256'] and loader['face_id'] == old['loader']['face_id']:
                raise ValueError('Changed installer requires a new watchface ID')
            for item in target['modules']:
                for prior in old['modules']:
                    if prior['id'] == item['id']:
                        check_version(item, prior)
        text = (repository / 'README.md').read_text(encoding='utf-8')
        modules = '、'.join(f"{m['name']} `{m['version_name']} / code{m['version']}`" for m in target['modules'])
        line = (f"当前发布：Chem 构建号 `0x{loader['version']:08X}`、安装器 ID `{loader['face_id']}`、"
                f"{modules}，ABI 2.0。客户端插件单独分发。")
        text, count = re.subn(r'(?m)^当前发布：.*$', lambda _: line, text)
        if count != 1:
            raise ValueError('README must contain exactly one current-release line')
        (staging / 'README.md').write_text(text, encoding='utf-8')
        paths = sorted(p.relative_to(staging).as_posix() for p in staging.rglob('*') if p.is_file())
        for path in paths:
            destination = repository / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staging / path, destination)
        return loader['version'], paths


def check_version(new, old):
    if new['version'] < old['version'] or (new['sha256'] != old['sha256'] and new['version'] == old['version']):
        raise ValueError('Changed artifacts require a newer version; downgrade/reused versions are refused')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    items = projects()
    available = [name for name, item in items.items() if item.get('publish')]
    parser.add_argument('projects', nargs='*', help='Projects to build and publish: ' + ', '.join(available) + ', all. Omit to publish current builds.')
    parser.add_argument('--skip-build', action='store_true', help='Publish existing verified builds')
    parser.add_argument('--dry-run', action='store_true', help='Validate only; do not build, commit or push')
    parser.add_argument('--no-push', action='store_true', help='Commit the release locally without pushing')
    args = parser.parse_args()
    selected = available if not args.projects or args.projects == ['all'] else list(dict.fromkeys(args.projects))
    if any(name not in available for name in selected):
        parser.error('Unknown or non-cloud project; choose ' + ', '.join(available) + ' or all')
    repository, music = ROOT, items['music']['path']
    if args.dry_run:
        with tempfile.TemporaryDirectory(prefix='chem-release-') as folder:
            staging = Path(folder)
            for name in ('README.md', 'index.json'):
                shutil.copy2(repository / name, staging / name)
            version, _ = sync_files(staging, music, selected)
            print(f'DRY RUN OK: current artifacts 0x{version:08X}; no files published')
        return
    if git(repository, 'branch', '--show-current') != 'main':
        raise ValueError('ChemCloud must be on main')
    if git(repository, 'status', '--porcelain'):
        raise ValueError('ChemCloud has local changes; commit or resolve them first')
    network_git(repository, 'fetch', 'origin')
    if git(repository, 'rev-list', '--count', 'origin/main..HEAD') != '0':
        raise ValueError('ChemCloud has unpushed commits; run python workspace.py push cloud to retry')
    run('git', 'merge', '--ff-only', 'origin/main', cwd=repository)
    if args.projects and not args.skip_build:
        for name in selected:
            if name == 'chem':
                bump_versions(repository)
            command(name, items[name]['build'])
            for test in items[name].get('tests', []):
                command(name, test)
    version, paths = sync_files(repository, music, selected)
    run('git', 'diff', '--check', cwd=repository)
    run('git', 'add', '--', *paths, cwd=repository)
    if not git(repository, 'diff', '--cached', '--name-only'):
        print('Already published; no changes to commit or push.')
        return
    run('git', 'commit', '-m', 'Publish ' + ', '.join(selected) + f' (Chem 0x{version:08X})', cwd=repository)
    if args.no_push:
        print('Committed locally; use python workspace.py push cloud to publish.')
        return
    network_git(repository, 'push', 'origin', 'main')
    print('Published: ' + git(repository, 'rev-parse', 'HEAD'))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, StopIteration) as error:
        print(f'Release stopped: {error}\nLocal changes are retained; no automatic rollback or force push.', file=sys.stderr)
        sys.exit(1)
