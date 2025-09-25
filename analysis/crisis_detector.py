from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class CrisisDetector:
    """Detects potential brand crises based on sentiment and volume"""
    
    def __init__(self, sentiment_threshold: float = -0.2, 
                 volume_threshold: float = 2.0,
                 time_window: int = 24):
        """
        Args:
            sentiment_threshold: Threshold for negative sentiment (lower is more negative)
            volume_threshold: Threshold for volume increase (multiplier of normal volume)
            time_window: Time window in hours for analysis
        """
        self.sentiment_threshold = sentiment_threshold
        self.volume_threshold = volume_threshold
        self.time_window = time_window
    
    def detect_crises(self, mentions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect potential crises from mentions
        
        Args:
            mentions: List of mentions with sentiment data
            
        Returns:
            List of detected crises
        """
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(mentions)
        
        if df.empty:
            return []
        
        # Ensure created_at is datetime
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Group by brand
        crises = []
        for brand, brand_df in df.groupby('brand'):
            # Sort by time
            brand_df = brand_df.sort_values('created_at')
            
            # Calculate time windows
            now = datetime.utcnow()
            window_end = now
            window_start = now - timedelta(hours=self.time_window)
            
            # Previous window for baseline
            prev_window_end = window_start
            prev_window_start = prev_window_end - timedelta(hours=self.time_window)
            
            # Filter mentions in current window
            current_window = brand_df[
                (brand_df['created_at'] >= window_start) & 
                (brand_df['created_at'] <= window_end)
            ]
            
            # Filter mentions in previous window
            previous_window = brand_df[
                (brand_df['created_at'] >= prev_window_start) & 
                (brand_df['created_at'] <= prev_window_end)
            ]
            
            # Skip if not enough data
            if len(current_window) < 5:
                continue
            
            # Calculate metrics
            current_sentiment = current_window['compound_score'].mean()
            current_volume = len(current_window)
            
            # Calculate baseline metrics
            baseline_sentiment = previous_window['compound_score'].mean() if len(previous_window) > 0 else 0
            baseline_volume = len(previous_window) if len(previous_window) > 0 else current_volume / 2
            
            # Calculate changes
            sentiment_change = current_sentiment - baseline_sentiment
            volume_ratio = current_volume / baseline_volume if baseline_volume > 0 else 1.0
            
            # Check for crisis conditions
            is_crisis = False
            crisis_reasons = []
            
            # Check sentiment threshold
            if current_sentiment < self.sentiment_threshold:
                is_crisis = True
                crisis_reasons.append(f"Negative sentiment: {current_sentiment:.2f}")
            
            # Check sentiment drop
            if sentiment_change < -0.1:
                is_crisis = True
                crisis_reasons.append(f"Sentiment drop: {sentiment_change:.2f}")
            
            # Check volume increase
            if volume_ratio > self.volume_threshold:
                is_crisis = True
                crisis_reasons.append(f"Volume spike: {volume_ratio:.1f}x normal")
            
            # If crisis detected, add to list
            if is_crisis:
                severity = self._calculate_severity(current_sentiment, sentiment_change, volume_ratio)
                
                crises.append({
                    "brand": brand,
                    "description": "Potential brand crisis: " + ", ".join(crisis_reasons),
                    "severity": severity,
                    "detected_at": now,
                    "status": "new"
                })
        
        return crises
    
    def _calculate_severity(self, sentiment: float, sentiment_change: float, 
                           volume_ratio: float) -> float:
        """Calculate crisis severity score
        
        Args:
            sentiment: Current sentiment score
            sentiment_change: Change in sentiment
            volume_ratio: Ratio of current volume to baseline
            
        Returns:
            Severity score (0-1, higher is more severe)
        """
        # Convert sentiment to 0-1 scale (more negative = higher severity)
        sentiment_factor = max(0, min(1, (-sentiment + 1) / 2))
        
        # Convert sentiment change to 0-1 scale
        change_factor = max(0, min(1, -sentiment_change / 2))
        
        # Convert volume ratio to 0-1 scale (capped at 5x)
        volume_factor = max(0, min(1, (volume_ratio - 1) / 4))
        
        # Weighted combination
        severity = (0.4 * sentiment_factor + 
                    0.4 * change_factor + 
                    0.2 * volume_factor)
        
        return severity