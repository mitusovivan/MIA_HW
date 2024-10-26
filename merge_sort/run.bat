@echo off
chcp 1251 > log
del log

set CPP_FILES="do_merge_sort.cpp io.cpp utility.cpp main.cpp"
set EXE=merge_sort.exe
set CHARSET="-finput-charset=utf-8 -fexec-charset=windows-1251"

if exist %EXE% del %EXE%

g++ "%CHARSET%" "%CPP_FILES%" -o %EXE%

%EXE%