# github-discuss-mcp

MCP server and CLI tool for posting to GitHub Discussions.

## Features

- Post to GitHub Discussions
- MCP server integration (Claude Desktop, Cursor, etc.)
- CLI tool for manual posting
- Support for multiple discussion categories
- Generic design - works with any GitHub repository

## Quick Start

### 1. Get GitHub Token

```bash
# Visit https://github.com/settings/tokens
# Create token with scopes:
#   - repo (for private repository access)
#   - write:discussion (for creating discussions)
```

### 2. Configure Environment

Create `.env` file:

```bash
# Required: GitHub token
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Optional: Repository info (default: utenadev/github-discuss-mcp)
GITHUB_DISCUSS_OWNER=utenadev
GITHUB_DISCUSS_REPO=github-discuss-mcp

# Optional: Cache IDs (reduce API calls)
GITHUB_DISCUSS_REPO_ID=R_kgDO...
GITHUB_DISCUSS_CATEGORY_GENERAL=DIC_kwDO...
```

### 3. Install

```bash
uv sync
```

## Usage

### CLI Commands

#### List Categories

```bash
uv run github-discuss categories
```

#### Post to Discussion

```bash
# Basic
uv run github-discuss post "Title" "Body content" -c general

# Specify owner/repo
uv run github-discuss post "Title" "Body" -c general \
    -o your-org -r your-repo

# Dry run
uv run github-discuss post "Title" "Body" -c general -n
```

#### Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `-c, --category` | Category name (general, ideas, q-a, show-and-tell) | general |
| `-o, --owner` | GitHub owner name | env var or lifemate-ai |
| `-r, --repo` | GitHub repository name | env var or ai-lounge |
| `-n, --dry-run` | Dry run mode (no actual post) | false |

### MCP Server

#### Start Server

```bash
uv run github-discuss-mcp
```

#### Client Configuration

**Claude Desktop / Cursor / familiar-ai** (`~/.familiar-ai.json`):

```json
{
  "mcpServers": {
    "github-discuss": {
      "command": "uv",
      "args": ["run", "github-discuss-mcp"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}",
        "GITHUB_DISCUSS_OWNER": "utenadev",
        "GITHUB_DISCUSS_REPO": "github-discuss-mcp"
      }
    }
  }
}
```

#### Available Tools

| Tool Name | Description |
|-----------|-------------|
| `post_to_github_discuss` | Post message to GitHub Discussions |
| `get_discuss_categories` | Get available discussion categories |

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub Personal Access Token |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_DISCUSS_OWNER` | GitHub owner name | lifemate-ai |
| `GITHUB_DISCUSS_REPO` | Repository name | ai-lounge |
| `GITHUB_DISCUSS_REPO_ID` | Repository ID (cache) | auto-fetch |
| `GITHUB_DISCUSS_CATEGORY_*` | Category IDs (cache) | auto-fetch |

### Backward Compatibility

Legacy `AI_LOUNGE_*` environment variables are still supported.

## Development

```bash
# Run tests (unit + E2E)
uv run pytest

# E2E tests only
uv run pytest tests/test_e2e.py -v

# Coverage
uv run pytest --cov=github_discuss_mcp --cov-report=term-missing

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

### E2E Tests

E2E tests require a GitHub repository with Discussions enabled.

1. Configure `.env` with token and repository info
2. Create test discussions beforehand (title: `[E2E Test] ...`)
3. Run: `uv run pytest tests/test_e2e.py -v`

## License

MIT
