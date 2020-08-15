from collections import defaultdict
from pathlib import Path
from setuptools import setup, find_namespace_packages


def frontend_files():
    source = Path('frontend/build')
    target = Path('djenius/www')

    dirs = defaultdict(list)

    for f in sorted(source.rglob('*')):
        if f.is_dir():
            continue
        relf = f.relative_to(source)
        dirs[target / relf.parent].append(f)

    for directory, targets in dirs.items():
        yield str(directory), [str(t) for t in targets]


setup(
    name="djenius",
    author="Alexandre Macabies",
    version="1.0",
    packages=find_namespace_packages(),
    data_files=list(frontend_files()),
    install_requires=[
        'aiohttp~=3',
        'aioprometheus~=20',
        'dataclasses_json~=0.5',
        'djenius_auth~=1',
        'sortedcontainers~=2',
        'whoosh~=2',
    ],
)
