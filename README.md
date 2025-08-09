# Social Media Brand Monitoring & Crisis Detection System

A comprehensive system for monitoring brand mentions across social media platforms and news sources, analyzing sentiment, detecting potential crises, and providing actionable insights through an interactive dashboard.

![Dashboard Preview](dashboard/assets/img/dashboard_preview.png)

## Features

- **Real-time Sentiment Tracking**: Monitor sentiment across Reddit and news sources
- **Automated Crisis Detection**: Get alerts when negative sentiment or volume spikes occur
- **Influencer Impact Analysis**: Identify key opinion leaders and measure their impact
- **Competitive Benchmarking**: Compare your brand's performance against competitors
- **Interactive Dashboard**: Visualize trends and insights through a Streamlit dashboard
- **Automated Reporting**: Generate periodic reports with actionable insights

## System Architecture

The system consists of several components:

1. **Data Collection Layer**: Collects data from Reddit and News APIs
2. **Data Processing Layer**: Cleans and preprocesses the collected data
3. **Analysis Layer**: Performs sentiment analysis, crisis detection, and other analyses
4. **Storage Layer**: Stores data in a PostgreSQL database
5. **Dashboard Layer**: Presents insights through a Streamlit dashboard

For more details, see the [Architecture Document](architecture.md).

## Project Structure

```
social_media_monitor/
│
├── collectors/           # Data collection modules
├── processors/           # Data processing modules
├── analysis/             # Analysis modules
├── db/                   # Database models and migrations
├── dashboard/            # Streamlit dashboard
├── alerts/               # Alerting system
├── reports/              # Reporting system
├── utils/                # Utility functions
└── tests/                # Unit and integration tests
```

For more details, see the [Project Structure Document](project_structure.md).

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Reddit API credentials
- News API key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/social-media-monitor.git
   cd social-media-monitor
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

5. Set up the database:
   ```bash
   # Create database
   psql -U postgres -c "CREATE DATABASE social_media_monitor;"
   
   # Run migration script
   psql -U postgres -d social_media_monitor -f db/migrations/initial_schema.sql
   ```

For more detailed installation instructions, see the [Implementation Guide](implementation_guide.md).

## Usage

### Running the Data Collection Service

```bash
python main.py
```

This will start the data collection service, which will periodically collect data from Reddit and News APIs, analyze sentiment, detect crises, and store the results in the database.

### Running the Dashboard

```bash
cd dashboard
streamlit run app.py
```

This will start the Streamlit dashboard, which you can access at http://localhost:8501.

### Configuration

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
5. Note your Client ID- D4dLR_kBEOhnyBdZvW12-Q and Client Secret- ze9ZkxuN_2MogskBxHEaM5y4VoA31w

### News API

1. Go to [News API](https://newsapi.org/register)
2. Fill in the registration form
3. Verify your email
4. Get your API key- 2ed4a40b77fe4494b0021c0a391bfc7e from the dashboard

## Development

### Testing

Run the tests:

```bash
pytest
```

For more detailed testing instructions, see the [Testing Strategy](testing_strategy.md).

### Deployment

For deployment instructions, see the [Deployment Guide](main_app_and_deployment.md).

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [PRAW](https://praw.readthedocs.io/) - Python Reddit API Wrapper
- [News API](https://newsapi.org/) - News API
- [TextBlob](https://textblob.readthedocs.io/) - Text processing and sentiment analysis
- [NLTK](https://www.nltk.org/) - Natural Language Toolkit
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [Streamlit](https://streamlit.io/) - Dashboard framework
- [Plotly](https://plotly.com/) - Interactive visualizations