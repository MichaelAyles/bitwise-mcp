# Installing for VSCode Claude Code

This guide shows how to set up the MCP server to work automatically with Claude Code in VSCode.

## Option 1: MCP Server (Recommended)

This approach makes the documentation available to Claude Code automatically - no need to remember anything!

### Step 1: Install the Server

On your Windows dev PC:

```powershell
# Clone this repo
git clone https://github.com/yourusername/bitwise-mcp.git
cd bitwise-mcp

# Install with Poetry (or pip)
poetry install

# Or with pip
pip install -e .
```

### Step 2: Index Your MCU Project Docs

```powershell
# Navigate to your MCU project
cd C:\path\to\your\mcu-project

# Index your docs folder
poetry run mcp-embedded-docs ingest docs/S32K-RM.pdf --title "S32K144 Reference Manual"

# Or if using pip
mcp-embedded-docs ingest docs/S32K-RM.pdf --title "S32K144 Reference Manual"
```

### Step 3: Configure Claude Code MCP Settings

Add this to your Claude Code MCP configuration. The config file location depends on your setup:

**For Windows:**
- Open VSCode settings (`Ctrl+,`)
- Search for "Claude Code MCP"
- Or edit the config file directly at: `%APPDATA%\Code\User\globalStorage\anthropic.claude-code\mcp_config.json`

**Add this server configuration:**

```json
{
  "mcpServers": {
    "embedded-docs": {
      "command": "poetry",
      "args": [
        "run",
        "mcp-embedded-docs",
        "serve"
      ],
      "cwd": "C:\\absolute\\path\\to\\bitwise-mcp"
    }
  }
}
```

**Or if installed with pip:**

```json
{
  "mcpServers": {
    "embedded-docs": {
      "command": "mcp-embedded-docs",
      "args": ["serve"],
      "cwd": "C:\\absolute\\path\\to\\bitwise-mcp"
    }
  }
}
```

### Step 4: Restart VSCode

After adding the MCP server configuration, restart VSCode. Claude Code will automatically connect to the server.

### Step 5: Use in Claude Code

Now in VSCode, you can ask Claude Code things like:

```
What's the memory map for the FlexCAN peripheral?
```

```
How do I configure GPIO pins on the S32K144?
```

```
Show me the clock configuration registers
```

Claude Code will automatically use the `search_docs` tool to find relevant information from your indexed documentation!

## Option 2: Per-Project Setup

If you want the docs server specific to your MCU project:

### 1. Add as a submodule or copy

```powershell
cd C:\path\to\your\mcu-project
git submodule add https://github.com/yourusername/bitwise-mcp.git .mcp-docs
cd .mcp-docs
poetry install
```

### 2. Create a local index

```powershell
# From your MCU project root
.mcp-docs\poetry run mcp-embedded-docs ingest docs/manual.pdf
```

### 3. Add to project's MCP config

Create `.claude/mcp_config.json` in your MCU project:

```json
{
  "mcpServers": {
    "project-docs": {
      "command": "poetry",
      "args": [
        "run",
        "mcp-embedded-docs",
        "serve"
      ],
      "cwd": "${workspaceFolder}\\.mcp-docs"
    }
  }
}
```

Now the docs are available only when you have this project open!

## Automated Indexing

To automatically re-index when docs change, create a simple script:

**`index-docs.ps1`** (Windows PowerShell):

```powershell
#!/usr/bin/env pwsh
# Auto-index all PDFs in docs folder

$docs = Get-ChildItem -Path "docs" -Filter "*.pdf"

foreach ($doc in $docs) {
    Write-Host "Indexing $($doc.Name)..."
    poetry run mcp-embedded-docs ingest $doc.FullName --title $doc.BaseName
}

Write-Host "✓ All documents indexed"
```

Run it whenever you add new documentation:

```powershell
.\index-docs.ps1
```

## Verifying Installation

Test that everything works:

```powershell
# Check the server starts
poetry run mcp-embedded-docs serve

# In another terminal, check indexed docs
poetry run mcp-embedded-docs list
```

## Troubleshooting

### "Command not found: poetry"

Install Poetry:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### "Module not found" errors

Make sure you're in the right directory and installed dependencies:

```powershell
cd C:\path\to\bitwise-mcp
poetry install
```

### Claude Code not seeing the MCP server

1. Check the MCP config path is correct (use absolute paths)
2. Restart VSCode completely
3. Check VSCode output panel for MCP errors (View > Output > Claude Code MCP)

### No search results

```powershell
# Verify docs are indexed
poetry run mcp-embedded-docs list

# Check index directory exists
dir index\
```

## Using with Multiple Projects

You can set up **one global MCP server** and index documentation from all your projects:

```powershell
# Index docs from multiple projects
poetry run mcp-embedded-docs ingest C:\projects\mcu1\docs\manual1.pdf --title "MCU1 Manual"
poetry run mcp-embedded-docs ingest C:\projects\mcu2\docs\manual2.pdf --title "MCU2 Manual"

# All docs available in single search
poetry run mcp-embedded-docs list
```

Then in Claude Code, you can search across all your projects' documentation at once!

## Example Usage in Claude Code

Once configured, just chat naturally with Claude Code:

**You:** "Look up the FlexCAN initialization sequence"

**Claude Code:** *Automatically uses search_docs tool, finds relevant sections, and provides answer*

**You:** "What's the base address for GPIO Port C?"

**Claude Code:** *Searches docs and returns the memory map information*

No need to remember commands or tool names - Claude Code handles it automatically!