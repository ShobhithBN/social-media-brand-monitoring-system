# Social Media Brand Monitoring & Crisis Detection System - Implementation Guide

This guide provides detailed instructions for implementing the Social Media Brand Monitoring & Crisis Detection System.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [API Access Setup](#api-access-setup)
3. [Database Setup](#database-setup)
4. [Implementation Details](#implementation-details)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Guidelines](#deployment-guidelines)

## Environment Setup

### Python Virtual Environment

```bash
# Create a new directory for the project
mkdir social_media_monitor
cd social_media_monitor

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Create basic project structure
mkdir -p config data/raw data/processed db/migrations collectors processors analysis dashboard/pages dashboard/components dashboard/assets/css dashboard/assets/img alerts reports/templates utils tests
```

### Dependencies

Create a `requirements.txt` file with the following dependencies:

```
# API Clients
praw==7.7.0  # Reddit API
newsapi-python==0.2.7  # News API
requests==2.28.2

# Data Processing
pandas==1.5.3
numpy==1.24.2

# NLP & Sentiment Analysis
nltk==3.8.1
textblob==0.17.1
spacy==3.5.1

# Database
sqlalchemy==2.0.5
psycopg2-binary==2.9.5
alembic==1.10.2  # For database migrations

# Dashboard
streamlit==1.19.0
plotly==5.13.1
matplotlib==3.7.1

# Utilities
python-dotenv==1.0.0
schedule==1.1.0  # For scheduling data collection
```

Install the dependencies:

```bash
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Download spaCy model
python -m spacy download en_core_web_sm
```

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
5. Note your:
   - Client ID: The string under "personal use script"
   - Client Secret: The string next to "secret"

### News API

1. Go to [News API](https://newsapi.org/register)
2. Fill in the registration form
3. Verify your email
4. Get your API key from the dashboard

### Environment Variables

Create a `.env` file in the project root:

```
# API Credentials
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=script:social_media_monitor:v1.0 (by /u/your_username)

NEWS_API_KEY=your_news_api_key

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=social_media_monitor
DB_USER=postgres
DB_PASSWORD=your_password

# Application Settings
LOG_LEVEL=INFO
COLLECTION_INTERVAL=3600  # in seconds
ALERT_THRESHOLD=0.7  # sentiment threshold for alerts
```

## Database Setup

### PostgreSQL Installation

1. Download and install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/)
2. Create a new database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE social_media_monitor;

# Exit
\q
```

### Database Schema

Create an initial migration script in `db/migrations/initial_schema.sql`:

```sql
-- Create tables

-- Mentions table
CREATE TABLE mentions (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- 'reddit', 'news', etc.
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    author VARCHAR(255),
    url TEXT,
    engagement INTEGER DEFAULT 0,
    brand VARCHAR(255) NOT NULL,
    title TEXT,
    subreddit VARCHAR(255),
    post_id VARCHAR(255),
    news_source VARCHAR(255)
);

-- Sentiment table
CREATE TABLE sentiment (
    id SERIAL PRIMARY KEY,
    mention_id INTEGER REFERENCES mentions(id),
    polarity FLOAT NOT NULL,
    subjectivity FLOAT NOT NULL,
    analyzed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    compound_score FLOAT,
    positive_score FLOAT,
    negative_score FLOAT,
    neutral_score FLOAT
);

-- Crisis alerts table
CREATE TABLE crisis_alerts (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity FLOAT NOT NULL,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'new',
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

-- Influencers table
CREATE TABLE influencers (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    followers INTEGER,
    impact_score FLOAT,
    brand_affinity VARCHAR(255),
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Competitive metrics table
CREATE TABLE competitive_metrics (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(255) NOT NULL,
    competitor VARCHAR(255) NOT NULL,
    sentiment_ratio FLOAT,
    mention_count INTEGER,
    engagement_rate FLOAT,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL
);

-- Create indexes
CREATE INDEX idx_mentions_brand ON mentions(brand);
CREATE INDEX idx_mentions_created_at ON mentions(created_at);
CREATE INDEX idx_sentiment_mention_id ON sentiment(mention_id);
CREATE INDEX idx_crisis_alerts_brand ON crisis_alerts(brand);
CREATE INDEX idx_crisis_alerts_status ON crisis_alerts(status);
CREATE INDEX idx_influencers_platform ON influencers(platform);
CREATE INDEX idx_competitive_metrics_brand ON competitive_metrics(brand);
```

Run the migration:

```bash
psql -U postgres -d social_media_monitor -f db/migrations/initial_schema.sql
```

## Implementation Details

### Database Connection

Create `db/connection.py`:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection details
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "social_media_monitor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Create SQLAlchemy engine
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Database Models

Create `db/models.py`:

```python
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .connection import Base

class Mention(Base):
    __tablename__ = "mentions"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    author = Column(String(255))
    url = Column(Text)
    engagement = Column(Integer, default=0)
    brand = Column(String(255), nullable=False, index=True)
    title = Column(Text)
    subreddit = Column(String(255))
    post_id = Column(String(255))
    news_source = Column(String(255))
    
    sentiment = relationship("Sentiment", back_populates="mention")

class Sentiment(Base):
    __tablename__ = "sentiment"
    
    id = Column(Integer, primary_key=True, index=True)
    mention_id = Column(Integer, ForeignKey("mentions.id"), index=True)
    polarity = Column(Float, nullable=False)
    subjectivity = Column(Float, nullable=False)
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    compound_score = Column(Float)
    positive_score = Column(Float)
    negative_score = Column(Float)
    neutral_score = Column(Float)
    
    mention = relationship("Mention", back_populates="sentiment")

class CrisisAlert(Base):
    __tablename__ = "crisis_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    severity = Column(Float, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="new", nullable=False, index=True)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)

class Influencer(Base):
    __tablename__ = "influencers"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False, index=True)
    followers = Column(Integer)
    impact_score = Column(Float)
    brand_affinity = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)

class CompetitiveMetric(Base):
    __tablename__ = "competitive_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(255), nullable=False, index=True)
    competitor = Column(String(255), nullable=False)
    sentiment_ratio = Column(Float)
    mention_count = Column(Integer)
    engagement_rate = Column(Float)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
```

### Data Collection

Create `collectors/base_collector.py`:

```python
from abc import ABC, abstractmethod
import logging
from datetime import datetime
from typing import List, Dict, Any

class BaseCollector(ABC):
    """Abstract base class for data collectors"""
    
    def __init__(self, brands: List[str], keywords: List[str] = None):
        self.brands = brands
        self.keywords = keywords or []
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        """Collect data from the source
        
        Returns:
            List of dictionaries containing collected data
        """
        pass
    
    def format_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format raw data into a standardized format
        
        Args:
            raw_data: Raw data from the source
            
        Returns:
            Formatted data dictionary
        """
        # Default implementation - override in subclasses
        return {
            "source": "unknown",
            "content": "",
            "created_at": datetime.utcnow(),
            "author": "",
            "url": "",
            "engagement": 0,
            "brand": "",
            "title": "",
        }
    
    def save_data(self, data: List[Dict[str, Any]]) -> None:
        """Save collected data
        
        Args:
            data: List of formatted data dictionaries
        """
        self.logger.info(f"Collected {len(data)} items")
        # Implementation will depend on storage method
        pass
```

Create `collectors/reddit_collector.py`:

```python
import os
import praw
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from .base_collector import BaseCollector

# Load environment variables
load_dotenv()

class RedditCollector(BaseCollector):
    """Collector for Reddit data"""
    
    def __init__(self, brands: List[str], keywords: List[str] = None, 
                 subreddits: List[str] = None, limit: int = 100):
        super().__init__(brands, keywords)
        self.subreddits = subreddits or []
        self.limit = limit
        
        # Initialize Reddit API client
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect data from Reddit
        
        Returns:
            List of dictionaries containing collected data
        """
        collected_data = []
        
        # Search for brand mentions
        for brand in self.brands:
            self.logger.info(f"Collecting data for brand: {brand}")
            
            # Search in specified subreddits
            if self.subreddits:
                for subreddit_name in self.subreddits:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Search for brand name in subreddit
                    for submission in subreddit.search(brand, limit=self.limit):
                        if self._is_relevant(submission.title, submission.selftext, brand):
                            collected_data.append(self.format_data({
                                "submission": submission,
                                "brand": brand
                            }))
                        
                        # Get comments
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments.list():
                            if self._is_relevant(comment.body, "", brand):
                                collected_data.append(self.format_data({
                                    "comment": comment,
                                    "submission": submission,
                                    "brand": brand
                                }))
            else:
                # Search across all of Reddit
                for submission in self.reddit.subreddit("all").search(brand, limit=self.limit):
                    if self._is_relevant(submission.title, submission.selftext, brand):
                        collected_data.append(self.format_data({
                            "submission": submission,
                            "brand": brand
                        }))
                    
                    # Get comments
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list():
                        if self._is_relevant(comment.body, "", brand):
                            collected_data.append(self.format_data({
                                "comment": comment,
                                "submission": submission,
                                "brand": brand
                            }))
        
        return collected_data
    
    def format_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Reddit data
        
        Args:
            raw_data: Raw data from Reddit
            
        Returns:
            Formatted data dictionary
        """
        if "comment" in raw_data:
            # Format comment data
            comment = raw_data["comment"]
            submission = raw_data["submission"]
            return {
                "source": "reddit",
                "content": comment.body,
                "created_at": datetime.fromtimestamp(comment.created_utc),
                "author": str(comment.author) if comment.author else "[deleted]",
                "url": f"https://www.reddit.com{comment.permalink}",
                "engagement": comment.score,
                "brand": raw_data["brand"],
                "title": submission.title,
                "subreddit": comment.subreddit.display_name,
                "post_id": submission.id
            }
        else:
            # Format submission data
            submission = raw_data["submission"]
            return {
                "source": "reddit",
                "content": submission.selftext,
                "created_at": datetime.fromtimestamp(submission.created_utc),
                "author": str(submission.author) if submission.author else "[deleted]",
                "url": submission.url,
                "engagement": submission.score,
                "brand": raw_data["brand"],
                "title": submission.title,
                "subreddit": submission.subreddit.display_name,
                "post_id": submission.id
            }
    
    def _is_relevant(self, title: str, content: str, brand: str) -> bool:
        """Check if the content is relevant to the brand
        
        Args:
            title: Title of the post
            content: Content of the post
            brand: Brand name
            
        Returns:
            True if relevant, False otherwise
        """
        # Simple relevance check - can be improved with NLP
        title_lower = title.lower()
        content_lower = content.lower()
        brand_lower = brand.lower()
        
        # Check if brand is mentioned
        if brand_lower in title_lower or brand_lower in content_lower:
            return True
        
        # Check if keywords are mentioned
        for keyword in self.keywords:
            if keyword.lower() in title_lower or keyword.lower() in content_lower:
                return True
        
        return False
```

Create `collectors/news_collector.py`:

```python
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from dotenv import load_dotenv
from .base_collector import BaseCollector

# Load environment variables
load_dotenv()

class NewsCollector(BaseCollector):
    """Collector for News API data"""
    
    def __init__(self, brands: List[str], keywords: List[str] = None, 
                 days_back: int = 7, language: str = "en"):
        super().__init__(brands, keywords)
        self.days_back = days_back
        self.language = language
        
        # Initialize News API client
        self.news_api = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect data from News API
        
        Returns:
            List of dictionaries containing collected data
        """
        collected_data = []
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.days_back)
        
        # Format dates for News API
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        # Search for brand mentions
        for brand in self.brands:
            self.logger.info(f"Collecting news for brand: {brand}")
            
            # Create query with brand and keywords
            query = brand
            if self.keywords:
                query += " AND (" + " OR ".join(self.keywords) + ")"
            
            # Get articles from News API
            try:
                response = self.news_api.get_everything(
                    q=query,
                    from_param=from_date,
                    to=to_date,
                    language=self.language,
                    sort_by="relevancy"
                )
                
                # Process articles
                if response["status"] == "ok":
                    for article in response["articles"]:
                        collected_data.append(self.format_data({
                            "article": article,
                            "brand": brand
                        }))
                else:
                    self.logger.error(f"News API error: {response}")
            
            except Exception as e:
                self.logger.error(f"Error collecting news for {brand}: {str(e)}")
        
        return collected_data
    
    def format_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format News API data
        
        Args:
            raw_data: Raw data from News API
            
        Returns:
            Formatted data dictionary
        """
        article = raw_data["article"]
        
        # Parse publication date
        try:
            published_at = datetime.strptime(article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
        except:
            published_at = datetime.utcnow()
        
        return {
            "source": "news",
            "content": article["description"] or "",
            "created_at": published_at,
            "author": article["author"] or "Unknown",
            "url": article["url"],
            "engagement": 0,  # News API doesn't provide engagement metrics
            "brand": raw_data["brand"],
            "title": article["title"],
            "news_source": article["source"]["name"] if article["source"] else "Unknown"
        }
```

### Sentiment Analysis

Create `analysis/sentiment.py`:

```python
from typing import Dict, Any, Tuple
from textblob import TextBlob
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

class SentimentAnalyzer:
    """Sentiment analysis for text content"""
    
    def __init__(self):
        # Ensure NLTK resources are downloaded
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        # Initialize VADER sentiment analyzer
        self.vader = SentimentIntensityAnalyzer()
    
    def analyze(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        if not text:
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "compound_score": 0.0,
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 0.0
            }
        
        # TextBlob sentiment analysis
        blob = TextBlob(text)
        polarity, subjectivity = blob.sentiment
        
        # VADER sentiment analysis
        vader_scores = self.vader.polarity_scores(text)
        
        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "compound_score": vader_scores["compound"],
            "positive_score": vader_scores["pos"],
            "negative_score": vader_scores["neg"],
            "neutral_score": vader_scores["neu"]
        }
    
    def get_sentiment_label(self, compound_score: float) -> str:
        """Get sentiment label based on compound score
        
        Args:
            compound_score: VADER compound sentiment score
            
        Returns:
            Sentiment label: "positive", "negative", or "neutral"
        """
        if compound_score >= 0.05:
            return "positive"
        elif compound_score <= -0.05:
            return "negative"
        else:
            return "neutral"
```

### Crisis Detection

Create `analysis/crisis_detector.py`:

```python
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class CrisisDetector:
    """Detects potential brand crises based on sentiment and volume"""
    
    def __init__(self, sentiment_threshold: float = -0.2, 
                 volume_threshold: float = 2.0,
                 time_window: int = 24):
        """
        Args:
            sentiment_threshold: Threshold for negative sentiment (lower is more negative)
            volume_threshold: Threshold for volume increase (multiplier of normal volume)
            time_window: Time window in hours for analysis
        """
        self.sentiment_threshold = sentiment_threshold
        self.volume_threshold = volume_threshold
        self.time_window = time_window
    
    def detect_crises(self, mentions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect potential crises from mentions
        
        Args:
            mentions: List of mentions with sentiment data
            
        Returns:
            List of detected crises
        """
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(mentions)
        
        if df.empty:
            return []
        
        # Ensure created_at is datetime
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Group by brand
        crises = []
        for brand, brand_df in df.groupby('brand'):
            # Sort by time
            brand_df = brand_df.sort_values('created_at')
            
            # Calculate time windows
            now = datetime.utcnow()
            window_end = now
            window_start = now - timedelta(hours=self.time_window)
            
            # Previous window for baseline
            prev_window_end = window_start
            prev_window_start = prev_window_end - timedelta(hours=self.time_window)
            
            # Filter mentions in current window
            current_window = brand_df[
                (brand_df['created_at'] >= window_start) & 
                (brand_df['created_at'] <= window_end)
            ]
            
            # Filter mentions in previous window
            previous_window = brand_df[
                (brand_df['created_at'] >= prev_window_start) & 
                (brand_df['created_at'] <= prev_window_end)
            ]
            
            # Skip if not enough data
            if len(current_window) < 5:
                continue
            
            # Calculate metrics
            current_sentiment = current_window['compound_score'].mean()
            current_volume = len(current_window)
            
            # Calculate baseline metrics
            baseline_sentiment = previous_window['compound_score'].mean() if len(previous_window) > 0 else 0
            baseline_volume = len(previous_window) if len(previous_window) > 0 else current_volume / 2
            
            # Calculate changes
            sentiment_change = current_sentiment - baseline_sentiment
            volume_ratio = current_volume / baseline_volume if baseline_volume > 0 else 1.0
            
            # Check for crisis conditions
            is_crisis = False
            crisis_reasons = []
            
            # Check sentiment threshold
            if current_sentiment < self.sentiment_threshold:
                is_crisis = True
                crisis_reasons.append(f"Negative sentiment: {current_sentiment:.2f}")
            
            # Check sentiment drop
            if sentiment_change < -0.1:
                is_crisis = True
                crisis_reasons.append(f"Sentiment drop: {sentiment_change:.2f}")
            
            # Check volume increase
            if volume_ratio > self.volume_threshold:
                is_crisis = True
                crisis_reasons.append(f"Volume spike: {volume_ratio:.1f}x normal")
            
            # If crisis detected, add to list
            if is_crisis:
                severity = self._calculate_severity(current_sentiment, sentiment_change, volume_ratio)
                
                crises.append({
                    "brand": brand,
                    "description": "Potential brand crisis: " + ", ".join(crisis_reasons),
                    "severity": severity,
                    "detected_at": now,
                    "status": "new"
                })
        
        return crises
    
    def _calculate_severity(self, sentiment: float, sentiment_change: float, 
                           volume_ratio: float) -> float:
        """Calculate crisis severity score
        
        Args:
            sentiment: Current sentiment score
            sentiment_change: Change in sentiment
            volume_ratio: Ratio of current volume to baseline
            
        Returns:
            Severity score (0-1, higher is more severe)
        """
        # Convert sentiment to 0-1 scale (more negative = higher severity)
        sentiment_factor = max(0, min(1, (-sentiment + 1) / 2))
        
        # Convert sentiment change to 0-1 scale
        change_factor = max(0, min(1, -sentiment_change / 2))
        
        # Convert volume ratio to 0-1 scale (capped at 5x)
        volume_factor = max(0, min(1, (volume_ratio - 1) / 4))
        
        # Weighted combination
        severity = (0.4 * sentiment_factor + 
                    0.4 * change_factor + 
                    0.2 * volume_factor)
        
        return severity
```

### Streamlit Dashboard

Create `dashboard/app.py`:

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project modules
from db.connection import get_db
from db.models import Mention, Sentiment, CrisisAlert, Influencer, CompetitiveMetric

# Set page config
st.set_page_config(
    page_title="Brand Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
st.sidebar.title("Brand Monitoring")

# Brand selection
brands = ["Apple", "Samsung", "Google", "Microsoft"]  # Replace with dynamic query
selected_brand = st.sidebar.selectbox("Select Brand", brands)

# Date range selection
date_ranges = {
    "Last 24 Hours": 1,
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "Last 90 Days": 90
}
selected_range = st.sidebar.selectbox("Time Period", list(date_ranges.keys()))
days_back = date_ranges[selected_range]

# Calculate date range
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=days_back)

# Source selection
sources = ["All", "Reddit", "News"]
selected_source = st.sidebar.selectbox("Data Source", sources)

# Main dashboard
st.title(f"{selected_brand} Brand Monitoring Dashboard")
st.subheader(f"{selected_range} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Sentiment Analysis", "Crisis Monitor", "Influencers"])

# Mock data for demonstration
# In a real implementation, this would be replaced with database queries

# Generate mock data
def generate_mock_data():
    # Date range
    dates = pd.date_range(start=start_date, end=end_date, freq='H')
    
    # Mentions data
    mentions_data = []
    for i in range(len(dates)):
        sentiment = -0.5 + i/len(dates)  # Trending from negative to positive
        volume = 10 + int(20 * (0.5 + 0.5 * np.sin(i