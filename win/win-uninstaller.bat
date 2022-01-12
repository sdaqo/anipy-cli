@echo off

net session >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Administrator privilages detected 
    pause
) else (
    echo No administrator privilages detected
    pause 
    exit
)

cd ..
rmdir /s bin
echo If you want you can now delete anipy-cli in your path variable, this will not be done automaticly.
pause