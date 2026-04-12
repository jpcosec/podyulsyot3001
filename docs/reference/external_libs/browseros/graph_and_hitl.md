# BrowserOS External Reference - Graph and HITL

## 5. Graph Directory — `~/.config/browser-os/.browseros/graph/`

BrowserOS stores OpenBrowser agent scripts here as TypeScript files. Each subdirectory is a script ID.

```
graph/
  code_l3aod1jcXf6w/
    graph.ts    ← the agent TypeScript script
```

### What `graph.ts` looks like

The TypeScript script uses the OpenBrowser SDK `Agent` API:

```typescript
export async function run(agent: Agent) {
  await agent.nav("https://www.xing.com/jobs/...");

  const state = await agent.extract("Is the apply modal open?", {
    schema: z.object({ isOpen: z.boolean() })
  });

  await agent.act("Fill the Vorname field with the user's first name", {
    context: { firstName: "Juan Pablo" },
    maxSteps: 5
  });

  const result = await agent.verify("The application was submitted successfully.");
  return { success: result.success };
}
```

### OpenBrowser Agent API (full)

| Method | Signature | What it does |
|--------|-----------|-------------|
| `agent.nav(url)` | `(url: string) => Promise<void>` | Navigate to URL |
| `agent.extract(prompt, {schema})` | Zod schema → structured data | LLM extracts structured info from current page |
| `agent.act(prompt, {context?, maxSteps?})` | Natural language → actions | LLM performs actions on page (multi-step) |
| `agent.verify(prompt)` | `=> {success, reason}` | LLM verifies a condition is true |

**`agent.act` with context:** Variables in `context` are interpolated into the prompt with `{{varName}}` syntax. This is how profile data gets passed to the agent without embedding it in the prompt string.

**This means we can write agent scripts and drop them in `graph/` for BrowserOS to execute.** The graph directory is the integration point for Level 2 execution from our pipeline.

---

## 6. HumanInteractTool — The Formal HITL API

Built into the OpenBrowser agent framework. When the agent needs human input, it calls this tool. The `callback` registered with the agent handles it.

```typescript
// interactType options:
"confirm"      // "Are you sure you want to submit?" → boolean
"input"        // "Enter your salary expectation" → string
"select"       // "Choose your German level" + options → string[]
"request_help" // "Login required" or "CAPTCHA" → boolean (solved?)
```

```typescript
// helpType for request_help:
"request_login"       // Portal requires authentication
"request_assistance"  // Anything else (CAPTCHA, unknown form, etc.)
```

**Login check:** Before surfacing `request_login` to the human, the tool takes a screenshot and asks the LLM "is this page logged in?" If yes, it skips the interruption. This is built-in.

**For our pipeline:** We implement the `callback` interface in Python (via the `/chat` endpoint or by writing a TypeScript wrapper) to route `request_help` and `input` calls to our HITL channel (terminal → Textual TUI).

---
