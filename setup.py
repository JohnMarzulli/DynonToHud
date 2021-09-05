#!/usr/bin/env python

from setuptools import setup

installs = ['pyserial']

setup(
      name='DynonToHud',
      version='1.0.1',
      python_requires='>=3.5',
      description='Service to convert serial output to GDL-90 usable by StratuxHud',
      author='John Marzulli',
      author_email='john.marzulli@outlook.com',
      url='https://github.com/JohnMarzulli/DynonToHud',
      license='GPL V3',
      install_requires=installs)
