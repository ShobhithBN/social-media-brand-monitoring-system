import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from dotenv import load_dotenv
from .base_collector import BaseCollector

# Load environment variables
load_dotenv()

class NewsCollector(BaseCollector):
    """Collector for News API data"""
    
    def __init__(self, brands: List[str], keywords: List[str] = None, 
                 days_back: int = 7, language: str = "en"):
        super().__init__(brands, keywords)
        self.days_back = days_back
        self.language = language
        
        # Initialize News API client
        self.news_api = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect data from News API
        
        Returns:
            List of dictionaries containing collected data
        """
        collected_data = []
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.days_back)
        
        # Format dates for News API
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        # Search for brand mentions
        for brand in self.brands:
            self.logger.info(f"Collecting news for brand: {brand}")
            
            # Create query with brand and keywords
            query = brand
            if self.keywords:
                query += " AND (" + " OR ".join(self.keywords) + ")"
            
            # Get articles from News API
            try:
                response = self.news_api.get_everything(
                    q=query,
                    from_param=from_date,
                    to=to_date,
                    language=self.language,
                    sort_by="relevancy"
                )
                
                # Process articles
                if response["status"] == "ok":
                    for article in response["articles"]:
                        collected_data.append(self.format_data({
                            "article": article,
                            "brand": brand
                        }))
                else:
                    self.logger.error(f"News API error: {response}")
            
            except Exception as e:
                self.logger.error(f"Error collecting news for {brand}: {str(e)}")
        
        return collected_data
    
    def format_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format News API data
        
        Args:
            raw_data: Raw data from News API
            
        Returns:
            Formatted data dictionary
        """
        article = raw_data["article"]
        
        # Parse publication date
        try:
            published_at = datetime.strptime(article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
        except:
            published_at = datetime.utcnow()
        
        return {
            "source": "news",
            "content": article["description"] or "",
            "created_at": published_at,
            "author": article["author"] or "Unknown",
            "url": article["url"],
            "engagement": 0,  # News API doesn't provide engagement metrics
            "brand": raw_data["brand"],
            "title": article["title"],
            "news_source": article["source"]["name"] if article["source"] else "Unknown"
        }