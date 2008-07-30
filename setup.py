#!/usr/bin/env python

from distutils.core import setup, Extension
import shutil

module1 = Extension('caml',
                    sources = ['caml.c'])

setup (name = 'caml',
       version = '1.0',
       description = 'Connect with OCaml to run election',
       ext_modules = [module1])

shutil.copyfile("./build/lib.linux-i686-2.5/caml.so","./caml.so")
