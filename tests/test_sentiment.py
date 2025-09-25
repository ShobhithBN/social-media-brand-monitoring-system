import unittest
from datetime import datetime
from social_media_monitor.analysis.sentiment import SentimentAnalyzer

class TestSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = SentimentAnalyzer()
        
        # Test texts
        self.positive_text = "I absolutely love this product! It's amazing and works perfectly."
        self.negative_text = "This is terrible. I hate it and it doesn't work at all."
        self.neutral_text = "This is a product that exists."
        self.empty_text = ""
    
    def test_positive_sentiment(self):
        """Test sentiment analysis on positive text"""
        result = self.analyzer.analyze(self.positive_text)
        
        # Check that sentiment scores are positive
        self.assertGreater(result["compound_score"], 0.5)
        self.assertGreater(result["polarity"], 0.5)
        self.assertGreater(result["positive_score"], 0.5)
        
        # Check sentiment label
        label = self.analyzer.get_sentiment_label(result["compound_score"])
        self.assertEqual(label, "positive")
    
    def test_negative_sentiment(self):
        """Test sentiment analysis on negative text"""
        result = self.analyzer.analyze(self.negative_text)
        
        # Check that sentiment scores are negative
        self.assertLess(result["compound_score"], -0.5)
        self.assertLess(result["polarity"], -0.5)
        self.assertGreater(result["negative_score"], 0.4)
        
        # Check sentiment label
        label = self.analyzer.get_sentiment_label(result["compound_score"])
        self.assertEqual(label, "negative")
    
    def test_neutral_sentiment(self):
        """Test sentiment analysis on neutral text"""
        result = self.analyzer.analyze(self.neutral_text)
        
        # Check that sentiment scores are neutral
        self.assertGreater(result["neutral_score"], 0.5)
        self.assertGreater(result["compound_score"], -0.05)
        self.assertLess(result["compound_score"], 0.05)
        
        # Check sentiment label
        label = self.analyzer.get_sentiment_label(result["compound_score"])
        self.assertEqual(label, "neutral")
    
    def test_empty_text(self):
        """Test sentiment analysis on empty text"""
        result = self.analyzer.analyze(self.empty_text)
        
        # Check that all scores are 0
        self.assertEqual(result["compound_score"], 0.0)
        self.assertEqual(result["polarity"], 0.0)
        self.assertEqual(result["subjectivity"], 0.0)
        self.assertEqual(result["positive_score"], 0.0)
        self.assertEqual(result["negative_score"], 0.0)
        self.assertEqual(result["neutral_score"], 0.0)
        
        # Check sentiment label
        label = self.analyzer.get_sentiment_label(result["compound_score"])
        self.assertEqual(label, "neutral")

if __name__ == "__main__":
    unittest.main()