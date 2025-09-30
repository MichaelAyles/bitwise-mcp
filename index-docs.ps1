#!/usr/bin/env pwsh
# Auto-index all PDFs in docs folder

param(
    [string]$DocsPath = "docs",
    [switch]$Verbose
)

Write-Host "🔍 Scanning for PDFs in $DocsPath..." -ForegroundColor Cyan

$docs = Get-ChildItem -Path $DocsPath -Filter "*.pdf" -ErrorAction SilentlyContinue

if ($docs.Count -eq 0) {
    Write-Host "❌ No PDF files found in $DocsPath" -ForegroundColor Red
    exit 1
}

Write-Host "📚 Found $($docs.Count) PDF(s) to index" -ForegroundColor Green
Write-Host ""

foreach ($doc in $docs) {
    Write-Host "📄 Indexing: $($doc.Name)" -ForegroundColor Yellow

    if ($Verbose) {
        poetry run mcp-embedded-docs ingest $doc.FullName --title $doc.BaseName
    } else {
        poetry run mcp-embedded-docs ingest $doc.FullName --title $doc.BaseName 2>&1 | Out-Null
        Write-Host "  ✓ Indexed" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "✅ All documents indexed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Indexed documents:" -ForegroundColor Cyan
poetry run mcp-embedded-docs list