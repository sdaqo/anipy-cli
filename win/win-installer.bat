@echo off

:: check for admin privilages
net session >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Administrator privilages detected 
    pause
) else (
    echo No administrator privilages detected
    pause 
    exit
)

:: install python libs
cd ..
pip install -r requirements.txt 

:: folder with the bat file
set bin_folder=%cd%\bin
set bat_file=%cd%\bin\anipy-cli.bat

:: Get main.py location
set anipy_path=%cd%\main.py
if not exist "%anipy_path%" echo "main.py not found"
echo Found %anipy_path%

:: create bin folder 
if not exist "%bin_folder%" mkdir "%bin_folder%"
echo Created %bin_folder%

:: create anipy-cli.bat 
echo @echo off > %bat_file%
echo python %anipy_path% %%1 %%2 %%3 %%4 >> %bat_file%
echo Created %bat_file%

:: add bin folder to path
set PATH=%PATH%;%bin_folder%
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v "Path" /t REG_EXPAND_SZ /d "%PATH%" /f
echo Added anipy-cli to System-Path
pause


