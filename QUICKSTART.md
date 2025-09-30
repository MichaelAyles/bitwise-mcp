# Quick Start (5 Minutes)

The fastest way to get your MCU documentation into Claude Code.

## Windows (Your Dev PC)

### Step 1: Clone & Install (2 min)

```powershell
# In your MCU project directory
git clone https://github.com/MichaelAyles/bitwise-mcp.git .mcp-docs
cd .mcp-docs
poetry install
```

### Step 2: Auto-Setup (30 sec)

```powershell
# Run the setup script
.\setup-mcp.ps1
```

This automatically:
- ✅ Installs dependencies
- ✅ Creates MCP config for Claude Code
- ✅ Tells you what to do next

### Step 3: Index Your Docs (1 min)

```powershell
# Back to your MCU project root
cd ..

# Index all PDFs in your docs folder
.mcp-docs\index-docs.ps1
```

### Step 4: Restart VSCode (1 min)

Close and reopen VSCode. That's it!

## Usage

Just ask Claude Code natural questions:

```
What's the FlexCAN base address?
```

```
How do I configure GPIO pins?
```

```
Show me the clock tree diagram section
```

Claude Code will automatically search your documentation and provide answers!

## Updating Docs

When you add new PDFs to your `docs/` folder:

```powershell
.mcp-docs\index-docs.ps1
```

Done! New docs are now searchable.

## Troubleshooting

### Don't have Poetry?

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Then restart your terminal and try again.

### Claude Code not seeing docs?

1. Check MCP config was created:
   ```powershell
   cat $env:APPDATA\Code\User\globalStorage\anthropic.claude-code\mcp_config.json
   ```

2. Verify docs are indexed:
   ```powershell
   cd .mcp-docs
   poetry run mcp-embedded-docs list
   ```

3. Check VSCode output panel:
   - View > Output
   - Select "Claude Code MCP" from dropdown

### Still stuck?

See `INSTALL_VSCODE.md` for detailed instructions.

## What Just Happened?

1. **MCP Server Installed** - A server that Claude Code can talk to
2. **Docs Indexed** - Your PDFs were parsed and embedded for search
3. **Auto-Connected** - Claude Code automatically connects on startup

Now Claude Code has instant access to all your MCU documentation without you having to do anything!