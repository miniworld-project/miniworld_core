
from codecs import open
from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
setup(
    name='miniworld',
    version='0.1',
    description='MiniWorld network emulation tool',
    long_description=long_description,
    url='https://github.com/miniworld-project/miniworld_core',
    author='Nils Schmidt',
    author_email='miniworldproject ät gmail.com',

    packages=find_packages(exclude=['tests*']),
    # by default only requirements for thw mw console script are installed
    install_requires=['argparse'],
    dependency_links=[
        'git+https://github.com/svinota/pyroute2.git@master#egg=pyroute2',
    ],
    extras_require={
        'server': ['ordered-set', 'argparse', 'ipaddress', 'colorlog', 'geojson', 'futures',
                   'netifaces', 'networkx', 'blessings', 'py-dictdiffer', 'pyroute2', 'psutil', 'LatLon23',
                   'requests', 'msgpack-python', 'zmq'],
        'develop': ['pytest', 'sphinx', 'pep8', 'flake8'],
    },
    scripts=['mwcli'],
    entry_points={
        'console_scripts': ['mwserver=miniworld.service.rpc.RPCServer:main'],
    }
)
