import re
import string
import nltk
from typing import List, Set

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Get stopwords
stopwords = set(nltk.corpus.stopwords.words('english'))

def clean_text(text: str) -> str:
    """Clean text by removing special characters, URLs, etc.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def tokenize_text(text: str) -> List[str]:
    """Tokenize text into words
    
    Args:
        text: Text to tokenize
        
    Returns:
        List of tokens
    """
    if not text:
        return []
    
    # Tokenize
    tokens = nltk.word_tokenize(text)
    
    # Remove stopwords
    tokens = [token for token in tokens if token not in stopwords]
    
    # Remove short tokens
    tokens = [token for token in tokens if len(token) > 2]
    
    return tokens

def extract_keywords(text: str, n: int = 10) -> List[str]:
    """Extract keywords from text
    
    Args:
        text: Text to extract keywords from
        n: Number of keywords to extract
        
    Returns:
        List of keywords
    """
    # Clean and tokenize text
    clean = clean_text(text)
    tokens = tokenize_text(clean)
    
    # Count word frequencies
    freq_dist = nltk.FreqDist(tokens)
    
    # Get top n keywords
    keywords = [word for word, _ in freq_dist.most_common(n)]
    
    return keywords

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using Jaccard similarity
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0-1)
    """
    # Clean and tokenize texts
    tokens1 = set(tokenize_text(clean_text(text1)))
    tokens2 = set(tokenize_text(clean_text(text2)))
    
    # Calculate Jaccard similarity
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union)

def is_relevant_to_brand(text: str, brand: str, keywords: List[str] = None) -> bool:
    """Check if text is relevant to a brand
    
    Args:
        text: Text to check
        brand: Brand name
        keywords: Additional keywords to check
        
    Returns:
        True if relevant, False otherwise
    """
    if not text:
        return False
    
    # Clean text
    clean = clean_text(text)
    
    # Check if brand is mentioned
    if brand.lower() in clean:
        return True
    
    # Check if keywords are mentioned
    if keywords:
        for keyword in keywords:
            if keyword.lower() in clean:
                return True
    
    return False

def summarize_text(text: str, max_sentences: int = 3) -> str:
    """Create a simple summary of text by extracting key sentences
    
    Args:
        text: Text to summarize
        max_sentences: Maximum number of sentences in summary
        
    Returns:
        Summarized text
    """
    if not text:
        return ""
    
    # Split into sentences
    sentences = nltk.sent_tokenize(text)
    
    # If text is already short, return as is
    if len(sentences) <= max_sentences:
        return text
    
    # Calculate sentence scores based on word frequency
    word_freq = {}
    for sentence in sentences:
        for word in tokenize_text(clean_text(sentence)):
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Score sentences
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        for word in tokenize_text(clean_text(sentence)):
            if word in word_freq:
                sentence_scores[i] = sentence_scores.get(i, 0) + word_freq[word]
    
    # Get top sentences
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
    top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Sort by original order
    
    # Create summary
    summary = ' '.join([sentences[i] for i, _ in top_sentences])
    
    return summary