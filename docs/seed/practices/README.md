# Documentation Practices

Meta-documentation about HOW to document and work with PhD 2.0.

## Files

| File | Description |
|------|-------------|
| `entrypoint.md` | **Start here** — Master development guide with 6-phase lifecycle |
| `11_routing_matrix.md` | Context routing matrix for AI agents |
| `12_context_router_protocol.md` | Orthogonal dimensions and MCP protocol |
| `13_agent_intervention_templates.md` | Standardized agent workflows (sync, implement, design, hotfix) |
| `planning_template_ui.md` | Template for React/UI feature specs |
| `planning_template_backend.md` | Template for backend/pipeline specs |
| `git_hooks.md` | Git hooks for automated policy enforcement |
| `scripts/` | Shell scripts for hook installation |

## Quick Start

1. Read `entrypoint.md` first — it explains the complete 6-phase development lifecycle
2. Use `planning_template_ui.md` for UI features OR `planning_template_backend.md` for backend/pipeline
3. Consult `11_routing_matrix.md` for routing context
4. Use agent templates in `13_agent_intervention_templates.md` when working with AI agents
5. Install hooks: `bash scripts/setup_hooks.sh`
