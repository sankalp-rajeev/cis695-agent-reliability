"""Python 3.6-compatible read-only probe, executed only in our audit containers.

Input is private audit data on stdin. Output contains counts, versions, hashes,
booleans and fixed rules only. No package imports or task code execution.
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import zipfile


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def git(args, data=None):
    return subprocess.check_output(['git', '-C', '/testbed'] + args, input=data,
                                   stderr=subprocess.PIPE)


def version_from_text(text):
    patterns = [r'(?m)^Version:\s*([^\s]+)',
                r'''(?m)^\s*__version__\s*=\s*['"]([^'"]+)''',
                r'''(?m)^\s*version\s*=\s*['"]([^'"]+)''']
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    match = re.search(r'(?m)^VERSION\s*=\s*\((\d+),\s*(\d+),\s*(\d+)', text)
    if match:
        return '.'.join(match.groups())
    return None


def package_version(directory, package):
    for name in ['__version__.py', '_version.py', 'version.py', '__init__.py']:
        try:
            with open(os.path.join(directory, name), errors='replace') as stream:
                value = version_from_text(stream.read())
            if value:
                return value
        except OSError:
            pass
    parent = os.path.dirname(directory)
    try:
        for name in os.listdir(parent):
            if re.sub(r'[-_.]+', '-', name.lower()).startswith(re.sub(r'[-_.]+', '-', package.lower()) + '-'):
                for leaf in ['METADATA', 'PKG-INFO']:
                    try:
                        with open(os.path.join(parent, name, leaf), errors='replace') as stream:
                            value = version_from_text(stream.read())
                        if value:
                            return value
                    except OSError:
                        pass
        # pip vendors have no dist-info. The pinned vendor manifest is evidence.
        vendor = os.path.join(parent, 'vendor.txt')
        if os.path.isfile(vendor):
            with open(vendor) as stream:
                match = re.search(r'(?mi)^' + re.escape(package) + r'==([^\s]+)', stream.read())
            if match:
                return match.group(1)
    except OSError:
        pass
    return None


def archives_version(path, package):
    """Inspect archive metadata even for hash-named pip HTTP cache bodies."""
    normalized = re.sub(r'[-_.]+', '-', package.lower())
    rows = []
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if name.endswith(('/METADATA', '/PKG-INFO')):
                        text = archive.read(name).decode(errors='replace')
                        match = re.search(r'(?m)^Name:\s*(\S+)', text)
                        if match and re.sub(r'[-_.]+', '-', match.group(1).lower()) == normalized:
                            rows.append(dict(kind='wheel' if name.endswith('/METADATA') else 'sdist',
                                             version=version_from_text(text), path_sha256=sha(path)))
        elif re.search(r'\.(?:tar(?:\.gz|\.bz2|\.xz)?|tgz|conda)$', path):
            if path.endswith('.conda'):
                return rows  # .conda is a zip; covered above when metadata exists.
            with tarfile.open(path) as archive:
                for member in archive:
                    if member.isfile() and member.name.endswith(('PKG-INFO', 'info/index.json')):
                        text = archive.extractfile(member).read().decode(errors='replace')
                        if member.name.endswith('index.json'):
                            data = json.loads(text)
                            if re.sub(r'[-_.]+', '-', data.get('name', '').lower()) == normalized:
                                rows.append(dict(kind='conda', version=data.get('version'), path_sha256=sha(path)))
                        else:
                            match = re.search(r'(?m)^Name:\s*(\S+)', text)
                            if match and re.sub(r'[-_.]+', '-', match.group(1).lower()) == normalized:
                                rows.append(dict(kind='sdist', version=version_from_text(text), path_sha256=sha(path)))
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile):
        pass
    return rows


def inspect_packages(request):
    masks = request['masked_paths']
    result = dict(masked={}, copies=[], errors=0)
    package, import_name = request['package'], request['import_name']
    for mask in masks:
        count, archives, extracted = 0, [], []
        for directory, folders, files in os.walk(mask):
            count += len(files)
            for name in files:
                path = os.path.join(directory, name)
                if name.endswith(('METADATA', 'PKG-INFO', 'index.json')):
                    try:
                        with open(path, errors='replace') as stream:
                            text = stream.read()
                        if name == 'index.json':
                            meta = json.loads(text)
                            if meta.get('name', '').replace('-', '_') == package.replace('-', '_'):
                                extracted.append(dict(kind='conda-extracted', version=meta.get('version'), path_sha256=sha(path)))
                    except (OSError, ValueError):
                        result['errors'] += 1
                # Cheap magic check avoids decompressing ordinary files.
                try:
                    with open(path, 'rb') as stream:
                        magic = stream.read(4)
                    if magic[:2] == b'PK' or name.endswith(('.tar.gz', '.tar.bz2', '.tgz', '.tar.xz')):
                        archives.extend(archives_version(path, package))
                except OSError:
                    result['errors'] += 1
        result['masked'][mask] = dict(exists=os.path.isdir(mask), file_count=count,
                                     repo_archives=archives, repo_extracted=extracted)
    roots = ['/opt', '/usr/local/lib', '/usr/lib', '/root', '/tmp', '/testbed']
    found = set()
    probes = request.get('patch_lines', [])
    for root in roots:
        for directory, folders, files in os.walk(root):
            folders[:] = [f for f in folders if f not in {'.git', '__pycache__'}
                          and not any(os.path.join(directory, f) == mask for mask in masks)]
            if any(directory == mask or directory.startswith(mask + '/') for mask in masks):
                folders[:] = []
                continue
            if os.path.basename(directory) != import_name:
                continue
            resolved = os.path.realpath(directory)
            if directory.startswith('/testbed/') or resolved.startswith('/testbed/') or resolved in found:
                continue
            found.add(resolved)
            version = package_version(directory, package)
            matches = set()
            file_count = 0
            for sub, dirs, leaves in os.walk(directory):
                dirs[:] = [f for f in dirs if f not in {'.git', '__pycache__'}]
                for leaf in leaves:
                    if not leaf.endswith(('.py', '.pyx', '.pxd', '.c', '.h', '.txt')):
                        continue
                    file_count += 1
                    try:
                        with open(os.path.join(sub, leaf), errors='replace') as stream:
                            text = stream.read()
                        matches.update(sha(p) for p in probes if p in text)
                    except OSError:
                        result['errors'] += 1
            result['copies'].append(dict(path=directory, version=version,
                base_version=request.get('base_version'),
                different_from_base=(version != request['base_version'] if version and request.get('base_version') else None),
                vendored='/pip/_vendor/' in directory, source_files=file_count,
                gold_added_line_count=len(matches)))
    return result


def inspect_git(request):
    base = request['base_commit']
    stamp = int(git(['show', '-s', '--format=%ct', base]).strip())
    reachable = {}
    for line in git(['rev-list', '--all', '--timestamp']).decode().splitlines():
        timestamp, oid = line.split()[:2]
        reachable[oid] = int(timestamp)
    # --batch-all-objects includes dangling/unreachable objects without fsck
    # writing lost-found files. Never use hash-object -w, checkout or fetch.
    all_commits = []
    proc = subprocess.Popen(['git', '-C', '/testbed', 'cat-file', '--batch-all-objects',
        '--batch-check=%(objecttype) %(objectname)'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    objects = 0
    for raw in proc.stdout:
        kind, oid = raw.decode().strip().split()
        objects += 1
        if kind == 'commit':
            all_commits.append(oid)
    if proc.wait():
        raise RuntimeError('object-enumeration-failed')
    stamps, parents = {}, {}
    process = subprocess.Popen(['git', '-C', '/testbed', 'cat-file', '--batch'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Feed from an in-memory file using communicate to avoid pipe deadlocks.
    raw, _ = process.communicate(('\n'.join(all_commits) + '\n').encode())
    if process.returncode:
        raise RuntimeError('commit-read-failed')
    stream = io.BytesIO(raw)
    while True:
        header = stream.readline()
        if not header:
            break
        oid, kind, size = header.decode().split()
        content = stream.read(int(size)); stream.read(1)
        match = re.search(br'(?m)^committer .* (\d+) [+-]\d{4}$', content)
        if match:
            stamps[oid] = int(match.group(1))
        parents[oid] = [m.decode() for m in re.findall(br'(?m)^parent ([0-9a-f]+)$', content)]
    children = {}
    for oid, ps in parents.items():
        for parent in ps:
            children.setdefault(parent, []).append(oid)
    descendants, todo = set(), list(children.get(base, []))
    while todo:
        oid = todo.pop()
        if oid not in descendants:
            descendants.add(oid); todo.extend(children.get(oid, []))
    future = {oid for oid, ts in stamps.items() if ts > stamp} | descendants
    gold = []
    import base64
    for value in request.get('post_images_b64', []):
        oid = git(['hash-object', '--stdin'], base64.b64decode(value)).decode().strip()
        present = subprocess.call(['git', '-C', '/testbed', 'cat-file', '-e', oid + '^{blob}'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        gold.append(dict(blob=oid, present=present))
    return dict(base_timestamp=stamp, object_count=objects, commit_count=len(stamps),
        reachable_commit_count=len(reachable), future_reachable_count=len(future & set(reachable)),
        future_object_count=len(future), future_commit_hashes=sorted(future),
        gold_post_image_blobs=gold, commit_timestamps=stamps)


def base_probes(request):
    """Exactly the legacy base Git and installed-dependency subtraction."""
    probes = request.get('all_lines', [])
    if not probes:
        return []
    process = subprocess.run(['git', '-C', '/testbed', 'grep', '-F', '-I', '-f', '/dev/stdin', '--', '.'],
        input=('\n'.join(probes) + '\n').encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode not in (0, 1) or process.returncode == 1 and process.stderr.strip():
        raise RuntimeError('base-grep-failed')
    text = process.stdout.decode(errors='replace')
    found = {sha(p) for p in probes if any(p in line.split(':', 1)[-1] for line in text.splitlines())}
    import glob
    roots = glob.glob('/opt/miniconda3/envs/testbed/lib/python*/site-packages')
    for root in roots:
        for directory, folders, files in os.walk(root):
            folders[:] = [f for f in folders if f != '_vendor']
            for name in files:
                try:
                    with open(os.path.join(directory, name), 'rb') as stream:
                        content = stream.read()
                    if b'\0' in content:
                        continue
                    text = content.decode(errors='replace')
                    found.update(sha(p) for p in probes if sha(p) not in found and p in text)
                except OSError:
                    pass
    return sorted(found)


def main():
    request = json.load(sys.stdin)
    result = dict(instance_id=request['instance_id'], checks={})
    for name, function in [('packages', inspect_packages), ('git', inspect_git), ('base_probes', base_probes)]:
        try:
            result['checks'][name] = dict(status='complete', result=function(request))
        except Exception as exc:
            # Error messages may contain source paths or subprocess output.
            result['checks'][name] = dict(status='incomplete', error_type=type(exc).__name__)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
