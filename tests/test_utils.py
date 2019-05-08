import os
import pytest
from delivery_merge import utils


KEYPAIRS = """FOO=FOO
FEED=FEED
FACE=FACE

moo=moo
meow=meow

"""


class TestUtils:
    def setup_class(self):
        pass

    def teardown_class(self):
        pass

    def test_sh(self):
        result = utils.sh('echo', 'testing').stdout.decode().strip()
        assert result == 'testing'

    def test_sh_variadic(self):
        result = utils.sh('echo',
                          'testing', '1', '2', '3').stdout.decode().strip()
        assert result == 'testing 1 2 3'

    def test_git_alive(self):
        assert utils.git('--version').stdout.decode().strip()

    def test_getenv(self):
        result = utils.getenv(KEYPAIRS)
        assert isinstance(result, dict)
        for k, v in result.items():
            assert k == v

    def test_getenv_empty_pair(self):
        result = utils.getenv("INFINITE_FUN=")
        assert not result.get('INFINITE_FUN')

    def test_getenv_multi_equal(self):
        result = utils.getenv("INFINITE_FUN=LINE=10")
        assert result.get('INFINITE_FUN') == 'LINE=10'

    def test_getenv_multi_equal(self):
        result = utils.getenv("INFINITE_FUN=LINE=10")
        assert result.get('INFINITE_FUN') == 'LINE=10'

    def test_pushd(self):
        orig_path = os.path.abspath('.')
        d = os.path.join(orig_path, 'pushd_test')

        if not os.path.exists(d):
            os.mkdir(d)

        with utils.pushd(d):
           new_path = os.path.abspath('.')
           assert new_path == os.path.join(orig_path, d)

        assert os.path.abspath('.') == orig_path
