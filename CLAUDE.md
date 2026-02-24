# CLAUDE.md - Project Guide for BobbyBot (nellybot)

## What This Is

BobbyBot is a personal AI assistant built on [nanobot](https://github.com/HKUDS/nanobot) (fork: [nellybot](https://github.com/bkpatel95/nellybot)). Nanobot is an ultra-lightweight agent framework (~4,000 lines of Python) that connects LLMs to chat channels with tool use, memory, and scheduling.

The bot's name is **Bobby**. It runs on a Mac Mini, talks to Bhavi via Telegram, and uses a local Llama model (via vLLM-MLX) as its default brain with Gemini 2.5 Pro as the "engineer" subagent.

## Repository Structure

```
bobbybot/
├── nanobot_config/              # Runtime configuration and workspace
│   ├── config.json              # Main config (providers, agents, channels, gateway)
│   ├── commands.txt             # Custom command definitions
│   ├── cron/jobs.json           # Scheduled tasks
│   ├── history/                 # Consolidated session history
│   └── workspace/               # Agent workspace (the bot's "home directory")
│       ├── SOUL.md              # Bot personality and identity
│       ├── USER.md              # Info about Bhavi (the human)
│       ├── AGENTS.md            # Operating instructions and behavior rules
│       ├── TOOLS.md             # Tool usage notes
│       ├── SKILLS.md            # Available skills reference
│       ├── HEARTBEAT.md         # Periodic background task checklist
│       ├── README.md            # Project readme (maintained by engineer agent)
│       ├── memory/
│       │   ├── MEMORY.md        # Curated persistent memory (facts, config, lessons)
│       │   └── HISTORY.md       # Chronological event log (auto-consolidated)
│       └── sessions/
│           └── *.jsonl          # Per-channel conversation history (append-only)
├── .venv-vllm/                  # Python venv for vLLM-MLX local model serving
└── CLAUDE.md                    # This file
```

## Architecture

```
Telegram (user) ──> nanobot gateway ──> MessageBus ──> AgentLoop ──> LLM Provider
                                            │                           │
                                      ChannelManager              Tool Execution
                                            │                    (shell, web, files,
                                      SessionManager              cron, spawn, mcp)
                                            │
                                       MemoryStore
                                    (MEMORY.md + HISTORY.md)
```

**Data flow:** Inbound messages arrive via Telegram long-polling, get queued on the MessageBus, consumed by the AgentLoop which builds context (system prompt + memory + skills), calls the LLM, executes any tool calls in a loop (up to 40 iterations), then publishes the response back through the ChannelManager.

## Agent Profiles

### Default Agent
- **Model:** `openai/mlx-community/Meta-Llama-3.1-8b-Instruct-bf16` (local vLLM-MLX)
- **Role:** Message parser and tool router. Does NOT write code or delete files without permission.
- **Temperature:** 0.0

### Engineer Agent (subagent)
- **Model:** `gemini/gemini-2.5-pro`
- **Role:** Principal Full Stack Software Engineer. Handles complex coding, repo maintenance, system architecture, Mermaid diagrams.
- **Spawned via:** `spawn` tool from the default agent

## Local Infrastructure

### vLLM-MLX (Local Model Server)
```bash
uv run --with vllm-mlx vllm-mlx serve mlx-community/Meta-Llama-3.1-8B-Instruct-bf16 \
  --host 127.0.0.1 --port 8080 --use-paged-cache --continuous-batching --max-cache-blocks 4000
```
- Serves on `http://127.0.0.1:8080/v1` (OpenAI-compatible API)
- Config uses `apiKey: "vllm"` (dummy key for local server)

### Nanobot Gateway
```bash
nanobot gateway
```
- Runs on `0.0.0.0:18790`
- Connects to Telegram channel
- Loads workspace from `nanobot_config/workspace/`

## Key Nanobot CLI Commands

| Command | Description |
|---------|-------------|
| `nanobot onboard` | Initialize config and workspace |
| `nanobot agent` | Interactive CLI agent (single-turn or multi-turn) |
| `nanobot gateway` | Start multi-channel server (Telegram, etc.) |
| `nanobot status` | Show config, workspace, model status |
| `nanobot channels status` | Show channel connection status |
| `nanobot cron list` | List scheduled jobs |
| `nanobot cron add` | Add a scheduled job |

## Configuration

Config lives at `nanobot_config/config.json`. Key sections:

- **providers** - LLM provider API keys and base URLs (openai for local vLLM, gemini for Google)
- **agents.defaults** - Default model, workspace path, temperature, custom instructions
- **agents.engineer** - Engineer subagent profile with Gemini model
- **channels.telegram** - Bot token, enabled flag, `allowFrom` whitelist (user ID)
- **gateway** - Host and port for the gateway server

Environment variables supported with `NANOBOT_` prefix (e.g., `NANOBOT_PROVIDERS__GEMINI__APIKEY`).

## Tools Available to the Bot

| Tool | Description |
|------|-------------|
| `exec` | Shell command execution (60s timeout, destructive patterns blocked) |
| `web_search` | Brave API web search |
| `web_fetch` | Fetch and extract web page content |
| `read_file` | Read files from workspace |
| `write_file` | Write/create files in workspace |
| `edit_file` | Patch files with search/replace |
| `list_dir` | List directory contents |
| `message` | Send messages to chat channels |
| `spawn` | Delegate tasks to subagents (max 15 iterations each) |
| `cron` | Add/list/remove scheduled jobs |

## Memory System

Two-layer persistence:
1. **MEMORY.md** - Curated facts, config, lessons learned. The bot reads this every session and updates it freely. Think of it as distilled knowledge.
2. **HISTORY.md** - Chronological event log. Raw session events get consolidated here automatically.

Memory is consolidated periodically by the LLM. The bot is instructed to write things down rather than rely on "mental notes" since memory doesn't survive session restarts.

## Heartbeat System

Every ~30 minutes, the bot receives a heartbeat poll and checks:
- Urgent unread emails
- Upcoming calendar events (24-48h)
- Weather if relevant
- Whether reminders have been completed

Quiet hours: 23:00-08:00 (replies `HEARTBEAT_OK` unless urgent). Heartbeat state is tracked in `memory/heartbeat-state.json`.

## Skills (Built-in)

Skills are markdown-defined capabilities loaded from `SKILL.md` files:
- **github** - GitHub CLI operations
- **weather** - Weather data retrieval
- **summarize** - Summarize URLs, files, or videos
- **tmux** - Tmux session control
- **cron** - Scheduling instructions
- **memory** - Memory management
- **clawhub** - Search and install community skills
- **skill-creator** - Generate new skills

## Channels Supported

Currently enabled: **Telegram** (long-polling, restricted to Bhavi's user ID)

Also available in nanobot: Discord, WhatsApp (via Node.js bridge on port 3001), Slack, Feishu, DingTalk, Email (IMAP/SMTP), QQ, Mochat.

## Development Notes

- **Python version:** 3.11+
- **Package:** `nanobot-ai` (installable via pip/uv)
- **Build system:** Hatchling
- **Tests:** `pytest` + `pytest-asyncio` (run with `pytest tests/`)
- **Linter:** `ruff`
- **Docker:** Dockerfile uses Python 3.12 + Node.js 20, docker-compose has gateway + CLI services

### Session Files

Conversations are stored as append-only JSONL in `workspace/sessions/`. Each line is a message event. File naming: `{channel}_{user_id}.jsonl`.

### Security Notes

- API keys live in `config.json` - never commit this file with real keys
- `allowFrom` whitelists restrict who can talk to the bot
- Shell exec blocks destructive patterns (`rm -rf`, `format`, `shutdown`, etc.)
- `restrictToWorkspace` can lock file operations to the workspace directory
- WhatsApp bridge binds to localhost only

## Common Workflows

**Start the full stack locally:**
1. Start vLLM-MLX model server (port 8080)
2. Run `nanobot gateway` to connect Telegram and start the agent loop

**Add a new scheduled task:**
Use the `cron` tool or `nanobot cron add` CLI command.

**Change the default model:**
Edit `agents.defaults.model` in `nanobot_config/config.json`.

**Spawn the engineer for code tasks:**
Send a message to Bobby asking to spawn the engineer, or configure tasks that require the engineer profile.
