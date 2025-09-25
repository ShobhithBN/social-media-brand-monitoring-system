@echo off
setlocal enabledelayedexpansion

:: Social Media Brand Monitoring & Crisis Detection System Setup Script for Windows

echo Social Media Brand Monitoring ^& Crisis Detection System Setup
echo This script will help you set up the environment for the system.
echo.

:: Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% == 0 (
    where docker-compose >nul 2>nul
    if %ERRORLEVEL% == 0 (
        echo Docker and Docker Compose are installed.
        set DOCKER_AVAILABLE=true
    ) else (
        echo Docker is installed, but Docker Compose is not.
        echo We'll set up the environment without Docker.
        set DOCKER_AVAILABLE=false
    )
) else (
    echo Docker is not installed.
    echo We'll set up the environment without Docker.
    set DOCKER_AVAILABLE=false
)

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% == 0 (
    echo Python is installed.
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo Python version: !PYTHON_VERSION!
) else (
    echo Python is not installed. Please install Python 3.9 or higher.
    exit /b 1
)

:: Check if PostgreSQL is installed (if not using Docker)
if "!DOCKER_AVAILABLE!"=="false" (
    where psql >nul 2>nul
    if %ERRORLEVEL% == 0 (
        echo PostgreSQL is installed.
    ) else (
        echo PostgreSQL is not installed. Please install PostgreSQL 13 or higher.
        exit /b 1
    )
)

:: Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo .env file created. Please edit it with your API keys and credentials.
) else (
    echo .env file already exists.
)

:: Setup based on available tools
if "!DOCKER_AVAILABLE!"=="true" (
    echo.
    echo Setting up with Docker...
    
    :: Build and start containers
    echo Building and starting containers...
    docker-compose up -d
    
    if %ERRORLEVEL% == 0 (
        echo Docker containers started successfully.
        echo.
        echo Setup completed successfully!
        echo You can access the dashboard at http://localhost:8501
        echo.
        echo To stop the services, run: docker-compose down
    ) else (
        echo Failed to start Docker containers.
        exit /b 1
    )
) else (
    echo.
    echo Setting up without Docker...
    
    :: Create virtual environment
    echo Creating virtual environment...
    python -m venv venv
    
    :: Activate virtual environment
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    
    :: Install dependencies
    echo Installing dependencies...
    pip install -r requirements.txt
    
    :: Install the package in development mode
    echo Installing package in development mode...
    pip install -e .
    
    :: Set up database
    echo Setting up database...
    set /p PG_USER=PostgreSQL username [postgres]: 
    if "!PG_USER!"=="" set PG_USER=postgres
    
    set /p PG_PASSWORD=PostgreSQL password: 
    
    :: Create database
    echo Creating database...
    set PGPASSWORD=!PG_PASSWORD!
    psql -U !PG_USER! -c "CREATE DATABASE social_media_monitor;" 2>nul
    
    :: Run migration script
    echo Running migration script...
    psql -U !PG_USER! -d social_media_monitor -f db/migrations/initial_schema.sql
    
    if %ERRORLEVEL% == 0 (
        echo Database setup completed successfully.
        echo.
        echo Setup completed successfully!
        echo To start the data collection service, run: python main.py
        echo To start the dashboard, run: streamlit run dashboard/app.py
    ) else (
        echo Failed to set up database.
        exit /b 1
    )
)

echo.
echo Important:
echo 1. Make sure to edit the .env file with your API keys and credentials.
echo 2. Obtain Reddit API credentials from https://www.reddit.com/prefs/apps
echo 3. Obtain News API key from https://newsapi.org/register
echo.
echo Thank you for using Social Media Brand Monitoring ^& Crisis Detection System!

endlocal