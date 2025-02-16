import re

def sanitize_filename(filename):
    """
    Create a clean, filesystem-friendly filename
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove or replace problematic characters
    # 1. Replace brackets, quotes, and special characters with underscores
    sanitized = re.sub(r'[\[\]\(\)\{\}\'"#]', '_', filename)
    # 2. Replace Windows-unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', sanitized)
    # 3. Replace other problematic characters (spaces, dots, etc)
    sanitized = re.sub(r'[^\w\-]', '_', sanitized)
    
    # Remove any leading/trailing underscores or dots
    sanitized = sanitized.strip('._')
    
    # Replace multiple underscores with a single one
    sanitized = re.sub(r'_+', '_', sanitized)
    
    return sanitized
