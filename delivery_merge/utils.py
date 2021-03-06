import os
from contextlib import contextmanager
from subprocess import run


def comment_find(s, delims=[';', '#']):
    """ Find the first occurence of a comment in a string

    :param s: string
    :param delims: list: of comment delimiters
    :returns: integer: index of first match
    """
    for delim in delims:
        index = s.find(delim)
        if index != -1:
            break

    return index


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
    return run(command, capture_output=True, env=os.environ)


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
    results = []
    for x in s.splitlines():
        if not x:
            continue
        pair = x.split('=', 1)
        if len(pair) < 2:
            pair.append('')
        results.append(pair)
    return dict(results)


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
