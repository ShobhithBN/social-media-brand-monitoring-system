#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h db -p 5432 -U "$DB_USER" -d "$DB_NAME"; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database is ready!"

# Create database tables if they don't exist
echo "Creating database tables..."
python -c "
from db.unified_connection import engine, Base
from db.models import *
try:
    Base.metadata.create_all(bind=engine)
    print('Database tables created successfully')
except Exception as e:
    print(f'Error creating tables: {e}')
"

# Execute the command based on the first argument
case "$1" in
    "main.py")
        echo "Starting main monitoring application..."
        exec python main.py
        ;;
    "dashboard/app.py")
        echo "Starting dashboard..."
        exec streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=8501
        ;;
    "mcp_server.py")
        echo "Starting MCP server..."
        exec python mcp_server.py
        ;;
    *)
        echo "Starting: $@"
        exec python "$@"
        ;;
esac