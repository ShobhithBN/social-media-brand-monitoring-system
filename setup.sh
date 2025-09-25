#!/bin/bash

# Social Media Brand Monitoring & Crisis Detection System Setup Script

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Social Media Brand Monitoring & Crisis Detection System Setup${NC}"
echo "This script will help you set up the environment for the system."
echo

# Check if Docker is installed
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}Docker and Docker Compose are installed.${NC}"
    DOCKER_AVAILABLE=true
else
    echo -e "${YELLOW}Docker and/or Docker Compose are not installed.${NC}"
    echo "We'll set up the environment without Docker."
    DOCKER_AVAILABLE=false
fi

# Check if Python is installed
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}Python is installed.${NC}"
    PYTHON_VERSION=$(python3 --version)
    echo "Python version: $PYTHON_VERSION"
else
    echo -e "${RED}Python 3 is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

# Check if PostgreSQL is installed (if not using Docker)
if [ "$DOCKER_AVAILABLE" = false ]; then
    if command -v psql &> /dev/null; then
        echo -e "${GREEN}PostgreSQL is installed.${NC}"
    else
        echo -e "${RED}PostgreSQL is not installed. Please install PostgreSQL 13 or higher.${NC}"
        exit 1
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}.env file created. Please edit it with your API keys and credentials.${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Setup based on available tools
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo
    echo -e "${GREEN}Setting up with Docker...${NC}"
    
    # Build and start containers
    echo "Building and starting containers..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Docker containers started successfully.${NC}"
        echo
        echo -e "${GREEN}Setup completed successfully!${NC}"
        echo "You can access the dashboard at http://localhost:8501"
        echo
        echo "To stop the services, run: docker-compose down"
    else
        echo -e "${RED}Failed to start Docker containers.${NC}"
        exit 1
    fi
else
    echo
    echo -e "${GREEN}Setting up without Docker...${NC}"
    
    # Create virtual environment
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    # Install the package in development mode
    echo "Installing package in development mode..."
    pip install -e .
    
    # Set up database
    echo "Setting up database..."
    read -p "PostgreSQL username [postgres]: " PG_USER
    PG_USER=${PG_USER:-postgres}
    
    read -s -p "PostgreSQL password: " PG_PASSWORD
    echo
    
    # Create database
    echo "Creating database..."
    PGPASSWORD=$PG_PASSWORD psql -U $PG_USER -c "CREATE DATABASE social_media_monitor;" || true
    
    # Run migration script
    echo "Running migration script..."
    PGPASSWORD=$PG_PASSWORD psql -U $PG_USER -d social_media_monitor -f db/migrations/initial_schema.sql
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database setup completed successfully.${NC}"
        echo
        echo -e "${GREEN}Setup completed successfully!${NC}"
        echo "To start the data collection service, run: python main.py"
        echo "To start the dashboard, run: streamlit run dashboard/app.py"
    else
        echo -e "${RED}Failed to set up database.${NC}"
        exit 1
    fi
fi

echo
echo -e "${YELLOW}Important:${NC}"
echo "1. Make sure to edit the .env file with your API keys and credentials."
echo "2. Obtain Reddit API credentials from https://www.reddit.com/prefs/apps"
echo "3. Obtain News API key from https://newsapi.org/register"
echo
echo -e "${GREEN}Thank you for using Social Media Brand Monitoring & Crisis Detection System!${NC}"