# Testing Strategy for Social Media Brand Monitoring System

This document outlines the testing approach for the Social Media Brand Monitoring & Crisis Detection System to ensure reliability, accuracy, and performance.

## Testing Levels

### 1. Unit Testing

Unit tests verify that individual components work as expected in isolation.

#### Key Components to Test:

- **Data Collectors**
  - Test parsing and formatting of API responses
  - Test error handling for API failures
  - Test relevance filtering logic

- **Sentiment Analysis**
  - Test sentiment scoring with known positive/negative text
  - Test handling of edge cases (empty text, very short text)
  - Test sentiment labeling thresholds

- **Crisis Detection**
  - Test detection algorithms with simulated data
  - Test severity calculation logic
  - Test threshold-based alerting

- **Database Models**
  - Test model validation
  - Test relationships between models

#### Example Unit Tests:

```python
# tests/test_sentiment.py
import unittest
from analysis.sentiment import SentimentAnalyzer

class TestSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_positive_sentiment(self):
        text = "I absolutely love this product! It's amazing and works perfectly."
        result = self.analyzer.analyze(text)
        self.assertGreater(result["compound_score"], 0.5)
        self.assertGreater(result["polarity"], 0.5)
    
    def test_negative_sentiment(self):
        text = "This is terrible. I hate it and it doesn't work at all."
        result = self.analyzer.analyze(text)
        self.assertLess(result["compound_score"], -0.5)
        self.assertLess(result["polarity"], -0.5)
    
    def test_neutral_sentiment(self):
        text = "This is a product that exists."
        result = self.analyzer.analyze(text)
        self.assertGreater(result["neutral_score"], 0.8)
    
    def test_empty_text(self):
        result = self.analyzer.analyze("")
        self.assertEqual(result["compound_score"], 0.0)
        self.assertEqual(result["polarity"], 0.0)

# tests/test_crisis_detector.py
import unittest
from datetime import datetime, timedelta
from analysis.crisis_detector import CrisisDetector

class TestCrisisDetector(unittest.TestCase):
    def setUp(self):
        self.detector = CrisisDetector(
            sentiment_threshold=-0.2,
            volume_threshold=2.0,
            time_window=24
        )
    
    def test_crisis_detection_negative_sentiment(self):
        # Create mock data with negative sentiment
        now = datetime.utcnow()
        mentions = [
            {
                "brand": "TestBrand",
                "created_at": now - timedelta(hours=i),
                "compound_score": -0.6,  # Very negative
                "engagement": 10
            }
            for i in range(10)  # 10 mentions in the last 10 hours
        ]
        
        crises = self.detector.detect_crises(mentions)
        
        self.assertEqual(len(crises), 1)
        self.assertEqual(crises[0]["brand"], "TestBrand")
        self.assertGreater(crises[0]["severity"], 0.5)
    
    def test_crisis_detection_volume_spike(self):
        # Create mock data with volume spike
        now = datetime.utcnow()
        
        # Previous period (few mentions)
        previous_mentions = [
            {
                "brand": "TestBrand",
                "created_at": now - timedelta(hours=30 + i),
                "compound_score": 0.1,  # Slightly positive
                "engagement": 5
            }
            for i in range(3)  # Only 3 mentions in the previous period
        ]
        
        # Current period (many mentions)
        current_mentions = [
            {
                "brand": "TestBrand",
                "created_at": now - timedelta(hours=i),
                "compound_score": 0.1,  # Still positive
                "engagement": 5
            }
            for i in range(20)  # 20 mentions in the current period (volume spike)
        ]
        
        mentions = previous_mentions + current_mentions
        
        crises = self.detector.detect_crises(mentions)
        
        self.assertEqual(len(crises), 1)
        self.assertEqual(crises[0]["brand"], "TestBrand")
        self.assertIn("Volume spike", crises[0]["description"])
```

### 2. Integration Testing

Integration tests verify that components work together correctly.

#### Key Integrations to Test:

- **Data Collection → Database**
  - Test that collected data is correctly stored in the database
  - Test handling of duplicate data

- **Database → Sentiment Analysis**
  - Test retrieval and analysis of stored mentions

- **Sentiment Analysis → Crisis Detection**
  - Test that sentiment scores are correctly used for crisis detection

- **Crisis Detection → Alerting**
  - Test that detected crises trigger appropriate alerts

#### Example Integration Tests:

```python
# tests/test_data_pipeline.py
import unittest
from unittest.mock import patch, MagicMock
from collectors.reddit_collector import RedditCollector
from db.connection import SessionLocal
from db.models import Mention, Sentiment

class TestDataPipeline(unittest.TestCase):
    def setUp(self):
        # Use test database
        self.db = SessionLocal()
        
        # Mock Reddit API
        self.praw_mock = patch('collectors.reddit_collector.praw.Reddit').start()
        self.reddit_instance = MagicMock()
        self.praw_mock.return_value = self.reddit_instance
        
        # Create collector
        self.collector = RedditCollector(
            brands=["TestBrand"],
            keywords=["test"],
            subreddits=["testsubreddit"]
        )
    
    def tearDown(self):
        patch.stopall()
        self.db.close()
    
    def test_collect_and_store(self):
        # Mock Reddit API response
        mock_submission = MagicMock()
        mock_submission.title = "TestBrand is amazing"
        mock_submission.selftext = "This is a test post about TestBrand"
        mock_submission.created_utc = 1625097600  # 2021-07-01
        mock_submission.author = "testuser"
        mock_submission.url = "https://reddit.com/r/testsubreddit/comments/123456"
        mock_submission.score = 42
        mock_submission.id = "123456"
        mock_submission.subreddit.display_name = "testsubreddit"
        
        # Mock comments
        mock_submission.comments.list.return_value = []
        
        # Set up mock search results
        mock_subreddit = MagicMock()
        mock_subreddit.search.return_value = [mock_submission]
        self.reddit_instance.subreddit.return_value = mock_subreddit
        
        # Collect data
        data = self.collector.collect()
        
        # Verify data was collected
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["brand"], "TestBrand")
        self.assertEqual(data[0]["title"], "TestBrand is amazing")
        
        # Store data in database
        mention = Mention(
            source=data[0]["source"],
            content=data[0]["content"],
            created_at=data[0]["created_at"],
            author=data[0]["author"],
            url=data[0]["url"],
            engagement=data[0]["engagement"],
            brand=data[0]["brand"],
            title=data[0]["title"],
            subreddit=data[0]["subreddit"],
            post_id=data[0]["post_id"]
        )
        
        self.db.add(mention)
        self.db.commit()
        
        # Verify data was stored
        stored_mention = self.db.query(Mention).filter(
            Mention.brand == "TestBrand",
            Mention.post_id == "123456"
        ).first()
        
        self.assertIsNotNone(stored_mention)
        self.assertEqual(stored_mention.title, "TestBrand is amazing")
        self.assertEqual(stored_mention.engagement, 42)
```

### 3. End-to-End Testing

End-to-end tests verify that the entire system works together correctly.

#### Key Scenarios to Test:

- **Complete Data Flow**
  - Test the entire pipeline from data collection to dashboard display

- **Crisis Detection and Alerting**
  - Test that a simulated crisis is detected and alerts are sent

- **Dashboard Functionality**
  - Test that the dashboard displays correct data and responds to user interactions

#### Example End-to-End Test:

```python
# tests/test_e2e.py
import unittest
import time
from datetime import datetime, timedelta
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the application in test mode
        cls.app_process = subprocess.Popen(
            ["python", "main.py", "--test"],
            env={"DB_NAME": "social_media_monitor_test"}
        )
        
        # Start the dashboard in test mode
        cls.dashboard_process = subprocess.Popen(
            ["streamlit", "run", "dashboard/app.py", "--", "--test"],
            env={"DB_NAME": "social_media_monitor_test"}
        )
        
        # Wait for services to start
        time.sleep(5)
        
        # Initialize Selenium WebDriver
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10)
    
    @classmethod
    def tearDownClass(cls):
        # Stop the browser
        cls.driver.quit()
        
        # Stop the application
        cls.app_process.terminate()
        cls.dashboard_process.terminate()
    
    def test_dashboard_loads(self):
        # Navigate to dashboard
        self.driver.get("http://localhost:8501")
        
        # Check that dashboard loads
        title = self.driver.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Brand Monitoring Dashboard", title)
        
        # Check that sidebar has brand selection
        brand_select = self.driver.find_element(By.XPATH, "//div[contains(@data-testid, 'stSelectbox')]")
        self.assertIsNotNone(brand_select)
    
    def test_crisis_detection(self):
        # Inject test data via API
        now = datetime.utcnow()
        
        # Create mentions with negative sentiment
        for i in range(20):
            requests.post(
                "http://localhost:5000/api/test/mentions",
                json={
                    "source": "test",
                    "content": "This is terrible! I hate this product!",
                    "created_at": (now - timedelta(hours=i)).isoformat(),
                    "author": f"testuser{i}",
                    "url": f"https://example.com/post{i}",
                    "engagement": 10,
                    "brand": "TestBrand",
                    "title": "Negative Post",
                    "sentiment": {
                        "compound_score": -0.8,
                        "polarity": -0.7,
                        "subjectivity": 0.9
                    }
                }
            )
        
        # Trigger crisis detection
        requests.post("http://localhost:5000/api/test/detect-crises")
        
        # Navigate to crisis monitor tab
        self.driver.get("http://localhost:8501")
        crisis_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Crisis Monitor')]")
        crisis_tab.click()
        
        # Wait for crisis alert to appear
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'TestBrand')]"))
        )
        
        # Check that crisis is displayed
        crisis_element = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Potential brand crisis')]")
        self.assertIsNotNone(crisis_element)
        self.assertIn("Negative sentiment", crisis_element.text)
```

### 4. Performance Testing

Performance tests verify that the system can handle the expected load.

#### Key Metrics to Test:

- **Data Collection Performance**
  - Test collection speed with large number of mentions
  - Test API rate limit handling

- **Database Performance**
  - Test query performance with large datasets
  - Test concurrent read/write operations

- **Dashboard Performance**
  - Test dashboard loading time with large datasets
  - Test real-time update performance

#### Example Performance Test:

```python
# tests/test_performance.py
import unittest
import time
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Mention, Sentiment
from dashboard.app import load_data

class TestPerformance(unittest.TestCase):
    def setUp(self):
        # Create test database
        self.engine = create_engine("postgresql://postgres:postgres@localhost/social_media_monitor_test")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        
        # Generate test data
        self.generate_test_data(10000)  # 10,000 mentions
    
    def tearDown(self):
        # Clean up test data
        self.db.execute("TRUNCATE mentions, sentiment CASCADE")
        self.db.commit()
        self.db.close()
    
    def generate_test_data(self, count):
        """Generate test data for performance testing"""
        brands = ["Brand1", "Brand2", "Brand3", "Brand4"]
        sources = ["reddit", "news"]
        
        # Generate mentions and sentiment
        now = datetime.utcnow()
        
        for i in range(count):
            # Create mention
            mention = Mention(
                source=random.choice(sources),
                content=f"Test content {i}",
                created_at=now - timedelta(hours=random.randint(0, 720)),
                author=f"user{i}",
                url=f"https://example.com/post{i}",
                engagement=random.randint(0, 1000),
                brand=random.choice(brands),
                title=f"Test post {i}"
            )
            
            self.db.add(mention)
            
            # Flush to get mention ID
            self.db.flush()
            
            # Create sentiment
            sentiment = Sentiment(
                mention_id=mention.id,
                polarity=random.uniform(-1.0, 1.0),
                subjectivity=random.uniform(0.0, 1.0),
                compound_score=random.uniform(-1.0, 1.0),
                positive_score=random.uniform(0.0, 1.0),
                negative_score=random.uniform(0.0, 1.0),
                neutral_score=random.uniform(0.0, 1.0)
            )
            
            self.db.add(sentiment)
        
        # Commit changes
        self.db.commit()
    
    def test_query_performance(self):
        """Test query performance with large dataset"""
        # Measure time to query all mentions for a brand
        start_time = time.time()
        
        mentions = self.db.query(Mention).filter(
            Mention.brand == "Brand1"
        ).all()
        
        query_time = time.time() - start_time
        
        print(f"Query time for all Brand1 mentions: {query_time:.4f} seconds")
        self.assertLess(query_time, 1.0)  # Should be less than 1 second
    
    def test_dashboard_data_loading(self):
        """Test dashboard data loading performance"""
        # Measure time to load dashboard data
        start_time = time.time()
        
        # Call dashboard data loading function
        data = load_data(
            brand="Brand1",
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            source="All"
        )
        
        load_time = time.time() - start_time
        
        print(f"Dashboard data loading time: {load_time:.4f} seconds")
        self.assertLess(load_time, 3.0)  # Should be less than 3 seconds
```

## Test Automation

### Continuous Integration

Set up GitHub Actions to run tests automatically on every push and pull request:

```yaml
# .github/workflows/test.yml
name: Run Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: social_media_monitor_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=./ --cov-report=xml
      env:
        DB_HOST: localhost
        DB_PORT: 5432
        DB_NAME: social_media_monitor_test
        DB_USER: postgres
        DB_PASSWORD: postgres
    
    - name: Upload coverage report
      uses: codecov/codecov-action@v1
```

### Local Test Runner

Create a script to run tests locally:

```python
# run_tests.py
import argparse
import subprocess
import os

def run_tests(test_type=None, coverage=False):
    """Run tests based on type"""
    # Set environment variables for testing
    env = os.environ.copy()
    env["DB_NAME"] = "social_media_monitor_test"
    
    # Build command
    cmd = ["pytest"]
    
    if coverage:
        cmd.extend(["--cov=./", "--cov-report=term"])
    
    if test_type == "unit":
        cmd.append("tests/test_*.py")
    elif test_type == "integration":
        cmd.append("tests/test_*_integration.py")
    elif test_type == "e2e":
        cmd.append("tests/test_e2e.py")
    elif test_type == "performance":
        cmd.append("tests/test_performance.py")
    
    # Run tests
    subprocess.run(cmd, env=env)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests for Social Media Monitor")
    parser.add_argument("--type", choices=["unit", "integration", "e2e", "performance"],
                        help="Type of tests to run")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    run_tests(args.type, args.coverage)
```

## Test Data Management

### Mock Data Generation

Create utilities for generating mock data for testing:

```python
# tests/utils/mock_data.py
import random
from datetime import datetime, timedelta

def generate_mock_mentions(count, brands=None, start_date=None, end_date=None):
    """Generate mock mentions for testing
    
    Args:
        count: Number of mentions to generate
        brands: List of brands (default: ["Brand1", "Brand2"])
        start_date: Start date for mentions (default: 30 days ago)
        end_date: End date for mentions (default: now)
        
    Returns:
        List of mention dictionaries
    """
    brands = brands or ["Brand1", "Brand2"]
    end_date = end_date or datetime.utcnow()
    start_date = start_date or (end_date - timedelta(days=30))
    
    sources = ["reddit", "news"]
    
    mentions = []
    
    for i in range(count):
        # Random date between start and end
        date_range = (end_date - start_date).total_seconds()
        random_seconds = random.randint(0, int(date_range))
        created_at = start_date + timedelta(seconds=random_seconds)
        
        # Random sentiment (weighted towards neutral)
        sentiment = random.choice([
            random.uniform(-1.0, -0.3),  # Negative
            random.uniform(-0.3, 0.3),   # Neutral
            random.uniform(0.3, 1.0),    # Positive
            random.uniform(-0.3, 0.3),   # Neutral
            random.uniform(-0.3, 0.3),   # Neutral
        ])
        
        mentions.append({
            "source": random.choice(sources),
            "content": f"Test content {i} with sentiment {sentiment:.2f}",
            "created_at": created_at,
            "author": f"user{i}",
            "url": f"https://example.com/post{i}",
            "engagement": random.randint(0, 1000),
            "brand": random.choice(brands),
            "title": f"Test post {i}",
            "compound_score": sentiment
        })
    
    return mentions

def generate_crisis_data(brand, severity=0.8, count=20):
    """Generate data that should trigger a crisis
    
    Args:
        brand: Brand name
        severity: Crisis severity (0-1)
        count: Number of mentions to generate
        
    Returns:
        List of mention dictionaries
    """
    now = datetime.utcnow()
    
    # Generate negative mentions in the last 24 hours
    mentions = []
    
    for i in range(count):
        mentions.append({
            "source": "reddit",
            "content": f"This is terrible! I hate {brand}! Worst product ever!",
            "created_at": now - timedelta(hours=random.randint(0, 23)),
            "author": f"angry_user{i}",
            "url": f"https://example.com/angry_post{i}",
            "engagement": random.randint(50, 500),  # High engagement
            "brand": brand,
            "title": f"Terrible experience with {brand}",
            "compound_score": random.uniform(-1.0, -0.7)  # Very negative
        })
    
    return mentions
```

### Test Database Setup

Create utilities for setting up and tearing down test databases:

```python
# tests/utils/db_setup.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Mention, Sentiment

def setup_test_db(db_url="postgresql://postgres:postgres@localhost/social_media_monitor_test"):
    """Set up test database
    
    Args:
        db_url: Database URL
        
    Returns:
        SQLAlchemy session
    """
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def teardown_test_db(session):
    """Clean up test database
    
    Args:
        session: SQLAlchemy session
    """
    session.execute("TRUNCATE mentions, sentiment, crisis_alerts, influencers, competitive_metrics CASCADE")
    session.commit()
    session.close()

def populate_test_data(session, mentions):
    """Populate test database with mentions
    
    Args:
        session: SQLAlchemy session
        mentions: List of mention dictionaries
    """
    for item in mentions:
        # Create mention
        mention = Mention(
            source=item["source"],
            content=item["content"],
            created_at=item["created_at"],
            author=item["author"],
            url=item["url"],
            engagement=item["engagement"],
            brand=item["brand"],
            title=item["title"]
        )
        
        session.add(mention)
        session.flush()
        
        # Create sentiment
        sentiment = Sentiment(
            mention_id=mention.id,
            polarity=item.get("polarity", item["compound_score"]),
            subjectivity=item.get("subjectivity", 0.5),
            compound_score=item["compound_score"],
            positive_score=item.get("positive_score", max(0, item["compound_score"])),
            negative_score=item.get("negative_score", max(0, -item["compound_score"])),
            neutral_score=item.get("neutral_score", 0.5)
        )
        
        session.add(sentiment)
    
    session.commit()
```

## Test Documentation

### Test Plan

Create a comprehensive test plan document:

1. **Test Objectives**
   - Verify functionality of all system components
   - Ensure data accuracy and reliability
   - Validate performance under expected load

2. **Test Scope**
   - Components to be tested
   - Features to be tested
   - Features not to be tested

3. **Test Schedule**
   - Unit tests: Before each commit
   - Integration tests: Daily
   - End-to-end tests: Weekly
   - Performance tests: Monthly

4. **Test Deliverables**
   - Test cases
   - Test scripts
   - Test reports
   - Coverage reports

5. **Test Resources**
   - Test environment
   - Test data
   - Test tools

### Test Reports

Generate test reports after each test run:

```python
# tests/utils/report.py
import json
import datetime

def generate_test_report(test_results, output_file="test_report.json"):
    """Generate test report
    
    Args:
        test_results: Dictionary of test results
        output_file: Output file path
    """
    report = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "results": test_results,
        "summary": {
            "total": len(test_results),
            "passed": sum(1 for r in test_results.values() if r["status"] == "passed"),
            "failed": sum(1 for r in test_results.values() if r["status"] == "failed"),
            "skipped": sum(1 for r in test_results.values() if r["status"] == "skipped")
        }
    }
    
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)
    
    return report
```

## Conclusion

This testing strategy provides a comprehensive approach to testing the Social Media Brand Monitoring & Crisis Detection System. By implementing these tests, we can ensure that the system functions correctly, performs well, and provides accurate insights.

The key aspects of this strategy are:

1. **Comprehensive Test Coverage**: Testing all components and their interactions
2. **Automated Testing**: Running tests automatically to catch issues early
3. **Performance Testing**: Ensuring the system can handle the expected load
4. **Test Data Management**: Generating realistic test data for thorough testing
5. **Continuous Integration**: Integrating testing into the development workflow

By following this strategy, we can build a reliable and robust system that meets the requirements and provides value to users.