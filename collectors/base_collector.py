from abc import ABC, abstractmethod
import logging
from datetime import datetime
from typing import List, Dict, Any

class BaseCollector(ABC):
    """Abstract base class for data collectors"""
    
    def __init__(self, brands: List[str], keywords: List[str] = None):
        self.brands = brands
        self.keywords = keywords or []
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        """Collect data from the source
        
        Returns:
            List of dictionaries containing collected data
        """
        pass
    
    def format_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format raw data into a standardized format
        
        Args:
            raw_data: Raw data from the source
            
        Returns:
            Formatted data dictionary
        """
        # Default implementation - override in subclasses
        return {
            "source": "unknown",
            "content": "",
            "created_at": datetime.utcnow(),
            "author": "",
            "url": "",
            "engagement": 0,
            "brand": "",
            "title": "",
        }
    
    def save_data(self, data: List[Dict[str, Any]]) -> None:
        """Save collected data
        
        Args:
            data: List of formatted data dictionaries
        """
        self.logger.info(f"Collected {len(data)} items")
        # Implementation will depend on storage method
        pass