import os
import requests
import sys
from .utils import getenv, sh
from contextlib import contextmanager
from subprocess import run


ENV_ORIG = os.environ.copy()


def conda_installer(ver, prefix='./miniconda3'):
    assert isinstance(ver, str)
    assert isinstance(prefix, str)

    prefix = os.path.abspath(prefix)

    if os.path.exists(prefix):
        print(f'{prefix}: exists', file=sys.stderr)
        return prefix

    name = 'Miniconda3'
    version = ver
    arch = 'x86_64'
    platform = sys.platform
    if sys.platform == 'darwin':
        platform = 'MacOSX'
    elif sys.platform == 'linux':
        platform = 'Linux'

    url_root = 'https://repo.continuum.io/miniconda'
    installer = f'{name}-{version}-{platform}-{arch}.sh'
    url = f'{url_root}/{installer}'
    install_command = f'./{installer} -b -p {prefix}'.split()

    if not os.path.exists(installer):
        with requests.get(url, stream=True) as data:
            with open(installer, 'wb') as fd:
                for chunk in data.iter_content(chunk_size=16384):
                    fd.write(chunk)
        os.chmod(installer, 0o755)
    run(install_command)

    return prefix


def conda_init_path(prefix):
    if os.environ['PATH'] != ENV_ORIG['PATH']:
        os.environ['PATH'] = ENV_ORIG['PATH']
    os.environ['PATH'] = ':'.join([os.path.join(prefix, 'bin'),
                                   os.environ['PATH']])
    print(f"PATH = {os.environ['PATH']}")


def conda_activate(env_name):
    proc = run(f"source activate {env_name} && env",
               capture_output=True,
               shell=True)
    proc.check_returncode()
    return getenv(proc.stdout.decode()).copy()


@contextmanager
def conda_env_load(env_name):
    last = os.environ.copy()
    os.environ = conda_activate(env_name)
    try:
        yield
    finally:
        os.environ = last.copy()


def conda(*args):
    command = ['conda']
    tmp = []
    for arg in args:
        tmp += arg.split()

    command += tmp
    print(f'Running: {" ".join(command)}')
    return run(command, capture_output=True)
