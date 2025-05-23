@echo off
setlocal EnableDelayedExpansion

set BUILD_TYPE=Ninja
set BUILD_SUFFIX=Ninja

chcp 65001

set BUILD_FOLDER=build_%BUILD_SUFFIX%
set SOURCE_FOLDER=project

if not exist %BUILD_FOLDER% mkdir %BUILD_FOLDER%

cd %BUILD_FOLDER%

cmake -G %BUILD_TYPE% ..\%SOURCE_FOLDER%
cmake --build .


copy ..\run_test.bat .