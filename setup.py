#!/usr/bin/env python

from setuptools import setup

setup(name='trialexplorer',
      version='0.0.1',
      description='Toolkit used for studying data on clinicaltrials.gov',
      author='Sylvain Chassang, Julia Kempe, Andrew Hopen, Anna Khazan, Rong Feng',
      author_email='chassang@nyu.edu, kempe@nyu.edu, ah182@nyu.edu, ak2962@nyu.edu, rmfeng@gmail.com',
      packages=['pdaactconn', 'trialexplorer'],
      install_requires=[
          'numpy==1.16.4',
          'pandas==0.25.1',
          'pytest==5.1.2',
          'pytest-cov==2.7.1',
          'psycopg2>=2.7'
        ]
      )
