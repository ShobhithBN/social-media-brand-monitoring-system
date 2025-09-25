#!/usr/bin/env python3
"""
Setup local demo with SQLite database for development
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import SQLite connection instead of PostgreSQL
from db.sqlite_connection import engine, SessionLocal, Base

# Import models and redefine them to use our SQLite Base
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Redefine models for SQLite
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

class CrisisAlert(Base):
    __tablename__ = "crisis_alerts"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    severity = Column(Float, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="new", nullable=False, index=True)

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

from analysis.sentiment import SentimentAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample brands
BRANDS = ["Apple", "Samsung", "Google", "Microsoft"]

def setup_demo_data():
    """Setup demo data with SQLite"""
    logger.info("Creating SQLite database and tables...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create database session
    db = SessionLocal()

    try:
        # Check if data already exists (only if tables exist)
        try:
            existing_mentions = db.query(Mention).count()
            if existing_mentions > 0:
                logger.info(f"Database already has {existing_mentions} mentions. Skipping data generation.")
                return
        except Exception:
            # Tables don't exist yet, continue with setup
            logger.info("Database is empty, proceeding with data generation...")

        # Generate sample data
        logger.info("Generating sample data...")

        # Create sentiment analyzer
        sentiment_analyzer = SentimentAnalyzer()

        # Generate random dates
        num_mentions = 100
        days_back = 30
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
            # 30% chance of having a crisis
            if np.random.random() < 0.3:
                severity = np.random.uniform(0.5, 0.9)

                # Create crisis alert
                crisis = CrisisAlert(
                    brand=brand,
                    description=f"Potential brand crisis detected: Negative sentiment spike detected for {brand}",
                    severity=severity,
                    detected_at=datetime.utcnow() - timedelta(days=np.random.randint(0, 7)),
                    status=np.random.choice(["new", "investigating", "resolved"], p=[0.5, 0.3, 0.2])
                )

                # Add to database
                db.add(crisis)

        # Generate influencers
        logger.info("Generating sample influencers...")

        for brand in BRANDS:
            # Generate 2-4 influencers per brand
            for _ in range(np.random.randint(2, 5)):
                # Create influencer
                influencer = Influencer(
                    username=f"tech_influencer_{np.random.randint(1, 100)}",
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

            for competitor in competitors[:2]:  # Limit to 2 competitors per brand
                # Create competitive metric
                metric = CompetitiveMetric(
                    brand=brand,
                    competitor=competitor,
                    sentiment_ratio=np.random.uniform(0.7, 1.3),
                    mention_count=np.random.randint(50, 300),
                    engagement_rate=np.random.uniform(0.01, 0.1),
                    period_start=start_date,
                    period_end=end_date
                )

                # Add to database
                db.add(metric)

        # Commit changes
        db.commit()
        logger.info("Sample data generation completed successfully.")

        # Print summary
        mentions_count = db.query(Mention).count()
        crises_count = db.query(CrisisAlert).count()
        influencers_count = db.query(Influencer).count()

        logger.info(f"Created:")
        logger.info(f"  - {mentions_count} mentions")
        logger.info(f"  - {crises_count} crisis alerts")
        logger.info(f"  - {influencers_count} influencers")

    except Exception as e:
        logger.error(f"Error setting up demo data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_demo_data()
    print("\nLocal demo setup complete!")
    print("You can now run the dashboard: streamlit run dashboard/app.py")
    print("Or test MCP tools with the local SQLite database")