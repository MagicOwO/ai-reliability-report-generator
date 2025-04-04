@echo off
echo Setting up the report generator project...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python and try again.
    exit /b 1
)

REM Run the setup script
python setup.py

if %ERRORLEVEL% NEQ 0 (
    echo There was an error during the setup process.
    exit /b 1
)

echo.
echo Setup completed! Now activating the virtual environment...

REM Activate the virtual environment and run the report generator
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    
    echo.
    echo Virtual environment activated. You can now run:
    echo python -m src.report_generator
    
    set /p run_now=Would you like to run the report generator now? (y/n): 
    if /i "%run_now%"=="y" (
        echo.
        echo Running report generator...
        python -m src.report_generator
    )
) else (
    echo Could not find the virtual environment activation script.
    echo Please try running: .\.venv\Scripts\activate
)

echo.
echo Press any key to exit...
pause > nul 