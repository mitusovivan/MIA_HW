@echo off

set BUILD_TYPE=Ninja
set BUILD_SUFFIX=Ninja

chcp 65001

set BUILD_FOLDER=build_%BUILD_SUFFIX%
set SOURCE_FOLDER=projects

if not exist %BUILD_FOLDER% mkdir %BUILD_FOLDER%

cd %BUILD_FOLDER%

cmake -G %BUILD_TYPE% ..\%SOURCE_FOLDER%
cmake --build .

copy ..\%SOURCE_FOLDER%\run.bat .\projects
copy ..\merge_sort\run.bat .\projects
copy ..\%SOURCE_FOLDER%\lib\googletest\run.bat .\projects
