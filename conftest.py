import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def _jail(tmp_path_factory):
    cwd = os.path.abspath('.')
    tmp = tmp_path_factory.mktemp("condatest")
    os.chdir(tmp)
    yield
    os.chdir(cwd)
