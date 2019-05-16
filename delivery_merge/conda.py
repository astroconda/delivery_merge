import os
import requests
import sys
from .utils import getenv, sh
from contextlib import contextmanager
from subprocess import run


ENV_ORIG = os.environ.copy()


class BadPlatform(Exception):
    pass


def ei_touch():
    py_version = sh('python', '--version').stdout.decode().strip().split()[1]
    py_version = '.'.join(py_version.split('.')[:2])
    root = run("python -c 'import sys; print(sys.prefix)'",
               capture_output=True,
               shell=True,
               env=os.environ).stdout.decode().strip()
    libsp = ['lib', f'python{py_version}', 'site-packages']
    site_packages = os.path.join(root, *libsp)
    pthfile = os.path.join(site_packages, 'easy-install.pth')

    print('PTHFILE = {}'.format(pthfile))
    if not os.path.exists(pthfile):
        open(pthfile, 'w+').write('')


def conda_installer(ver, prefix='./miniconda3'):
    """ Install miniconda into a user-defined prefix and return its path

    :param ver: str: miniconda version (not conda version)
    :param prefix: str: path to install miniconda into
    :returns: str: absolute path to installation prefix
    :raises delivery_merge.conda.BadPlatform: when platform check fails
    :raises subprocess.CalledProcessError: via check_returncode method
    """
    assert isinstance(ver, str)
    assert isinstance(prefix, str)

    prefix = os.path.abspath(prefix)

    # Is miniconda already installed?
    if os.path.exists(prefix):
        print(f'{prefix}: exists', file=sys.stderr)
        return prefix

    name = 'Miniconda3'
    version = ver
    arch = 'x86_64'
    platform = sys.platform

    # Emit their installer's concept of "platform"
    if sys.platform == 'darwin':
        platform = 'MacOSX'
    elif sys.platform == 'linux':
        platform = 'Linux'
    else:
        raise BadPlatform(f'{sys.platform} is not supported.')

    url_root = 'https://repo.continuum.io/miniconda'
    installer = f'{name}-{version}-{platform}-{arch}.sh'
    url = f'{url_root}/{installer}'
    install_command = f'./{installer} -b -p {prefix}'.split()

    # Download installer
    if not os.path.exists(installer):
        with requests.get(url, stream=True) as data:
            with open(installer, 'wb') as fd:
                for chunk in data.iter_content(chunk_size=16384):
                    fd.write(chunk)
        os.chmod(installer, 0o755)

    # Perform installation
    run(install_command, env=os.environ).check_returncode()

    return prefix


def conda_init_path(prefix):
    """ Redefines $PATH so subsequent shell calls use the just-installed
    miniconda prefix. This function will not continue prepending to $PATH
    so it's safe to call more than once.

    :param prefix: str: path to miniconda installation
    :returns: None
    """
    if os.environ['PATH'] != ENV_ORIG['PATH']:
        os.environ['PATH'] = ENV_ORIG['PATH']
    os.environ['PATH'] = ':'.join([os.path.join(prefix, 'bin'),
                                   os.environ['PATH']])


def conda_site():
    """ Retrieve current environment's site-packages path
    """
    result = run("python -c 'import site; print(site.getsitepackages()[-1])'",
                 capture_output=True,
                 shell=True,
                 env=os.environ)
    result.check_returncode()
    return result.stdout.decode().strip()


def conda_activate(env_name):
    """ Activate a conda environment

    Assume: `conda_init_path` as been called beforehand
    Warning: Arbitrary code execution is possible here due to `shell` usage.

    :param env_name: str: conda environment to activate
    :returns: dict: new runtime environment
    :raises subprocess.CalledProcessError: via check_returncode method
    """
    proc = run(f". activate {env_name} && env",
               capture_output=True,
               shell=True,
               env=os.environ)
    proc.check_returncode()
    return getenv(proc.stdout.decode()).copy()


@contextmanager
def conda_env_load(env_name):
    """ A simple wrapper for `conda_activate`
    The current runtime environment is replaced and restored

    >>> with conda_env_load('some_env') as _:
    >>>     # do something

    :param env_name: str: conda environment to activate
    :returns: None
    """
    last = os.environ.copy()
    os.environ = conda_activate(env_name)
    try:
        yield
    finally:
        os.environ = last.copy()


def conda(*args):
    """ Execute conda shell commands

    :returns: subprocess.CompletedProcess object
    """
    return sh('conda', *args)


def conda_cmd_channels(conda_channels, override=True):
    """ Generate conda command arguments for handling channels
    :param conda_channels: list: URI to channel
    :param override: bool: channel order is preserved when True
    """
    assert isinstance(conda_channels, list)
    channels_result = '--override-channels ' if override else ''
    for channel in conda_channels:
        channels_result += f'-c {channel} '

    return channels_result
