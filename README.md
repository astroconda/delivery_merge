# delivery_merge

[![Build Status](https://dev.azure.com/astroconda/delivery_merge/_apis/build/status/astroconda.delivery_merge?branchName=master)](https://dev.azure.com/astroconda/delivery_merge/_build/latest?definitionId=1&branchName=master)
[![codecov](https://codecov.io/gh/astroconda/delivery_merge/branch/master/graph/badge.svg)](https://codecov.io/gh/astroconda/delivery_merge)

## What does it do?

1. Install miniconda3 in the current working directory
2. Create a new environment based on an explicit dump file
3. Transpose packages listed in a `dmfile` into the new environment
4. Generate a YAML and explicit dump of the new environment
5. [optionally] Scan packages installed via `dmfile` and execute tests (if possible) inside the new environment

## Where should I run this?

Inside of a CI/CD pipeline.


## Usage

```
usage: delivery_merge [-h] [--env-name ENV_NAME] --installer-version
                      INSTALLER_VERSION [--run-tests] --dmfile DMFILE
                      base_spec

positional arguments:
  base_spec

optional arguments:
  -h, --help            show this help message and exit
  --env-name ENV_NAME   name of environment
  --installer-version INSTALLER_VERSION
                        miniconda3 installer version
  --run-tests
  --dmfile DMFILE
```

## The dmfile

Comment characters: `;` or `#`

Line format: `{conda_package}[=<>]{version}`

**Example:**

```
; This is a comment
package_a=1.0.0
package_b<=1.0.0
package_c>=1.0.0  # This is also a comment
package_d>1.0.0
package_e<1.0.0
```


## Execution example

```sh
$ cat < EOF > hstdp-2019.3-py36.dm
python=3.6
numpy=1.16.3
EOF
$ git clone https://github.com/astroconda/astroconda-releases
$ delivery_merge --env-name delivery \
    --installer-version=4.5.12 \
    --dmfile hstdp-2019.3-py36.dm \
    astroconda-releases/hstdp/2019.2/latest-linux

# >>> Actual output here <<<
```
