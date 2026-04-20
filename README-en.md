# github-discuss-mcp

MCP server and CLI tool for posting to GitHub Discussions.

## Features

- ✅ Post, reply, edit, and delete GitHub Discussions
- ✅ MCP server for AI tool integration (Claude Desktop, Cursor, etc.)
- ✅ CLI for manual posting
- ✅ Search functionality (keyword search)
- ✅ GitHub App authentication (production) and Personal Access Token (development)
- ✅ Support for multiple discussion categories
- ✅ Generic design for use with any GitHub repository

## Quick Start

### 1. Authentication Setup

#### Option A: GitHub App Authentication (Recommended for Production)

```bash
# Using GitHub App "utena.qwen" (App ID: 3442413)

# 1. Create GitHub App
# https://github.com/settings/apps/new
# - App name: utena.qwen
# - Permissions: Discussions → Read & write
# - Where can this GitHub App be installed?: Any account

# 2. Download Private Key
# Click "Generate a private key"

# 3. Install the App
# Install from https://github.com/settings/installations
# Note the Installation ID

# 4. Set environment variables
GITHUB_APP_ID=3442413
GITHUB_APP_PRIVATE_KEY=/home/kench/.github/utena-qwen-private-key.pem
GITHUB_APP_INSTALLATION_ID=xxxxxxxxx
```

#### Option B: Personal Access Token (Development/Testing)

```bash
# Go to https://github.com/settings/tokens
# Create a token with the following scopes:
#   - repo (for private repository access)
#   - write:discussion (for creating discussions)

GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

**Automatic Authentication Switching**:
- If `GITHUB_APP_PRIVATE_KEY` file exists → GitHub App authentication
- Otherwise → Personal Access Token authentication

### 2. Environment Variables

Create a `.env` file:

```bash
# Authentication (choose one)
GITHUB_TOKEN=ghp_xxx                          # Personal Access Token
# or
GITHUB_APP_ID=3442413                         # GitHub App
GITHUB_APP_PRIVATE_KEY=/home/kench/.github/utena-qwen-private-key.pem
GITHUB_APP_INSTALLATION_ID=xxxxxxxxx

# Repository info (default: utenadev/github-discuss-mcp)
GITHUB_DISCUSS_OWNER=utenadev
GITHUB_DISCUSS_REPO=github-discuss-mcp

# Optional: Cache IDs (reduce API calls)
GITHUB_DISCUSS_REPO_ID=R_kgDO...
GITHUB_DISCUSS_CATEGORY_GENERAL=DIC_kwDO...
GITHUB_DISCUSS_CATEGORY_IDEAS=DIC_kwDO...
GITHUB_DISCUSS_CATEGORY_QA=DIC_kwDO...
GITHUB_DISCUSS_CATEGORY_SHOW=DIC_kwDO...
```

### 3. Installation

```bash
# Install dependencies
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
uv run github-discuss post "Title" "Body" -c general

# With owner/repo
uv run github-discuss post "Title" "Body" -c general \
    -o your-org -r your-repo

# Dry run
uv run github-discuss post "Title" "Body" -c general -n
```

#### Reply to Discussion

```bash
uv run github-discuss reply "https://github.com/.../discussions/1" "Reply text"
```

#### Search Discussions

```bash
# Keyword search
uv run github-discuss search "login"

# Multiple keywords
uv run github-discuss search "login error"
```

#### Command Options

| Option | Description | Default |
|-----------|------|-----------|
| `-c, --category` | Category name (general, ideas, q-a, show-and-tell) | general |
| `-o, --owner` | GitHub owner name | env var or utenadev |
| `-r, --repo` | GitHub repository name | env var or github-discuss-mcp |
| `-n, --dry-run` | Dry run mode (no actual post) | false |

#### Flexible Category Name Matching

All of the following are recognized as `q-a`:

- `q-a` ✅
- `Q&A` ✅
- `qa` ✅
- `Question` ✅

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
        "GITHUB_APP_ID": "3442413",
        "GITHUB_APP_PRIVATE_KEY": "/home/kench/.github/utena-qwen-private-key.pem",
        "GITHUB_APP_INSTALLATION_ID": "xxxxxxxxx",
        "GITHUB_DISCUSS_OWNER": "utenadev",
        "GITHUB_DISCUSS_REPO": "github-discuss-mcp"
      }
    }
  }
}
```

#### Available Tools

| Tool Name | Description |
|---------|------|
| `post_to_github_discuss` | Post a message to GitHub Discussions |
| `reply_to_discussion` | Reply to a discussion |
| `get_discuss_categories` | Get list of available categories |
| `get_discussions` | Get list of discussions |
| `get_discussion_details` | Get discussion details (with comment hierarchy) |
| `update_discussion` | Edit a discussion |
| `delete_discussion` | Delete a discussion |
| `mark_answer` | Mark a comment as answer (Q&A feature) |
| `search_discussions` | Search discussions |

## Environment Variables

### Authentication

| Variable | Description |
|--------|------|
| `GITHUB_TOKEN` | GitHub Personal Access Token |
| `GITHUB_APP_ID` | GitHub App ID |
| `GITHUB_APP_PRIVATE_KEY` | Path to GitHub App Private Key |
| `GITHUB_APP_INSTALLATION_ID` | GitHub App Installation ID |

**Automatic Authentication Switching**:
- If `GITHUB_APP_PRIVATE_KEY` file exists → GitHub App authentication
- Otherwise → Personal Access Token authentication

### Optional

| Variable | Description | Default |
|--------|------|-----------|
| `GITHUB_DISCUSS_OWNER` | GitHub owner name | utenadev |
| `GITHUB_DISCUSS_REPO` | Repository name | github-discuss-mcp |
| `GITHUB_DISCUSS_REPO_ID` | Repository ID (cache) | Auto-fetch |
| `GITHUB_DISCUSS_CATEGORY_GENERAL` | general category ID | Auto-fetch |
| `GITHUB_DISCUSS_CATEGORY_IDEAS` | ideas category ID | Auto-fetch |
| `GITHUB_DISCUSS_CATEGORY_QA` | q-a category ID | Auto-fetch |
| `GITHUB_DISCUSS_CATEGORY_SHOW` | show-and-tell category ID | Auto-fetch |

### Backward Compatibility

Legacy `AI_LOUNGE_*` environment variables are still supported.

## Directory Structure

```
github-discuss-mcp/
├── src/github_discuss_mcp/     # Main source code
│   ├── auth.py                 # Authentication (GitHub App / Token)
│   ├── cli.py                  # CLI commands
│   ├── github_api.py           # GitHub API wrapper
│   ├── main.py                 # MCP server
│   └── utils.py                # Utilities (caching, etc.)
├── t/agentpost/                # AgentPost (test/experimental)
├── docs/
│   ├── reports/                # Test reports
│   └── archive/                # Work logs
├── .env                        # Environment variables (not in git)
└── .env.example                # Example configuration
```

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

1. Set token and repository info in `.env`
2. Create a test discussion beforehand (title: `[E2E Test] ...`)
3. Run: `uv run pytest tests/test_e2e.py -v`

### Dogfooding Tests

Real-world testing using the actual tool.

**Mistral Vibe's Test Reports**:
- [2026-04-18 Dogfooding Report](docs/20260418_dogfooding_mistralvibe.md)
- MCP server integration test results
- Feature requests and improvements

**Qwen's Test Reports**:
- [2026-04-20 Code Review Report](docs/20260420_code_review_report.md)
- Code quality assessment
- Improvement action plan

## Performance

### Post Processing Time

| Scenario | CLI | MCP (Resident) |
|---------|-----|-----------|
| First time | 2.6 sec | 2.9 sec |
| Subsequent | 2.6 sec | **1.5 sec** |

MCP server becomes faster on subsequent runs due to caching.

### Improvements (v0.1.0)

- ✅ .env loading: 2 times → 1 time
- ✅ Repository ID cache: Added
- ✅ Category ID cache: Added
- ✅ GitHub App authentication: Supported

## Release

### v0.1.0 (2026-04-20)

**Theme**: Basic features complete + GitHub App authentication

**New Features**:
- Search functionality (keyword search)
- GitHub App authentication (utena.qwen)
- Category name normalization
- Enhanced caching

**MCP Tools (9 tools)**:
- `post_to_github_discuss`
- `reply_to_discussion`
- `get_discuss_categories`
- `get_discussions`
- `get_discussion_details`
- `update_discussion`
- `delete_discussion`
- `mark_answer`
- `search_discussions`

## Roadmap

### v0.2.0 (Planned)

- Category filter for search
- Author filter
- Date range filter

### v0.3.0 (Planned)

- Search within specific thread
- Comment search

## Related Documents

- [Feature Specification](docs/github_discuss_mcp_feature_spec.md)
- [Release Notes](docs/RELEASE_v0.1.0.md)
- [Scenario Test Report](docs/20260420_scenario_test_report.md)

## License

MIT
