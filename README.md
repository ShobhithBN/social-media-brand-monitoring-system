# Social Media Brand Monitoring & Crisis Detection System

A comprehensive system for monitoring brand mentions across social media platforms and news sources, analyzing sentiment, detecting potential crises, and providing actionable insights through an interactive dashboard.

## Features

- **Real-time Sentiment Tracking**: Monitor sentiment across Reddit and news sources
- **Automated Crisis Detection**: Get alerts when negative sentiment or volume spikes occur
- **Influencer Impact Analysis**: Identify key opinion leaders and measure their impact
- **Competitive Benchmarking**: Compare your brand's performance against competitors
- **Interactive Dashboard**: Visualize trends and insights through a Streamlit dashboard
- **Automated Reporting**: Generate periodic reports with actionable insights
- **Local Database Support**: SQLite database for local development and testing

## Prerequisites

- Python 3.9+
- PostgreSQL 13+ (for production) or SQLite (for local development)
- Reddit API credentials
- News API key

## Installation

### Option 1: Automated Setup (Recommended)

Use the provided setup script for automatic configuration:

```bash
# On Linux/macOS
chmod +x setup.sh
./setup.sh

# On Windows
setup.bat
```

The setup script will:
- Check for system requirements
- Set up Docker environment (if available) or local environment
- Create necessary configuration files
- Install dependencies
- Initialize the database

### Option 2: Using Docker

1. Ensure Docker and Docker Compose are installed
2. Create a `.env` file with your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Start all services:
   ```bash
   docker-compose up -d
   ```

4. Access the dashboard at http://localhost:8501

### Option 3: Local Development Setup

1. **Prerequisites**: Ensure Python 3.10+ is installed

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

4. **For local development** (uses SQLite):
   ```bash
   python setup_local_demo.py
   ```

5. **For production** (requires PostgreSQL):
   ```bash
   # Create database
   psql -U postgres -c "CREATE DATABASE social_media_monitor;"

   # Run migration script
   psql -U postgres -d social_media_monitor -f db/migrations/initial_schema.sql
   ```

6. **Install package**:
   ```bash
   pip install -e .
   ```

## Usage

### Running the System

#### Option 1: Complete Setup (Docker)
```bash
docker-compose up -d
# Starts all services: app, dashboard, database
```

#### Option 2: Individual Components

**Data Collection Service:**
```bash
# With Docker
docker-compose up -d app

# Local
python main.py
```

**Dashboard:**
```bash
# With Docker
docker-compose up -d dashboard

# Local
cd dashboard
streamlit run app.py
```

### Quick Demo

Run the local demo to see the system in action:
```bash
python setup_local_demo.py  # Sets up SQLite database with sample data
python run_demo.py          # Runs a demonstration
```

### Generating Reports

```python
from datetime import datetime, timedelta
from reports.generator import ReportGenerator

# Create report generator
generator = ReportGenerator()

# Generate report for the last 30 days
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=30)

generator.generate_report(
    brand="YourBrand",
    start_date=start_date,
    end_date=end_date,
    output_file="report.html"
)
```

## Configuration

You can configure the system by editing the `.env` file. Here are some key configuration options:

- `COLLECTION_INTERVAL`: Interval between data collection runs (in seconds)
- `ALERT_THRESHOLD`: Sentiment threshold for crisis alerts
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

## API Access Setup

### Reddit API

1. Go to [Reddit's App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App" button at the bottom
3. Fill in the details:
   - Name: Social Media Monitor
   - App type: Script
   - Description: Brand monitoring application
   - About URL: (Optional)
   - Redirect URI: http://localhost:8000/reddit_callback
4. Click "Create app" button
5. Note your Client ID and Client Secret

### News API

1. Go to [News API](https://newsapi.org/register)
2. Fill in the registration form
3. Verify your email
4. Get your API key from the dashboard

## Project Structure

```
social-media-brand-monitoring-system/
│
├── collectors/           # Data collection modules
│   ├── reddit_collector.py
│   └── news_collector.py
├── processors/           # Data processing modules
├── analysis/             # Analysis modules
│   ├── sentiment.py
│   └── crisis_detector.py
├── db/                   # Database models and migrations
│   ├── models.py
│   ├── connection.py
│   └── migrations/
├── dashboard/            # Streamlit dashboard
│   └── app.py
├── alerts/               # Alerting system
│   └── notifier.py
├── reports/              # Reporting system
├── utils/                # Utility functions
├── tests/                # Unit and integration tests
├── config/               # Configuration files
├── main.py              # Main application entry point
├── setup_local_demo.py  # Local demo setup
├── run_demo.py          # Demo runner
├── setup.sh             # Linux/macOS setup script
├── setup.bat            # Windows setup script
├── docker-compose.yml   # Docker services configuration
├── Dockerfile           # Docker image definition
└── requirements.txt     # Python dependencies
```

## Testing

Run the tests:

```bash
pytest
```

## Docker Deployment

The project includes comprehensive Docker configuration:

- `Dockerfile`: Multi-stage container image with all dependencies
- `docker-compose.yml`: Complete service orchestration (app, dashboard, database)
- `docker-entrypoint.sh`: Container initialization script

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.