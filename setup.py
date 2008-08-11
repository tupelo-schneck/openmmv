#!/usr/bin/env python
# USAGE: 
# python setup.py build
# python setup.py clean
# (Note: setup.cfg ensures that caml.so appears in this directory)

from distutils.core import setup, Extension

module1 = Extension('caml',
                    sources = ['caml.c'])

setup (name = 'caml',
       version = '1.0',
       description = 'Connect with OCaml to run election',
       ext_modules = [module1])
