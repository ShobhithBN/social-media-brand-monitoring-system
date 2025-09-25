import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import base64
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

# Import project modules
from db.connection import SessionLocal
from db.models import Mention, Sentiment, CrisisAlert, Influencer, CompetitiveMetric

class ReportGenerator:
    """Generates reports from collected data"""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set template directory
        if template_dir is None:
            template_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "templates"
            )
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
    
    def generate_report(self, brand: str, start_date: datetime, end_date: datetime,
                        output_file: str, template_name: str = "default_report.html") -> bool:
        """Generate a report for a brand
        
        Args:
            brand: Brand name
            start_date: Start date
            end_date: End date
            output_file: Output file path
            template_name: Template name
            
        Returns:
            True if report was generated successfully, False otherwise
        """
        try:
            # Get data
            data = self._get_data(brand, start_date, end_date)
            
            # Generate charts
            charts = self._generate_charts(data)
            
            # Prepare template context
            context = self._prepare_context(brand, start_date, end_date, data, charts)
            
            # Render template
            template = self.env.get_template(template_name)
            output = template.render(**context)
            
            # Write to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)
            
            self.logger.info(f"Report generated successfully: {output_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            return False
    
    def _get_data(self, brand: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get data for report
        
        Args:
            brand: Brand name
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with data for report
        """
        db = SessionLocal()
        
        try:
            # Get mentions with sentiment
            mentions_query = db.query(Mention, Sentiment).join(
                Sentiment, Mention.id == Sentiment.mention_id
            ).filter(
                Mention.brand == brand,
                Mention.created_at >= start_date,
                Mention.created_at <= end_date
            )
            
            # Convert to DataFrame
            mentions_data = []
            for mention, sentiment in mentions_query.all():
                mentions_data.append({
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
            
            mentions_df = pd.DataFrame(mentions_data)
            
            # Get crisis alerts
            crisis_query = db.query(CrisisAlert).filter(
                CrisisAlert.brand == brand,
                CrisisAlert.detected_at >= start_date,
                CrisisAlert.detected_at <= end_date
            )
            
            crisis_data = []
            for alert in crisis_query.all():
                # Determine severity label
                severity = alert.severity
                if severity >= 0.8:
                    severity_label = "Critical"
                elif severity >= 0.6:
                    severity_label = "High"
                elif severity >= 0.4:
                    severity_label = "Medium"
                else:
                    severity_label = "Low"
                
                crisis_data.append({
                    "id": alert.id,
                    "brand": alert.brand,
                    "description": alert.description,
                    "severity": alert.severity,
                    "severity_label": severity_label,
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
            
            # Get competitors
            competitor_query = db.query(CompetitiveMetric.competitor).filter(
                CompetitiveMetric.brand == brand
            ).distinct()
            
            competitors = [competitor[0] for competitor in competitor_query.all()]
            
            # Get competitor mentions
            competitor_mentions = []
            for competitor in competitors:
                competitor_query = db.query(Mention, Sentiment).join(
                    Sentiment, Mention.id == Sentiment.mention_id
                ).filter(
                    Mention.brand == competitor,
                    Mention.created_at >= start_date,
                    Mention.created_at <= end_date
                )
                
                for mention, sentiment in competitor_query.all():
                    competitor_mentions.append({
                        "id": mention.id,
                        "brand": mention.brand,
                        "source": mention.source,
                        "content": mention.content,
                        "created_at": mention.created_at,
                        "author": mention.author,
                        "url": mention.url,
                        "engagement": mention.engagement,
                        "title": mention.title,
                        "compound_score": sentiment.compound_score
                    })
            
            competitor_mentions_df = pd.DataFrame(competitor_mentions)
            
            return {
                "mentions": mentions_df,
                "crisis_alerts": crisis_df,
                "influencers": influencer_df,
                "competitive": competitive_df,
                "competitors": competitors,
                "competitor_mentions": competitor_mentions_df
            }
        
        finally:
            db.close()
    
    def _generate_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate charts for report
        
        Args:
            data: Data for report
            
        Returns:
            Dictionary with chart images as base64 strings
        """
        charts = {}
        
        mentions_df = data["mentions"]
        
        if not mentions_df.empty:
            # Sentiment over time
            try:
                mentions_df["date"] = mentions_df["created_at"].dt.date
                sentiment_by_day = mentions_df.groupby("date")["compound_score"].mean().reset_index()
                
                fig = px.line(
                    sentiment_by_day,
                    x="date",
                    y="compound_score",
                    title="Average Sentiment by Day",
                    labels={"date": "Date", "compound_score": "Sentiment Score"}
                )
                
                charts["sentiment_chart"] = self._fig_to_base64(fig)
            except Exception as e:
                self.logger.error(f"Error generating sentiment chart: {str(e)}")
            
            # Sentiment distribution
            try:
                fig = px.histogram(
                    mentions_df,
                    x="compound_score",
                    nbins=20,
                    title="Distribution of Sentiment Scores",
                    labels={"compound_score": "Sentiment Score"}
                )
                
                charts["sentiment_distribution_chart"] = self._fig_to_base64(fig)
            except Exception as e:
                self.logger.error(f"Error generating sentiment distribution chart: {str(e)}")
            
            # Mentions over time
            try:
                mentions_by_day = mentions_df.groupby("date").size().reset_index(name="count")
                
                fig = px.line(
                    mentions_by_day,
                    x="date",
                    y="count",
                    title="Mentions by Day",
                    labels={"date": "Date", "count": "Number of Mentions"}
                )
                
                charts["mentions_chart"] = self._fig_to_base64(fig)
            except Exception as e:
                self.logger.error(f"Error generating mentions chart: {str(e)}")
            
            # Source breakdown
            try:
                source_counts = mentions_df["source"].value_counts().reset_index()
                source_counts.columns = ["source", "count"]
                
                fig = px.pie(
                    source_counts,
                    values="count",
                    names="source",
                    title="Mentions by Source"
                )
                
                charts["source_chart"] = self._fig_to_base64(fig)
            except Exception as e:
                self.logger.error(f"Error generating source chart: {str(e)}")
        
        # Competitor charts
        competitor_mentions_df = data["competitor_mentions"]
        
        if not competitor_mentions_df.empty:
            # Competitor sentiment comparison
            try:
                competitor_sentiment = competitor_mentions_df.groupby("brand")["compound_score"].mean().reset_index()
                
                fig = px.bar(
                    competitor_sentiment,
                    x="brand",
                    y="compound_score",
                    title="Average Sentiment by Brand",
                    labels={"brand": "Brand", "compound_score": "Average Sentiment"}
                )
                
                charts["competitor_sentiment_chart"] = self._fig_to_base64(fig)
            except Exception as e:
                self.logger.error(f"Error generating competitor sentiment chart: {str(e)}")
            
            # Competitor volume comparison
            try:
                competitor_volume = competitor_mentions_df.groupby("brand").size().reset_index(name="count")
                
                fig = px.bar(
                    competitor_volume,
                    x="brand",
                    y="count",
                    title="Mention Volume by Brand",
                    labels={"brand": "Brand", "count": "Number of Mentions"}
                )
                
                charts["competitor_volume_chart"] = self._fig_to_base64(fig)
            except Exception as e:
                self.logger.error(f"Error generating competitor volume chart: {str(e)}")
        
        return charts
    
    def _prepare_context(self, brand: str, start_date: datetime, end_date: datetime,
                         data: Dict[str, Any], charts: Dict[str, str]) -> Dict[str, Any]:
        """Prepare context for template
        
        Args:
            brand: Brand name
            start_date: Start date
            end_date: End date
            data: Data for report
            charts: Chart images
            
        Returns:
            Template context
        """
        mentions_df = data["mentions"]
        crisis_df = data["crisis_alerts"]
        influencer_df = data["influencers"]
        competitive_df = data["competitive"]
        competitor_mentions_df = data["competitor_mentions"]
        
        context = {
            "brand": brand,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "generation_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "current_year": datetime.utcnow().year
        }
        
        # Add charts
        context.update(charts)
        
        if not mentions_df.empty:
            # Calculate metrics
            total_mentions = len(mentions_df)
            avg_sentiment = mentions_df["compound_score"].mean()
            total_engagement = mentions_df["engagement"].sum()
            active_crises = len(crisis_df[crisis_df["status"] == "new"]) if not crisis_df.empty else 0
            
            # Get sentiment label
            if avg_sentiment > 0.05:
                sentiment_label = "Positive"
            elif avg_sentiment < -0.05:
                sentiment_label = "Negative"
            else:
                sentiment_label = "Neutral"
            
            # Add metrics to context
            context.update({
                "total_mentions": total_mentions,
                "avg_sentiment": f"{avg_sentiment:.2f} ({sentiment_label})",
                "total_engagement": total_engagement,
                "active_crises": active_crises
            })
            
            # Generate summary
            summary = self._generate_summary(brand, mentions_df, crisis_df, avg_sentiment, sentiment_label)
            context["summary"] = summary
            
            # Get top mentions
            positive_mentions = mentions_df.sort_values("compound_score", ascending=False).head(5)
            negative_mentions = mentions_df.sort_values("compound_score").head(5)
            engaging_mentions = mentions_df.sort_values("engagement", ascending=False).head(5)
            
            # Format mentions for template
            context["positive_mentions"] = self._format_mentions(positive_mentions)
            context["negative_mentions"] = self._format_mentions(negative_mentions)
            context["engaging_mentions"] = self._format_mentions(engaging_mentions)
        else:
            # No data
            context.update({
                "total_mentions": 0,
                "avg_sentiment": "0.00 (Neutral)",
                "total_engagement": 0,
                "active_crises": 0,
                "summary": f"No mentions found for {brand} in the selected time period.",
                "positive_mentions": [],
                "negative_mentions": [],
                "engaging_mentions": []
            })
        
        # Add crisis alerts
        if not crisis_df.empty:
            context["crises"] = crisis_df.to_dict("records")
        else:
            context["crises"] = []
        
        # Add influencers
        if not influencer_df.empty:
            context["influencers"] = influencer_df.to_dict("records")
        else:
            context["influencers"] = []
        
        # Add competitors
        if not competitor_mentions_df.empty:
            # Group by brand
            competitors = []
            for brand_name, group in competitor_mentions_df.groupby("brand"):
                competitors.append({
                    "brand": brand_name,
                    "mentions": len(group),
                    "sentiment": group["compound_score"].mean(),
                    "engagement_rate": group["engagement"].sum() / len(group) if len(group) > 0 else 0
                })
            
            context["competitors"] = competitors
        else:
            context["competitors"] = []
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            brand, mentions_df, crisis_df, avg_sentiment if "avg_sentiment" in locals() else 0
        )
        context["recommendations"] = recommendations
        
        return context
    
    def _generate_summary(self, brand: str, mentions_df: pd.DataFrame,
                         crisis_df: pd.DataFrame, avg_sentiment: float,
                         sentiment_label: str) -> str:
        """Generate summary for report
        
        Args:
            brand: Brand name
            mentions_df: Mentions DataFrame
            crisis_df: Crisis alerts DataFrame
            avg_sentiment: Average sentiment
            sentiment_label: Sentiment label
            
        Returns:
            Summary text
        """
        total_mentions = len(mentions_df)
        active_crises = len(crisis_df[crisis_df["status"] == "new"]) if not crisis_df.empty else 0
        
        # Calculate sentiment change
        mentions_df["date"] = mentions_df["created_at"].dt.date
        sentiment_by_day = mentions_df.groupby("date")["compound_score"].mean()
        
        if len(sentiment_by_day) >= 2:
            first_half = sentiment_by_day.iloc[:len(sentiment_by_day)//2].mean()
            second_half = sentiment_by_day.iloc[len(sentiment_by_day)//2:].mean()
            sentiment_change = second_half - first_half
            
            if sentiment_change > 0.1:
                sentiment_trend = "improving significantly"
            elif sentiment_change > 0.05:
                sentiment_trend = "improving"
            elif sentiment_change < -0.1:
                sentiment_trend = "declining significantly"
            elif sentiment_change < -0.05:
                sentiment_trend = "declining"
            else:
                sentiment_trend = "remaining stable"
        else:
            sentiment_trend = "stable"
        
        # Generate summary
        summary = f"During the reporting period, {brand} received {total_mentions} mentions across monitored platforms. "
        summary += f"The overall sentiment was {sentiment_label.lower()} ({avg_sentiment:.2f}), with sentiment {sentiment_trend} over time. "
        
        if active_crises > 0:
            summary += f"There {'is' if active_crises == 1 else 'are'} currently {active_crises} active crisis alert{'s' if active_crises != 1 else ''} that require{'s' if active_crises == 1 else ''} attention. "
        
        # Add source breakdown
        source_counts = mentions_df["source"].value_counts()
        if not source_counts.empty:
            top_source = source_counts.index[0]
            top_source_pct = source_counts.iloc[0] / total_mentions * 100
            summary += f"The majority of mentions ({top_source_pct:.1f}%) came from {top_source}. "
        
        # Add engagement info
        total_engagement = mentions_df["engagement"].sum()
        avg_engagement = total_engagement / total_mentions if total_mentions > 0 else 0
        summary += f"Total engagement was {total_engagement}, with an average of {avg_engagement:.1f} per mention."
        
        return summary
    
    def _generate_recommendations(self, brand: str, mentions_df: pd.DataFrame,
                                 crisis_df: pd.DataFrame, avg_sentiment: float) -> List[str]:
        """Generate recommendations based on data
        
        Args:
            brand: Brand name
            mentions_df: Mentions DataFrame
            crisis_df: Crisis alerts DataFrame
            avg_sentiment: Average sentiment
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if mentions_df.empty:
            recommendations.append(f"Increase social media presence to generate more mentions for {brand}.")
            recommendations.append("Implement a content strategy to boost brand visibility.")
            return recommendations
        
        # Sentiment-based recommendations
        if avg_sentiment < -0.2:
            recommendations.append("Address negative sentiment by engaging with dissatisfied customers and resolving their issues.")
            recommendations.append("Develop a PR strategy to improve brand perception.")
        elif avg_sentiment < 0:
            recommendations.append("Monitor negative mentions closely and respond promptly to prevent escalation.")
            recommendations.append("Highlight positive aspects of the brand to balance negative perceptions.")
        elif avg_sentiment < 0.2:
            recommendations.append("Work on improving brand sentiment by creating more engaging and positive content.")
            recommendations.append("Encourage satisfied customers to share their positive experiences.")
        else:
            recommendations.append("Leverage positive sentiment by showcasing customer testimonials and success stories.")
            recommendations.append("Continue the current strategy that's generating positive sentiment.")
        
        # Crisis-based recommendations
        active_crises = len(crisis_df[crisis_df["status"] == "new"]) if not crisis_df.empty else 0
        if active_crises > 0:
            recommendations.append("Prioritize addressing the active crisis alerts to prevent further damage to brand reputation.")
            recommendations.append("Develop a crisis communication plan to respond quickly to future incidents.")
        
        # Source-based recommendations
        source_counts = mentions_df["source"].value_counts()
        if not source_counts.empty:
            least_source = source_counts.index[-1]
            recommendations.append(f"Increase presence on {least_source} to reach a wider audience.")
        
        # Engagement-based recommendations
        avg_engagement = mentions_df["engagement"].mean()
        if avg_engagement < 10:
            recommendations.append("Improve content engagement by creating more interactive and shareable posts.")
            recommendations.append("Experiment with different content formats to identify what resonates with the audience.")
        
        return recommendations
    
    def _format_mentions(self, mentions_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Format mentions for template
        
        Args:
            mentions_df: Mentions DataFrame
            
        Returns:
            List of formatted mentions
        """
        formatted_mentions = []
        
        for _, mention in mentions_df.iterrows():
            formatted_mentions.append({
                "created_at": mention["created_at"].strftime("%Y-%m-%d"),
                "source": mention["source"],
                "title": mention["title"],
                "sentiment": f"{mention['compound_score']:.2f}",
                "engagement": mention["engagement"]
            })
        
        return formatted_mentions
    
    def _fig_to_base64(self, fig) -> str:
        """Convert Plotly figure to base64 string
        
        Args:
            fig: Plotly figure
            
        Returns:
            Base64 encoded image
        """
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"