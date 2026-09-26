# Agent helper scripts

The `.sh` and `.ps1` files are thin wrappers over `agent_tool.py`.

Shared logic lives in one place to avoid shell/PowerShell behavior drift.

Project-specific commands are data in `.agent/project.json` hooks rather than hard-coded workflow text.
