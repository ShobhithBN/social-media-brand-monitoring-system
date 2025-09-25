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