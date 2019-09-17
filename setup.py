from os.path import join, dirname

from setuptools import setup, find_packages


def read(filename):
    with open(join(dirname(__file__), filename)) as fileobj:
        return fileobj.read()


def get_version(package):
    return [
        line for line in read('{}/__init__.py'.format(package)).splitlines()
        if line.startswith('__version__ = ')][0].split("'")[1]


PROJECT_NAME = 'pyvcr'
PACKAGE_NAME = 'pyvcr'
VERSION = get_version(PACKAGE_NAME)


setup(
    name=PROJECT_NAME,
    version=VERSION,
    description='A tool to record video streams.',
    author='Jeffrey Muller',
    author_email='jeffrey.muller92@gmail.com',
    url='https://github.com/j-muller/PyVCR',
    packages=find_packages(exclude=['tests', 'tests.*']),
    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
            'pylint',
            'xenon',
            'pydocstyle',
            'pycodestyle',
            'cobertura-clover-transform',
        ],
        'doc': [
            'sphinx<2', # Sphinx 2 needs Python>=3.5.2
        ],
        'dev': [
            'ipython',
            'pdbpp',
        ],
    },
    install_requires=[
        'docopt==0.6.2',
        'requests>=2.22.0,<3.0.0',
        'python-dateutil>=2.8.0,<3.0.0',
    ],
    entry_points={
        'console_scripts': [
            'pyvcr = pyvcr.cli.pyvcr:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3.5',
    ],
)
