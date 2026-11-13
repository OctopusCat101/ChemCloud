#!/usr/bin/env python3
"""Publish verified local build outputs into a Chem module repository (no push)."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import shutil
import tomllib
import zipfile

from tools.projects import projects

ROOT = projects()['chem']['path']

def merge_target(catalog, target):
    if catalog.get('schema') != 1:
        raise ValueError('Unsupported repository schema')
    previous = next((t for t in catalog['targets'] if t['target'] == target['target']), None)
    if previous:
        def check(new, old):
            if new['version'] < old['version'] or (new['version'] == old['version'] and new['sha256'] != old['sha256']):
                raise ValueError('Changed artifacts require a newer version')
        check(target['loader'], previous['loader'])
        if target['loader']['sha256'] != previous['loader']['sha256'] and target['loader']['face_id'] == previous['loader']['face_id']:
            raise ValueError('Changed installer requires a new watchface ID')
        modules = {m['id']: m for m in previous['modules']}
        for item in target['modules']:
            if item['id'] in modules:
                check(item, modules[item['id']])
            modules[item['id']] = item
        target['modules'] = list(modules.values())
    return {**catalog, 'targets': [target if t['target'] == target['target'] else t
                                 for t in catalog['targets']] if previous else [*catalog['targets'], target]}


def publish(repository, music, magic=None, selected=('chem', 'music', 'magic')):
    config = tomllib.loads((ROOT / 'build.toml').read_text(encoding='utf-8'))
    profile = tomllib.loads((ROOT / 'targets' / config['target'] / 'target.toml').read_text(encoding='utf-8'))
    previous_path = repository / 'index.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else {'schema': 1, 'targets': []}
    old_target = next((t for t in previous['targets'] if t['target'] == config['target']), None)
    if 'chem' in selected:
        face = ROOT / 'dist' / (config['output_name'] + '.face')
        build = json.loads((ROOT / 'out' / config['target'] / 'build-manifest.json').read_text(encoding='utf-8'))
        if hashlib.sha256(face.read_bytes()).hexdigest() != build['output_sha256']:
            raise ValueError('Framework face does not match its successful build manifest')
        version = re.search(r'#define CHEM_BAND9_MANAGER_BUILD_ID\s+UINT32_C\((0x[0-9a-fA-F]+)\)',
                            (ROOT / 'manager/target/lvgl_v8/chem_manager_target_lvgl_v8.c').read_text(encoding='utf-8'))
        if not version:
            raise ValueError('Missing framework release revision')
    spec = importlib.util.spec_from_file_location('chem_native_package', ROOT / 'scripts/package-module.py')
    packer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packer)
    base = Path('xiaomi-band-9') / profile['firmware_version']
    copies = []

    def artifact(source, directory):
        relative = base / directory / source.name
        data = source.read_bytes()
        copies.append((source, relative))
        return {'path': relative.as_posix(), 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def module(project, directory):
        settings = tomllib.loads((project / 'build.toml').read_text(encoding='utf-8'))
        source = project / 'dist' / (settings['output_name'] + '.chem')
        report = json.loads((project / 'out' / config['target'] / 'build-manifest.json').read_text(encoding='utf-8'))
        if hashlib.sha256(source.read_bytes()).hexdigest() != report.get('output_sha256', report.get('sha256')):
            raise ValueError(directory + ' package does not match successful build manifest')
        with zipfile.ZipFile(source) as archive:
            manifest = json.loads(archive.read('manifest.json'))
            signed, elf = archive.read('receipt.bin'), archive.read('module.elf')
            packer.verify_receipt(signed)
            if (manifest['id'] != signed[32:64].split(b'\0', 1)[0].decode('ascii') or
                manifest['target'] != signed[64:112].split(b'\0', 1)[0].decode('ascii') or
                manifest['version'] != int.from_bytes(signed[20:24], 'little') or
                manifest['artifact_size'] != len(elf) or len(elf) != int.from_bytes(signed[24:28], 'little') or
                manifest['artifact_sha256'] != hashlib.sha256(elf).hexdigest() or
                hashlib.sha256(elf).digest() != signed[144:176] or
                manifest['firmware_sha256'] != signed[112:144].hex()):
                raise ValueError(directory + ' manifest does not match signed receipt')
            for resource in manifest['resources']:
                data = archive.read('resources/' + resource['name'])
                if len(data) != resource['size'] or hashlib.sha256(data).hexdigest() != resource['sha256']:
                    raise ValueError(directory + ' resource does not match manifest')
        if manifest['target'] != config['target'] or manifest['firmware_sha256'] != profile['firmware_sha256']:
            raise ValueError(directory + ' does not match target firmware')
        result = {key: manifest[key] for key in ('id', 'name', 'version', 'version_name')}
        if settings.get('cloud', {}).get('description'):
            result['description'] = settings['cloud']['description']
        return {**result, **artifact(source, directory)}

    modules = [module(music, 'NoirMusic')] if 'music' in selected else []
    magic = magic if magic is not None else projects()['magic']['path']
    resources = None
    if 'magic' in selected:
        modules.append(module(magic, 'Magic'))
        settings = tomllib.loads((magic / 'build.toml').read_text(encoding='utf-8'))
        spec = importlib.util.spec_from_file_location('magic_resources', magic / 'scripts/package.py')
        compiler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compiler)
        resources = {'schema': 1, 'target': config['target'], 'packages': []}
        for filename, source_dir in settings.get('cloud', {}).get('resource_packages', {}).items():
            if Path(filename).name != filename or not filename.endswith('.magic'):
                raise ValueError('Invalid resource package filename')
            source_root = (magic / source_dir).resolve()
            if not source_root.is_relative_to(magic.resolve()):
                raise ValueError('Resource source leaves project')
            source = magic / 'dist' / filename
            if compiler.build(source_root) != source.read_bytes():
                raise ValueError(filename + ' does not match resource sources; rebuild first')
            metadata = json.loads((source_root / 'magic.json').read_text(encoding='utf-8'))
            resources['packages'].append({'id': metadata['id'], 'name': metadata['name'], **artifact(source, 'Magic')})
        for source, filename in [(magic / 'docs/cloud.md', 'README.md'), (magic / 'CHANGELOG.md', 'CHANGELOG.md'),
                                 (magic / 'NOTICE.md', 'NOTICE.md'), (magic / 'LICENSE', 'LICENSE')]:
            copies.append((source, base / 'Magic' / filename))

    if 'chem' in selected:
        loader = {'version': int(version[1], 16), 'face_id': config['watchface_id'], **artifact(face, 'chem-loader')}
    elif old_target:
        loader = old_target['loader']
    else:
        raise ValueError('Publish Chem before publishing modules for a new target')
    target = {'model': 'xiaomi-band-9', 'firmware': profile['firmware_version'],
              'target': config['target'], 'firmware_sha256': profile['firmware_sha256'],
              'device_ids': ['M2346B1', 'miwear.watch.n66tc', 'n66tc', 'N66TC', 'xiaomi.watch.n66', 'M2345B1'],
              'loader': loader,
              'modules': modules}
    catalog_path = repository / 'index.json'
    catalog = merge_target(previous, target)
    for source, relative in copies:
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    if resources is not None:
        (repository / base / 'Magic/resources.json').write_text(json.dumps(resources, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Published local repository: ' + str(repository))
    print('Remote URL unchanged; no commit or push performed.')
