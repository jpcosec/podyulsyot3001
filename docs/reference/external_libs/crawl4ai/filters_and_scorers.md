# Crawl4AI External Reference - Advanced Filters & Scorers

## Advanced Filters & Scorers - Full Content
Component ID: deep_crawl_advanced_filters_scorers
Context Type: memory
Estimated tokens: 2,713

## Deep Crawling Filters & Scorers

Advanced URL filtering and scoring strategies for intelligent deep crawling with performance optimization.

### URL Filters - Content and Domain Control

```python
from crawl4ai.deep_crawling.filters import (
    URLPatternFilter, DomainFilter, ContentTypeFilter, 
    FilterChain, ContentRelevanceFilter, SEOFilter
)

# Pattern-based filtering
pattern_filter = URLPatternFilter(
    patterns=[
        "*.html",           # HTML pages only
        "*/blog/*",         # Blog posts
        "*/articles/*",     # Article pages
        "*2024*",          # Recent content
        "^https://example.com/docs/.*"  # Regex pattern
    ],
    use_glob=True,
    reverse=False  # False = include matching, True = exclude matching
)

# Domain filtering with subdomains
domain_filter = DomainFilter(
    allowed_domains=["example.com", "docs.example.com"],
    blocked_domains=["ads.example.com", "tracker.com"]
)

# Content type filtering
content_filter = ContentTypeFilter(
    allowed_types=["text/html", "application/pdf"],
    check_extension=True
)

# Apply individual filters
url = "https://example.com/blog/2024/article.html"
print(f"Pattern filter: {pattern_filter.apply(url)}")
print(f"Domain filter: {domain_filter.apply(url)}")
print(f"Content filter: {content_filter.apply(url)}")
```

### Filter Chaining - Combine Multiple Filters

```python
# Create filter chain for comprehensive filtering
filter_chain = FilterChain([
    DomainFilter(allowed_domains=["example.com"]),
    URLPatternFilter(patterns=["*/blog/*", "*/docs/*"]),
    ContentTypeFilter(allowed_types=["text/html"])
])

# Apply chain to URLs
urls = [
    "https://example.com/blog/post1.html",
    "https://spam.com/content.html",
    "https://example.com/blog/image.jpg",
    "https://example.com/docs/guide.html"
]

async def filter_urls(urls, filter_chain):
    filtered = []
    for url in urls:
        if await filter_chain.apply(url):
            filtered.append(url)
    return filtered

# Usage
filtered_urls = await filter_urls(urls, filter_chain)
print(f"Filtered URLs: {filtered_urls}")

# Check filter statistics
for filter_obj in filter_chain.filters:
    stats = filter_obj.stats
    print(f"{filter_obj.name}: {stats.passed_urls}/{stats.total_urls} passed")
```

### Advanced Content Filters

```python
# BM25-based content relevance filtering
relevance_filter = ContentRelevanceFilter(
    query="python machine learning tutorial",
    threshold=0.5,  # Minimum relevance score
    k1=1.2,        # TF saturation parameter
    b=0.75,        # Length normalization
    avgdl=1000     # Average document length
)

# SEO quality filtering
seo_filter = SEOFilter(
    threshold=0.65,  # Minimum SEO score
    keywords=["python", "tutorial", "guide"],
    weights={
        "title_length": 0.15,
        "title_kw": 0.18,
        "meta_description": 0.12,
        "canonical": 0.10,
        "robot_ok": 0.20,
        "schema_org": 0.10,
        "url_quality": 0.15
    }
)

# Apply advanced filters
url = "https://example.com/python-ml-tutorial"
relevance_score = await relevance_filter.apply(url)
seo_score = await seo_filter.apply(url)

print(f"Relevance: {relevance_score}, SEO: {seo_score}")
```

### URL Scorers - Quality and Relevance Scoring

```python
from crawl4ai.deep_crawling.scorers import (
    KeywordRelevanceScorer, PathDepthScorer, ContentTypeScorer,
    FreshnessScorer, DomainAuthorityScorer, CompositeScorer
)

# Keyword relevance scoring
keyword_scorer = KeywordRelevanceScorer(
    keywords=["python", "tutorial", "guide", "machine", "learning"],
    weight=1.0,
    case_sensitive=False
)

# Path depth scoring (optimal depth = 3)
depth_scorer = PathDepthScorer(
    optimal_depth=3,  # /category/subcategory/article
    weight=0.8
)

# Content type scoring
content_type_scorer = ContentTypeScorer(
    type_weights={
        "html": 1.0,    # Highest priority
        "pdf": 0.8,     # Medium priority
        "txt": 0.6,     # Lower priority
        "doc": 0.4      # Lowest priority
    },
    weight=0.9
)

# Freshness scoring
freshness_scorer = FreshnessScorer(
    weight=0.7,
    current_year=2024
)

# Domain authority scoring
domain_scorer = DomainAuthorityScorer(
    domain_weights={
        "python.org": 1.0,
        "github.com": 0.9,
        "stackoverflow.com": 0.85,
        "medium.com": 0.7,
        "personal-blog.com": 0.3
    },
    default_weight=0.5,
    weight=1.0
)

# Score individual URLs
url = "https://python.org/tutorial/2024/machine-learning.html"
scores = {
    "keyword": keyword_scorer.score(url),
    "depth": depth_scorer.score(url),
    "content": content_type_scorer.score(url),
    "freshness": freshness_scorer.score(url),
    "domain": domain_scorer.score(url)
}

print(f"Individual scores: {scores}")
```

### Composite Scoring - Combine Multiple Scorers

```python
# Create composite scorer combining all strategies
composite_scorer = CompositeScorer(
    scorers=[
        KeywordRelevanceScorer(["python", "tutorial"], weight=1.5),
        PathDepthScorer(optimal_depth=3, weight=1.0),
        ContentTypeScorer({"html": 1.0, "pdf": 0.8}, weight=1.2),
        FreshnessScorer(weight=0.8, current_year=2024),
        DomainAuthorityScorer({
            "python.org": 1.0,
            "github.com": 0.9
        }, weight=1.3)
    ],
    normalize=True  # Normalize by number of scorers
)

# Score multiple URLs
urls_to_score = [
    "https://python.org/tutorial/2024/basics.html",
    "https://github.com/user/python-guide/blob/main/README.md",
    "https://random-blog.com/old/2018/python-stuff.html",
    "https://python.org/docs/deep/nested/advanced/guide.html"
]

scored_urls = []
for url in urls_to_score:
    score = composite_scorer.score(url)
    scored_urls.append((url, score))

# Sort by score (highest first)
scored_urls.sort(key=lambda x: x[1], reverse=True)

for url, score in scored_urls:
    print(f"Score: {score:.3f} - {url}")

# Check scorer statistics
print(f"\nScoring statistics:")
print(f"URLs scored: {composite_scorer.stats._urls_scored}")
print(f"Average score: {composite_scorer.stats.get_average():.3f}")
```

### Advanced Filter Patterns

```python
# Complex pattern matching
advanced_patterns = URLPatternFilter(
    patterns=[
        r"^https://docs\.python\.org/\d+/",  # Python docs with version
        r".*/tutorial/.*\.html$",             # Tutorial pages
        r".*/guide/(?!deprecated).*",         # Guides but not deprecated
        "*/blog/{2020,2021,2022,2023,2024}/*", # Recent blog posts
        "**/{api,reference}/**/*.html"        # API/reference docs
    ],
    use_glob=True
)

# Exclude patterns (reverse=True)
exclude_filter = URLPatternFilter(
    patterns=[
        "*/admin/*",
        "*/login/*", 
        "*/private/*",
        "**/.*",          # Hidden files
        "*.{jpg,png,gif,css,js}$"  # Media and assets
    ],
    reverse=True  # Exclude matching patterns
)

# Content type with extension mapping
detailed_content_filter = ContentTypeFilter(
    allowed_types=["text", "application"],
    check_extension=True,
    ext_map={
        "html": "text/html",
        "htm": "text/html", 
        "md": "text/markdown",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
)
```

### Performance-Optimized Filtering

```python
# High-performance filter chain for large-scale crawling
class OptimizedFilterChain:
    def __init__(self):
        # Fast filters first (domain, patterns)
        self.fast_filters = [
            DomainFilter(
                allowed_domains=["example.com", "docs.example.com"],
                blocked_domains=["ads.example.com"]
            ),
            URLPatternFilter([
                "*.html", "*.pdf", "*/blog/*", "*/docs/*"
            ])
        ]
        
        # Slower filters last (content analysis)
        self.slow_filters = [
            ContentRelevanceFilter(
                query="important content",
                threshold=0.3
            )
        ]
    
    async def apply_optimized(self, url: str) -> bool:
        # Apply fast filters first
        for filter_obj in self.fast_filters:
            if not filter_obj.apply(url):
                return False
        
        # Only apply slow filters if fast filters pass
        for filter_obj in self.slow_filters:
            if not await filter_obj.apply(url):
                return False
        
        return True

# Batch filtering with concurrency
async def batch_filter_urls(urls, filter_chain, max_concurrent=50):
    import asyncio
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def filter_single(url):
        async with semaphore:
            return await filter_chain.apply(url), url
    
    tasks = [filter_single(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    return [url for passed, url in results if passed]

# Usage with 1000 URLs
large_url_list = [f"https://example.com/page{i}.html" for i in range(1000)]
optimized_chain = OptimizedFilterChain()
filtered = await batch_filter_urls(large_url_list, optimized_chain)
```

### Custom Filter Implementation

```python
from crawl4ai.deep_crawling.filters import URLFilter
import re

class CustomLanguageFilter(URLFilter):
    """Filter URLs by language indicators"""
    
    def __init__(self, allowed_languages=["en"], weight=1.0):
        super().__init__()
        self.allowed_languages = set(allowed_languages)
        self.lang_patterns = {
            "en": re.compile(r"/en/|/english/|lang=en"),
            "es": re.compile(r"/es/|/spanish/|lang=es"),
            "fr": re.compile(r"/fr/|/french/|lang=fr"),
            "de": re.compile(r"/de/|/german/|lang=de")
        }
    
    def apply(self, url: str) -> bool:
        # Default to English if no language indicators
        if not any(pattern.search(url) for pattern in self.lang_patterns.values()):
            result = "en" in self.allowed_languages
            self._update_stats(result)
            return result
        
        # Check for allowed languages
        for lang in self.allowed_languages:
            if lang in self.lang_patterns:
                if self.lang_patterns[lang].search(url):
                    self._update_stats(True)
                    return True
        
        self._update_stats(False)
        return False

# Custom scorer implementation
from crawl4ai.deep_crawling.scorers import URLScorer

class CustomComplexityScorer(URLScorer):
    """Score URLs by content complexity indicators"""
    
    def __init__(self, weight=1.0):
        super().__init__(weight)
        self.complexity_indicators = {
            "tutorial": 0.9,
            "guide": 0.8, 
            "example": 0.7,
            "reference": 0.6,
            "api": 0.5
        }
    
    def _calculate_score(self, url: str) -> float:
        url_lower = url.lower()
        max_score = 0.0
        
        for indicator, score in self.complexity_indicators.items():
            if indicator in url_lower:
                max_score = max(max_score, score)
        
        return max_score

# Use custom filters and scorers
custom_filter = CustomLanguageFilter(allowed_languages=["en", "es"])
custom_scorer = CustomComplexityScorer(weight=1.2)

url = "https://example.com/en/tutorial/advanced-guide.html"
passes_filter = custom_filter.apply(url)
complexity_score = custom_scorer.score(url)

print(f"Passes language filter: {passes_filter}")
print(f"Complexity score: {complexity_score}")
```

### Integration with Deep Crawling

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import DeepCrawlStrategy

async def deep_crawl_with_filtering():
    # Create comprehensive filter chain
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["python.org"]),
        URLPatternFilter(["*/tutorial/*", "*/guide/*", "*/docs/*"]),
        ContentTypeFilter(["text/html"]),
        SEOFilter(threshold=0.6, keywords=["python", "programming"])
    ])
    
    # Create composite scorer
    scorer = CompositeScorer([
        KeywordRelevanceScorer(["python", "tutorial"], weight=1.5),
        FreshnessScorer(weight=0.8),
        PathDepthScorer(optimal_depth=3, weight=1.0)
    ], normalize=True)
    
    # Configure deep crawl strategy with filters and scorers
    deep_strategy = DeepCrawlStrategy(
        max_depth=3,
        max_pages=100,
        url_filter=filter_chain,
        url_scorer=scorer,
        score_threshold=0.6  # Only crawl URLs scoring above 0.6
    )
    
    config = CrawlerRunConfig(
        deep_crawl_strategy=deep_strategy,
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://python.org",
            config=config
        )
        
        print(f"Deep crawl completed: {result.success}")
        if hasattr(result, 'deep_crawl_results'):
            print(f"Pages crawled: {len(result.deep_crawl_results)}")

# Run the deep crawl
await deep_crawl_with_filtering()
```

**📖 Learn more:** [Deep Crawling Strategy](https://docs.crawl4ai.com/core/deep-crawling/), [Custom Filter Development](https://docs.crawl4ai.com/advanced/custom-filters/), [Performance Optimization](https://docs.crawl4ai.com/advanced/performance-tuning/)

---


## Advanced Filters & Scorers - Diagrams & Workflows
Component ID: deep_crawl_advanced_filters_scorers
Context Type: reasoning
Estimated tokens: 3,030

## Deep Crawling Filters & Scorers Architecture

Visual representations of advanced URL filtering, scoring strategies, and performance optimization workflows for intelligent deep crawling.

### Filter Chain Processing Pipeline

```mermaid
flowchart TD
    A[URL Input] --> B{Domain Filter}
    B -->|✓ Pass| C{Pattern Filter}
    B -->|✗ Fail| X1[Reject: Invalid Domain]
    
    C -->|✓ Pass| D{Content Type Filter}
    C -->|✗ Fail| X2[Reject: Pattern Mismatch]
    
    D -->|✓ Pass| E{SEO Filter}
    D -->|✗ Fail| X3[Reject: Wrong Content Type]
    
    E -->|✓ Pass| F{Content Relevance Filter}
    E -->|✗ Fail| X4[Reject: Low SEO Score]
    
    F -->|✓ Pass| G[URL Accepted]
    F -->|✗ Fail| X5[Reject: Low Relevance]
    
    G --> H[Add to Crawl Queue]
    
    subgraph "Fast Filters"
        B
        C
        D
    end
    
    subgraph "Slow Filters"
        E
        F
    end
    
    style A fill:#e3f2fd
    style G fill:#c8e6c9
    style H fill:#e8f5e8
    style X1 fill:#ffcdd2
    style X2 fill:#ffcdd2
    style X3 fill:#ffcdd2
    style X4 fill:#ffcdd2
    style X5 fill:#ffcdd2
```

### URL Scoring System Architecture

```mermaid
graph TB
    subgraph "Input URL"
        A[https://python.org/tutorial/2024/ml-guide.html]
    end
    
    subgraph "Individual Scorers"
        B[Keyword Relevance Scorer]
        C[Path Depth Scorer]
        D[Content Type Scorer]
        E[Freshness Scorer]
        F[Domain Authority Scorer]
    end
    
    subgraph "Scoring Process"
        B --> B1[Keywords: python, tutorial, ml<br/>Score: 0.85]
        C --> C1[Depth: 4 levels<br/>Optimal: 3<br/>Score: 0.75]
        D --> D1[Content: HTML<br/>Score: 1.0]
        E --> E1[Year: 2024<br/>Score: 1.0]
        F --> F1[Domain: python.org<br/>Score: 1.0]
    end
    
    subgraph "Composite Scoring"
        G[Weighted Combination]
        B1 --> G
        C1 --> G
        D1 --> G
        E1 --> G
        F1 --> G
    end
    
    subgraph "Final Result"
        H[Composite Score: 0.92]
        I{Score > Threshold?}
        J[Accept URL]
        K[Reject URL]
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    
    G --> H
    H --> I
    I -->|✓ 0.92 > 0.6| J
    I -->|✗ Score too low| K
    
    style A fill:#e3f2fd
    style G fill:#fff3e0
    style H fill:#e8f5e8
    style J fill:#c8e6c9
    style K fill:#ffcdd2
```

### Filter vs Scorer Decision Matrix

```mermaid
flowchart TD
    A[URL Processing Decision] --> B{Binary Decision Needed?}
    
    B -->|Yes - Include/Exclude| C[Use Filters]
    B -->|No - Quality Rating| D[Use Scorers]
    
    C --> C1{Filter Type Needed?}
    C1 -->|Domain Control| C2[DomainFilter]
    C1 -->|Pattern Matching| C3[URLPatternFilter]
    C1 -->|Content Type| C4[ContentTypeFilter]
    C1 -->|SEO Quality| C5[SEOFilter]
    C1 -->|Content Relevance| C6[ContentRelevanceFilter]
    
    D --> D1{Scoring Criteria?}
    D1 -->|Keyword Relevance| D2[KeywordRelevanceScorer]
    D1 -->|URL Structure| D3[PathDepthScorer]
    D1 -->|Content Quality| D4[ContentTypeScorer]
    D1 -->|Time Sensitivity| D5[FreshnessScorer]
    D1 -->|Source Authority| D6[DomainAuthorityScorer]
    
    C2 --> E[Chain Filters]
    C3 --> E
    C4 --> E
    C5 --> E
    C6 --> E
    
    D2 --> F[Composite Scorer]
    D3 --> F
    D4 --> F
    D5 --> F
    D6 --> F
    
    E --> G[Binary Output: Pass/Fail]
    F --> H[Numeric Score: 0.0-1.0]
    
    G --> I[Apply to URL Queue]
    H --> J[Priority Ranking]
    
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#f3e5f5
    style F fill:#e3f2fd
    style G fill:#c8e6c9
    style H fill:#ffecb3
```

### Performance Optimization Strategy

```mermaid
sequenceDiagram
    participant Queue as URL Queue
    participant Fast as Fast Filters
    participant Slow as Slow Filters
    participant Score as Scorers
    participant Output as Filtered URLs
    
    Note over Queue, Output: Batch Processing (1000 URLs)
    
    Queue->>Fast: Apply Domain Filter
    Fast-->>Queue: 60% passed (600 URLs)
    
    Queue->>Fast: Apply Pattern Filter
    Fast-->>Queue: 70% passed (420 URLs)
    
    Queue->>Fast: Apply Content Type Filter
    Fast-->>Queue: 90% passed (378 URLs)
    
    Note over Fast: Fast filters eliminate 62% of URLs
    
    Queue->>Slow: Apply SEO Filter (378 URLs)
    Slow-->>Queue: 80% passed (302 URLs)
    
    Queue->>Slow: Apply Relevance Filter
    Slow-->>Queue: 75% passed (227 URLs)
    
    Note over Slow: Content analysis on remaining URLs
    
    Queue->>Score: Calculate Composite Scores
    Score-->>Queue: Scored and ranked
    
    Queue->>Output: Top 100 URLs by score
    Output-->>Queue: Processing complete
    
    Note over Queue, Output: Total: 90% filtered out, 10% high-quality URLs retained
```

### Custom Filter Implementation Flow

```mermaid
stateDiagram-v2
    [*] --> Planning
    
    Planning --> IdentifyNeeds: Define filtering criteria
    IdentifyNeeds --> ChooseType: Binary vs Scoring decision
    
    ChooseType --> FilterImpl: Binary decision needed
    ChooseType --> ScorerImpl: Quality rating needed
    
    FilterImpl --> InheritURLFilter: Extend URLFilter base class
    ScorerImpl --> InheritURLScorer: Extend URLScorer base class
    
    InheritURLFilter --> ImplementApply: def apply(url) -> bool
    InheritURLScorer --> ImplementScore: def _calculate_score(url) -> float
    
    ImplementApply --> AddLogic: Add custom filtering logic
    ImplementScore --> AddLogic
    
    AddLogic --> TestFilter: Unit testing
    TestFilter --> OptimizePerf: Performance optimization
    
    OptimizePerf --> Integration: Integrate with FilterChain
    Integration --> Production: Deploy to production
    
    Production --> Monitor: Monitor performance
    Monitor --> Tune: Tune parameters
    Tune --> Production
    
    note right of Planning : Consider performance impact
    note right of AddLogic : Handle edge cases
    note right of OptimizePerf : Cache frequently accessed data
```

### Filter Chain Optimization Patterns

```mermaid
graph TB
    subgraph "Naive Approach - Poor Performance"
        A1[All URLs] --> B1[Slow Filter 1]
        B1 --> C1[Slow Filter 2]
        C1 --> D1[Fast Filter 1]
        D1 --> E1[Fast Filter 2]
        E1 --> F1[Final Results]
        
        B1 -.->|High CPU| G1[Performance Issues]
        C1 -.->|Network Calls| G1
    end
    
    subgraph "Optimized Approach - High Performance"
        A2[All URLs] --> B2[Fast Filter 1]
        B2 --> C2[Fast Filter 2]
        C2 --> D2[Batch Process]
        D2 --> E2[Slow Filter 1]
        E2 --> F2[Slow Filter 2]
        F2 --> G2[Final Results]
        
        D2 --> H2[Concurrent Processing]
        H2 --> I2[Semaphore Control]
    end
    
    subgraph "Performance Metrics"
        J[Processing Time]
        K[Memory Usage]
        L[CPU Utilization]
        M[Network Requests]
    end
    
    G1 -.-> J
    G1 -.-> K
    G1 -.-> L
    G1 -.-> M
    
    G2 -.-> J
    G2 -.-> K
    G2 -.-> L
    G2 -.-> M
    
    style A1 fill:#ffcdd2
    style G1 fill:#ffcdd2
    style A2 fill:#c8e6c9
    style G2 fill:#c8e6c9
    style H2 fill:#e8f5e8
    style I2 fill:#e8f5e8
```

### Composite Scoring Weight Distribution

```mermaid
pie title Composite Scorer Weight Distribution
    "Keyword Relevance (30%)" : 30
    "Domain Authority (25%)" : 25
    "Content Type (20%)" : 20
    "Freshness (15%)" : 15
    "Path Depth (10%)" : 10
```

### Deep Crawl Integration Architecture

```mermaid
graph TD
    subgraph "Deep Crawl Strategy"
        A[Start URL] --> B[Extract Links]
        B --> C[Apply Filter Chain]
        C --> D[Calculate Scores]
        D --> E[Priority Queue]
        E --> F[Crawl Next URL]
        F --> B
    end
    
    subgraph "Filter Chain Components"
        C --> C1[Domain Filter]
        C --> C2[Pattern Filter]
        C --> C3[Content Filter]
        C --> C4[SEO Filter]
        C --> C5[Relevance Filter]
    end
    
    subgraph "Scoring Components"
        D --> D1[Keyword Scorer]
        D --> D2[Depth Scorer]
        D --> D3[Freshness Scorer]
        D --> D4[Authority Scorer]
        D --> D5[Composite Score]
    end
    
    subgraph "Queue Management"
        E --> E1{Score > Threshold?}
        E1 -->|Yes| E2[High Priority Queue]
        E1 -->|No| E3[Low Priority Queue]
        E2 --> F
        E3 --> G[Delayed Processing]
    end
    
    subgraph "Control Flow"
        H{Max Depth Reached?}
        I{Max Pages Reached?}
        J[Stop Crawling]
    end
    
    F --> H
    H -->|No| I
    H -->|Yes| J
    I -->|No| B
    I -->|Yes| J
    
    style A fill:#e3f2fd
    style E2 fill:#c8e6c9
    style E3 fill:#fff3e0
    style J fill:#ffcdd2
```

### Filter Performance Comparison

```mermaid
xychart-beta
    title "Filter Performance Comparison (1000 URLs)"
    x-axis [Domain, Pattern, ContentType, SEO, Relevance]
    y-axis "Processing Time (ms)" 0 --> 1000
    bar [50, 80, 45, 300, 800]
```

### Scoring Algorithm Workflow

```mermaid
flowchart TD
    A[Input URL] --> B[Parse URL Components]
    B --> C[Extract Features]
    
    C --> D[Domain Analysis]
    C --> E[Path Analysis] 
    C --> F[Content Type Detection]
    C --> G[Keyword Extraction]
    C --> H[Freshness Detection]
    
    D --> I[Domain Authority Score]
    E --> J[Path Depth Score]
    F --> K[Content Type Score]
    G --> L[Keyword Relevance Score]
    H --> M[Freshness Score]
    
    I --> N[Apply Weights]
    J --> N
    K --> N
    L --> N
    M --> N
    
    N --> O[Normalize Scores]
    O --> P[Calculate Final Score]
    P --> Q{Score >= Threshold?}
    
    Q -->|Yes| R[Accept for Crawling]
    Q -->|No| S[Reject URL]
    
    R --> T[Add to Priority Queue]
    S --> U[Log Rejection Reason]
    
    style A fill:#e3f2fd
    style P fill:#fff3e0
    style R fill:#c8e6c9
    style S fill:#ffcdd2
    style T fill:#e8f5e8
```

**📖 Learn more:** [Deep Crawling Strategy](https://docs.crawl4ai.com/core/deep-crawling/), [Performance Optimization](https://docs.crawl4ai.com/advanced/performance-tuning/), [Custom Implementations](https://docs.crawl4ai.com/advanced/custom-filters/)

---
