#!/usr/bin/env python
"""
Demo script for Social Media Brand Monitoring & Crisis Detection System.
This script sets up a demo environment with sample data for testing.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time
import argparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from db.connection import engine, SessionLocal, Base
from db.models import Mention, Sentiment, CrisisAlert, Influencer, CompetitiveMetric
from analysis.sentiment import SentimentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Sample brands
BRANDS = ["Apple", "Samsung", "Google", "Microsoft"]

# Sample data generation
def generate_sample_data(db, num_mentions=100, days_back=30):
    """Generate sample data for demo purposes"""
    logger.info(f"Generating {num_mentions} sample mentions...")
    
    # Create sentiment analyzer
    sentiment_analyzer = SentimentAnalyzer()
    
    # Generate random dates
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    dates = [start_date + timedelta(
        seconds=np.random.randint(0, int((end_date - start_date).total_seconds()))
    ) for _ in range(num_mentions)]
    
    # Sample sources
    sources = ["reddit", "news"]
    
    # Sample content templates
    positive_templates = [
        "I love {brand}! Their products are amazing.",
        "{brand} has the best customer service I've ever experienced.",
        "Just got a new {brand} device and it's fantastic!",
        "The new {brand} release is incredible, highly recommend it.",
        "{brand} is leading the industry with their innovative approach."
    ]
    
    negative_templates = [
        "I'm disappointed with {brand}, their quality has gone down.",
        "{brand} customer service is terrible, waited hours for a response.",
        "My {brand} device broke after just a few months of use.",
        "The new {brand} release is a step backward, don't buy it.",
        "{brand} is falling behind their competitors in innovation."
    ]
    
    neutral_templates = [
        "Just saw a {brand} ad on TV.",
        "Does anyone use {brand} products?",
        "{brand} announced a new product today.",
        "Comparing {brand} with other options in the market.",
        "Interesting article about {brand}'s market position."
    ]
    
    # Generate mentions
    for i in range(num_mentions):
        # Select random brand
        brand = np.random.choice(BRANDS)
        
        # Select random source
        source = np.random.choice(sources)
        
        # Select random sentiment
        sentiment_type = np.random.choice(["positive", "negative", "neutral"], p=[0.4, 0.3, 0.3])
        
        if sentiment_type == "positive":
            content = np.random.choice(positive_templates).format(brand=brand)
        elif sentiment_type == "negative":
            content = np.random.choice(negative_templates).format(brand=brand)
        else:
            content = np.random.choice(neutral_templates).format(brand=brand)
        
        # Create mention
        mention = Mention(
            source=source,
            content=content,
            created_at=dates[i],
            author=f"user_{np.random.randint(1, 100)}",
            url=f"https://example.com/{source}/{np.random.randint(1000, 9999)}",
            engagement=np.random.randint(0, 1000),
            brand=brand,
            title=f"{brand} {sentiment_type.capitalize()} Mention",
            subreddit="technology" if source == "reddit" else None,
            post_id=f"post_{np.random.randint(1000, 9999)}" if source == "reddit" else None,
            news_source="TechNews" if source == "news" else None
        )
        
        # Add to database
        db.add(mention)
        db.flush()  # Flush to get mention ID
        
        # Analyze sentiment
        sentiment_scores = sentiment_analyzer.analyze(content)
        
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
    
    # Generate crisis alerts
    logger.info("Generating sample crisis alerts...")
    
    for brand in BRANDS:
        # 50% chance of having a crisis
        if np.random.random() < 0.5:
            severity = np.random.uniform(0.5, 0.9)
            
            # Determine severity label
            if severity >= 0.8:
                severity_label = "Critical"
            elif severity >= 0.6:
                severity_label = "High"
            else:
                severity_label = "Medium"
            
            # Create crisis alert
            crisis = CrisisAlert(
                brand=brand,
                description=f"Potential brand crisis: Negative sentiment: -0.75, Volume spike: 2.5x normal",
                severity=severity,
                detected_at=datetime.utcnow() - timedelta(days=np.random.randint(0, 7)),
                status=np.random.choice(["new", "investigating", "resolved"], p=[0.4, 0.3, 0.3])
            )
            
            # Add to database
            db.add(crisis)
    
    # Generate influencers
    logger.info("Generating sample influencers...")
    
    for brand in BRANDS:
        # Generate 3-5 influencers per brand
        for _ in range(np.random.randint(3, 6)):
            # Create influencer
            influencer = Influencer(
                username=f"influencer_{np.random.randint(1, 100)}",
                platform=np.random.choice(["Twitter", "Instagram", "YouTube", "TikTok"]),
                followers=np.random.randint(10000, 1000000),
                impact_score=np.random.uniform(0.5, 0.95),
                brand_affinity=brand,
                last_updated=datetime.utcnow() - timedelta(days=np.random.randint(0, 14))
            )
            
            # Add to database
            db.add(influencer)
    
    # Generate competitive metrics
    logger.info("Generating sample competitive metrics...")
    
    for brand in BRANDS:
        # Compare with other brands
        competitors = [b for b in BRANDS if b != brand]
        
        for competitor in competitors:
            # Create competitive metric
            metric = CompetitiveMetric(
                brand=brand,
                competitor=competitor,
                sentiment_ratio=np.random.uniform(0.7, 1.3),
                mention_count=np.random.randint(50, 500),
                engagement_rate=np.random.uniform(0.01, 0.1),
                period_start=start_date,
                period_end=end_date
            )
            
            # Add to database
            db.add(metric)
    
    # Commit changes
    db.commit()
    logger.info("Sample data generation completed.")

def run_streamlit():
    """Run Streamlit dashboard"""
    os.system("streamlit run dashboard/app.py")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run Social Media Brand Monitoring demo")
    parser.add_argument("--mentions", type=int, default=100, help="Number of sample mentions to generate")
    parser.add_argument("--days", type=int, default=30, help="Number of days back for sample data")
    parser.add_argument("--no-dashboard", action="store_true", help="Don't launch the dashboard")
    
    args = parser.parse_args()
    
    try:
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Generate sample data
            generate_sample_data(db, args.mentions, args.days)
            
            # Launch dashboard
            if not args.no_dashboard:
                logger.info("Launching Streamlit dashboard...")
                dashboard_thread = threading.Thread(target=run_streamlit)
                dashboard_thread.daemon = True
                dashboard_thread.start()
                
                # Keep main thread alive
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Demo stopped by user.")
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error running demo: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()