import os
from contextlib import contextmanager
from subprocess import run


def sh(prog, *args):
    command = [prog]
    tmp = []
    for arg in args:
        tmp += arg.split()

    command += tmp
    print(f'Running: {" ".join(command)}')
    return run(command, capture_output=True)


def git(*args):
    return sh('git', *args)


def getenv(s):
    """ Convert string of key pairs to dictionary format
    """
    return dict([x.split('=', 1) for x in s.splitlines()])


@contextmanager
def pushd(path):
    """ Equivalent to shell pushd/popd behavior
    """
    last = os.path.abspath(os.getcwd())
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(last)

