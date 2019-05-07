from setuptools import setup, find_packages

setup(
    name='delivery_merge',
    version='0.0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'delivery_merge=delivery_merge.cli.merge:main',
        ],
    },
    install_requires=[
        'requests',
        'pyyaml',
    ]
)
