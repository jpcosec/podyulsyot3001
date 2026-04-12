# Crawl4AI External Reference - Multi URLs Crawling

## Multi URLs Crawling - Full Content
Component ID: multi_urls_crawling
Context Type: memory
Estimated tokens: 2,230

## Multi-URL Crawling

Concurrent crawling of multiple URLs with intelligent resource management, rate limiting, and real-time monitoring.

### Basic Multi-URL Crawling

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

# Batch processing (default) - get all results at once
async def batch_crawl():
    urls = [
        "https://example.com/page1",
        "https://example.com/page2", 
        "https://example.com/page3"
    ]
    
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=False  # Default: batch mode
    )
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(urls, config=config)
        
        for result in results:
            if result.success:
                print(f"✅ {result.url}: {len(result.markdown)} chars")
            else:
                print(f"❌ {result.url}: {result.error_message}")

# Streaming processing - handle results as they complete
async def streaming_crawl():
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=True  # Enable streaming
    )
    
    async with AsyncWebCrawler() as crawler:
        # Process results as they become available
        async for result in await crawler.arun_many(urls, config=config):
            if result.success:
                print(f"🔥 Just completed: {result.url}")
                await process_result_immediately(result)
            else:
                print(f"❌ Failed: {result.url}")
```

### Memory-Adaptive Dispatching

```python
from crawl4ai import AsyncWebCrawler, MemoryAdaptiveDispatcher, CrawlerMonitor, DisplayMode

# Automatically manages concurrency based on system memory
async def memory_adaptive_crawl():
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=80.0,  # Pause if memory exceeds 80%
        check_interval=1.0,             # Check memory every second
        max_session_permit=15,          # Max concurrent tasks
        memory_wait_timeout=300.0       # Wait up to 5 minutes for memory
    )
    
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=50
    )
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=large_url_list,
            config=config,
            dispatcher=dispatcher
        )
        
        # Each result includes dispatch information
        for result in results:
            if result.dispatch_result:
                dr = result.dispatch_result
                print(f"Memory used: {dr.memory_usage:.1f}MB")
                print(f"Duration: {dr.end_time - dr.start_time}")
```

### Rate-Limited Crawling

```python
from crawl4ai import RateLimiter, SemaphoreDispatcher

# Control request pacing and handle server rate limits
async def rate_limited_crawl():
    rate_limiter = RateLimiter(
        base_delay=(1.0, 3.0),          # Random delay 1-3 seconds
        max_delay=60.0,                 # Cap backoff at 60 seconds
        max_retries=3,                  # Retry failed requests 3 times
        rate_limit_codes=[429, 503]     # Handle these status codes
    )
    
    dispatcher = SemaphoreDispatcher(
        max_session_permit=5,           # Fixed concurrency limit
        rate_limiter=rate_limiter
    )
    
    config = CrawlerRunConfig(
        user_agent_mode="random",       # Randomize user agents
        simulate_user=True              # Simulate human behavior
    )
    
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun_many(
            urls=urls,
            config=config,
            dispatcher=dispatcher
        ):
            print(f"Processed: {result.url}")
```

### Real-Time Monitoring

```python
from crawl4ai import CrawlerMonitor, DisplayMode

# Monitor crawling progress in real-time
async def monitored_crawl():
    monitor = CrawlerMonitor(
        max_visible_rows=20,                    # Show 20 tasks in display
        display_mode=DisplayMode.DETAILED       # Show individual task details
    )
    
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=75.0,
        max_session_permit=10,
        monitor=monitor  # Attach monitor to dispatcher
    )
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=urls,
            dispatcher=dispatcher
        )
```

### Advanced Dispatcher Configurations

```python
# Memory-adaptive with comprehensive monitoring
memory_dispatcher = MemoryAdaptiveDispatcher(
    memory_threshold_percent=85.0,      # Higher memory tolerance
    check_interval=0.5,                 # Check memory more frequently
    max_session_permit=20,              # More concurrent tasks
    memory_wait_timeout=600.0,          # Wait longer for memory
    rate_limiter=RateLimiter(
        base_delay=(0.5, 1.5),
        max_delay=30.0,
        max_retries=5
    ),
    monitor=CrawlerMonitor(
        max_visible_rows=15,
        display_mode=DisplayMode.AGGREGATED  # Summary view
    )
)

# Simple semaphore-based dispatcher
semaphore_dispatcher = SemaphoreDispatcher(
    max_session_permit=8,               # Fixed concurrency
    rate_limiter=RateLimiter(
        base_delay=(1.0, 2.0),
        max_delay=20.0
    )
)

# Usage with custom dispatcher
async with AsyncWebCrawler() as crawler:
    results = await crawler.arun_many(
        urls=urls,
        config=config,
        dispatcher=memory_dispatcher  # or semaphore_dispatcher
    )
```

### Handling Large-Scale Crawling

```python
async def large_scale_crawl():
    # For thousands of URLs
    urls = load_urls_from_file("large_url_list.txt")  # 10,000+ URLs
    
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,  # Conservative memory usage
        max_session_permit=25,          # Higher concurrency
        rate_limiter=RateLimiter(
            base_delay=(0.1, 0.5),      # Faster for large batches
            max_retries=2               # Fewer retries for speed
        ),
        monitor=CrawlerMonitor(display_mode=DisplayMode.AGGREGATED)
    )
    
    config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,   # Use caching for efficiency
        stream=True,                    # Stream for memory efficiency
        word_count_threshold=100,       # Skip short content
        exclude_external_links=True     # Reduce processing overhead
    )
    
    successful_crawls = 0
    failed_crawls = 0
    
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun_many(
            urls=urls,
            config=config,
            dispatcher=dispatcher
        ):
            if result.success:
                successful_crawls += 1
                await save_result_to_database(result)
            else:
                failed_crawls += 1
                await log_failure(result.url, result.error_message)
            
            # Progress reporting
            if (successful_crawls + failed_crawls) % 100 == 0:
                print(f"Progress: {successful_crawls + failed_crawls}/{len(urls)}")
    
    print(f"Completed: {successful_crawls} successful, {failed_crawls} failed")
```

### Robots.txt Compliance

```python
async def compliant_crawl():
    config = CrawlerRunConfig(
        check_robots_txt=True,          # Respect robots.txt
        user_agent="MyBot/1.0",         # Identify your bot
        mean_delay=2.0,                 # Be polite with delays
        max_range=1.0
    )
    
    dispatcher = SemaphoreDispatcher(
        max_session_permit=3,           # Conservative concurrency
        rate_limiter=RateLimiter(
            base_delay=(2.0, 5.0),      # Slower, more respectful
            max_retries=1
        )
    )
    
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun_many(
            urls=urls,
            config=config,
            dispatcher=dispatcher
        ):
            if result.success:
                print(f"✅ Crawled: {result.url}")
            elif "robots.txt" in result.error_message:
                print(f"🚫 Blocked by robots.txt: {result.url}")
            else:
                print(f"❌ Error: {result.url}")
```

### Performance Analysis

```python
async def analyze_crawl_performance():
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=80.0,
        max_session_permit=12,
        monitor=CrawlerMonitor(display_mode=DisplayMode.DETAILED)
    )
    
    start_time = time.time()
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=urls,
            dispatcher=dispatcher
        )
    
    end_time = time.time()
    
    # Analyze results
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"Total time: {end_time - start_time:.2f}s")
    print(f"Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Avg time per URL: {(end_time - start_time)/len(results):.2f}s")
    
    # Memory usage analysis
    if successful and successful[0].dispatch_result:
        memory_usage = [r.dispatch_result.memory_usage for r in successful if r.dispatch_result]
        peak_memory = [r.dispatch_result.peak_memory for r in successful if r.dispatch_result]
        
        print(f"Avg memory usage: {sum(memory_usage)/len(memory_usage):.1f}MB")
        print(f"Peak memory usage: {max(peak_memory):.1f}MB")
```

### Error Handling and Recovery

```python
async def robust_multi_crawl():
    failed_urls = []
    
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=True,
        page_timeout=30000  # 30 second timeout
    )
    
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=85.0,
        max_session_permit=10
    )
    
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun_many(
            urls=urls,
            config=config,
            dispatcher=dispatcher
        ):
            if result.success:
                await process_successful_result(result)
            else:
                failed_urls.append({
                    'url': result.url,
                    'error': result.error_message,
                    'status_code': result.status_code
                })
                
                # Retry logic for specific errors
                if result.status_code in [503, 429]:  # Server errors
                    await schedule_retry(result.url)
    
    # Report failures
    if failed_urls:
        print(f"Failed to crawl {len(failed_urls)} URLs:")
        for failure in failed_urls[:10]:  # Show first 10
            print(f"  {failure['url']}: {failure['error']}")
```

**📖 Learn more:** [Advanced Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/), [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/), [arun_many() API Reference](https://docs.crawl4ai.com/api/arun_many/)

---


## Multi URLs Crawling - Diagrams & Workflows
Component ID: multi_urls_crawling
Context Type: reasoning
Estimated tokens: 2,853

## Multi-URL Crawling Workflows and Architecture

Visual representations of concurrent crawling patterns, resource management, and monitoring systems for handling multiple URLs efficiently.

### Multi-URL Processing Modes

```mermaid
flowchart TD
    A[Multi-URL Crawling Request] --> B{Processing Mode?}
    
    B -->|Batch Mode| C[Collect All URLs]
    B -->|Streaming Mode| D[Process URLs Individually]
    
    C --> C1[Queue All URLs]
    C1 --> C2[Execute Concurrently]
    C2 --> C3[Wait for All Completion]
    C3 --> C4[Return Complete Results Array]
    
    D --> D1[Queue URLs]
    D1 --> D2[Start First Batch]
    D2 --> D3[Yield Results as Available]
    D3 --> D4{More URLs?}
    D4 -->|Yes| D5[Start Next URLs]
    D4 -->|No| D6[Stream Complete]
    D5 --> D3
    
    C4 --> E[Process Results]
    D6 --> E
    
    E --> F[Success/Failure Analysis]
    F --> G[End]
    
    style C fill:#e3f2fd
    style D fill:#f3e5f5
    style C4 fill:#c8e6c9
    style D6 fill:#c8e6c9
```

### Memory-Adaptive Dispatcher Flow

```mermaid
stateDiagram-v2
    [*] --> Initializing
    
    Initializing --> MonitoringMemory: Start dispatcher
    
    MonitoringMemory --> CheckingMemory: Every check_interval
    CheckingMemory --> MemoryOK: Memory < threshold
    CheckingMemory --> MemoryHigh: Memory >= threshold
    
    MemoryOK --> DispatchingTasks: Start new crawls
    MemoryHigh --> WaitingForMemory: Pause dispatching
    
    DispatchingTasks --> TaskRunning: Launch crawler
    TaskRunning --> TaskCompleted: Crawl finished
    TaskRunning --> TaskFailed: Crawl error
    
    TaskCompleted --> MonitoringMemory: Update stats
    TaskFailed --> MonitoringMemory: Update stats
    
    WaitingForMemory --> CheckingMemory: Wait timeout
    WaitingForMemory --> MonitoringMemory: Memory freed
    
    note right of MemoryHigh: Prevents OOM crashes
    note right of DispatchingTasks: Respects max_session_permit
    note right of WaitingForMemory: Configurable timeout
```

### Concurrent Crawling Architecture

```mermaid
graph TB
    subgraph "URL Queue Management"
        A[URL Input List] --> B[URL Queue]
        B --> C[Priority Scheduler]
        C --> D[Batch Assignment]
    end
    
    subgraph "Dispatcher Layer"
        E[Memory Adaptive Dispatcher]
        F[Semaphore Dispatcher]
        G[Rate Limiter]
        H[Resource Monitor]
        
        E --> I[Memory Checker]
        F --> J[Concurrency Controller]
        G --> K[Delay Calculator]
        H --> L[System Stats]
    end
    
    subgraph "Crawler Pool"
        M[Crawler Instance 1]
        N[Crawler Instance 2]
        O[Crawler Instance 3]
        P[Crawler Instance N]
        
        M --> Q[Browser Session 1]
        N --> R[Browser Session 2]
        O --> S[Browser Session 3]
        P --> T[Browser Session N]
    end
    
    subgraph "Result Processing"
        U[Result Collector]
        V[Success Handler]
        W[Error Handler]
        X[Retry Queue]
        Y[Final Results]
    end
    
    D --> E
    D --> F
    E --> M
    F --> N
    G --> O
    H --> P
    
    Q --> U
    R --> U
    S --> U
    T --> U
    
    U --> V
    U --> W
    W --> X
    X --> B
    V --> Y
    
    style E fill:#e3f2fd
    style F fill:#f3e5f5
    style G fill:#e8f5e8
    style H fill:#fff3e0
```

### Rate Limiting and Backoff Strategy

```mermaid
sequenceDiagram
    participant C as Crawler
    participant RL as Rate Limiter
    participant S as Server
    participant D as Dispatcher
    
    C->>RL: Request to crawl URL
    RL->>RL: Calculate delay
    RL->>RL: Apply base delay (1-3s)
    RL->>C: Delay applied
    
    C->>S: HTTP Request
    
    alt Success Response
        S-->>C: 200 OK + Content
        C->>RL: Report success
        RL->>RL: Reset failure count
        C->>D: Return successful result
    else Rate Limited
        S-->>C: 429 Too Many Requests
        C->>RL: Report rate limit
        RL->>RL: Exponential backoff
        RL->>RL: Increase delay (up to max_delay)
        RL->>C: Apply longer delay
        C->>S: Retry request after delay
    else Server Error
        S-->>C: 503 Service Unavailable
        C->>RL: Report server error
        RL->>RL: Moderate backoff
        RL->>C: Retry with backoff
    else Max Retries Exceeded
        RL->>C: Stop retrying
        C->>D: Return failed result
    end
```

### Large-Scale Crawling Workflow

```mermaid
flowchart TD
    A[Load URL List 10k+ URLs] --> B[Initialize Dispatcher]
    
    B --> C{Select Dispatcher Type}
    C -->|Memory Constrained| D[Memory Adaptive]
    C -->|Fixed Resources| E[Semaphore Based]
    
    D --> F[Set Memory Threshold 70%]
    E --> G[Set Concurrency Limit]
    
    F --> H[Configure Monitoring]
    G --> H
    
    H --> I[Start Crawling Process]
    I --> J[Monitor System Resources]
    
    J --> K{Memory Usage?}
    K -->|< Threshold| L[Continue Dispatching]
    K -->|>= Threshold| M[Pause New Tasks]
    
    L --> N[Process Results Stream]
    M --> O[Wait for Memory]
    O --> K
    
    N --> P{Result Type?}
    P -->|Success| Q[Save to Database]
    P -->|Failure| R[Log Error]
    
    Q --> S[Update Progress Counter]
    R --> S
    
    S --> T{More URLs?}
    T -->|Yes| U[Get Next Batch]
    T -->|No| V[Generate Final Report]
    
    U --> L
    V --> W[Analysis Complete]
    
    style A fill:#e1f5fe
    style D fill:#e8f5e8
    style E fill:#f3e5f5
    style V fill:#c8e6c9
    style W fill:#a5d6a7
```

### Real-Time Monitoring Dashboard Flow

```mermaid
graph LR
    subgraph "Data Collection"
        A[Crawler Tasks] --> B[Performance Metrics]
        A --> C[Memory Usage]
        A --> D[Success/Failure Rates]
        A --> E[Response Times]
    end
    
    subgraph "Monitor Processing"
        F[CrawlerMonitor] --> G[Aggregate Statistics]
        F --> H[Display Formatter]
        F --> I[Update Scheduler]
    end
    
    subgraph "Display Modes"
        J[DETAILED Mode]
        K[AGGREGATED Mode]
        
        J --> L[Individual Task Status]
        J --> M[Task-Level Metrics]
        K --> N[Summary Statistics]
        K --> O[Overall Progress]
    end
    
    subgraph "Output Interface"
        P[Console Display]
        Q[Progress Bars]
        R[Status Tables]
        S[Real-time Updates]
    end
    
    B --> F
    C --> F
    D --> F
    E --> F
    
    G --> J
    G --> K
    H --> J
    H --> K
    I --> J
    I --> K
    
    L --> P
    M --> Q
    N --> R
    O --> S
    
    style F fill:#e3f2fd
    style J fill:#f3e5f5
    style K fill:#e8f5e8
```

### Error Handling and Recovery Pattern

```mermaid
stateDiagram-v2
    [*] --> ProcessingURL
    
    ProcessingURL --> CrawlAttempt: Start crawl
    
    CrawlAttempt --> Success: HTTP 200
    CrawlAttempt --> NetworkError: Connection failed
    CrawlAttempt --> RateLimit: HTTP 429
    CrawlAttempt --> ServerError: HTTP 5xx
    CrawlAttempt --> Timeout: Request timeout
    
    Success --> [*]: Return result
    
    NetworkError --> RetryCheck: Check retry count
    RateLimit --> BackoffWait: Apply exponential backoff
    ServerError --> RetryCheck: Check retry count
    Timeout --> RetryCheck: Check retry count
    
    BackoffWait --> RetryCheck: After delay
    
    RetryCheck --> CrawlAttempt: retries < max_retries
    RetryCheck --> Failed: retries >= max_retries
    
    Failed --> ErrorLog: Log failure details
    ErrorLog --> [*]: Return failed result
    
    note right of BackoffWait: Exponential backoff for rate limits
    note right of RetryCheck: Configurable max_retries
    note right of ErrorLog: Detailed error tracking
```

### Resource Management Timeline

```mermaid
gantt
    title Multi-URL Crawling Resource Management
    dateFormat X
    axisFormat %s
    
    section Memory Usage
    Initialize Dispatcher    :0, 1
    Memory Monitoring       :1, 10
    Peak Usage Period       :3, 7
    Memory Cleanup          :7, 9
    
    section Task Execution
    URL Queue Setup         :0, 2
    Batch 1 Processing      :2, 5
    Batch 2 Processing      :4, 7
    Batch 3 Processing      :6, 9
    Final Results           :9, 10
    
    section Rate Limiting
    Normal Delays           :2, 4
    Backoff Period          :4, 6
    Recovery Period         :6, 8
    
    section Monitoring
    System Health Check     :0, 10
    Progress Updates        :1, 9
    Performance Metrics     :2, 8
```

### Concurrent Processing Performance Matrix

```mermaid
graph TD
    subgraph "Input Factors"
        A[Number of URLs]
        B[Concurrency Level]
        C[Memory Threshold]
        D[Rate Limiting]
    end
    
    subgraph "Processing Characteristics"
        A --> E[Low 1-100 URLs]
        A --> F[Medium 100-1k URLs]
        A --> G[High 1k-10k URLs]
        A --> H[Very High 10k+ URLs]
        
        B --> I[Conservative 1-5]
        B --> J[Moderate 5-15]
        B --> K[Aggressive 15-30]
        
        C --> L[Strict 60-70%]
        C --> M[Balanced 70-80%]
        C --> N[Relaxed 80-90%]
    end
    
    subgraph "Recommended Configurations"
        E --> O[Simple Semaphore]
        F --> P[Memory Adaptive Basic]
        G --> Q[Memory Adaptive Advanced]
        H --> R[Memory Adaptive + Monitoring]
        
        I --> O
        J --> P
        K --> Q
        K --> R
        
        L --> Q
        M --> P
        N --> O
    end
    
    style O fill:#c8e6c9
    style P fill:#fff3e0
    style Q fill:#ffecb3
    style R fill:#ffcdd2
```

**📖 Learn more:** [Multi-URL Crawling Guide](https://docs.crawl4ai.com/advanced/multi-url-crawling/), [Dispatcher Configuration](https://docs.crawl4ai.com/advanced/crawl-dispatcher/), [Performance Optimization](https://docs.crawl4ai.com/advanced/multi-url-crawling/#performance-optimization)

---
