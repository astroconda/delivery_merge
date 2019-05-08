import os
import pytest
from delivery_merge import conda


class TestConda:
    def setup_class(self):
        self.version = '4.5.12'
        self.prefix = conda.conda_installer(self.version)
        assert os.path.exists(self.prefix)

    def teardown_class(self):
        pass

    def test_init_path(self):
        conda.conda_init_path(self.prefix)
        assert os.environ.get('PATH', '').startswith(self.prefix)

    def test_shell_wrapper(self):
        output = conda.conda('info').stdout.decode()
        assert self.prefix in output
        assert self.version in output

    def test_env_load(self):
        with conda.conda_env_load('base') as _:
            assert os.environ.get('CONDA_PREFIX', '')
