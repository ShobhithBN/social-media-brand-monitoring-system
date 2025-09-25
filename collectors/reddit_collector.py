import os
import praw
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from .base_collector import BaseCollector

# Load environment variables
load_dotenv()

class RedditCollector(BaseCollector):
    """Collector for Reddit data"""
    
    def __init__(self, brands: List[str], keywords: List[str] = None, 
                 subreddits: List[str] = None, limit: int = 100):
        super().__init__(brands, keywords)
        self.subreddits = subreddits or []
        self.limit = limit
        
        # Initialize Reddit API client
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect data from Reddit
        
        Returns:
            List of dictionaries containing collected data
        """
        collected_data = []
        
        # Search for brand mentions
        for brand in self.brands:
            self.logger.info(f"Collecting data for brand: {brand}")
            
            # Search in specified subreddits
            if self.subreddits:
                for subreddit_name in self.subreddits:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Search for brand name in subreddit
                    for submission in subreddit.search(brand, limit=self.limit):
                        if self._is_relevant(submission.title, submission.selftext, brand):
                            collected_data.append(self.format_data({
                                "submission": submission,
                                "brand": brand
                            }))
                        
                        # Get comments
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments.list():
                            if self._is_relevant(comment.body, "", brand):
                                collected_data.append(self.format_data({
                                    "comment": comment,
                                    "submission": submission,
                                    "brand": brand
                                }))
            else:
                # Search across all of Reddit
                for submission in self.reddit.subreddit("all").search(brand, limit=self.limit):
                    if self._is_relevant(submission.title, submission.selftext, brand):
                        collected_data.append(self.format_data({
                            "submission": submission,
                            "brand": brand
                        }))
                    
                    # Get comments
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list():
                        if self._is_relevant(comment.body, "", brand):
                            collected_data.append(self.format_data({
                                "comment": comment,
                                "submission": submission,
                                "brand": brand
                            }))
        
        return collected_data
    
    def format_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Reddit data
        
        Args:
            raw_data: Raw data from Reddit
            
        Returns:
            Formatted data dictionary
        """
        if "comment" in raw_data:
            # Format comment data
            comment = raw_data["comment"]
            submission = raw_data["submission"]
            return {
                "source": "reddit",
                "content": comment.body,
                "created_at": datetime.fromtimestamp(comment.created_utc),
                "author": str(comment.author) if comment.author else "[deleted]",
                "url": f"https://www.reddit.com{comment.permalink}",
                "engagement": comment.score,
                "brand": raw_data["brand"],
                "title": submission.title,
                "subreddit": comment.subreddit.display_name,
                "post_id": submission.id
            }
        else:
            # Format submission data
            submission = raw_data["submission"]
            return {
                "source": "reddit",
                "content": submission.selftext,
                "created_at": datetime.fromtimestamp(submission.created_utc),
                "author": str(submission.author) if submission.author else "[deleted]",
                "url": submission.url,
                "engagement": submission.score,
                "brand": raw_data["brand"],
                "title": submission.title,
                "subreddit": submission.subreddit.display_name,
                "post_id": submission.id
            }
    
    def _is_relevant(self, title: str, content: str, brand: str) -> bool:
        """Check if the content is relevant to the brand
        
        Args:
            title: Title of the post
            content: Content of the post
            brand: Brand name
            
        Returns:
            True if relevant, False otherwise
        """
        # Simple relevance check - can be improved with NLP
        title_lower = title.lower()
        content_lower = content.lower()
        brand_lower = brand.lower()
        
        # Check if brand is mentioned
        if brand_lower in title_lower or brand_lower in content_lower:
            return True
        
        # Check if keywords are mentioned
        for keyword in self.keywords:
            if keyword.lower() in title_lower or keyword.lower() in content_lower:
                return True
        
        return False