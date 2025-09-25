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