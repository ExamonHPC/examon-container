# -*- coding: utf-8 -*-
from setuptools import setup

setup(name='examon-common',
      version='v0.2.4',
      description='Examon common utilities',
      url='http://github.com/fbeneventi/examon-common',
      author='Francesco Beneventi',
      author_email='francesco.beneventi@unibo.it',
      license='MIT',
      packages=['examon', 'examon.plugin', 'examon.utils', 'examon.db', 'examon.transport'],      
      install_requires=[
          'requests >= 2.21.0',
          'paho-mqtt == 1.4.0',
          'setuptools >= 40.6.3',
          'concurrent-log-handler >= 0.9.16',
          'pytest>=6.0.0',
          'pytest-mock>=3.0.0'
      ],
      zip_safe=False)
