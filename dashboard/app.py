import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os
import sys
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project modules
from db.unified_connection import SessionLocal
from db.models import Mention, Sentiment, CrisisAlert, Influencer, CompetitiveMetric

# Set page config
st.set_page_config(
    page_title="Brand Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
def load_css():
    with open(os.path.join(os.path.dirname(__file__), "assets/css/style.css")) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Try to load CSS, but don't fail if file doesn't exist yet
try:
    load_css()
except:
    pass

# Sidebar
st.sidebar.title("Brand Monitoring")

# Database connection
@st.cache_resource
def get_db_session():
    return SessionLocal()

# Data loading functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data(brand: str, start_date: datetime, end_date: datetime, source: str = "All") -> Dict[str, Any]:
    """Load data from database
    
    Args:
        brand: Brand name
        start_date: Start date
        end_date: End date
        source: Data source filter
        
    Returns:
        Dictionary with loaded data
    """
    db = get_db_session()
    
    # Base query for mentions with sentiment
    query = db.query(Mention, Sentiment).join(
        Sentiment, Mention.id == Sentiment.mention_id
    ).filter(
        Mention.brand == brand,
        Mention.created_at >= start_date,
        Mention.created_at <= end_date
    )
    
    # Apply source filter
    if source != "All":
        query = query.filter(Mention.source == source.lower())
    
    # Execute query
    results = query.all()
    
    # Convert to DataFrame
    data = []
    for mention, sentiment in results:
        data.append({
            "id": mention.id,
            "source": mention.source,
            "content": mention.content,
            "created_at": mention.created_at,
            "author": mention.author,
            "url": mention.url,
            "engagement": mention.engagement,
            "title": mention.title,
            "polarity": sentiment.polarity,
            "subjectivity": sentiment.subjectivity,
            "compound_score": sentiment.compound_score,
            "positive_score": sentiment.positive_score,
            "negative_score": sentiment.negative_score,
            "neutral_score": sentiment.neutral_score
        })
    
    mentions_df = pd.DataFrame(data)
    
    # Get crisis alerts
    crisis_query = db.query(CrisisAlert).filter(
        CrisisAlert.brand == brand,
        CrisisAlert.detected_at >= start_date,
        CrisisAlert.detected_at <= end_date
    )
    
    crisis_data = []
    for alert in crisis_query.all():
        crisis_data.append({
            "id": alert.id,
            "brand": alert.brand,
            "description": alert.description,
            "severity": alert.severity,
            "detected_at": alert.detected_at,
            "status": alert.status,
            "resolved_at": alert.resolved_at,
            "resolution_notes": alert.resolution_notes
        })
    
    crisis_df = pd.DataFrame(crisis_data)
    
    # Get influencers
    influencer_query = db.query(Influencer).filter(
        Influencer.brand_affinity == brand
    )
    
    influencer_data = []
    for influencer in influencer_query.all():
        influencer_data.append({
            "id": influencer.id,
            "username": influencer.username,
            "platform": influencer.platform,
            "followers": influencer.followers,
            "impact_score": influencer.impact_score,
            "brand_affinity": influencer.brand_affinity,
            "last_updated": influencer.last_updated
        })
    
    influencer_df = pd.DataFrame(influencer_data)
    
    # Get competitive metrics
    competitive_query = db.query(CompetitiveMetric).filter(
        CompetitiveMetric.brand == brand,
        CompetitiveMetric.period_end >= start_date,
        CompetitiveMetric.period_start <= end_date
    )
    
    competitive_data = []
    for metric in competitive_query.all():
        competitive_data.append({
            "id": metric.id,
            "brand": metric.brand,
            "competitor": metric.competitor,
            "sentiment_ratio": metric.sentiment_ratio,
            "mention_count": metric.mention_count,
            "engagement_rate": metric.engagement_rate,
            "period_start": metric.period_start,
            "period_end": metric.period_end
        })
    
    competitive_df = pd.DataFrame(competitive_data)
    
    return {
        "mentions": mentions_df,
        "crisis_alerts": crisis_df,
        "influencers": influencer_df,
        "competitive": competitive_df
    }

# Get available brands
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_available_brands() -> List[str]:
    """Get list of available brands in the database"""
    db = get_db_session()
    brands = db.query(Mention.brand).distinct().all()
    return [brand[0] for brand in brands] or ["Apple", "Samsung", "Google", "Microsoft"]  # Default brands if none in DB

# Brand selection
brands = get_available_brands()
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

# Load data
try:
    data = load_data(selected_brand, start_date, end_date, selected_source)
    mentions_df = data["mentions"]
    crisis_df = data["crisis_alerts"]
    influencer_df = data["influencers"]
    competitive_df = data["competitive"]
    
    # Check if we have data
    if mentions_df.empty:
        st.info(f"No data available for {selected_brand} in the selected time period. Please try a different brand or time period.")
        
        # Generate mock data for demonstration
        if st.button("Generate Demo Data"):
            # This would be replaced with actual data generation in a real implementation
            st.info("Demo data generation would be implemented here in a real system.")
    
    else:
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Sentiment Analysis", "Crisis Monitor", "Influencers"])
        
        # Tab 1: Overview
        with tab1:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_mentions = len(mentions_df)
                st.metric("Total Mentions", total_mentions)
            
            with col2:
                avg_sentiment = mentions_df["compound_score"].mean()
                sentiment_label = "Positive" if avg_sentiment > 0.05 else "Negative" if avg_sentiment < -0.05 else "Neutral"
                st.metric("Average Sentiment", f"{avg_sentiment:.2f} ({sentiment_label})")
            
            with col3:
                total_engagement = mentions_df["engagement"].sum()
                st.metric("Total Engagement", total_engagement)
            
            with col4:
                active_crises = len(crisis_df[crisis_df["status"] == "new"])
                st.metric("Active Crises", active_crises)
            
            # Mentions over time
            st.subheader("Mentions Over Time")
            
            # Group by day
            mentions_df["date"] = mentions_df["created_at"].dt.date
            mentions_by_day = mentions_df.groupby("date").size().reset_index(name="count")
            
            # Create line chart
            fig = px.line(
                mentions_by_day, 
                x="date", 
                y="count",
                title="Mentions by Day",
                labels={"date": "Date", "count": "Number of Mentions"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Source breakdown
            st.subheader("Source Breakdown")
            
            # Group by source
            source_counts = mentions_df["source"].value_counts().reset_index()
            source_counts.columns = ["source", "count"]
            
            # Create pie chart
            fig = px.pie(
                source_counts,
                values="count",
                names="source",
                title="Mentions by Source"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 2: Sentiment Analysis
        with tab2:
            # Sentiment over time
            st.subheader("Sentiment Over Time")
            
            # Group by day and calculate average sentiment
            sentiment_by_day = mentions_df.groupby("date")["compound_score"].mean().reset_index()
            
            # Create line chart
            fig = px.line(
                sentiment_by_day,
                x="date",
                y="compound_score",
                title="Average Sentiment by Day",
                labels={"date": "Date", "compound_score": "Sentiment Score"}
            )
            
            # Add reference lines
            fig.add_shape(
                type="line",
                x0=sentiment_by_day["date"].min(),
                y0=0.05,
                x1=sentiment_by_day["date"].max(),
                y1=0.05,
                line=dict(color="green", width=1, dash="dash"),
            )
            
            fig.add_shape(
                type="line",
                x0=sentiment_by_day["date"].min(),
                y0=-0.05,
                x1=sentiment_by_day["date"].max(),
                y1=-0.05,
                line=dict(color="red", width=1, dash="dash"),
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Sentiment distribution
            st.subheader("Sentiment Distribution")
            
            # Create histogram
            fig = px.histogram(
                mentions_df,
                x="compound_score",
                nbins=20,
                title="Distribution of Sentiment Scores",
                labels={"compound_score": "Sentiment Score"}
            )
            
            # Add reference lines
            fig.add_shape(
                type="line",
                x0=0.05,
                y0=0,
                x1=0.05,
                y1=mentions_df["compound_score"].value_counts().max(),
                line=dict(color="green", width=1, dash="dash"),
            )
            
            fig.add_shape(
                type="line",
                x0=-0.05,
                y0=0,
                x1=-0.05,
                y1=mentions_df["compound_score"].value_counts().max(),
                line=dict(color="red", width=1, dash="dash"),
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Most positive and negative mentions
            st.subheader("Most Positive and Negative Mentions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Most Positive")
                positive_mentions = mentions_df.sort_values("compound_score", ascending=False).head(5)
                
                for _, mention in positive_mentions.iterrows():
                    with st.expander(f"{mention['title']} ({mention['compound_score']:.2f})"):
                        st.write(f"**Source:** {mention['source']}")
                        st.write(f"**Date:** {mention['created_at'].strftime('%Y-%m-%d')}")
                        st.write(f"**Content:** {mention['content']}")
                        st.write(f"**URL:** {mention['url']}")
            
            with col2:
                st.subheader("Most Negative")
                negative_mentions = mentions_df.sort_values("compound_score").head(5)
                
                for _, mention in negative_mentions.iterrows():
                    with st.expander(f"{mention['title']} ({mention['compound_score']:.2f})"):
                        st.write(f"**Source:** {mention['source']}")
                        st.write(f"**Date:** {mention['created_at'].strftime('%Y-%m-%d')}")
                        st.write(f"**Content:** {mention['content']}")
                        st.write(f"**URL:** {mention['url']}")
        
        # Tab 3: Crisis Monitor
        with tab3:
            # Crisis alerts
            st.subheader("Crisis Alerts")
            
            if crisis_df.empty:
                st.info("No crisis alerts detected in the selected time period.")
            else:
                # Sort by severity and detection time
                crisis_df = crisis_df.sort_values(["severity", "detected_at"], ascending=[False, False])
                
                for _, crisis in crisis_df.iterrows():
                    # Determine severity color
                    severity = crisis["severity"]
                    if severity >= 0.8:
                        severity_color = "red"
                    elif severity >= 0.6:
                        severity_color = "orange"
                    elif severity >= 0.4:
                        severity_color = "yellow"
                    else:
                        severity_color = "blue"
                    
                    # Create expander with colored header
                    with st.expander(f"{crisis['detected_at'].strftime('%Y-%m-%d %H:%M')} - Severity: {severity:.2f}"):
                        st.markdown(f"<div style='color:{severity_color};font-weight:bold;'>{crisis['description']}</div>", unsafe_allow_html=True)
                        
                        # Status badge
                        status = crisis["status"]
                        if status == "new":
                            st.markdown("<span style='background-color:red;color:white;padding:3px 8px;border-radius:3px;'>NEW</span>", unsafe_allow_html=True)
                        elif status == "investigating":
                            st.markdown("<span style='background-color:orange;color:white;padding:3px 8px;border-radius:3px;'>INVESTIGATING</span>", unsafe_allow_html=True)
                        elif status == "resolved":
                            st.markdown("<span style='background-color:green;color:white;padding:3px 8px;border-radius:3px;'>RESOLVED</span>", unsafe_allow_html=True)
                        
                        # Resolution notes if available
                        if crisis["resolved_at"] is not None:
                            st.write(f"**Resolved at:** {crisis['resolved_at'].strftime('%Y-%m-%d %H:%M')}")
                            st.write(f"**Resolution notes:** {crisis['resolution_notes'] or 'No notes provided'}")
            
            # Crisis detection settings
            st.subheader("Crisis Detection Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                sentiment_threshold = st.slider("Sentiment Threshold", -1.0, 0.0, -0.2, 0.05)
            
            with col2:
                volume_threshold = st.slider("Volume Threshold", 1.0, 5.0, 2.0, 0.1)
        
        # Tab 4: Influencers
        with tab4:
            # Influencers
            st.subheader("Top Influencers")
            
            if influencer_df.empty:
                st.info("No influencer data available for the selected brand.")
            else:
                # Sort by impact score
                influencer_df = influencer_df.sort_values("impact_score", ascending=False)
                
                # Create table
                st.dataframe(
                    influencer_df[["username", "platform", "followers", "impact_score"]],
                    column_config={
                        "username": "Username",
                        "platform": "Platform",
                        "followers": st.column_config.NumberColumn("Followers", format="%d"),
                        "impact_score": st.column_config.ProgressColumn("Impact Score", min_value=0, max_value=1, format="%.2f")
                    },
                    hide_index=True
                )
            
            # Engagement by author
            st.subheader("Top Engagers")
            
            # Group by author and calculate total engagement
            author_engagement = mentions_df.groupby("author")["engagement"].sum().reset_index()
            author_engagement = author_engagement.sort_values("engagement", ascending=False).head(10)
            
            # Create bar chart
            fig = px.bar(
                author_engagement,
                x="author",
                y="engagement",
                title="Top 10 Authors by Engagement",
                labels={"author": "Author", "engagement": "Total Engagement"}
            )
            st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("This is likely because the database is not yet set up or there is no data available. Please make sure the database is properly configured and data has been collected.")

# Footer
st.markdown("---")
st.markdown("Social Media Brand Monitoring & Crisis Detection System")