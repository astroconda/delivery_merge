import os
import re
import yaml
from .conda import conda, conda_env_load
from .utils import git, pushd
from glob import glob
from subprocess import run


DMFILE_RE = re.compile(r'^(?P<name>.*)[=<>~\!](?P<version>.*).*$')


def comment_find(s, delims=[';', '#']):
    """ Return index of first match
    """
    for delim in delims:
        pos = s.find(delim)
        if pos != -1:
            break

    return pos


def dmfile(filename):
    result = []
    with open(filename, 'r') as fp:
        for line in fp:
            line = line.strip()
            comment_pos = comment_find(line)

            if comment_pos >= 0:
                line = line[:comment_pos]

            if not line:
                continue

            result.append(line)
    return result


def env_combine(filename, conda_env, conda_channels=[]):
    packages = []
    channels_result = '--override-channels '

    for line in dmfile(filename):
        packages.append(f"'{line}'")

    for channel in conda_channels:
        channels_result += f'-c {channel} '

    packages_result = ' '.join([x for x in packages])
    proc = conda('install', '-q', '-y', '-n',
                 conda_env, channels_result, packages_result)
    if proc.stderr:
        print(proc.stderr.decode())


def testable_packages(filename, prefix):
    """ Scan a mini/anaconda prefix for unpacked packages matching versions
    requested by dmfile.
    """
    pkgdir = os.path.join(prefix, 'pkgs')
    paths = []

    for line in dmfile(filename):
        match = DMFILE_RE.match(line)
        if match:
            pkg = match.groupdict()

            # Reconstruct ${package}-${version} format from
            # ${package}${specifier}${version}
            pattern = f"{pkg['name']}-{pkg['version']}*"

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

        with open(os.path.join(recipe_d, 'meta.yaml')) as yaml_data:
            source = yaml.load(yaml_data.read())['source']

        if not isinstance(source, dict):
            continue

        repository = source['git_url']
        head = open(git_log).readlines()[1].split()[1]
        yield dict(repo=repository, commit=head)


def integration_test(pkg_data, conda_env, results_root='.'):
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

            with conda_env_load(conda_env):
                results = os.path.abspath(os.path.join(results_root,
                                                       repo_root,
                                                       'result.xml'))
                run("pip install -e .[test]".split()).check_returncode()
                run(f"pytest -v --junitxml={results}".split(), check=True)
