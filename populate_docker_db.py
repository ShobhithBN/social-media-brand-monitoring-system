#!/usr/bin/env python3
"""
Populate Docker PostgreSQL database with sample data
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.sentiment import SentimentAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'social_media_monitor',
    'user': 'postgres',
    'password': '33699'
}

# Sample brands
BRANDS = ["Apple", "Samsung", "Google", "Microsoft"]

def populate_database():
    """Populate the database with sample data"""
    logger.info("Connecting to PostgreSQL database...")

    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Check if data already exists
        cur.execute("SELECT COUNT(*) FROM mentions;")
        existing_mentions = cur.fetchone()['count']

        if existing_mentions > 0:
            logger.info(f"Database already has {existing_mentions} mentions. Skipping data generation.")
            return

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
        mention_ids = []
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

            # Insert mention
            cur.execute("""
                INSERT INTO mentions (source, content, created_at, author, url, engagement, brand, title, subreddit, post_id, news_source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                source,
                content,
                dates[i],
                f"user_{np.random.randint(1, 100)}",
                f"https://example.com/{source}/{np.random.randint(1000, 9999)}",
                np.random.randint(0, 1000),
                brand,
                f"{brand} {sentiment_type.capitalize()} Mention",
                "technology" if source == "reddit" else None,
                f"post_{np.random.randint(1000, 9999)}" if source == "reddit" else None,
                "TechNews" if source == "news" else None
            ))

            mention_id = cur.fetchone()['id']
            mention_ids.append(mention_id)

            # Analyze sentiment
            sentiment_scores = sentiment_analyzer.analyze(content)

            # Insert sentiment record
            cur.execute("""
                INSERT INTO sentiment (mention_id, polarity, subjectivity, compound_score, positive_score, negative_score, neutral_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                mention_id,
                sentiment_scores["polarity"],
                sentiment_scores["subjectivity"],
                sentiment_scores["compound_score"],
                sentiment_scores["positive_score"],
                sentiment_scores["negative_score"],
                sentiment_scores["neutral_score"]
            ))

        # Generate crisis alerts
        logger.info("Generating sample crisis alerts...")

        for brand in BRANDS:
            # 30% chance of having a crisis
            if np.random.random() < 0.3:
                severity = np.random.uniform(0.5, 0.9)

                cur.execute("""
                    INSERT INTO crisis_alerts (brand, description, severity, detected_at, status)
                    VALUES (%s, %s, %s, %s, %s);
                """, (
                    brand,
                    f"Potential brand crisis detected: Negative sentiment spike detected for {brand}",
                    severity,
                    datetime.utcnow() - timedelta(days=np.random.randint(0, 7)),
                    np.random.choice(["new", "investigating", "resolved"], p=[0.5, 0.3, 0.2])
                ))

        # Generate influencers
        logger.info("Generating sample influencers...")

        for brand in BRANDS:
            # Generate 2-4 influencers per brand
            for _ in range(np.random.randint(2, 5)):
                cur.execute("""
                    INSERT INTO influencers (username, platform, followers, impact_score, brand_affinity, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (
                    f"tech_influencer_{np.random.randint(1, 100)}",
                    np.random.choice(["Twitter", "Instagram", "YouTube", "TikTok"]),
                    np.random.randint(10000, 1000000),
                    np.random.uniform(0.5, 0.95),
                    brand,
                    datetime.utcnow() - timedelta(days=np.random.randint(0, 14))
                ))

        # Generate competitive metrics
        logger.info("Generating sample competitive metrics...")

        for brand in BRANDS:
            # Compare with other brands
            competitors = [b for b in BRANDS if b != brand]

            for competitor in competitors[:2]:  # Limit to 2 competitors per brand
                cur.execute("""
                    INSERT INTO competitive_metrics (brand, competitor, sentiment_ratio, mention_count, engagement_rate, period_start, period_end)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (
                    brand,
                    competitor,
                    np.random.uniform(0.7, 1.3),
                    np.random.randint(50, 300),
                    np.random.uniform(0.01, 0.1),
                    start_date,
                    end_date
                ))

        # Commit changes
        conn.commit()
        logger.info("Sample data generation completed successfully.")

        # Print summary
        cur.execute("SELECT COUNT(*) FROM mentions;")
        mentions_count = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) FROM crisis_alerts;")
        crises_count = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) FROM influencers;")
        influencers_count = cur.fetchone()['count']

        logger.info(f"Created:")
        logger.info(f"  - {mentions_count} mentions")
        logger.info(f"  - {crises_count} crisis alerts")
        logger.info(f"  - {influencers_count} influencers")

    except Exception as e:
        logger.error(f"Error populating database: {str(e)}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    populate_database()
    print("\nPostgreSQL database populated successfully!")
    print("You can now run the applications with PostgreSQL backend")