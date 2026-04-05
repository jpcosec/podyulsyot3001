# Portal Contracts

Date: 2026-04-05
Status: design-only

## Purpose

Contracts that define what a portal provides to the system. Portals are
source-specific knowledge packages. They don't own execution — motors do.
They don't own path schema — Ariadne does. They provide the domain knowledge
that populates AriadneTarget fields, routing decisions, and source-specific
hints.

## Portal definition contracts

### PortalDefinition

The root contract for a portal. One per source.

```python
class PortalDefinition(BaseModel):
    source_name: str                          # "linkedin", "xing", "stepstone", "tuberlin"
    base_url: str                             # portal base URL
    capabilities: PortalCapabilities
    scrape: PortalScrapeConfig | None = None  # None if portal doesn't support scraping
    apply: PortalApplyConfig | None = None    # None if portal doesn't support applying
    routing: PortalRoutingConfig
```

### PortalCapabilities

What this portal supports.

```python
class PortalCapabilities(BaseModel):
    supports_scrape: bool
    supports_apply: bool
    supported_apply_backends: list[str] = []  # ["crawl4ai", "browseros-cli", etc.]
    supported_scrape_backends: list[str] = [] # ["crawl4ai"]
    requires_auth: bool = True                # most portals need login
    auth_method: Literal["cookie_session", "oauth", "none"] = "cookie_session"
```

### PortalScrapeConfig

Scraping-specific portal knowledge. Feeds the Crawl4AI scraping engine.

```python
class PortalScrapeConfig(BaseModel):
    search_url_template: str                  # URL template with {query}, {location}, etc.
    supported_params: list[str]               # CLI filter names (job_query, location, etc.)
    schema_path: str | None = None            # cached CSS extraction schema
    llm_instructions: str | None = None       # portal-specific extraction hints
    schema_generation_hints: str | None = None
    link_extraction: PortalLinkExtraction
```

### PortalLinkExtraction

How to extract job links from a listing page.

```python
class PortalLinkExtraction(BaseModel):
    method: Literal["css", "regex", "custom"]
    selector: str | None = None               # CSS selector for job links
    pattern: str | None = None                # regex pattern for job URLs
    id_extraction: str                        # regex or function name to extract job_id from URL
```

### PortalApplyConfig

Apply-specific portal knowledge. Feeds motors via AriadneTarget fields.

```python
class PortalApplyConfig(BaseModel):
    flows: list[PortalApplyFlow]
    session_profile_dir: str | None = None    # persistent browser profile path (Crawl4AI)
```

### PortalApplyFlow

One apply flow for a portal (a portal may have multiple: easy apply, standard, external ATS).

```python
class PortalApplyFlow(BaseModel):
    flow_name: str                            # "easy_apply", "standard_apply", etc.
    ariadne_path_id: str                      # which Ariadne path to use
    entry_detection: PortalEntryDetection
    form_targets: dict[str, AriadneTarget]    # named targets for known form elements
```

### PortalEntryDetection

How to detect which apply flow is available for a given job.

```python
class PortalEntryDetection(BaseModel):
    url_pattern: str | None = None            # regex matching the apply URL
    trigger_target: AriadneTarget | None = None  # element whose presence indicates this flow
    detection_priority: int = 0               # higher = checked first
```

### PortalRoutingConfig

Application routing logic: given a job, which flow applies?

```python
class PortalRoutingConfig(BaseModel):
    routing_method: Literal["url_pattern", "element_detection", "metadata", "manual"]
    routes: list[PortalRoute]
```

### PortalRoute

One routing rule.

```python
class PortalRoute(BaseModel):
    condition: str                            # what makes this route match
    flow_name: str | None = None              # which apply flow to use
    outcome: Literal["apply", "external_ats", "email_apply", "unsupported"]
    description: str | None = None
```

## Form target dictionary

The `form_targets` field in `PortalApplyFlow` maps well-known form element names
to AriadneTargets. This is how portals supply the multi-strategy target descriptors.

```python
# Example for LinkedIn Easy Apply
{
    "first_name": AriadneTarget(
        text="First name",
        css="input[name='firstName']",
    ),
    "last_name": AriadneTarget(
        text="Last name",
        css="input[name='lastName']",
    ),
    "phone": AriadneTarget(
        text="Mobile phone number",
        css="input[name='phone']",
    ),
    "cv_upload": AriadneTarget(
        text="Boton para cargar curriculum",
        css="input[type='file']",
    ),
    "submit": AriadneTarget(
        text="Enviar solicitud",
        css="button[aria-label='Submit application']",
    ),
}
```

Each target carries both `text` (for BrowserOS) and `css` (for Crawl4AI).
Vision fields (`image_template`, `ocr_text`) are added when templates are captured.

## Current equivalents

| Contract | Current code | Location |
|---|---|---|
| `PortalDefinition` | (no unified equivalent) | — |
| `PortalCapabilities` | (implicit in `build_providers()` backend selection) | `src/apply/main.py` |
| `PortalScrapeConfig` | `SmartScraperAdapter` abstract methods | `src/scraper/smart_adapter.py` |
| `PortalLinkExtraction` | `extract_links()` + `extract_job_id()` | same |
| `PortalApplyConfig` | `ApplyAdapter` abstract methods | `src/apply/smart_adapter.py` |
| `PortalApplyFlow` | (implicit — one flow per adapter) | — |
| `PortalEntryDetection` | `PlaybookEntryPoint` | `src/apply/browseros_models.py` |
| `PortalRoutingConfig` | (no equivalent — routing not implemented) | — |
| Form targets | `FormSelectors` (CSS only) | `src/apply/models.py` |

The current code splits portal knowledge across scraper adapters (abstract methods),
apply adapters (abstract methods + FormSelectors), and BrowserOS models (entry points).
The portal contracts unify this into one definition per source.
