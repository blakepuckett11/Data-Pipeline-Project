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
            self.rate_limiter.wait_if_needed()
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            logger.debug(f"Retrieved metadata for dataset {dataset_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch metadata for {dataset_id}: {e}")
            raise
    
    def get_dataset_data(
        self,
        dataset_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        where: Optional[str] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from a CDC dataset
        
        Args:
            dataset_id: Socrata dataset ID
            limit: Maximum number of rows to return
            offset: Number of rows to skip (for pagination)
            where: SoQL WHERE clause (e.g., "state='CA'")
            order: SoQL ORDER BY clause (e.g., "date DESC")
            
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
            self.rate_limiter.wait_if_needed()
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            records = [row.get("row", {}) for row in data] if isinstance(data, list) else []
            
            logger.info(f"Retrieved {len(records)} records from dataset {dataset_id}")
            return records
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data for {dataset_id}: {e}")
            raise
    
    def get_all_dataset_data(
        self,
        dataset_id: str,
        batch_size: int = 5000,
        where: Optional[str] = None,
        order: Optional[str] = None
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
            batch = self.get_dataset_data(
                dataset_id=dataset_id,
                limit=batch_size,
                offset=offset,
                where=where,
                order=order
            )
            
            if not batch:
                break
            
            all_records.extend(batch)
            offset += len(batch)
            
            logger.debug(f"Fetched {len(all_records)} total records so far...")
            
            # If we got fewer records than batch_size, we've reached the end
            if len(batch) < batch_size:
                break
        
        logger.info(f"Completed fetching {len(all_records)} total records")
        return all_records
