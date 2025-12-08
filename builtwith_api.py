"""
BuiltWith API Python Interface

Python clients for BuiltWith APIs:
- Lists API: Query websites using specific technologies
- Keywords API: Get keywords for domains

Documentation: 
- https://api.builtwith.com/lists-api
- https://api.builtwith.com/keywords-api
"""

import requests
from typing import Optional, Dict, List, Union, Literal
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
builtWithAPIKey = os.getenv("BUILTWITH_API_KEY")

class BuiltWithAPIError(Exception):
    """Base exception for BuiltWith API errors"""
    pass


class BuiltWithListsClient:
    """Client for interacting with the BuiltWith Lists API to get websites using a specific technology"""
    
    BASE_URL = "https://api.builtwith.com/lists12/api"
    
    def __init__(self, api_key: str = builtWithAPIKey):
        """
        Initialize the BuiltWith API client.
        
        Args:
            api_key: Your BuiltWith API key
        """
        self.api_key = api_key
        self.session = requests.Session()
    
    def _build_url(self, format: Literal["json", "xml", "txt", "csv", "tsv"] = "json") -> str:
        """
        Build the API endpoint URL with the specified format.
        
        Args:
            format: Response format (json, xml, txt, csv, tsv)
            
        Returns:
            Full API endpoint URL
        """
        return f"{self.BASE_URL}.{format}"
    
    def _make_request(
        self,
        params: Dict[str, Union[str, bool]],
        format: str = "json"
    ) -> Union[Dict, str]:
        """
        Make a request to the BuiltWith API.
        
        Args:
            params: Query parameters for the API request
            format: Response format (json, xml, txt, csv, tsv)
            
        Returns:
            Parsed JSON dict for json format, raw text for other formats
            
        Raises:
            BuiltWithAPIError: If the API returns an error or request fails
        """
        url = self._build_url(format)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            if format == "json":
                data = response.json()
                if isinstance(data, dict) and 'Errors' in data:
                    raise BuiltWithAPIError(f"API Error: {data['Errors']}")
                return data
            return response.text
                
        except requests.exceptions.RequestException as e:
            raise BuiltWithAPIError(f"Request failed: {str(e)}")
    
    def get_tech_list(
        self,
        technology: str,
        include_meta: bool = False,
        country: Optional[Union[str, List[str]]] = None,
        offset: Optional[str] = None,
        since: Optional[str] = None,
        include_all: bool = False,
        format: Literal["json", "xml", "txt", "csv", "tsv"] = "json"
    ) -> Union[Dict, str]:
        """
        Get websites using a specific technology.
        
        Args:
            technology: Technology name (e.g., "Shopify", "Magento")
            include_meta: Include company metadata (name, emails, phones, social)
            country: ISO 3166-1 alpha-2 code(s) (e.g., "US" or ["US", "CA"])
            offset: Pagination token from NextOffset field
            since: Date filter (e.g., "2024-01-01" or "30 Days Ago")
            include_all: Include sites that stopped using the technology
            format: Response format (json, xml, txt, csv, tsv)
            
        Returns:
            Dict with 'NextOffset' and 'Results' keys for json format, raw text for other formats
            
        Raises:
            ValueError: If both 'since' and 'include_all' are specified
            BuiltWithAPIError: If the API request fails
        """
        params = {
            "KEY": self.api_key,
            "TECH": technology.replace(" ", "-")
        }
        
        if include_meta:
            params["META"] = "yes"
        
        if country:
            if isinstance(country, list):
                params["COUNTRY"] = ",".join(country)
            else:
                params["COUNTRY"] = country
        
        if offset:
            params["OFFSET"] = offset
        
        if since:
            if include_all:
                raise ValueError("Cannot use 'since' parameter with 'include_all=True'")
            params["SINCE"] = since
        
        if include_all:
            params["ALL"] = "yes"
        
        return self._make_request(params, format)
    
    def iterate_tech_list(
        self,
        technology: str,
        include_meta: bool = False,
        country: Optional[Union[str, List[str]]] = None,
        since: Optional[str] = None,
        include_all: bool = False,
        max_pages: Optional[int] = None
    ):
        """
        Generator that handles pagination automatically.
        
        Args:
            technology: Technology name
            include_meta: Include company metadata
            country: ISO 3166-1 alpha-2 code(s)
            since: Date filter
            include_all: Include sites that stopped using the technology
            max_pages: Maximum number of pages to fetch (None = unlimited)
            
        Yields:
            Dict: Each page of results with 'NextOffset' and 'Results' keys
        """
        offset = None
        page_count = 0
        
        while True:
            # Check if we've reached max pages
            if max_pages is not None and page_count >= max_pages:
                break
            
            result = self.get_tech_list(
                technology=technology,
                include_meta=include_meta,
                country=country,
                offset=offset,
                since=since,
                include_all=include_all
            )
            
            yield result
            page_count += 1
            
            next_offset = result.get('NextOffset')
            if not next_offset or next_offset == 'END':
                break
            
            offset = next_offset
    
    def get_all_tech_list(
        self,
        technology: str,
        include_meta: bool = False,
        country: Optional[Union[str, List[str]]] = None,
        since: Optional[str] = None,
        include_all: bool = False,
        max_pages: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all results for a technology query with automatic pagination.
        
        Args:
            technology: Technology name
            include_meta: Include company metadata
            country: ISO 3166-1 alpha-2 code(s)
            since: Date filter
            include_all: Include sites that stopped using the technology
            max_pages: Maximum number of pages to fetch (None = unlimited)
            
        Returns:
            List of all site result dicts combined from all pages
        """
        all_results = []
        
        for page in self.iterate_tech_list(
            technology=technology,
            include_meta=include_meta,
            country=country,
            since=since,
            include_all=include_all,
            max_pages=max_pages
        ):
            all_results.extend(page.get('Results', []))
        
        return all_results
    
    def parse_result(self, result: Dict) -> Dict:
        """
        Parse API result into readable format with datetime objects.
        
        Args:
            result: Single result dict from API response
            
        Returns:
            Dict with readable field names and datetime objects instead of epoch timestamps
        """
        parsed = {
            'domain': result.get('D'),
            'locations_on_site': result.get('LOS', []),
            'first_detected': self._parse_epoch(result.get('FD')),
            'last_detected': self._parse_epoch(result.get('LD')),
            'monthly_spend_usd': result.get('S'),
            'unique_products': result.get('SKU'),
            'estimated_revenue': result.get('R'),
            'social_followers': result.get('F'),
            'employee_count': result.get('E'),
            'page_rank': result.get('A'),
            'tranco_rank': result.get('Q'),
            'majestic_rank': result.get('M'),
            'umbrella_rank': result.get('U'),
        }
        
        if 'META' in result:
            parsed['metadata'] = result['META']
        
        return parsed
    
    @staticmethod
    def _parse_epoch(epoch_seconds: Optional[int]) -> Optional[datetime]:
        """
        Convert epoch seconds to datetime object.
        
        Args:
            epoch_seconds: Unix timestamp in seconds
            
        Returns:
            datetime object or None if input is None
        """
        if epoch_seconds:
            return datetime.fromtimestamp(epoch_seconds)
        return None


class BuiltWithKeywordsClient:
    """Client for interacting with the BuiltWith Keywords API to get keywords for domains"""
    
    BASE_URL = "https://api.builtwith.com/kw2/api"
    
    def __init__(self, api_key: str = builtWithAPIKey):
        """
        Initialize the BuiltWith Keywords API client.
        
        Args:
            api_key: Your BuiltWith API key
        """
        self.api_key = api_key
        self.session = requests.Session()
    
    def _build_url(self, format: Literal["json", "xml"] = "json") -> str:
        """
        Build the API endpoint URL with the specified format.
        
        Args:
            format: Response format (json, xml)
            
        Returns:
            Full API endpoint URL
        """
        return f"{self.BASE_URL}.{format}"
    
    def _make_request(
        self,
        params: Dict[str, str],
        format: str = "json"
    ) -> Union[Dict, str]:
        """
        Make a request to the BuiltWith Keywords API.
        
        Args:
            params: Query parameters for the API request
            format: Response format (json, xml)
            
        Returns:
            Parsed JSON dict for json format, raw text for xml format
            
        Raises:
            BuiltWithAPIError: If the API returns an error or request fails
        """
        url = self._build_url(format)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            if format == "json":
                data = response.json()
                if isinstance(data, dict) and 'Errors' in data:
                    raise BuiltWithAPIError(f"API Error: {data['Errors']}")
                return data
            return response.text
                
        except requests.exceptions.RequestException as e:
            raise BuiltWithAPIError(f"Request failed: {str(e)}")
    
    def get_keywords(
        self,
        domain: Union[str, List[str]],
        format: Literal["json", "xml"] = "json"
    ) -> Union[Dict, str]:
        """
        Get keywords for one or more domains.
        
        Args:
            domain: Single domain string or list of up to 16 domains (root domains only, no subdomains)
            format: Response format (json, xml)
            
        Returns:
            Dict with domain and keywords for json format, raw text for xml format
            
        Raises:
            BuiltWithAPIError: If the API request fails
            ValueError: If more than 16 domains are provided
        """
        if isinstance(domain, list):
            if len(domain) > 16:
                raise ValueError("Maximum 16 domains allowed per request")
            lookup = ",".join(domain)
        else:
            lookup = domain
        
        params = {
            "KEY": self.api_key,
            "LOOKUP": lookup
        }
        
        return self._make_request(params, format)
    
    def get_keywords_batch(
        self,
        domains: List[str],
        batch_size: int = 16
    ) -> List[Dict]:
        """
        Get keywords for a large list of domains by batching requests.
        
        Args:
            domains: List of domain strings
            batch_size: Number of domains per request (max 16)
            
        Returns:
            List of result dicts from all batches combined
            
        Raises:
            ValueError: If batch_size > 16
        """
        if batch_size > 16:
            raise ValueError("Maximum batch size is 16 domains")
        
        all_results = []
        
        for i in range(0, len(domains), batch_size):
            batch = domains[i:i + batch_size]
            result = self.get_keywords(batch)
            
            if isinstance(result, dict):
                all_results.append(result)
        
        return all_results

if __name__ == "__main__":
    # Test Lists API
    lists_client = BuiltWithListsClient()
    response = lists_client.get_tech_list("Shopify")
    print(f"Found {len(response['Results'])} Shopify sites")
    for result in response['Results'][:5]:
        print(f"  - {result.get('D')}: Revenue ${result.get('R', 0):,}")
    
    # Test Keywords API
    keywords_client = BuiltWithKeywordsClient()
    kw_response = keywords_client.get_keywords("wayfair.com")
    print(f"\nKeywords for {kw_response.get('Domain', 'N/A')}:")
    for kw in kw_response.get('Keywords', [])[:5]:
        print(f"  - {kw}")
