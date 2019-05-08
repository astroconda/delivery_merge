import os
from contextlib import contextmanager
from subprocess import run


def sh(prog, *args):
    """ Execute a program with arguments
    :param prog: str: path to program
    :param args: tuple: variadic arguments
                 Accepts any combination of strings passed as arguments
    :returns: subprocess.CompletedProcess
    """
    command = [prog]
    tmp = []
    for arg in args:
        tmp += arg.split()

    command += tmp
    print(f'Running: {" ".join(command)}')
    return run(command, capture_output=True)


def git(*args):
    """ Execute git commands
    :param args: tuple: variadic arguments to pass to git
    :returns: subprocess.CompletedProcess
    """
    return sh('git', *args)


def getenv(s):
    """ Convert string of key pairs to dictionary format
    :param s: str: key pairs separated by newlines
    :returns: dict: converted key pairs
    """
    return dict([x.split('=', 1) for x in s.splitlines() if x])


@contextmanager
def pushd(path):
    """ Equivalent to shell pushd/popd behavior
    :param path: str: path to directory
    """
    last = os.path.abspath(os.getcwd())
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(last)

