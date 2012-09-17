# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

from setuptools import setup

version = '0.1'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

install_requires = []

if sys.version_info[:2] < (2, 7):
    install_requires += ['argparse']


setup(
    name='qdo',
    version=version,
    description="Queuey worker library",
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='',
    author='Mozilla Services',
    author_email='services-dev@mozilla.org',
    url='http://qdo.readthedocs.org/',
    license='MPLv2.0',
    packages=[
        'qdo',
        'qdo.tests',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'kazoo',
        'metlog-py',
        'queuey-py',
        'requests',
        'ujson',
    ] + install_requires,
    entry_points="""
    [console_scripts]
    qdo-worker = qdo.runner:run
    """,
    )
