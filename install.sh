#!/bin/bash

if [ $# -ne 1 ] 
then
  echo Usage: install.sh directory
  echo where the directory argument is the location of OpenSTV 1.5.
  echo Note: under MacOSX this is OpenSTV.app/Contents/Resources
  exit 1
fi

cp BltpBallotLoader.py $1/LoaderPlugins
cp projectBallots.py $1
cp projectElection.py $1/MethodPlugins


