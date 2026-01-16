"""
CDC Open Data API Client
Handles HTTP requests to CDC API with rate limiting and error handling
"""
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.config import cdc_api_config
from utils.logger import logger


class RateLimiter:
    """
    Simple rate limiter using token bucket algorithm
    Tracks requests and enforces rate limits
    """
    
    def __init__(self, max_requests: int, period_seconds: int):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed
            period_seconds: Time period in seconds
        """
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self.requests = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove requests older than the period
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.period_seconds]
        
        # If at limit, wait until oldest request expires
        if len(self.requests) >= self.max_requests:
            sleep_time = self.period_seconds - (now - self.requests[0]) + 0.1
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                # Clean up again after sleep
                self.requests = [req_time for req_time in self.requests 
                               if time.time() - req_time < self.period_seconds]
        
        # Record this request
        self.requests.append(time.time())


class CDCAPIClient:
    """
    Client for interacting with CDC Open Data API (Socrata API)
    
    The CDC uses Socrata Open Data API which provides:
    - Dataset metadata via /api/views/{dataset_id}
    - Data export via /api/views/{dataset_id}/rows.json
    - Query capabilities with SoQL (Socrata Query Language)
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        rate_limit_requests: Optional[int] = None,
        rate_limit_period: Optional[int] = None
    ):
        """
        Initialize CDC API client
        
        Args:
            base_url: Base URL for CDC API (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
            rate_limit_requests: Max requests per period (defaults to config)
            rate_limit_period: Period in seconds (defaults to config)
        """
        self.base_url = base_url or cdc_api_config.base_url
        self.timeout = timeout or cdc_api_config.timeout
        
        # Set up rate limiter
        max_reqs = rate_limit_requests or cdc_api_config.rate_limit_requests
        period = rate_limit_period or cdc_api_config.rate_limit_period
        self.rate_limiter = RateLimiter(max_reqs, period)
        
        # Set up requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"CDC API Client initialized: {self.base_url}")
    
    def get_dataset_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get metadata for a CDC dataset
        
        Args:
            dataset_id: Socrata dataset ID (found in dataset URL)
            
        Returns:
            Dictionary containing dataset metadata
            
        Example:
            dataset_id = "8xkx-amqh"  # Example COVID-19 dataset
        """
        url = f"{self.base_url}/{dataset_id}.json"
        
        try:
            logger.info(f"Fetching metadata from CDC API: {url}")
            self.rate_limiter.wait_if_needed()
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            metadata = response.json()
            logger.info(f"✓ Retrieved metadata for dataset {dataset_id}: {metadata.get('name', 'N/A')}")
            return metadata
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching metadata for {dataset_id} (timeout: {self.timeout}s)")
            raise Exception(f"API request timed out after {self.timeout} seconds. The dataset may be unavailable or the API is slow.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch metadata for {dataset_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text[:200]}")
            raise
    
    def get_dataset_data(
        self,
        dataset_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        where: Optional[str] = None,
        order: Optional[str] = None,
        use_resource_endpoint: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from a CDC dataset
        
        Args:
            dataset_id: Socrata dataset ID or resource ID
            limit: Maximum number of rows to return
            offset: Number of rows to skip (for pagination)
            where: SoQL WHERE clause (e.g., "state='CA'")
            order: SoQL ORDER BY clause (e.g., "date DESC")
            use_resource_endpoint: If True, use /resource/ endpoint instead of /api/views/
            
        Returns:
            List of records as dictionaries
            
        Example:
            data = client.get_dataset_data(
                "8xkx-amqh",
                limit=1000,
                where="state='CA'",
                order="date DESC"
            )
        """
        # Support both endpoint formats
        if use_resource_endpoint:
            # Format: https://data.cdc.gov/resource/{dataset_id}.json
            url = f"https://data.cdc.gov/resource/{dataset_id}.json"
        else:
            # Format: https://data.cdc.gov/api/views/{dataset_id}/rows.json
            url = f"{self.base_url}/{dataset_id}/rows.json"
        params = {}
        
        if limit:
            params["$limit"] = limit
        if offset:
            params["$offset"] = offset
        if where:
            params["$where"] = where
        if order:
            params["$order"] = order
        
        try:
            logger.debug(f"Fetching data from CDC API: {url} (limit={limit}, offset={offset})")
            self.rate_limiter.wait_if_needed()
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Socrata API can return data in different formats:
            # 1. List of objects with "row" key: [{"row": {...}}, ...] (old /api/views/ format)
            # 2. Dictionary with "data" key: {"data": [[...], ...]}
            # 3. Direct list: [{...}, ...] (new /resource/ format - what we're getting)
            
            records = []
            if isinstance(data, list):
                # Check if it's format 1: list with "row" keys
                if len(data) > 0 and isinstance(data[0], dict) and "row" in data[0]:
                    records = [row.get("row", {}) for row in data]
                # Format 3: direct list of records (most common for /resource/ endpoint)
                elif len(data) > 0 and isinstance(data[0], dict):
                    records = data
            elif isinstance(data, dict):
                # Try format 2: dictionary with "data" key
                if "data" in data:
                    # Data is usually a list of lists, need to map to column names
                    logger.warning(f"Dataset {dataset_id} uses 'data' format - may need column mapping")
                    records = []
                else:
                    # Try other dictionary formats
                    records = []
            
            if len(records) == 0 and data:
                # Log the actual structure for debugging
                logger.warning(f"Unexpected API response format for {dataset_id}")
                logger.debug(f"Response type: {type(data)}, Length: {len(data) if isinstance(data, list) else 'N/A'}")
                if isinstance(data, list) and len(data) > 0:
                    logger.debug(f"First item keys: {list(data[0].keys())[:10] if isinstance(data[0], dict) else 'N/A'}")
            
            logger.info(f"✓ Retrieved {len(records)} records from dataset {dataset_id}")
            return records
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching data for {dataset_id} (timeout: {self.timeout}s)")
            raise Exception(f"API request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data for {dataset_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
            raise
    
    def get_all_dataset_data(
        self,
        dataset_id: str,
        batch_size: int = 5000,
        where: Optional[str] = None,
        order: Optional[str] = None,
        use_resource_endpoint: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch all data from a dataset with automatic pagination
        
        Args:
            dataset_id: Socrata dataset ID
            batch_size: Number of records per batch
            where: SoQL WHERE clause
            order: SoQL ORDER BY clause
            
        Returns:
            List of all records
        """
        all_records = []
        offset = 0
        
        logger.info(f"Fetching all data from dataset {dataset_id} (batch size: {batch_size})")
        
        while True:
            logger.info(f"Fetching batch starting at offset {offset}...")
            batch = self.get_dataset_data(
                dataset_id=dataset_id,
                limit=batch_size,
                offset=offset,
                where=where,
                order=order,
                use_resource_endpoint=use_resource_endpoint
            )
            
            if not batch:
                logger.info("No more records to fetch")
                break
            
            all_records.extend(batch)
            offset += len(batch)
            
            logger.info(f"Progress: {len(all_records)} total records fetched...")
            
            # If we got fewer records than batch_size, we've reached the end
            if len(batch) < batch_size:
                logger.info("Reached end of dataset")
                break
        
        logger.info(f"Completed fetching {len(all_records)} total records")
        return all_records
