# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from setuptools import setup, find_packages

version = '0.1'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

reqs = [
    'argparse',
    'metlog-py',
    'mozsvc',
    'requests',
    'zc.zk',
    'zktools',
]

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if not on_rtd:
    reqs.extend([
    ])

setup(name='qdo',
      version=version,
      description="Queuey worker library",
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          'Development Status :: 3 - Alpha',
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
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=reqs,
      tests_require=[
          'nose',
          ],
      test_suite='nose.collector',
      entry_points="""
      [console_scripts]
      qdo-worker = qdo.runner:run
      """,
      )
