@echo off
setlocal EnableDelayedExpansion

set BUILD_TYPE=Ninja
set BUILD_SUFFIX=Ninja

chcp 65001

set BUILD_FOLDER=build_%BUILD_SUFFIX%
set SOURCE_FOLDER=projects

if not exist %BUILD_FOLDER% mkdir %BUILD_FOLDER%

cd %BUILD_FOLDER%

cmake -G %BUILD_TYPE% ..\%SOURCE_FOLDER%
cmake --build .

set arr[0].file=run.bat
set arr[1].file=run1.bat

set arr[0].folder=merge_sort
set arr[1].folder=Obuchaika

copy ..\%SOURCE_FOLDER%\!arr[0].folder!\!arr[0].file! .\!arr[0].folder!
copy ..\%SOURCE_FOLDER%\!arr[1].folder!\!arr[1].file! .\!arr[1].folder!


copy ..\run_test.bat .