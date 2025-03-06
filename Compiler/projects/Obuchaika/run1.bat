@echo off
chcp 65001 > log
del log

::set CPP_FILES="menu_functions.cpp menu_items.cpp main.cpp"
set EXE=Obuchaika.exe
::set CHARSET="-finput-charset=utf-8 -fexec-charset=windows-1251"

::if exist %EXE% del %EXE%

::g++ "%CHARSET%" "%CPP_FILES%" -o %EXE%

%EXE%