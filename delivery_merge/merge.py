import os
import re
import sys
from .conda import conda, conda_env_load, conda_cmd_channels, ei_touch
from .utils import comment_find, git, pushd, sh
from configparser import ConfigParser
from glob import glob
from ruamel.yaml import YAML


DMFILE_RE = re.compile(r'^(?P<name>[A-z\-_l]+)(?:[=<>\!]+)?(?P<version>[A-z0-9. ]+)?')   # noqa
DMFILE_INVALID_VERSION_RE = re.compile(r'[\ \!\@\#\$\%\^\&\*\(\)\-_]+')
DELIVERY_NAME_RE = re.compile(r'(?P<name>.*)[-_](?P<version>.*)[-_]py(?P<python_version>\d+)[-_.](?P<iteration>\d+)[-_.](?P<ext>.*)')  # noqa


class EmptyPackageSpec(Exception):
    pass


class InvalidPackageSpec(Exception):
    pass


def dmfile(filename):
    """ Return the contents of a file without comments

    :param filename: string: path to file
    :returns: list: of dicts, one per package
    """
    result = []
    with open(filename, 'r') as fp:
        for line in fp:
            line = line.strip()
            comment_pos = comment_find(line)

            if comment_pos >= 0:
                line = line[:comment_pos].strip()

            if not line:
                continue

            match = DMFILE_RE.match(line)
            if match is None:
                raise InvalidPackageSpec(f"'{line}'")

            pkg = match.groupdict()
            if pkg['version']:
                invalid = DMFILE_INVALID_VERSION_RE.match(pkg['version'])
                if invalid:
                    raise InvalidPackageSpec(f"'{line}'")

            pkg['fullspec'] = line
            result.append(pkg)

    if not result:
        raise EmptyPackageSpec("Nothing to do")

    return result


def env_combine(filename, conda_env, conda_channels=[]):
    """ Install packages listed in `filename` inside `conda_env`.
    Packages are quote-escaped to prevent spurious file redirection.

    :param filename: str: path to file
    :param conda_env: str: conda environment name
    :param conda_channels: list: channel URLs
    :returns: None
    :raises subprocess.CalledProcessError: via check_returncode method
    """
    packages = []

    for record in dmfile(filename):
        packages.append(f"'{record['fullspec']}'")

    packages_result = ' '.join([x for x in packages])

    with conda_env_load(conda_env):
        ei_touch()
        # Perform package installation
        proc = conda('install', '-q', '-y',
                     '-n', conda_env,
                     conda_cmd_channels(conda_channels),
                     packages_result)

        if proc.stderr:
            print(proc.stderr.decode())

        proc.check_returncode()


def testable_packages(filename, prefix):
    """ Scan a mini/anaconda prefix for unpacked packages matching versions
    requested by dmfile.

    :param filename: str: path to file
    :param prefix: str: path to conda root directory (aka prefix)
    :returns: dict: git commit hash and repository URL information
    """
    pkgdir = os.path.join(prefix, 'pkgs')
    paths = []
    yaml = YAML(typ='safe')

    for record in dmfile(filename):
        # Reconstruct ${package}-${version} format (when possible)
        pattern = f"{record['name']}-"
        if record['version']:
            pattern += record['version']
        pattern += '*'

        # Record path to extracted package
        path = ''.join([x for x in glob(os.path.join(pkgdir, pattern))
                        if os.path.isdir(x)])
        paths.append(path)

    for root in paths:
        info_d = os.path.join(root, 'info')
        recipe_d = os.path.join(info_d, 'recipe')
        git_log = os.path.join(info_d, 'git')

        if not os.path.exists(git_log):
            continue

        git_log_data = open(git_log).readlines()

        if not git_log_data:
            continue

        with open(os.path.join(recipe_d, 'meta.yaml')) as yaml_data:
            source = yaml.load(yaml_data)['source']

        if not isinstance(source, dict):
            continue

        repository = source['git_url']
        head = git_log_data[1].split()[1]
        yield dict(repo=repository, commit=head)


def integration_test(pkg_data, conda_env, results_root='.'):
    """
    :param pkg_data: dict: data returned by `testable_packages` method
    :param conda_env: str: conda environment name
    :param results_root: str: path to store XML reports
    :returns: str: path to XML report
    :raises subprocess.CalledProcessError: via check_returncode method
    """
    results = ''
    results_root = os.path.abspath(os.path.join(results_root, 'results'))
    src_root = os.path.abspath('src')

    if not os.path.exists(src_root):
        os.mkdir(src_root, 0o755)

    with pushd(src_root) as _:
        repo_root = os.path.basename(pkg_data['repo']).replace('.git', '')

        if not os.path.exists(repo_root):
            git(f"clone --recursive {pkg_data['repo']} {repo_root}")

        with pushd(repo_root) as _:
            git(f"checkout {pkg_data['commit']}")
            force_xunit2()

            with conda_env_load(conda_env):
                ei_touch()
                results = os.path.abspath(os.path.join(results_root,
                                                       repo_root,
                                                       'result.xml'))

                conda("uninstall", "-y", repo_root)

                proc_pip_install = sh("python", "-m pip install --upgrade pip pytest ci-watson")
                if proc_pip_install.returncode:
                    print(proc_pip_install.stdout.decode())
                    print(proc_pip_install.stderr.decode())

                proc_pip = sh("python", "-m pip install -v .[test]")
                proc_pip_stderr = proc_pip.stderr.decode()
                if proc_pip.returncode:
                    print(proc_pip.stdout.decode())
                    print(proc_pip.stderr.decode())

                if 'consider upgrading' not in proc_pip_stderr:
                    proc_pip.check_returncode()

                proc_egg = sh("python", "setup.py egg_info")
                if proc_egg.returncode:
                    print(proc_egg.stdout.decode())
                    print(proc_egg.stderr.decode())

                proc_pytest = sh("python", "-m pytest", f"-v --basetemp=.tmp --junitxml={results}")
                print(proc_pytest.stdout.decode())
                if proc_pytest.returncode:
                    print(proc_pytest.stderr.decode())

    return results


def force_xunit2(project='.'):
    """ Set project configuration to emit xunit2 regardless of orignal settings
    :param project: str: path project (i.e. source directory)
    """
    configs = [os.path.abspath(os.path.join(project, x))
               for x in ['pytest.ini', 'setup.cfg']]

    if any([os.path.exists(x) for x in configs]):
        for filename in configs:
            if not os.path.exists(filename):
                continue

            cfg = ConfigParser()
            cfg.read(filename)
            cfg['tool:pytest'] = {'junit_family': 'xunit2'}
            with open(filename, 'w') as data:
                cfg.write(data)
            break
    else:
        data = """[pytest]\njunit_family = xunit2\n"""
        with open('pytest.ini', 'w+') as cfg:
            cfg.write(data)
        return


def force_yaml_channels(yamlfile, channels):
    """ Replace the `channels:` block with `channels`
    :param yamlfile: str: path to yaml file
    :param channels: list: channel URLs
    """
    if not isinstance(channels, list):
        raise TypeError("Expecting a list of URLs")

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(offset=2)

    with open(yamlfile) as yaml_data:
        result = yaml.load(yaml_data)

    if not result.get('channels'):
        print(f"{yamlfile} has no channels", file=sys.stderr)
        return

    # Assuming there's a reason to change the file...
    if result['channels'] != channels:
        result['channels'] = channels

        with open(yamlfile, 'w') as fp:
            yaml.dump(result, fp)
