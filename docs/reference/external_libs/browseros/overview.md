# BrowserOS External Reference - Overview

# BrowserOS — Technical Interface Reference

> This document catalogs every known programmatic interface to BrowserOS, verified from live inspection of the running instance and the OpenBrowser open-source codebase. Updated: 2026-04-02.

---
## Instance Info

```json
{
  "browseros_version": "0.44.0.1",
  "chromium_version": "146.0.7821.31",
  "install_id": "edf3cf07-bdb1-42c7-be01-de7b3043fbf8",
  "binary": "/home/jp/BrowserOS.AppImage",
  "pid": "check server.lock"
}
```

---

## Supported Integration Modes

BrowserOS is practically usable in three supported ways:

1. **CLI** — `browseros-cli` for direct terminal control.
2. **MCP server** — connect Claude Code, Gemini CLI, Codex, or any MCP client.
3. **Node SDK** — `@browseros-ai/agent-sdk` for programmatic agent control.

What BrowserOS does **not** currently present as the main integration surface is a
typical public cloud REST API. The primary low-level interface is the local MCP
endpoint speaking JSON-RPC 2.0 / StreamableHTTP.

### CLI workflow

Officially documented flow:

```bash
# macOS / Linux
curl -fsSL https://cdn.browseros.com/cli/install.sh | bash

# Alternative entry points
npx browseros-cli --help
npm install -g browseros-cli

# Typical startup flow
browseros-cli install
browseros-cli launch
browseros-cli init --auto
browseros-cli health
browseros-cli status
```

Useful CLI examples (maps to MCP tools under the hood):

```bash
browseros-cli open https://example.com
browseros-cli nav https://example.com
browseros-cli pages
browseros-cli active
browseros-cli snap
browseros-cli text
browseros-cli click e5
browseros-cli fill e12 "hola"
browseros-cli eval "document.title"
browseros-cli ss -o shot.png
browseros-cli pdf -o page.pdf
```

Notes:
- CLI config is stored at `~/.config/browseros-cli/config.yaml`.
- The CLI can autodetect BrowserOS server metadata from local config/state.

### MCP workflow

BrowserOS ships with an integrated MCP server. Official docs describe opening
`chrome://browseros/mcp`, copying the local MCP URL, and wiring that into the
agent client of choice.

Examples from BrowserOS docs:

```bash
# Claude Code
claude mcp add --transport http browseros http://127.0.0.1:9239/mcp --scope user

# Gemini CLI
gemini mcp add local-server http://127.0.0.1:9239/mcp --transport http --scope user

# OpenAI Codex CLI
codex mcp add browseros http://127.0.0.1:9239/mcp --transport http
```

Important local note:
- The docs often show `9239`.
- On this machine, BrowserOS backend ports rotated across `9200` and `9201` during the session.
- `http://127.0.0.1:9000/mcp` behaved like the most stable MCP entrypoint and is the best current default for local integration here.

### Node SDK workflow

BrowserOS also exposes a Node SDK via `@browseros-ai/agent-sdk`.

```bash
npm install @browseros-ai/agent-sdk
```

Example shape from the SDK README:

```ts
import { Agent } from '@browseros-ai/agent-sdk'
import { z } from 'zod'

const agent = new Agent({
  url: 'http://localhost:9100',
  llm: {
    provider: 'openai',
    apiKey: process.env.OPENAI_API_KEY,
  },
})

await agent.nav('https://example.com')
await agent.act('click the login button')

const { data } = await agent.extract('get all product names and prices', {
  schema: z.array(
    z.object({
      name: z.string(),
      price: z.number(),
    })
  ),
})

const { success, reason } = await agent.verify('user is logged in')
```

Operational takeaway:
- **terminal automation** → use `browseros-cli`
- **external agent integration** → use MCP
- **embedded application logic** → use the Node SDK

---
