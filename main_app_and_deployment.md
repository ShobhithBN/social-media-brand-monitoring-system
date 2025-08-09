# Main Application and Deployment Guide

## Main Application Entry Point

Create `main.py` in the project root:

```python
import os
import logging
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy.orm import Session

# Import project modules
from db.connection import engine, SessionLocal, Base
from db.models import Mention, Sentiment, CrisisAlert
from collectors.reddit_collector import RedditCollector
from collectors.news_collector import NewsCollector
from analysis.sentiment import SentimentAnalyzer
from analysis.crisis_detector import CrisisDetector
from alerts.notifier import AlertNotifier

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

# Configuration
BRANDS = ["Apple", "Samsung", "Google", "Microsoft"]  # Replace with your target brands
KEYWORDS = ["smartphone", "laptop", "tablet", "tech"]  # Replace with relevant keywords
SUBREDDITS = ["technology", "gadgets", "apple", "android"]  # Replace with relevant subreddits
COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", 3600))  # in seconds

def collect_and_process_data():
    """Collect and process data from all sources"""
    logger.info("Starting data collection and processing")
    
    # Create collectors
    reddit_collector = RedditCollector(BRANDS, KEYWORDS, SUBREDDITS)
    news_collector = NewsCollector(BRANDS, KEYWORDS)
    
    # Collect data
    reddit_data = reddit_collector.collect()
    news_data = news_collector.collect()
    
    # Combine data
    all_data = reddit_data + news_data
    
    if not all_data:
        logger.warning("No data collected")
        return
    
    logger.info(f"Collected {len(all_data)} mentions")
    
    # Process and store data
    process_data(all_data)
    
    logger.info("Data collection and processing completed")

def process_data(data):
    """Process and store collected data"""
    # Create sentiment analyzer
    sentiment_analyzer = SentimentAnalyzer()
    
    # Create crisis detector
    crisis_detector = CrisisDetector()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Process each mention
        for item in data:
            # Check if mention already exists
            existing = db.query(Mention).filter(
                Mention.source == item["source"],
                Mention.url == item["url"]
            ).first()
            
            if existing:
                # Skip if already exists
                continue
            
            # Create new mention
            mention = Mention(
                source=item["source"],
                content=item["content"],
                created_at=item["created_at"],
                author=item["author"],
                url=item["url"],
                engagement=item["engagement"],
                brand=item["brand"],
                title=item["title"],
                subreddit=item.get("subreddit"),
                post_id=item.get("post_id"),
                news_source=item.get("news_source")
            )
            
            # Add to database
            db.add(mention)
            db.flush()  # Flush to get mention ID
            
            # Analyze sentiment
            sentiment_scores = sentiment_analyzer.analyze(item["content"])
            
            # Create sentiment record
            sentiment = Sentiment(
                mention_id=mention.id,
                polarity=sentiment_scores["polarity"],
                subjectivity=sentiment_scores["subjectivity"],
                compound_score=sentiment_scores["compound_score"],
                positive_score=sentiment_scores["positive_score"],
                negative_score=sentiment_scores["negative_score"],
                neutral_score=sentiment_scores["neutral_score"]
            )
            
            # Add to database
            db.add(sentiment)
        
        # Commit changes
        db.commit()
        
        # Detect crises
        detect_crises(db)
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        db.rollback()
    finally:
        db.close()

def detect_crises(db: Session):
    """Detect potential crises from recent data"""
    try:
        # Get recent mentions with sentiment
        recent_mentions = db.query(Mention, Sentiment).join(
            Sentiment, Mention.id == Sentiment.mention_id
        ).filter(
            Mention.created_at >= datetime.utcnow() - pd.Timedelta(hours=48)
        ).all()
        
        # Convert to list of dictionaries
        mentions_data = []
        for mention, sentiment in recent_mentions:
            mentions_data.append({
                "brand": mention.brand,
                "created_at": mention.created_at,
                "compound_score": sentiment.compound_score,
                "engagement": mention.engagement
            })
        
        # Create crisis detector
        crisis_detector = CrisisDetector()
        
        # Detect crises
        crises = crisis_detector.detect_crises(mentions_data)
        
        if crises:
            logger.info(f"Detected {len(crises)} potential crises")
            
            # Store crises
            for crisis in crises:
                # Check if similar crisis already exists
                existing = db.query(CrisisAlert).filter(
                    CrisisAlert.brand == crisis["brand"],
                    CrisisAlert.status == "new",
                    CrisisAlert.detected_at >= datetime.utcnow() - pd.Timedelta(hours=24)
                ).first()
                
                if existing:
                    # Skip if similar crisis already exists
                    continue
                
                # Create new crisis alert
                crisis_alert = CrisisAlert(
                    brand=crisis["brand"],
                    description=crisis["description"],
                    severity=crisis["severity"],
                    detected_at=crisis["detected_at"],
                    status=crisis["status"]
                )
                
                # Add to database
                db.add(crisis_alert)
            
            # Commit changes
            db.commit()
            
            # Send notifications
            send_crisis_alerts(crises)
    
    except Exception as e:
        logger.error(f"Error detecting crises: {str(e)}")
        db.rollback()

def send_crisis_alerts(crises):
    """Send notifications for detected crises"""
    try:
        # Create notifier
        notifier = AlertNotifier()
        
        # Send notifications
        for crisis in crises:
            notifier.send_alert(crisis)
    
    except Exception as e:
        logger.error(f"Error sending crisis alerts: {str(e)}")

def run_scheduler():
    """Run scheduler for periodic data collection"""
    logger.info("Starting scheduler")
    
    # Schedule data collection
    schedule.every(COLLECTION_INTERVAL).seconds.do(collect_and_process_data)
    
    # Run initial collection
    collect_and_process_data()
    
    # Run scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    logger.info("Starting Social Media Brand Monitoring System")
    run_scheduler()
```

## Deployment Guidelines

### Local Deployment

1. Set up the environment:
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd social_media_monitor
   
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

2. Set up the database:
   ```bash
   # Create database
   psql -U postgres -c "CREATE DATABASE social_media_monitor;"
   
   # Run migration script
   psql -U postgres -d social_media_monitor -f db/migrations/initial_schema.sql
   ```

3. Run the application:
   ```bash
   # Run data collection and processing
   python main.py
   
   # In a separate terminal, run the dashboard
   cd dashboard
   streamlit run app.py
   ```

### Docker Deployment

1. Create a `Dockerfile` in the project root:
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   # Install dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application code
   COPY . .
   
   # Expose ports
   EXPOSE 8501
   
   # Set environment variables
   ENV PYTHONPATH=/app
   
   # Run the application
   CMD ["python", "main.py"]
   ```

2. Create a `docker-compose.yml` file:
   ```yaml
   version: '3'
   
   services:
     db:
       image: postgres:13
       environment:
         POSTGRES_USER: postgres
         POSTGRES_PASSWORD: postgres
         POSTGRES_DB: social_media_monitor
       volumes:
         - postgres_data:/var/lib/postgresql/data
         - ./db/migrations/initial_schema.sql:/docker-entrypoint-initdb.d/initial_schema.sql
       ports:
         - "5432:5432"
   
     app:
       build: .
       depends_on:
         - db
       environment:
         - DB_HOST=db
         - DB_PORT=5432
         - DB_NAME=social_media_monitor
         - DB_USER=postgres
         - DB_PASSWORD=postgres
         - REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
         - REDDIT_CLIENT_SECRET=${REDDIT_CLIENT_SECRET}
         - REDDIT_USERNAME=${REDDIT_USERNAME}
         - REDDIT_PASSWORD=${REDDIT_PASSWORD}
         - REDDIT_USER_AGENT=${REDDIT_USER_AGENT}
         - NEWS_API_KEY=${NEWS_API_KEY}
       volumes:
         - .:/app
       command: python main.py
   
     dashboard:
       build: .
       depends_on:
         - db
         - app
       environment:
         - DB_HOST=db
         - DB_PORT=5432
         - DB_NAME=social_media_monitor
         - DB_USER=postgres
         - DB_PASSWORD=postgres
       ports:
         - "8501:8501"
       volumes:
         - .:/app
       command: streamlit run dashboard/app.py
   
   volumes:
     postgres_data:
   ```

3. Build and run with Docker Compose:
   ```bash
   # Build and start containers
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   ```

### Cloud Deployment (AWS)

1. Set up AWS resources:
   - EC2 instance for the application
   - RDS PostgreSQL instance for the database
   - Elastic Load Balancer for the dashboard

2. Configure security groups:
   - Allow inbound traffic on port 8501 for Streamlit
   - Allow inbound traffic on port 5432 for PostgreSQL

3. Deploy the application:
   ```bash
   # SSH into EC2 instance
   ssh -i key.pem ec2-user@your-instance-ip
   
   # Clone the repository
   git clone <repository-url>
   cd social_media_monitor
   
   # Set up environment
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Configure environment variables
   # Update .env with RDS endpoint and credentials
   
   # Run the application
   nohup python main.py > app.log 2>&1 &
   nohup streamlit run dashboard/app.py > dashboard.log 2>&1 &
   ```

4. Set up monitoring and logging:
   - Configure CloudWatch for monitoring
   - Set up log rotation for application logs

### Continuous Integration/Deployment

1. Create a `.github/workflows/ci.yml` file for GitHub Actions:
   ```yaml
   name: CI/CD Pipeline
   
   on:
     push:
       branches: [ main ]
     pull_request:
       branches: [ main ]
   
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
   
     deploy:
       needs: test
       if: github.ref == 'refs/heads/main'
       runs-on: ubuntu-latest
       
       steps:
       - uses: actions/checkout@v2
       
       - name: Deploy to EC2
         uses: appleboy/ssh-action@master
         with:
           host: ${{ secrets.EC2_HOST }}
           username: ${{ secrets.EC2_USERNAME }}
           key: ${{ secrets.EC2_SSH_KEY }}
           script: |
             cd social_media_monitor
             git pull
             source venv/bin/activate
             pip install -r requirements.txt
             sudo systemctl restart social_media_monitor
             sudo systemctl restart social_media_dashboard
   ```

## Maintenance and Scaling

### Maintenance

1. Regular database maintenance:
   ```bash
   # Connect to PostgreSQL
   psql -U postgres -d social_media_monitor
   
   # Vacuum the database
   VACUUM ANALYZE;
   
   # Check for slow queries
   SELECT * FROM pg_stat_activity WHERE state = 'active';
   ```

2. Log rotation:
   ```bash
   # Create logrotate configuration
   sudo nano /etc/logrotate.d/social_media_monitor
   
   # Add configuration
   /path/to/social_media_monitor/app.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
       create 0640 user group
   }
   ```

### Scaling

1. Horizontal scaling:
   - Deploy multiple instances of the application behind a load balancer
   - Use a message queue (e.g., RabbitMQ, Redis) for distributing data collection tasks

2. Database scaling:
   - Use read replicas for read-heavy operations
   - Implement database sharding for large datasets
   - Consider using a caching layer (e.g., Redis) for frequently accessed data

3. Performance optimization:
   - Implement batch processing for data collection
   - Use asynchronous processing for non-blocking operations
   - Optimize database queries with proper indexing