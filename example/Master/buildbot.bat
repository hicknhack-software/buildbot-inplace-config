@echo off
set BUILDBOTMASTERPATH=..\..\..\buildbot\master
set PYTHONPATH=%BUILDBOTMASTERPATH%;%PYTHONPATH%;..\..
python ..\..\..\buildbot\master\bin\buildbot %*
