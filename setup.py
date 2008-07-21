#!/usr/bin/env python

from distutils.core import setup, Extension
import shutil

module1 = Extension('election',
                    sources = ['election.c'])

setup (name = 'election',
       version = '1.0',
       description = 'Run an election',
       ext_modules = [module1])

shutil.copyfile("./build/lib.linux-i686-2.5/election.so","./election.so")
