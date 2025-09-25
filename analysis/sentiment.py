from typing import Dict, Any, Tuple
from textblob import TextBlob
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

class SentimentAnalyzer:
    """Sentiment analysis for text content"""
    
    def __init__(self):
        # Ensure NLTK resources are downloaded
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        # Initialize VADER sentiment analyzer
        self.vader = SentimentIntensityAnalyzer()
    
    def analyze(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        if not text:
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "compound_score": 0.0,
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 0.0
            }
        
        # TextBlob sentiment analysis
        blob = TextBlob(text)
        polarity, subjectivity = blob.sentiment
        
        # VADER sentiment analysis
        vader_scores = self.vader.polarity_scores(text)
        
        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "compound_score": vader_scores["compound"],
            "positive_score": vader_scores["pos"],
            "negative_score": vader_scores["neg"],
            "neutral_score": vader_scores["neu"]
        }
    
    def get_sentiment_label(self, compound_score: float) -> str:
        """Get sentiment label based on compound score
        
        Args:
            compound_score: VADER compound sentiment score
            
        Returns:
            Sentiment label: "positive", "negative", or "neutral"
        """
        if compound_score >= 0.05:
            return "positive"
        elif compound_score <= -0.05:
            return "negative"
        else:
            return "neutral"