from subprocess import run

def git(*args):
    command = ['git']
    tmp = []
    for arg in args:
        tmp += arg.split()

    command += tmp
    print(f'Running: {" ".join(command)}')
    return run(command, capture_output=True)
