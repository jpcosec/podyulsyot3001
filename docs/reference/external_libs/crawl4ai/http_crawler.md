# Crawl4AI External Reference - HTTP-based Crawler

## HTTP-based Crawler - Full Content
Component ID: http_based_crawler_strategy
Context Type: memory
Estimated tokens: 2,390

## HTTP Crawler Strategy

Fast, lightweight HTTP-only crawling without browser overhead for cases where JavaScript execution isn't needed.

### Basic HTTP Crawler Setup

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, HTTPCrawlerConfig, CacheMode
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from crawl4ai.async_logger import AsyncLogger

async def main():
    # Initialize HTTP strategy
    http_strategy = AsyncHTTPCrawlerStrategy(
        browser_config=HTTPCrawlerConfig(
            method="GET",
            verify_ssl=True,
            follow_redirects=True
        ),
        logger=AsyncLogger(verbose=True)
    )

    # Use with AsyncWebCrawler
    async with AsyncWebCrawler(crawler_strategy=http_strategy) as crawler:
        result = await crawler.arun("https://example.com")
        print(f"Status: {result.status_code}")
        print(f"Content: {len(result.html)} chars")

if __name__ == "__main__":
    asyncio.run(main())
```

### HTTP Request Types

```python
# GET request (default)
http_config = HTTPCrawlerConfig(
    method="GET",
    headers={"Accept": "application/json"}
)

# POST with JSON data
http_config = HTTPCrawlerConfig(
    method="POST",
    json={"key": "value", "data": [1, 2, 3]},
    headers={"Content-Type": "application/json"}
)

# POST with form data
http_config = HTTPCrawlerConfig(
    method="POST",
    data={"username": "user", "password": "pass"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

# Advanced configuration
http_config = HTTPCrawlerConfig(
    method="GET",
    headers={"User-Agent": "Custom Bot/1.0"},
    follow_redirects=True,
    verify_ssl=False  # For testing environments
)

strategy = AsyncHTTPCrawlerStrategy(browser_config=http_config)
```

### File and Raw Content Handling

```python
async def test_content_types():
    strategy = AsyncHTTPCrawlerStrategy()
    
    # Web URLs
    result = await strategy.crawl("https://httpbin.org/get")
    print(f"Web content: {result.status_code}")
    
    # Local files
    result = await strategy.crawl("file:///path/to/local/file.html")
    print(f"File content: {len(result.html)}")
    
    # Raw HTML content
    raw_html = "raw://<html><body><h1>Test</h1><p>Content</p></body></html>"
    result = await strategy.crawl(raw_html)
    print(f"Raw content: {result.html}")
    
    # Raw content with complex HTML
    complex_html = """raw://<!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <div class="content">
            <h1>Main Title</h1>
            <p>Paragraph content</p>
            <ul><li>Item 1</li><li>Item 2</li></ul>
        </div>
    </body>
    </html>"""
    result = await strategy.crawl(complex_html)
```

### Custom Hooks and Request Handling

```python
async def setup_hooks():
    strategy = AsyncHTTPCrawlerStrategy()
    
    # Before request hook
    async def before_request(url, kwargs):
        print(f"Requesting: {url}")
        kwargs['headers']['X-Custom-Header'] = 'crawl4ai'
        kwargs['headers']['Authorization'] = 'Bearer token123'
    
    # After request hook
    async def after_request(response):
        print(f"Response: {response.status_code}")
        if hasattr(response, 'redirected_url'):
            print(f"Redirected to: {response.redirected_url}")
    
    # Error handling hook
    async def on_error(error):
        print(f"Request failed: {error}")
    
    # Set hooks
    strategy.set_hook('before_request', before_request)
    strategy.set_hook('after_request', after_request)
    strategy.set_hook('on_error', on_error)
    
    # Use with hooks
    result = await strategy.crawl("https://httpbin.org/headers")
    return result
```

### Performance Configuration

```python
# High-performance setup
strategy = AsyncHTTPCrawlerStrategy(
    max_connections=50,        # Concurrent connections
    dns_cache_ttl=300,        # DNS cache timeout
    chunk_size=128 * 1024     # 128KB chunks for large files
)

# Memory-efficient setup for large files
strategy = AsyncHTTPCrawlerStrategy(
    max_connections=10,
    chunk_size=32 * 1024,     # Smaller chunks
    dns_cache_ttl=600
)

# Custom timeout configuration
config = CrawlerRunConfig(
    page_timeout=30000,       # 30 second timeout
    cache_mode=CacheMode.BYPASS
)

result = await strategy.crawl("https://slow-server.com", config=config)
```

### Error Handling and Retries

```python
from crawl4ai.async_crawler_strategy import (
    ConnectionTimeoutError, 
    HTTPStatusError, 
    HTTPCrawlerError
)

async def robust_crawling():
    strategy = AsyncHTTPCrawlerStrategy()
    
    urls = [
        "https://example.com",
        "https://httpbin.org/status/404",
        "https://nonexistent.domain.test"
    ]
    
    for url in urls:
        try:
            result = await strategy.crawl(url)
            print(f"✓ {url}: {result.status_code}")
            
        except HTTPStatusError as e:
            print(f"✗ {url}: HTTP {e.status_code}")
            
        except ConnectionTimeoutError as e:
            print(f"✗ {url}: Timeout - {e}")
            
        except HTTPCrawlerError as e:
            print(f"✗ {url}: Crawler error - {e}")
            
        except Exception as e:
            print(f"✗ {url}: Unexpected error - {e}")

# Retry mechanism
async def crawl_with_retry(url, max_retries=3):
    strategy = AsyncHTTPCrawlerStrategy()
    
    for attempt in range(max_retries):
        try:
            return await strategy.crawl(url)
        except (ConnectionTimeoutError, HTTPCrawlerError) as e:
            if attempt == max_retries - 1:
                raise
            print(f"Retry {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Batch Processing with HTTP Strategy

```python
async def batch_http_crawling():
    strategy = AsyncHTTPCrawlerStrategy(max_connections=20)
    
    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers",
        "https://example.com",
        "https://httpbin.org/json"
    ]
    
    # Sequential processing
    results = []
    async with strategy:
        for url in urls:
            try:
                result = await strategy.crawl(url)
                results.append((url, result.status_code, len(result.html)))
            except Exception as e:
                results.append((url, "ERROR", str(e)))
    
    for url, status, content_info in results:
        print(f"{url}: {status} - {content_info}")

# Concurrent processing
async def concurrent_http_crawling():
    strategy = AsyncHTTPCrawlerStrategy()
    urls = ["https://httpbin.org/delay/1"] * 5
    
    async def crawl_single(url):
        try:
            result = await strategy.crawl(url)
            return f"✓ {result.status_code}"
        except Exception as e:
            return f"✗ {e}"
    
    async with strategy:
        tasks = [crawl_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        print(f"URL {i+1}: {result}")
```

### Integration with Content Processing

```python
from crawl4ai import DefaultMarkdownGenerator, PruningContentFilter

async def http_with_processing():
    # HTTP strategy with content processing
    http_strategy = AsyncHTTPCrawlerStrategy(
        browser_config=HTTPCrawlerConfig(verify_ssl=True)
    )
    
    # Configure markdown generation
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=10
            )
        ),
        word_count_threshold=5,
        excluded_tags=['script', 'style', 'nav'],
        exclude_external_links=True
    )
    
    async with AsyncWebCrawler(crawler_strategy=http_strategy) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=crawler_config
        )
        
        print(f"Status: {result.status_code}")
        print(f"Raw HTML: {len(result.html)} chars")
        if result.markdown:
            print(f"Markdown: {len(result.markdown.raw_markdown)} chars")
            if result.markdown.fit_markdown:
                print(f"Filtered: {len(result.markdown.fit_markdown)} chars")
```

### HTTP vs Browser Strategy Comparison

```python
async def strategy_comparison():
    # Same URL with different strategies
    url = "https://example.com"
    
    # HTTP Strategy (fast, no JS)
    http_strategy = AsyncHTTPCrawlerStrategy()
    start_time = time.time()
    http_result = await http_strategy.crawl(url)
    http_time = time.time() - start_time
    
    # Browser Strategy (full features)
    from crawl4ai import BrowserConfig
    browser_config = BrowserConfig(headless=True)
    start_time = time.time()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        browser_result = await crawler.arun(url)
    browser_time = time.time() - start_time
    
    print(f"HTTP Strategy:")
    print(f"  Time: {http_time:.2f}s")
    print(f"  Content: {len(http_result.html)} chars")
    print(f"  Features: Fast, lightweight, no JS")
    
    print(f"Browser Strategy:")
    print(f"  Time: {browser_time:.2f}s") 
    print(f"  Content: {len(browser_result.html)} chars")
    print(f"  Features: Full browser, JS, screenshots, etc.")
    
    # When to use HTTP strategy:
    # - Static content sites
    # - APIs returning HTML
    # - Fast bulk processing
    # - No JavaScript required
    # - Memory/resource constraints
    
    # When to use Browser strategy:
    # - Dynamic content (SPA, AJAX)
    # - JavaScript-heavy sites
    # - Screenshots/PDFs needed
    # - Complex interactions required
```

### Advanced Configuration

```python
# Custom session configuration
import aiohttp

async def advanced_http_setup():
    # Custom connector with specific settings
    connector = aiohttp.TCPConnector(
        limit=100,              # Connection pool size
        ttl_dns_cache=600,      # DNS cache TTL
        use_dns_cache=True,     # Enable DNS caching
        keepalive_timeout=30,   # Keep-alive timeout
        force_close=False       # Reuse connections
    )
    
    strategy = AsyncHTTPCrawlerStrategy(
        max_connections=50,
        dns_cache_ttl=600,
        chunk_size=64 * 1024
    )
    
    # Custom headers for all requests
    http_config = HTTPCrawlerConfig(
        headers={
            "User-Agent": "Crawl4AI-HTTP/1.0",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1"
        },
        verify_ssl=True,
        follow_redirects=True
    )
    
    strategy.browser_config = http_config
    
    # Use with custom timeout
    config = CrawlerRunConfig(
        page_timeout=45000,  # 45 seconds
        cache_mode=CacheMode.ENABLED
    )
    
    result = await strategy.crawl("https://example.com", config=config)
    await strategy.close()
```

**📖 Learn more:** [AsyncWebCrawler API](https://docs.crawl4ai.com/api/async-webcrawler/), [Browser vs HTTP Strategy](https://docs.crawl4ai.com/core/browser-crawler-config/), [Performance Optimization](https://docs.crawl4ai.com/advanced/multi-url-crawling/)

---


## HTTP-based Crawler - Diagrams & Workflows
Component ID: http_based_crawler_strategy
Context Type: reasoning
Estimated tokens: 3,413

## HTTP Crawler Strategy Workflows

Visual representations of HTTP-based crawling architecture, request flows, and performance characteristics compared to browser-based strategies.

### HTTP vs Browser Strategy Decision Tree

```mermaid
flowchart TD
    A[Content Crawling Need] --> B{Content Type Analysis}
    
    B -->|Static HTML| C{JavaScript Required?}
    B -->|Dynamic SPA| D[Browser Strategy Required]
    B -->|API Endpoints| E[HTTP Strategy Optimal]
    B -->|Mixed Content| F{Primary Content Source?}
    
    C -->|No JS Needed| G[HTTP Strategy Recommended]
    C -->|JS Required| H[Browser Strategy Required]
    C -->|Unknown| I{Performance Priority?}
    
    I -->|Speed Critical| J[Try HTTP First]
    I -->|Accuracy Critical| K[Use Browser Strategy]
    
    F -->|Mostly Static| G
    F -->|Mostly Dynamic| D
    
    G --> L{Resource Constraints?}
    L -->|Memory Limited| M[HTTP Strategy - Lightweight]
    L -->|CPU Limited| N[HTTP Strategy - No Browser]
    L -->|Network Limited| O[HTTP Strategy - Efficient]
    L -->|No Constraints| P[Either Strategy Works]
    
    J --> Q[Test HTTP Results]
    Q --> R{Content Complete?}
    R -->|Yes| S[Continue with HTTP]
    R -->|No| T[Switch to Browser Strategy]
    
    D --> U[Browser Strategy Features]
    H --> U
    K --> U
    T --> U
    
    U --> V[JavaScript Execution]
    U --> W[Screenshots/PDFs]
    U --> X[Complex Interactions]
    U --> Y[Session Management]
    
    M --> Z[HTTP Strategy Benefits]
    N --> Z
    O --> Z
    S --> Z
    
    Z --> AA[10x Faster Processing]
    Z --> BB[Lower Memory Usage]
    Z --> CC[Higher Concurrency]
    Z --> DD[Simpler Deployment]
    
    style G fill:#c8e6c9
    style M fill:#c8e6c9
    style N fill:#c8e6c9
    style O fill:#c8e6c9
    style S fill:#c8e6c9
    style D fill:#e3f2fd
    style H fill:#e3f2fd
    style K fill:#e3f2fd
    style T fill:#e3f2fd
    style U fill:#e3f2fd
```

### HTTP Request Lifecycle Sequence

```mermaid
sequenceDiagram
    participant Client
    participant HTTPStrategy as HTTP Strategy
    participant Session as HTTP Session
    participant Server as Target Server
    participant Processor as Content Processor
    
    Client->>HTTPStrategy: crawl(url, config)
    HTTPStrategy->>HTTPStrategy: validate_url()
    
    alt URL Type Check
        HTTPStrategy->>HTTPStrategy: handle_file_url()
        Note over HTTPStrategy: file:// URLs
    else
        HTTPStrategy->>HTTPStrategy: handle_raw_content()
        Note over HTTPStrategy: raw:// content
    else
        HTTPStrategy->>Session: prepare_request()
        Session->>Session: apply_config()
        Session->>Session: set_headers()
        Session->>Session: setup_auth()
        
        Session->>Server: HTTP Request
        Note over Session,Server: GET/POST/PUT with headers
        
        alt Success Response
            Server-->>Session: HTTP 200 + Content
            Session-->>HTTPStrategy: response_data
        else Redirect Response
            Server-->>Session: HTTP 3xx + Location
            Session->>Server: Follow redirect
            Server-->>Session: HTTP 200 + Content
            Session-->>HTTPStrategy: final_response
        else Error Response
            Server-->>Session: HTTP 4xx/5xx
            Session-->>HTTPStrategy: error_response
        end
    end
    
    HTTPStrategy->>Processor: process_content()
    Processor->>Processor: clean_html()
    Processor->>Processor: extract_metadata()
    Processor->>Processor: generate_markdown()
    Processor-->>HTTPStrategy: processed_result
    
    HTTPStrategy-->>Client: CrawlResult
    
    Note over Client,Processor: Fast, lightweight processing
    Note over HTTPStrategy: No browser overhead
```

### HTTP Strategy Architecture

```mermaid
graph TB
    subgraph "HTTP Crawler Strategy"
        A[AsyncHTTPCrawlerStrategy] --> B[Session Manager]
        A --> C[Request Builder]
        A --> D[Response Handler]
        A --> E[Error Manager]
        
        B --> B1[Connection Pool]
        B --> B2[DNS Cache]
        B --> B3[SSL Context]
        
        C --> C1[Headers Builder]
        C --> C2[Auth Handler]
        C --> C3[Payload Encoder]
        
        D --> D1[Content Decoder]
        D --> D2[Redirect Handler]
        D --> D3[Status Validator]
        
        E --> E1[Retry Logic]
        E --> E2[Timeout Handler]
        E --> E3[Exception Mapper]
    end
    
    subgraph "Content Processing"
        F[Raw HTML] --> G[HTML Cleaner]
        G --> H[Markdown Generator]
        H --> I[Link Extractor]
        I --> J[Media Extractor]
        J --> K[Metadata Parser]
    end
    
    subgraph "External Resources"
        L[Target Websites]
        M[Local Files]
        N[Raw Content]
    end
    
    subgraph "Output"
        O[CrawlResult]
        O --> O1[HTML Content]
        O --> O2[Markdown Text]
        O --> O3[Extracted Links]
        O --> O4[Media References]
        O --> O5[Status Information]
    end
    
    A --> F
    L --> A
    M --> A
    N --> A
    K --> O
    
    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style F fill:#e8f5e8
    style O fill:#fff3e0
```

### Performance Comparison Flow

```mermaid
graph LR
    subgraph "HTTP Strategy Performance"
        A1[Request Start] --> A2[DNS Lookup: 50ms]
        A2 --> A3[TCP Connect: 100ms]
        A3 --> A4[HTTP Request: 200ms]
        A4 --> A5[Content Download: 300ms]
        A5 --> A6[Processing: 50ms]
        A6 --> A7[Total: ~700ms]
    end
    
    subgraph "Browser Strategy Performance"
        B1[Request Start] --> B2[Browser Launch: 2000ms]
        B2 --> B3[Page Navigation: 1000ms]
        B3 --> B4[JS Execution: 500ms]
        B4 --> B5[Content Rendering: 300ms]
        B5 --> B6[Processing: 100ms]
        B6 --> B7[Total: ~3900ms]
    end
    
    subgraph "Resource Usage"
        C1[HTTP Memory: ~50MB]
        C2[Browser Memory: ~500MB]
        C3[HTTP CPU: Low]
        C4[Browser CPU: High]
        C5[HTTP Concurrency: 100+]
        C6[Browser Concurrency: 10-20]
    end
    
    A7 --> D[5.5x Faster]
    B7 --> D
    C1 --> E[10x Less Memory]
    C2 --> E
    C5 --> F[5x More Concurrent]
    C6 --> F
    
    style A7 fill:#c8e6c9
    style B7 fill:#ffcdd2
    style C1 fill:#c8e6c9
    style C2 fill:#ffcdd2
    style C5 fill:#c8e6c9
    style C6 fill:#ffcdd2
```

### HTTP Request Types and Configuration

```mermaid
stateDiagram-v2
    [*] --> HTTPConfigSetup
    
    HTTPConfigSetup --> MethodSelection
    
    MethodSelection --> GET: Simple data retrieval
    MethodSelection --> POST: Form submission
    MethodSelection --> PUT: Data upload
    MethodSelection --> DELETE: Resource removal
    
    GET --> HeaderSetup: Set Accept headers
    POST --> PayloadSetup: JSON or form data
    PUT --> PayloadSetup: File or data upload
    DELETE --> AuthSetup: Authentication required
    
    PayloadSetup --> JSONPayload: application/json
    PayloadSetup --> FormPayload: form-data
    PayloadSetup --> RawPayload: custom content
    
    JSONPayload --> HeaderSetup
    FormPayload --> HeaderSetup
    RawPayload --> HeaderSetup
    
    HeaderSetup --> AuthSetup
    AuthSetup --> SSLSetup
    SSLSetup --> RedirectSetup
    RedirectSetup --> RequestExecution
    
    RequestExecution --> [*]: Request complete
    
    note right of GET : Default method for most crawling
    note right of POST : API interactions, form submissions
    note right of JSONPayload : Structured data transmission
    note right of HeaderSetup : User-Agent, Accept, Custom headers
```

### Error Handling and Retry Workflow

```mermaid
flowchart TD
    A[HTTP Request] --> B{Response Received?}
    
    B -->|No| C[Connection Error]
    B -->|Yes| D{Status Code Check}
    
    C --> C1{Timeout Error?}
    C1 -->|Yes| C2[ConnectionTimeoutError]
    C1 -->|No| C3[Network Error]
    
    D -->|2xx| E[Success Response]
    D -->|3xx| F[Redirect Response]
    D -->|4xx| G[Client Error]
    D -->|5xx| H[Server Error]
    
    F --> F1{Follow Redirects?}
    F1 -->|Yes| F2[Follow Redirect]
    F1 -->|No| F3[Return Redirect Response]
    F2 --> A
    
    G --> G1{Retry on 4xx?}
    G1 -->|No| G2[HTTPStatusError]
    G1 -->|Yes| I[Check Retry Count]
    
    H --> H1{Retry on 5xx?}
    H1 -->|Yes| I
    H1 -->|No| H2[HTTPStatusError]
    
    C2 --> I
    C3 --> I
    
    I --> J{Retries < Max?}
    J -->|No| K[Final Error]
    J -->|Yes| L[Calculate Backoff]
    
    L --> M[Wait Backoff Time]
    M --> N[Increment Retry Count]
    N --> A
    
    E --> O[Process Content]
    F3 --> O
    O --> P[Return CrawlResult]
    
    G2 --> Q[Error CrawlResult]
    H2 --> Q
    K --> Q
    
    style E fill:#c8e6c9
    style P fill:#c8e6c9
    style G2 fill:#ffcdd2
    style H2 fill:#ffcdd2
    style K fill:#ffcdd2
    style Q fill:#ffcdd2
```

### Batch Processing Architecture

```mermaid
sequenceDiagram
    participant Client
    participant BatchManager as Batch Manager
    participant HTTPPool as Connection Pool
    participant Workers as HTTP Workers
    participant Targets as Target Servers
    
    Client->>BatchManager: batch_crawl(urls)
    BatchManager->>BatchManager: create_semaphore(max_concurrent)
    
    loop For each URL batch
        BatchManager->>HTTPPool: acquire_connection()
        HTTPPool->>Workers: assign_worker()
        
        par Concurrent Processing
            Workers->>Targets: HTTP Request 1
            Workers->>Targets: HTTP Request 2
            Workers->>Targets: HTTP Request N
        end
        
        par Response Handling
            Targets-->>Workers: Response 1
            Targets-->>Workers: Response 2
            Targets-->>Workers: Response N
        end
        
        Workers->>HTTPPool: return_connection()
        HTTPPool->>BatchManager: batch_results()
    end
    
    BatchManager->>BatchManager: aggregate_results()
    BatchManager-->>Client: final_results()
    
    Note over Workers,Targets: 20-100 concurrent connections
    Note over BatchManager: Memory-efficient processing
    Note over HTTPPool: Connection reuse optimization
```

### Content Type Processing Pipeline

```mermaid
graph TD
    A[HTTP Response] --> B{Content-Type Detection}
    
    B -->|text/html| C[HTML Processing]
    B -->|application/json| D[JSON Processing]
    B -->|text/plain| E[Text Processing]
    B -->|application/xml| F[XML Processing]
    B -->|Other| G[Binary Processing]
    
    C --> C1[Parse HTML Structure]
    C1 --> C2[Extract Text Content]
    C2 --> C3[Generate Markdown]
    C3 --> C4[Extract Links/Media]
    
    D --> D1[Parse JSON Structure]
    D1 --> D2[Extract Data Fields]
    D2 --> D3[Format as Readable Text]
    
    E --> E1[Clean Text Content]
    E1 --> E2[Basic Formatting]
    
    F --> F1[Parse XML Structure]
    F1 --> F2[Extract Text Nodes]
    F2 --> F3[Convert to Markdown]
    
    G --> G1[Save Binary Content]
    G1 --> G2[Generate Metadata]
    
    C4 --> H[Content Analysis]
    D3 --> H
    E2 --> H
    F3 --> H
    G2 --> H
    
    H --> I[Link Extraction]
    H --> J[Media Detection]
    H --> K[Metadata Parsing]
    
    I --> L[CrawlResult Assembly]
    J --> L
    K --> L
    
    L --> M[Final Output]
    
    style C fill:#e8f5e8
    style H fill:#fff3e0
    style L fill:#e3f2fd
    style M fill:#c8e6c9
```

### Integration with Processing Strategies

```mermaid
graph LR
    subgraph "HTTP Strategy Core"
        A[HTTP Request] --> B[Raw Content]
        B --> C[Content Decoder]
    end
    
    subgraph "Processing Pipeline"
        C --> D[HTML Cleaner]
        D --> E[Markdown Generator]
        E --> F{Content Filter?}
        
        F -->|Yes| G[Pruning Filter]
        F -->|Yes| H[BM25 Filter]
        F -->|No| I[Raw Markdown]
        
        G --> J[Fit Markdown]
        H --> J
    end
    
    subgraph "Extraction Strategies"
        I --> K[CSS Extraction]
        J --> K
        I --> L[XPath Extraction]
        J --> L
        I --> M[LLM Extraction]
        J --> M
    end
    
    subgraph "Output Generation"
        K --> N[Structured JSON]
        L --> N
        M --> N
        
        I --> O[Clean Markdown]
        J --> P[Filtered Content]
        
        N --> Q[Final CrawlResult]
        O --> Q
        P --> Q
    end
    
    style A fill:#e3f2fd
    style C fill:#f3e5f5
    style E fill:#e8f5e8
    style Q fill:#c8e6c9
```

**📖 Learn more:** [HTTP vs Browser Strategies](https://docs.crawl4ai.com/core/browser-crawler-config/), [Performance Optimization](https://docs.crawl4ai.com/advanced/multi-url-crawling/), [Error Handling](https://docs.crawl4ai.com/api/async-webcrawler/)

---
