# BuiltWith API Python Client

Python client library for interacting with the BuiltWith APIs. This package provides clean, typed interfaces for querying websites using specific technologies and retrieving keyword data for domains.

## Features

- **Lists API Client**: Query websites using specific technologies (e.g., Shopify, Magento)
- **Keywords API Client**: Get SEO keywords for domains
- Automatic pagination handling
- Type hints for better IDE support
- Multiple output formats (JSON, XML, CSV, TSV, TXT)
- Built-in error handling
- Session management for optimal performance

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd CompanySearch
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API key:
Create a `.env` file in the project root:
```
BUILTWITH_API_KEY=your_api_key_here
```

Get your API key from [BuiltWith](https://api.builtwith.com/).

## Usage

### Lists API - Find Websites Using Technologies

#### Basic Query

```python
from builtwith_api import BuiltWithListsClient

# Initialize the client
client = BuiltWithListsClient()

# Get websites using Shopify
response = client.get_tech_list("Shopify")

for site in response['Results']:
    print(f"Domain: {site['D']}")
    print(f"Revenue: ${site.get('R', 0):,}")
```

#### Advanced Query with Filters

```python
# Get Shopify sites in the US added in the last 30 days
response = client.get_tech_list(
    technology="Shopify",
    country="US",
    since="30 Days Ago",
    include_meta=True  # Include company metadata (emails, phones, etc.)
)
```

#### Automatic Pagination

```python
# Get all results with automatic pagination
all_results = client.get_all_tech_list(
    technology="Magento",
    country=["US", "CA"],
    max_pages=10  # Optional: limit number of pages
)

print(f"Total sites found: {len(all_results)}")
```

#### Manual Pagination with Iterator

```python
# Process results page by page
for page in client.iterate_tech_list(technology="WooCommerce", max_pages=5):
    for site in page['Results']:
        print(site['D'])
```

#### Parse Results for Readability

```python
response = client.get_tech_list("Shopify")

for result in response['Results']:
    # Convert to readable format with datetime objects
    parsed = client.parse_result(result)
    print(f"Domain: {parsed['domain']}")
    print(f"First Detected: {parsed['first_detected']}")
    print(f"Last Detected: {parsed['last_detected']}")
    print(f"Revenue: ${parsed['estimated_revenue']:,}")
```

### Keywords API - Get Domain Keywords

#### Single Domain

```python
from builtwith_api import BuiltWithKeywordsClient

# Initialize the client
client = BuiltWithKeywordsClient()

# Get keywords for a domain
response = client.get_keywords("wayfair.com")

print(f"Domain: {response['Domain']}")
for keyword in response['Keywords']:
    print(f"  - {keyword}")
```

#### Multiple Domains (up to 16 per request)

```python
# Query multiple domains at once
response = client.get_keywords([
    "amazon.com",
    "ebay.com",
    "etsy.com"
])
```

#### Batch Processing for Large Lists

```python
# Process hundreds or thousands of domains
domains = ["domain1.com", "domain2.com", ...]  # Your domain list

results = client.get_keywords_batch(
    domains=domains,
    batch_size=16  # Max 16 per request
)

for batch in results:
    print(f"Domain: {batch.get('Domain')}")
    print(f"Keywords: {len(batch.get('Keywords', []))}")
```

## API Reference

### BuiltWithListsClient

#### `get_tech_list()`

Get websites using a specific technology.

**Parameters:**
- `technology` (str): Technology name (e.g., "Shopify", "WordPress")
- `include_meta` (bool): Include company metadata (name, emails, phones, social)
- `country` (str or List[str]): ISO 3166-1 alpha-2 code(s) (e.g., "US" or ["US", "CA"])
- `offset` (str, optional): Pagination token from NextOffset field
- `since` (str, optional): Date filter (e.g., "2024-01-01" or "30 Days Ago")
- `include_all` (bool): Include sites that stopped using the technology
- `format` (str): Response format ("json", "xml", "txt", "csv", "tsv")

**Returns:** Dict with 'NextOffset' and 'Results' keys

#### `iterate_tech_list()`

Generator that yields pages of results with automatic pagination.

**Parameters:** Same as `get_tech_list()` plus:
- `max_pages` (int, optional): Maximum number of pages to fetch

**Yields:** Dict for each page

#### `get_all_tech_list()`

Get all results with automatic pagination combined into a single list.

**Returns:** List of all site result dicts

#### `parse_result(result)`

Parse API result into readable format with datetime objects.

**Parameters:**
- `result` (Dict): Single result dict from API response

**Returns:** Dict with readable field names

### BuiltWithKeywordsClient

#### `get_keywords()`

Get keywords for one or more domains.

**Parameters:**
- `domain` (str or List[str]): Single domain or list of up to 16 domains
- `format` (str): Response format ("json", "xml")

**Returns:** Dict with domain and keywords

#### `get_keywords_batch()`

Get keywords for large lists of domains by batching requests.

**Parameters:**
- `domains` (List[str]): List of domain strings
- `batch_size` (int): Number of domains per request (max 16)

**Returns:** List of result dicts from all batches

## Response Fields

### Lists API Response Fields

| Field | Key | Description |
|-------|-----|-------------|
| Domain | D | Website domain |
| Locations on Site | LOS | Where technology was detected |
| First Detected | FD | Unix timestamp (use `parse_result()` for datetime) |
| Last Detected | LD | Unix timestamp |
| Monthly Spend USD | S | Estimated monthly technology spend |
| SKU Count | SKU | Number of unique products |
| Revenue | R | Estimated annual revenue |
| Social Followers | F | Total social media followers |
| Employee Count | E | Estimated employee count |
| Page Rank | A | Alexa rank |
| Tranco Rank | Q | Tranco rank |
| Majestic Rank | M | Majestic rank |
| Umbrella Rank | U | Cisco Umbrella rank |
| Metadata | META | Company info (when `include_meta=True`) |

## Error Handling

```python
from builtwith_api import BuiltWithAPIError

try:
    client = BuiltWithListsClient(api_key="your_key")
    response = client.get_tech_list("Shopify")
except BuiltWithAPIError as e:
    print(f"API Error: {e}")
```

## Export Formats

```python
# Export as CSV
csv_data = client.get_tech_list("Shopify", format="csv")

# Export as TSV
tsv_data = client.get_tech_list("Shopify", format="tsv")

# Export as XML
xml_data = client.get_tech_list("Shopify", format="xml")
```

## Requirements

- Python 3.7+
- requests
- python-dotenv

## Documentation

- [BuiltWith Lists API Documentation](https://api.builtwith.com/lists-api)
- [BuiltWith Keywords API Documentation](https://api.builtwith.com/keywords-api)

## License

See LICENSE file for details.
