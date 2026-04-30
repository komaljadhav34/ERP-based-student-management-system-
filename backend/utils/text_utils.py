import re

def preprocess_text(text: str) -> str:
    """
    Cleans raw text for chunking by removing extra spaces and normalizing whitespace,
    while preserving punctuation that affects meaning.
    
    Args:
        text (str): The input text to be processed.
    
    Returns:
        str: The cleaned and normalized text.
    """
    if not isinstance(text, str):
        return ""
        
    # Collapse all whitespace (spaces, tabs, newlines) into a single space
    cleaned_text = re.sub(r'\s+', ' ', text)
    
    # Strip leading and trailing whitespace
    return cleaned_text.strip()
