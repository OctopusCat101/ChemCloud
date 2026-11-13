from pathlib import Path
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def projects():
    config = tomllib.loads((ROOT / 'projects.toml').read_text(encoding='utf-8'))
    if config.get('schema') != 1:
        raise ValueError('Unsupported workspace configuration')
    items = config['projects']
    local = ROOT / 'projects.local.toml'
    if local.exists():
        for name, settings in tomllib.loads(local.read_text(encoding='utf-8')).get('projects', {}).items():
            if name not in items:
                raise ValueError('Unknown project: ' + name)
            items[name].update(settings)
    return {name: {**item, 'path': (ROOT / item['path']).resolve()} for name, item in items.items()}


def command(name, arguments):
    items = projects()
    substitutions = {key: str(item['path']) for key, item in items.items()}
    argv = [str(arg).format(**substitutions) for arg in arguments]
    print('+ ' + name + ': ' + subprocess.list2cmdline(argv), flush=True)
    subprocess.run([sys.executable, '-X', 'utf8', *argv], cwd=items[name]['path'], check=True)
