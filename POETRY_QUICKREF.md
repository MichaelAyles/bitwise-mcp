# Poetry Quick Reference

**Poetry** = Better way to manage Python projects (like npm for Node.js)

## Why Poetry?

Instead of this mess:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install package1 package2 package3
# Hope versions work together...
```

Just do this:
```powershell
poetry install
```

Done! Everything installed, environment created, dependencies locked.

## Installation (One Time)

**Windows:**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Restart terminal.

## Basic Commands

| What You Want | Poetry Command | Old Way |
|---------------|----------------|---------|
| Install everything | `poetry install` | `pip install -r requirements.txt` + venv setup |
| Run a command | `poetry run <command>` | Activate venv first, then run |
| Add a package | `poetry add <package>` | `pip install <package>` |
| Show what's installed | `poetry show` | `pip list` |
| Open shell in env | `poetry shell` | `source venv/bin/activate` |

## For This Project

```powershell
# Install dependencies
poetry install

# Run the MCP server
poetry run mcp-embedded-docs serve

# Index a PDF
poetry run mcp-embedded-docs ingest docs/manual.pdf

# List indexed docs
poetry run mcp-embedded-docs list
```

## Key Benefits

1. **No manual virtual environment** - Poetry creates and manages it
2. **Automatic activation** - `poetry run` uses the right environment
3. **Locked versions** - `poetry.lock` ensures everyone gets same versions
4. **One command** - `poetry install` does everything

## Common Questions

### Do I need to activate the environment?

**No!** Just use `poetry run` before your command:
```powershell
poetry run mcp-embedded-docs serve
```

### Where is the virtual environment?

Poetry hides it. You don't need to know. It just works.

### Can I use pip instead?

Yes, see [INSTALLATION_OPTIONS.md](INSTALLATION_OPTIONS.md) for alternatives.

### What if I don't want Poetry?

You can use regular pip + venv, but it's more manual work. See [INSTALLATION_OPTIONS.md](INSTALLATION_OPTIONS.md).

## Troubleshooting

### "poetry: command not found"

Restart your terminal. If still not found, add to PATH:
- Windows: `%APPDATA%\Python\Scripts`

### Takes too long to install?

Poetry is installing PyTorch and other ML libraries. First time takes 5-10 minutes.

### Want to see what's happening?

Add `-vvv` for verbose output:
```powershell
poetry install -vvv
```

## That's It!

Poetry makes Python project management painless. Just remember:
- `poetry install` - Set up project
- `poetry run <command>` - Run things
- No manual environment activation needed

For more details: https://python-poetry.org/docs/