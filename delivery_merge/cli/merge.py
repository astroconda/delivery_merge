import os
from ..conda import conda, conda_installer, conda_init_path
from ..merge import env_combine, testable_packages, integration_test
from argparse import ArgumentParser


def main():
    parser = ArgumentParser()
    parser.add_argument('--env-name', default='delivery',
                        help='name of environment')
    parser.add_argument('--installer-version', required=True,
                        help='miniconda3 installer version')
    parser.add_argument('--run-tests', action='store_true')
    parser.add_argument('--dmfile', required=True)
    parser.add_argument('base_spec')
    args = parser.parse_args()

    name = args.env_name
    base_spec = args.base_spec
    dmfile = args.dmfile
    channels = ['https://astroconda.org/channel/main',
                'defaults',
                'http://ssb.stsci.edu/conda-dev']
    delivery_root = 'delivery'
    yamlfile = os.path.join(delivery_root, name + '.yml')
    specfile = os.path.join(delivery_root, name + '.txt')

    if not os.path.exists(delivery_root):
        os.mkdir(delivery_root, 0o755)

    prefix = conda_installer(args.installer_version)
    conda_init_path(prefix)

    if not os.path.exists(os.path.join(prefix, 'envs', name)):
        print(f"Creating environment {name}...")
        proc = conda('create', '-q', '-y', '-n',  name, '--file', base_spec)
        if proc.stderr:
            print(proc.stderr.decode())

    print(f"Merging requested packages into environment: {name}")
    env_combine(dmfile, name, channels)

    print("Exporting yaml configuration...")
    conda('env', 'export', '-n', name, '--file', yamlfile)

    print("Exporting explicit dump...")
    with open(specfile, 'w+') as spec:
        proc = conda('list', '--explicit', '-n', name)
        spec.write(proc.stdout.decode())

    if args.run_tests:
        for package in testable_packages(args.dmfile, prefix):
            print(f"Running tests: {package}")
            integration_test(package, name)

    print("Done!")
