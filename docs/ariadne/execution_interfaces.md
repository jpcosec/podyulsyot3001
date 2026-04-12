# Ariadne 2.0: Execution Interfaces (SOLID Segregation)

## 1. Taxonomy of Actors
Ariadne 2.0 strictly segregates browser interaction into three roles to ensure Dependency Inversion (DIP) and Interface Segregation (ISP).

### A. Executors (Deterministic Slaves)
Executors are "dumb" workers that perform low-level primitives. They receive an exact target or coordinate and return a result.
- **Contract**: `async def execute(command: MotorCommand) -> ExecutionResult`
- **Implementations**: `Crawl4AIExecutor`, `BrowserOSCliExecutor`, `OSNativeExecutor`.

### B. Planners (Agentic Rescuers)
Planners are autonomous agents that decide the next semantic action when the graph path is lost.
- **Contract**: `async def plan_action(state: AriadneState) -> list[AriadneEdge]`
- **Implementation**: `LangGraphBrowserOSAgent` (Direct MCP).

### C. Capabilities (Stateless Tools)
Capabilities provide specific information about the current page to Planners or Executors.
- **HintingTool**: Injects alphanumeric markers (Set-of-Mark) into the UI.
- **VisionTool**: Resolves coordinates via OCR or Template Matching.
- **DangerDetector**: Evaluates Captchas and security blocks.

## 2. JIT Translation Pattern
Ariadne uses **Just-In-Time (JIT) Translation**. The orchestrator translates exactly one Intent into one Motor Command at the moment of execution.

```python
class AriadneTranslator(ABC):
    @abstractmethod
    def translate_intent(self, intent: AriadneIntent, target: AriadneTarget, state: AriadneState) -> MotorCommand:
        """Resolves {{placeholders}} and produces a motor-specific command."""
```

### Micro-Batching (Crawl4AI Optimization)
To maintain performance, the orchestrator can group a sequence of deterministic, safe intents (e.g. filling a form) and pass them to the `Crawl4AITranslator` as a single multi-line `CrawlCommand` (C4A-Script).

## 3. Motor Commands (JIT Payloads)

### BrowserOSCommand
```python
class BrowserOSCommand(BaseModel):
    tool: Literal["click", "fill", "upload", "press"]
    selector_text: str  # Resolved fuzzy text
    value: str | None = None
```

### CrawlCommand
```python
class CrawlCommand(BaseModel):
    c4a_script: str     # Multi-line script if batched
    hooks: list[dict]   # Playwright hooks (e.g. file upload)
```

## 4. Outcome Contracts

### ExecutionResult
```python
class ExecutionResult(BaseModel):
    status: Literal["success", "failed", "aborted"]
    extracted_data: dict[str, Any] # Data written to session_memory
    error: str | None = None
    screenshot_path: str | None = None
```
