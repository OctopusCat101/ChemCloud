#!/usr/bin/env python3
"""Inspect, build, commit or push the projects registered in projects.toml."""
import argparse
import subprocess
import sys
from release import git, network_git
from tools.projects import projects, command


def is_repository(path):
    return (path / '.git').exists()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', default='status', choices=['status', 'build', 'check', 'commit', 'push', 'init'])
    parser.add_argument('projects', nargs='*', help='Project names, or all; status defaults to all')
    parser.add_argument('-m', '--message', help='Commit message')
    parser.add_argument('--remote', help='Origin URL, only with init')
    args = parser.parse_args()
    items = projects()
    if args.action != 'status' and not args.projects:
        parser.error('Choose project names explicitly, or all')
    if args.action == 'commit' and not args.message:
        parser.error('commit requires -m with a meaningful message')
    if args.remote and args.action != 'init':
        parser.error('--remote is only supported with init')
    selected = list(items) if not args.projects or args.projects == ['all'] else list(dict.fromkeys(args.projects))
    if any(name not in items for name in selected):
        parser.error('Choose from: ' + ', '.join(items))
    if args.action in ('commit', 'push'):
        for name in selected:
            path = items[name]['path']
            if not is_repository(path):
                if args.projects == ['all']:
                    print(f'{name}: no Git repository; skipped')
                    continue
                raise ValueError(f'{name}: no Git repository; run workspace.py init {name} first')
            if not git(path, 'branch', '--show-current'):
                raise ValueError(name + ': detached HEAD; choose a branch first')
            if git(path, 'diff', '--name-only', '--diff-filter=U'):
                raise ValueError(name + ': resolve merge conflicts first')
    for name in selected:
        item = items[name]
        path = item['path']
        if args.action == 'status':
            if not is_repository(path):
                print(f'{name}: {path} — no Git repository')
                continue
            print(f'\n{name}: {path}')
            print(git(path, 'status', '--short', '--branch'))
            continue
        if args.action == 'build':
            if item.get('build'):
                command(name, item['build'])
            else:
                print(name + ': no build step')
        elif args.action == 'check':
            for test in item.get('tests', []):
                command(name, test)
        elif args.action == 'init':
            if not path.is_dir():
                raise ValueError('Project folder does not exist: ' + str(path))
            if not is_repository(path):
                subprocess.run(['git', 'init', '-b', 'main'], cwd=path, check=True)
            if args.remote:
                subprocess.run(['git', 'remote', 'add', 'origin', args.remote], cwd=path, check=True)
        elif is_repository(path):
            if args.action == 'commit':
                if not git(path, 'status', '--porcelain'):
                    print(name + ': clean; skipped')
                    continue
                subprocess.run(['git', 'add', '-A', '--', '.'], cwd=path, check=True)
                subprocess.run(['git', 'diff', '--cached', '--check'], cwd=path, check=True)
                subprocess.run(['git', 'commit', '-m', args.message], cwd=path, check=True)
            elif args.action == 'push':
                if 'origin' not in git(path, 'remote').splitlines():
                    raise ValueError(name + ': configure origin before pushing')
                branch = git(path, 'branch', '--show-current')
                network_git(path, 'push', '--set-upstream', 'origin', branch)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f'Workspace stopped: {error}\nCompleted work is retained; remaining projects were not processed.', file=sys.stderr)
        sys.exit(1)
