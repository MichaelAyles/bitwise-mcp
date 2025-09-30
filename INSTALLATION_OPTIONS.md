# Installation Options

This guide covers different ways to install the MCP server depending on your preferences.

## What is Poetry?

**Poetry** is a Python dependency manager (like npm for JavaScript). It:
- Manages dependencies automatically
- Creates isolated virtual environments
- Handles package versions
- Makes Python projects easier to use

### Installing Poetry

**Windows:**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

After installation, restart your terminal.

## Option 1: Poetry (Recommended)

Poetry is the easiest and most reliable method:

```powershell
git clone https://github.com/MichaelAyles/bitwise-mcp.git
cd bitwise-mcp
poetry install

# Use the tools
poetry run mcp-embedded-docs ingest docs/manual.pdf
poetry run mcp-embedded-docs serve
```

**Pros:**
- ✅ Automatic virtual environment
- ✅ Exact dependency versions
- ✅ One command to install everything
- ✅ No manual environment activation

**Cons:**
- ❌ Requires Poetry installation

## Option 2: pip + venv (Manual)

If you prefer not to use Poetry:

```powershell
git clone https://github.com/MichaelAyles/bitwise-mcp.git
cd bitwise-mcp

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e .

# Use the tools (venv must be activated)
mcp-embedded-docs ingest docs/manual.pdf
mcp-embedded-docs serve
```

**Pros:**
- ✅ No additional tools needed
- ✅ Standard Python approach

**Cons:**
- ❌ Manual venv activation required
- ❌ More commands to remember
- ❌ Dependency versions may vary

## Option 3: Global pip Install

Install globally (not recommended for development):

```powershell
git clone https://github.com/MichaelAyles/bitwise-mcp.git
cd bitwise-mcp
pip install -e .

# Use anywhere
mcp-embedded-docs ingest docs/manual.pdf
mcp-embedded-docs serve
```

**Pros:**
- ✅ Available everywhere
- ✅ No activation needed

**Cons:**
- ❌ Can conflict with other Python packages
- ❌ Pollutes global Python environment
- ❌ Not isolated

## Comparison Table

| Method | Setup Complexity | Usage Complexity | Isolation | Recommended |
|--------|-----------------|------------------|-----------|-------------|
| Poetry | Easy | Easy | ✅ Yes | ✅ **Best** |
| pip + venv | Medium | Medium | ✅ Yes | ⚠️ OK |
| Global pip | Easy | Easy | ❌ No | ❌ Not recommended |

## Recommendation

**Use Poetry** unless you have a specific reason not to. It makes everything easier and is what the automation scripts (`setup-mcp.ps1`, `index-docs.ps1`) expect.

## Converting Between Methods

### From Poetry to pip

```powershell
# Export Poetry dependencies to requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Install with pip
pip install -r requirements.txt
```

### From pip to Poetry

```powershell
# Poetry can read from existing setup.py
poetry install
```

## Windows-Specific Notes

### Python Not Found?

If `python` command doesn't work, you might need to:

1. Install Python from [python.org](https://www.python.org/downloads/)
2. Check "Add Python to PATH" during installation
3. Or use `py` instead of `python`:
   ```powershell
   py -m pip install poetry
   ```

### PowerShell Script Execution

If you get "execution policy" errors:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## MCP Config for Different Methods

### Poetry-based config:
```json
{
  "mcpServers": {
    "embedded-docs": {
      "command": "poetry",
      "args": ["run", "mcp-embedded-docs", "serve"],
      "cwd": "C:\\path\\to\\bitwise-mcp"
    }
  }
}
```

### pip-based config:
```json
{
  "mcpServers": {
    "embedded-docs": {
      "command": "C:\\path\\to\\bitwise-mcp\\venv\\Scripts\\mcp-embedded-docs.exe",
      "args": ["serve"]
    }
  }
}
```

### Global install config:
```json
{
  "mcpServers": {
    "embedded-docs": {
      "command": "mcp-embedded-docs",
      "args": ["serve"]
    }
  }
}
```

## Troubleshooting

### "poetry: command not found"

Poetry wasn't added to PATH. Restart terminal or add manually:
- Windows: `%APPDATA%\Python\Scripts`
- macOS/Linux: `$HOME/.local/bin`

### "Module not found" errors

Make sure you're in the right directory and ran install:
```powershell
cd bitwise-mcp
poetry install  # or pip install -e .
```

### Dependencies won't install

Try updating pip first:
```powershell
python -m pip install --upgrade pip
poetry install
```

## Still Need Help?

See [QUICKSTART.md](QUICKSTART.md) for the fastest setup path, or [INSTALL_VSCODE.md](INSTALL_VSCODE.md) for detailed VSCode integration.