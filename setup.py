#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='omnibot',
    version='0.1.0',
    description='A multi-platform chatbot',
    long_description=long_description,
    long_description_content_type='text/markdown',
    # url='https://github.com/pypa/sampleproject',
    author='Alek Ratzloff',
    author_email='alekratz < at > gmail',
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='irc chatbot',
    packages=find_packages(exclude=['docs', 'tests', 'modules']),

    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['ucl==0.8.1', 'pydle==0.9.0', 'aiohttp==3.5.4', 'async-irc==0.1.7'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],

    #   $ pip install sampleproject[dev]
    #extras_require={
    #    'dev': ['check-manifest'],
    #    'test': ['coverage'],
    #},
    #package_data={
    #    'sample': ['package_data.dat'],
    #},
    #entry_points={
    #    'console_scripts': [
    #        'sample=sample:main',
    #    ],
    #},
    #project_urls={
        #'Bug Reports': 'https://github.com/pypa/sampleproject/issues',
        #'Funding': 'https://donate.pypi.org',
        #'Say Thanks!': 'http://saythanks.io/to/example',
        #'Source': 'https://github.com/pypa/sampleproject/',
    #},
)
