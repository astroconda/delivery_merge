import os
import pytest
from delivery_merge import conda, merge


CHANNELS = ['http://ssb.stsci.edu/astroconda',
            'defaults',
            'http://ssb.stsci.edu/astroconda-dev']
BASE_SPEC = """# This file may be used to create an environment using:
# $ conda create --name <env> --file <this file>
# platform: linux-64
@EXPLICIT
https://repo.anaconda.com/pkgs/main/linux-64/ca-certificates-2019.1.23-0.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/libgcc-ng-8.2.0-hdf63c60_1.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/libstdcxx-ng-8.2.0-hdf63c60_1.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/libffi-3.2.1-hd88cf55_4.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/ncurses-6.1-he6710b0_1.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/openssl-1.1.1b-h7b6447c_1.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/xz-5.2.4-h14c3975_4.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/zlib-1.2.11-h7b6447c_3.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/libedit-3.1.20181209-hc058e9b_0.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/readline-7.0-h7b6447c_5.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/tk-8.6.8-hbc83047_0.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/sqlite-3.28.0-h7b6447c_0.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/python-3.7.3-h0371630_0.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/certifi-2019.3.9-py37_0.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/setuptools-41.0.1-py37_0.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/wheel-0.33.1-py37_0.tar.bz2
https://repo.anaconda.com/pkgs/main/linux-64/pip-19.1-py37_0.tar.bz2
"""
COMMENTS_DELIM = [';', '#']
COMMENTS = """; comment
; comment ; comment
;comment;comment
;comment#comment
data  ; comment
data ; comment
data; comment
data;comment
# comment
# comment # comment
#comment#comment
#comment;comment
data  # comment
data # comment
data# comment
data#comment
"""
DMFILE = """
; Example
python  # dmfile
setuptools
relic   # tiny package providing its own test suite

"""
DMFILE_INVALID = f"""
{DMFILE}
invalid package specification
"""


class TestMerge:
    def setup_class(self):
        self.env_name = 'delivery_env'
        self.input_file_base_spec = 'base_spec.txt'
        self.version = '4.5.12'
        self.input_file = 'sample.dm'
        self.input_file_invalid = 'sample_invalid.dm'
        self.input_file_empty = 'sample_empty.dm'
        open(self.input_file, 'w+').write(DMFILE)
        open(self.input_file_invalid, 'w+').write(DMFILE_INVALID)
        open(self.input_file_empty, 'w+').write("")
        open(self.input_file_base_spec, 'w+').write(BASE_SPEC)

        self.prefix = conda.conda_installer(self.version)
        conda.conda_init_path(self.prefix)
        conda.conda('create', '-q', '-y',
                    '-n',  self.env_name,
                    '--file', self.input_file_base_spec)

    def teardown_class(self):
        pass

    @pytest.mark.parametrize('comments', [x for x in COMMENTS.splitlines()])
    def test_comment_find(self, comments):
        index = merge.comment_find(comments)
        assert comments[index] in COMMENTS_DELIM

    def test_dmfile(self):
        data = merge.dmfile(self.input_file)
        assert COMMENTS_DELIM not in [x['fullspec'] for x in data]
        assert all([x['name'] for x in data])

    def test_dmfile_raises_InvalidPackageSpec(self):
        with pytest.raises(merge.InvalidPackageSpec):
            merge.dmfile(self.input_file_invalid)

    def test_dmfile_raises_EmptyPackageSpec(self):
        with pytest.raises(merge.EmptyPackageSpec):
            merge.dmfile(self.input_file_empty)

    def test_env_combine(self):
        merge.env_combine(self.input_file, self.env_name, CHANNELS)

        input_data = merge.dmfile(self.input_file)
        output_data = conda.conda(f'list -n {self.env_name}')
        output_data.check_returncode()
        installed = [x.split()[0]
                     for x in output_data.stdout.decode().splitlines()
                     if not x.startswith('#')]
        requested = [x['name'] for x in input_data]
        for req in requested:
            assert req in installed

    def test_testable_packages(self):
        merge.env_combine(self.input_file, self.env_name, CHANNELS)
        result = list(merge.testable_packages(self.input_file, self.prefix))
        assert result

        for data in result:
            assert isinstance(data, dict)
            assert [isinstance(x, str) for x in data.values()]

    def test_integration_test(self):
        merge.env_combine(self.input_file, self.env_name, CHANNELS)
        input_data = list(merge.testable_packages(self.input_file,
                                                  self.prefix))
        assert input_data

        output_dir = 'test_results'
        for pkg in input_data:
            result = merge.integration_test(pkg, self.env_name, output_dir)
            assert os.path.exists(result)
            contents = open(result).read()
            assert contents.startswith('<?xml') and contents.endswith('</testsuite>')

    def test_force_xunit2_no_config(self):
        merge.force_xunit2()
        assert os.path.exists('pytest.ini')
        assert 'junit_family = xunit2' in open('pytest.ini').read()
        os.remove('pytest.ini')

    def test_force_xunit2_no_setup(self):
        open('pytest.ini', 'w+').write('')
        merge.force_xunit2()
        assert not os.path.exists('setup.cfg')
        assert os.path.exists('pytest.ini')
        assert 'junit_family = xunit2' in open('pytest.ini').read()
        os.remove('pytest.ini')

    def test_force_xunit2_no_pytest(self):
        open('setup.cfg', 'w+').write('')
        merge.force_xunit2()
        assert not os.path.exists('pytest.ini')
        assert os.path.exists('setup.cfg')
        assert 'junit_family = xunit2' in open('setup.cfg').read()
        os.remove('setup.cfg')

