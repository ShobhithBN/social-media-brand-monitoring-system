import os
import logging
import schedule
import time
import socket
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

def wait_for_db(host, port, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, int(port)), timeout=5):
                return True
        except Exception:
            time.sleep(1)
    return False

# Wait for DB service (use resolved host from connection module vars)
db_host = os.getenv("DB_HOST", "db")
db_port = os.getenv("DB_PORT", "5432")
if not wait_for_db(db_host, db_port):
    logger.error(f"Database not reachable at {db_host}:{db_port} after timeout")
else:
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