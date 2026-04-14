# Crawl4AI Custom LLM Context
Generated on: 2026-04-14T00:15:35.391Z
Total files: 2
Estimated tokens: 4,116

---

## Installation - Full Content
Component ID: installation
Context Type: memory
Estimated tokens: 1,458

## Installation

Multiple installation options for different environments and use cases.

### Basic Installation

```bash
# Install core library
pip install crawl4ai

# Initial setup (installs Playwright browsers)
crawl4ai-setup

# Verify installation
crawl4ai-doctor
```

### Quick Verification

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown[:300])

if __name__ == "__main__":
    asyncio.run(main())
```

**📖 Learn more:** [Basic Usage Guide](https://docs.crawl4ai.com/core/quickstart.md)

### Advanced Features (Optional)

```bash
# PyTorch-based features (text clustering, semantic chunking)
pip install crawl4ai[torch]
crawl4ai-setup

# Transformers (Hugging Face models)
pip install crawl4ai[transformer]
crawl4ai-setup

# All features (large download)
pip install crawl4ai[all]
crawl4ai-setup

# Pre-download models (optional)
crawl4ai-download-models
```

**📖 Learn more:** [Advanced Features Documentation](https://docs.crawl4ai.com/extraction/llm-strategies.md)

### Docker Deployment

```bash
# Pull pre-built image (specify platform for consistency)
docker pull --platform linux/amd64 unclecode/crawl4ai:latest
# For ARM (M1/M2 Macs): docker pull --platform linux/arm64 unclecode/crawl4ai:latest

# Setup environment for LLM support
cat > .llm.env << EOL
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=your-anthropic-key
EOL

# Run with LLM support (specify platform)
docker run -d \
  --platform linux/amd64 \
  -p 11235:11235 \
  --name crawl4ai \
  --env-file .llm.env \
  --shm-size=1g \
  unclecode/crawl4ai:latest

# For ARM Macs, use: --platform linux/arm64

# Basic run (no LLM)
docker run -d \
  --platform linux/amd64 \
  -p 11235:11235 \
  --name crawl4ai \
  --shm-size=1g \
  unclecode/crawl4ai:latest
```

**📖 Learn more:** [Complete Docker Guide](https://docs.crawl4ai.com/core/docker-deployment.md)

### Docker Compose

```bash
# Clone repository
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai

# Copy environment template
cp deploy/docker/.llm.env.example .llm.env
# Edit .llm.env with your API keys

# Run pre-built image
IMAGE=unclecode/crawl4ai:latest docker compose up -d

# Build and run locally
docker compose up --build -d

# Build with all features
INSTALL_TYPE=all docker compose up --build -d

# Stop service
docker compose down
```

**📖 Learn more:** [Docker Compose Configuration](https://docs.crawl4ai.com/core/docker-deployment.md#option-2-using-docker-compose)

### Manual Docker Build

```bash
# Build multi-architecture image (specify platform)
docker buildx build --platform linux/amd64 -t crawl4ai-local:latest --load .
# For ARM: docker buildx build --platform linux/arm64 -t crawl4ai-local:latest --load .

# Build with specific features
docker buildx build \
  --platform linux/amd64 \
  --build-arg INSTALL_TYPE=all \
  --build-arg ENABLE_GPU=false \
  -t crawl4ai-local:latest --load .

# Run custom build (specify platform)
docker run -d \
  --platform linux/amd64 \
  -p 11235:11235 \
  --name crawl4ai-custom \
  --env-file .llm.env \
  --shm-size=1g \
  crawl4ai-local:latest
```

**📖 Learn more:** [Manual Build Guide](https://docs.crawl4ai.com/core/docker-deployment.md#option-3-manual-local-build--run)

### Google Colab

```python
# Install in Colab
!pip install crawl4ai
!crawl4ai-setup

# If setup fails, manually install Playwright browsers
!playwright install chromium

# Install with all features (may take 5-10 minutes)
!pip install crawl4ai[all]
!crawl4ai-setup
!crawl4ai-download-models

# If still having issues, force Playwright install
!playwright install chromium --force

# Quick test
import asyncio
from crawl4ai import AsyncWebCrawler

async def test_crawl():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print("✅ Installation successful!")
        print(f"Content length: {len(result.markdown)}")

# Run test in Colab
await test_crawl()
```

**📖 Learn more:** [Colab Examples Notebook](https://colab.research.google.com/github/unclecode/crawl4ai/blob/main/docs/examples/quickstart.ipynb)

### Docker API Usage

```python
# Using Docker SDK
import asyncio
from crawl4ai.docker_client import Crawl4aiDockerClient
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    async with Crawl4aiDockerClient(base_url="http://localhost:11235") as client:
        results = await client.crawl(
            ["https://example.com"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        )
        for result in results:
            print(f"Success: {result.success}, Length: {len(result.markdown)}")

asyncio.run(main())
```

**📖 Learn more:** [Docker Client API](https://docs.crawl4ai.com/core/docker-deployment.md#python-sdk)

### Direct API Calls

```python
# REST API example
import requests

payload = {
    "urls": ["https://example.com"],
    "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
    "crawler_config": {"type": "CrawlerRunConfig", "params": {"cache_mode": "bypass"}}
}

response = requests.post("http://localhost:11235/crawl", json=payload)
print(response.json())
```

**📖 Learn more:** [REST API Reference](https://docs.crawl4ai.com/core/docker-deployment.md#rest-api-examples)

### Health Check

```bash
# Check Docker service
curl http://localhost:11235/health

# Access playground
open http://localhost:11235/playground

# View metrics
curl http://localhost:11235/metrics
```

**📖 Learn more:** [Monitoring & Metrics](https://docs.crawl4ai.com/core/docker-deployment.md#metrics--monitoring)

---


## Installation - Diagrams & Workflows
Component ID: installation
Context Type: reasoning
Estimated tokens: 2,658

## Installation Workflows and Architecture

Visual representations of Crawl4AI installation processes, deployment options, and system interactions.

### Installation Decision Flow

```mermaid
flowchart TD
    A[Start Installation] --> B{Environment Type?}
    
    B -->|Local Development| C[Basic Python Install]
    B -->|Production| D[Docker Deployment]
    B -->|Research/Testing| E[Google Colab]
    B -->|CI/CD Pipeline| F[Automated Setup]
    
    C --> C1[pip install crawl4ai]
    C1 --> C2[crawl4ai-setup]
    C2 --> C3{Need Advanced Features?}
    
    C3 -->|No| C4[Basic Installation Complete]
    C3 -->|Text Clustering| C5[pip install crawl4ai with torch]
    C3 -->|Transformers| C6[pip install crawl4ai with transformer]
    C3 -->|All Features| C7[pip install crawl4ai with all]
    
    C5 --> C8[crawl4ai-download-models]
    C6 --> C8
    C7 --> C8
    C8 --> C9[Advanced Installation Complete]
    
    D --> D1{Deployment Method?}
    D1 -->|Pre-built Image| D2[docker pull unclecode/crawl4ai]
    D1 -->|Docker Compose| D3[Clone repo + docker compose]
    D1 -->|Custom Build| D4[docker buildx build]
    
    D2 --> D5[Configure .llm.env]
    D3 --> D5
    D4 --> D5
    D5 --> D6[docker run with ports]
    D6 --> D7[Docker Deployment Complete]
    
    E --> E1[Colab pip install]
    E1 --> E2[playwright install chromium]
    E2 --> E3[Test basic crawl]
    E3 --> E4[Colab Setup Complete]
    
    F --> F1[Automated pip install]
    F1 --> F2[Automated setup scripts]
    F2 --> F3[CI/CD Integration Complete]
    
    C4 --> G[Verify with crawl4ai-doctor]
    C9 --> G
    D7 --> H[Health check via API]
    E4 --> I[Run test crawl]
    F3 --> G
    
    G --> J[Installation Verified]
    H --> J
    I --> J
    
    style A fill:#e1f5fe
    style J fill:#c8e6c9
    style C4 fill:#fff3e0
    style C9 fill:#fff3e0
    style D7 fill:#f3e5f5
    style E4 fill:#fce4ec
    style F3 fill:#e8f5e8
```

### Basic Installation Sequence

```mermaid
sequenceDiagram
    participant User
    participant PyPI
    participant System
    participant Playwright
    participant Crawler
    
    User->>PyPI: pip install crawl4ai
    PyPI-->>User: Package downloaded
    
    User->>System: crawl4ai-setup
    System->>Playwright: Install browser binaries
    Playwright-->>System: Chromium, Firefox installed
    System-->>User: Setup complete
    
    User->>System: crawl4ai-doctor
    System->>System: Check Python version
    System->>System: Verify Playwright installation
    System->>System: Test browser launch
    System-->>User: Diagnostics report
    
    User->>Crawler: Basic crawl test
    Crawler->>Playwright: Launch browser
    Playwright-->>Crawler: Browser ready
    Crawler->>Crawler: Navigate to test URL
    Crawler-->>User: Success confirmation
```

### Docker Deployment Architecture

```mermaid
graph TB
    subgraph "Host System"
        A[Docker Engine] --> B[Crawl4AI Container]
        C[.llm.env File] --> B
        D[Port 11235] --> B
    end
    
    subgraph "Container Environment"
        B --> E[FastAPI Server]
        B --> F[Playwright Browsers]
        B --> G[Python Runtime]
        
        E --> H[/crawl Endpoint]
        E --> I[/playground Interface]
        E --> J[/health Monitoring]
        E --> K[/metrics Prometheus]
        
        F --> L[Chromium Browser]
        F --> M[Firefox Browser]
        F --> N[WebKit Browser]
    end
    
    subgraph "External Services"
        O[OpenAI API] --> B
        P[Anthropic API] --> B
        Q[Local LLM Ollama] --> B
    end
    
    subgraph "Client Applications"
        R[Python SDK] --> H
        S[REST API Calls] --> H
        T[Web Browser] --> I
        U[Monitoring Tools] --> J
        V[Prometheus] --> K
    end
    
    style B fill:#e3f2fd
    style E fill:#f3e5f5
    style F fill:#e8f5e8
    style G fill:#fff3e0
```

### Advanced Features Installation Flow

```mermaid
stateDiagram-v2
    [*] --> BasicInstall
    
    BasicInstall --> FeatureChoice: crawl4ai installed
    
    FeatureChoice --> TorchInstall: Need text clustering
    FeatureChoice --> TransformerInstall: Need HuggingFace models
    FeatureChoice --> AllInstall: Need everything
    FeatureChoice --> Complete: Basic features sufficient
    
    TorchInstall --> TorchSetup: pip install crawl4ai with torch
    TransformerInstall --> TransformerSetup: pip install crawl4ai with transformer  
    AllInstall --> AllSetup: pip install crawl4ai with all
    
    TorchSetup --> ModelDownload: crawl4ai-setup
    TransformerSetup --> ModelDownload: crawl4ai-setup
    AllSetup --> ModelDownload: crawl4ai-setup
    
    ModelDownload --> PreDownload: crawl4ai-download-models
    PreDownload --> Complete: All models cached
    
    Complete --> Verification: crawl4ai-doctor
    Verification --> [*]: Installation verified
    
    note right of TorchInstall : PyTorch for semantic operations
    note right of TransformerInstall : HuggingFace for LLM features
    note right of AllInstall : Complete feature set
```

### Platform-Specific Installation Matrix

```mermaid
graph LR
    subgraph "Installation Methods"
        A[Python Package] --> A1[pip install]
        B[Docker Image] --> B1[docker pull]
        C[Source Build] --> C1[git clone + build]
        D[Cloud Platform] --> D1[Colab/Kaggle]
    end
    
    subgraph "Operating Systems"
        E[Linux x86_64]
        F[Linux ARM64] 
        G[macOS Intel]
        H[macOS Apple Silicon]
        I[Windows x86_64]
    end
    
    subgraph "Feature Sets"
        J[Basic crawling]
        K[Text clustering torch]
        L[LLM transformers]
        M[All features]
    end
    
    A1 --> E
    A1 --> F
    A1 --> G
    A1 --> H
    A1 --> I
    
    B1 --> E
    B1 --> F
    B1 --> G
    B1 --> H
    
    C1 --> E
    C1 --> F
    C1 --> G
    C1 --> H
    C1 --> I
    
    D1 --> E
    D1 --> I
    
    E --> J
    E --> K
    E --> L
    E --> M
    
    F --> J
    F --> K
    F --> L
    F --> M
    
    G --> J
    G --> K
    G --> L
    G --> M
    
    H --> J
    H --> K
    H --> L
    H --> M
    
    I --> J
    I --> K
    I --> L
    I --> M
    
    style A1 fill:#e3f2fd
    style B1 fill:#f3e5f5
    style C1 fill:#e8f5e8
    style D1 fill:#fff3e0
```

### Docker Multi-Stage Build Process

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as GitHub Repo
    participant Docker as Docker Engine
    participant Registry as Docker Hub
    participant User as End User
    
    Dev->>Git: Push code changes
    
    Docker->>Git: Clone repository
    Docker->>Docker: Stage 1 - Base Python image
    Docker->>Docker: Stage 2 - Install dependencies
    Docker->>Docker: Stage 3 - Install Playwright
    Docker->>Docker: Stage 4 - Copy application code
    Docker->>Docker: Stage 5 - Setup FastAPI server
    
    Note over Docker: Multi-architecture build
    Docker->>Docker: Build for linux/amd64
    Docker->>Docker: Build for linux/arm64
    
    Docker->>Registry: Push multi-arch manifest
    Registry-->>Docker: Build complete
    
    User->>Registry: docker pull unclecode/crawl4ai
    Registry-->>User: Download appropriate architecture
    
    User->>Docker: docker run with configuration
    Docker->>Docker: Start container
    Docker->>Docker: Initialize FastAPI server
    Docker->>Docker: Setup Playwright browsers
    Docker-->>User: Service ready on port 11235
```

### Installation Verification Workflow

```mermaid
flowchart TD
    A[Installation Complete] --> B[Run crawl4ai-doctor]
    
    B --> C{Python Version Check}
    C -->|✓ 3.10+| D{Playwright Check}
    C -->|✗ < 3.10| C1[Upgrade Python]
    C1 --> D
    
    D -->|✓ Installed| E{Browser Binaries}
    D -->|✗ Missing| D1[Run crawl4ai-setup]
    D1 --> E
    
    E -->|✓ Available| F{Test Browser Launch}
    E -->|✗ Missing| E1[playwright install]
    E1 --> F
    
    F -->|✓ Success| G[Test Basic Crawl]
    F -->|✗ Failed| F1[Check system dependencies]
    F1 --> F
    
    G --> H{Crawl Test Result}
    H -->|✓ Success| I[Installation Verified ✓]
    H -->|✗ Failed| H1[Check network/permissions]
    H1 --> G
    
    I --> J[Ready for Production Use]
    
    style I fill:#c8e6c9
    style J fill:#e8f5e8
    style C1 fill:#ffcdd2
    style D1 fill:#fff3e0
    style E1 fill:#fff3e0
    style F1 fill:#ffcdd2
    style H1 fill:#ffcdd2
```

### Resource Requirements by Installation Type

```mermaid
graph TD
    subgraph "Basic Installation"
        A1[Memory: 512MB]
        A2[Disk: 2GB]
        A3[CPU: 1 core]
        A4[Network: Required for setup]
    end
    
    subgraph "Advanced Features torch"
        B1[Memory: 2GB+]
        B2[Disk: 5GB+]
        B3[CPU: 2+ cores]
        B4[GPU: Optional CUDA]
    end
    
    subgraph "All Features"
        C1[Memory: 4GB+]
        C2[Disk: 10GB+]
        C3[CPU: 4+ cores]
        C4[GPU: Recommended]
    end
    
    subgraph "Docker Deployment"
        D1[Memory: 1GB+]
        D2[Disk: 3GB+]
        D3[CPU: 2+ cores]
        D4[Ports: 11235]
        D5[Shared Memory: 1GB]
    end
    
    style A1 fill:#e8f5e8
    style B1 fill:#fff3e0
    style C1 fill:#ffecb3
    style D1 fill:#e3f2fd
```

**📖 Learn more:** [Installation Guide](https://docs.crawl4ai.com/core/installation/), [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/), [System Requirements](https://docs.crawl4ai.com/core/installation/#prerequisites)

---

