#!/usr/bin/env pwsh
# Setup script for Windows to configure MCP server for Claude Code

param(
    [switch]$Global,
    [string]$ProjectPath = $PWD
)

Write-Host "🚀 Setting up MCP Embedded Docs Server" -ForegroundColor Cyan
Write-Host ""

# Get absolute path
$McpPath = Resolve-Path $ProjectPath
Write-Host "📁 MCP Server Path: $McpPath" -ForegroundColor Yellow

# Check if poetry is installed
try {
    poetry --version | Out-Null
    Write-Host "✓ Poetry is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Poetry not found. Install it first:" -ForegroundColor Red
    Write-Host "   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -"
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
Set-Location $McpPath
poetry install

# Create MCP config
$configContent = @"
{
  "mcpServers": {
    "embedded-docs": {
      "command": "poetry",
      "args": [
        "run",
        "mcp-embedded-docs",
        "serve"
      ],
      "cwd": "$($McpPath -replace '\\', '\\')"
    }
  }
}
"@

Write-Host ""
Write-Host "📝 MCP Server Configuration:" -ForegroundColor Cyan
Write-Host $configContent -ForegroundColor White
Write-Host ""

if ($Global) {
    # Global config (for all VSCode projects)
    $configDir = "$env:APPDATA\Code\User\globalStorage\anthropic.claude-code"
    $configPath = "$configDir\mcp_config.json"

    Write-Host "🌍 Installing globally to:" -ForegroundColor Yellow
    Write-Host "   $configPath" -ForegroundColor White
} else {
    # Project-specific config
    $configDir = "$ProjectPath\.claude"
    $configPath = "$configDir\mcp_config.json"

    Write-Host "📁 Installing to current project:" -ForegroundColor Yellow
    Write-Host "   $configPath" -ForegroundColor White
}

# Create directory if it doesn't exist
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Write config
$configContent | Out-File -FilePath $configPath -Encoding utf8

Write-Host ""
Write-Host "✅ MCP server configured!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Index your documentation:" -ForegroundColor White
Write-Host "      poetry run mcp-embedded-docs ingest docs/manual.pdf" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Restart VSCode" -ForegroundColor White
Write-Host ""
Write-Host "   3. Ask Claude Code about your docs!" -ForegroundColor White
Write-Host "      Example: 'Search the docs for GPIO configuration'" -ForegroundColor Gray
Write-Host ""