---
description: Ingest a PDF datasheet or reference manual into the search index
---

Help the user ingest a PDF documentation file into the embedded docs search index. Use the `ingest_docs` MCP tool with the path to the PDF file.

Steps:
1. Ask the user for the path to the PDF if not provided
2. Optionally ask for a title and version
3. Call `ingest_docs` with the path
4. Report the results (number of chunks, register tables found)

Note: Ingestion may take several minutes for large documents (1000+ pages).
