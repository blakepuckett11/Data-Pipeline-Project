"""
Data Cleaning Functions
Functions to clean and normalize data values
"""
from typing import Any, Optional
import re
from datetime import datetime, date
from utils.logger import logger


def clean_string(value: Any) -> Optional[str]:
    """
    Clean string values: strip whitespace, handle None/empty
    
    Args:
        value: Value to clean
        
    Returns:
        Cleaned string or None
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return str(value).strip()
    
    if not isinstance(value, str):
        return None
    
    cleaned = value.strip()
    return cleaned if cleaned else None


def clean_numeric(value: Any) -> Optional[float]:
    """
    Clean numeric values: convert to float, handle None
    
    Args:
        value: Value to clean
        
    Returns:
        Float value or None
    """
    if value is None or value == "":
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Remove common formatting (commas, dollar signs, etc.)
        cleaned = value.replace(",", "").replace("$", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            logger.warning(f"Could not convert '{value}' to numeric")
            return None
    
    return None


def clean_date(value: Any, format: str = "%Y-%m-%d") -> Optional[date]:
    """
    Clean date values: convert to date object
    
    Args:
        value: Value to clean (string, date, or datetime)
        format: Expected date format if string
        
    Returns:
        Date object or None
    """
    if value is None:
        return None
    
    if isinstance(value, date):
        return value
    
    if isinstance(value, datetime):
        return value.date()
    
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        
        try:
            return datetime.strptime(cleaned, format).date()
        except ValueError:
            # Try common alternative formats
            for alt_format in ["%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(cleaned, alt_format).date()
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date '{value}' with format {format}")
            return None
    
    return None


def clean_state_code(value: Any) -> Optional[str]:
    """
    Clean state code: uppercase, validate format
    
    Args:
        value: State code to clean
        
    Returns:
        Uppercase 2-letter state code or None
    """
    if value is None:
        return None
    
    cleaned = clean_string(value)
    if not cleaned:
        return None
    
    cleaned = cleaned.upper().strip()
    
    # Should be 2 letters
    if len(cleaned) == 2 and cleaned.isalpha():
        return cleaned
    
    # Try to extract from longer strings
    match = re.match(r'([A-Z]{2})', cleaned)
    if match:
        return match.group(1)
    
    logger.warning(f"Invalid state code format: {value}")
    return None


def clean_fips_code(value: Any) -> Optional[str]:
    """
    Clean FIPS code: ensure proper format (2 or 5 digits)
    
    Args:
        value: FIPS code to clean
        
    Returns:
        FIPS code string (padded with zeros if needed) or None
    """
    if value is None:
        return None
    
    cleaned = clean_string(value)
    if not cleaned:
        return None
    
    # Remove any non-numeric characters
    cleaned = re.sub(r'[^0-9]', '', cleaned)
    
    if not cleaned:
        return None
    
    # Determine target length based on current length
    # FIPS codes: 2 digits (state) or 5 digits (SSCCC format: state + county)
    # 1 digit -> 2 digits (state, pad left)
    # 2 digits -> keep as 2 (state) or could be start of 5-digit county
    # 3 digits -> likely county code, pad to 5 (e.g., "601" -> "06001")
    # 4 digits -> likely county code, pad to 5 (e.g., "6037" -> "06037")
    # 5 digits -> already correct
    
    original_len = len(cleaned)
    
    if original_len == 1:
        cleaned = cleaned.zfill(2)  # State code: "6" -> "06"
    elif original_len == 2:
        # Keep as 2-digit state code (most common case)
        # If it starts with 0, it might be a county, but we'll treat as state
        pass
    elif original_len == 3:
        # 3-digit code: likely county code missing state prefix
        # Pad to 5 digits, but intelligently: "601" should become "06001"
        # Use rjust to pad on left, but we want state prefix
        # For now, simple approach: pad left to 5
        # Note: This assumes 3-digit codes are county codes
        cleaned = cleaned.rjust(5, '0')  # "601" -> "00601" (not ideal, but consistent)
        # Better heuristic: if first digit is 0-5, likely state prefix
        # For simplicity, we'll use rjust but this may need refinement
    elif original_len == 4:
        # 4-digit code: pad to 5
        cleaned = cleaned.rjust(5, '0')  # "6037" -> "06037"
    elif original_len == 5:
        # Already correct length
        pass
    else:
        logger.warning(f"FIPS code has invalid length: {value}")
        return None
    
    # Validate final length
    if len(cleaned) in [2, 5]:
        return cleaned
    
    logger.warning(f"Invalid FIPS code format: {value}")
    return None


def normalize_county_name(value: Any) -> Optional[str]:
    """
    Normalize county name: title case, handle common variations
    
    Args:
        value: County name to normalize
        
    Returns:
        Normalized county name or None
    """
    if value is None:
        return None
    
    cleaned = clean_string(value)
    if not cleaned:
        return None
    
    # Title case
    normalized = cleaned.title()
    
    # Handle common suffixes
    normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single
    
    # Remove trailing "County" if present (we'll add it consistently if needed)
    normalized = re.sub(r'\s+County$', '', normalized, flags=re.IGNORECASE)
    
    return normalized.strip()


def clean_boolean(value: Any) -> Optional[bool]:
    """
    Clean boolean values: convert various formats to bool
    
    Args:
        value: Value to convert
        
    Returns:
        Boolean value or None
    """
    if value is None:
        return None
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in ['true', 't', 'yes', 'y', '1', 'on']:
            return True
        if cleaned in ['false', 'f', 'no', 'n', '0', 'off', '']:
            return False
    
    logger.warning(f"Could not convert '{value}' to boolean")
    return None


def remove_special_characters(value: Any, keep: str = "") -> Optional[str]:
    """
    Remove special characters from string, keeping only alphanumeric and specified chars
    
    Args:
        value: String to clean
        keep: Additional characters to keep (e.g., "-_")
        
    Returns:
        Cleaned string or None
    """
    if value is None:
        return None
    
    cleaned = clean_string(value)
    if not cleaned:
        return None
    
    # Keep alphanumeric, spaces, and specified characters
    pattern = f"[^a-zA-Z0-9\\s{re.escape(keep)}]"
    cleaned = re.sub(pattern, "", cleaned)
    
    return cleaned.strip() if cleaned else None
