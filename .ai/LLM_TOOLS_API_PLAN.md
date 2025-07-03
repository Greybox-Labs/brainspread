# LLM Tool Use API Implementation Plan

## Overview
Create a dedicated LLM Tools API that provides structured endpoints for LLM providers (Anthropic, OpenAI, Google Gemini) to interact with the brainspread knowledge base using function calling/tool use.

## Current Codebase Analysis
- **Architecture**: Django + PostgreSQL with command pattern
- **Existing Apps**: `core` (users), `knowledge` (pages/blocks), `ai_chat`, `tagging`
- **Models**: `Page` (containers), `Block` (hierarchical content), `Tag` (taggable content)
- **Current APIs**: REST endpoints with DRF, token auth, command pattern

## Implementation Plan

### Phase 1: New LLM Tools App
Create `llm_tools/` Django app with:

**Core Tools:**
- `create-page` - Create new page with optional blocks and tags
- `search-content` - Semantic search across user's content
- `get-page` - Retrieve specific page with all blocks
- `add-block` - Add block to existing page
- `update-block` - Modify existing block content
- `get-recent-activity` - Get recent pages/blocks for context
- `tag-content` - Add/manage tags on pages/blocks
- `get-tagged-content` - Retrieve content by tags

### Phase 2: LLM-Optimized Design
**Response Format Standardization:**
```json
{
  "success": true,
  "data": {...},
  "metadata": {
    "timestamp": "...",
    "user_id": "...",
    "operation": "..."
  }
}
```

**Tool Definitions:** Create JSON schema definitions compatible with:
- Anthropic (detailed descriptions, JSON Schema)
- OpenAI (structured outputs, strict mode)
- Google Gemini (function declarations, parameter objects)

### Phase 3: Implementation Structure
```
llm_tools/
├── commands/           # Business logic commands
├── forms/             # Input validation forms
├── serializers.py     # DRF response serializers
├── views.py           # API endpoints
├── urls.py            # URL routing
├── tool_definitions.py # LLM tool schemas
└── permissions.py     # LLM-specific auth
```

**Key Features:**
- Follow existing command pattern architecture
- Reuse existing models and repositories
- Support both Token and API key authentication
- Comprehensive error handling and validation
- Rate limiting for LLM API calls

### Phase 4: Tool Schema Definitions
Create tool definitions for each LLM provider format:
- **Anthropic**: Detailed descriptions, comprehensive JSON Schema
- **OpenAI**: Structured outputs with `strict: true`, simplified schemas
- **Google Gemini**: Function declarations with parameter objects

The API will provide a unified interface while maintaining compatibility with each provider's specific requirements and limitations.

## LLM Provider Requirements

### Anthropic Claude
- **Tool Definition Format**: JSON Schema with detailed descriptions
- **Key Requirements**:
  - `name`: String matching regex `^[a-zA-Z0-9_-]{1,64}$`
  - `description`: Detailed 3-4 sentence explanations
  - `input_schema`: Full JSON Schema with type definitions
- **Best Practices**: Extremely detailed descriptions explaining purpose, usage, parameters, and limitations

### OpenAI GPT
- **Tool Definition Format**: Function calling with structured outputs
- **Key Requirements**:
  - Support for `strict: true` mode for guaranteed schema adherence
  - JSON Schema Draft 8 Patch 1 compatibility
  - `additionalProperties: false` on all objects
  - All object keys must be in `required` array
- **Models**: gpt-4o-2024-08-06, gpt-4o-mini-2024-07-18, gpt-4-turbo

### Google Gemini
- **Tool Definition Format**: Function declarations with parameter objects
- **Key Requirements**:
  - `name`: Unique function identifier
  - `description`: Clear function purpose explanation
  - `parameters`: Object with type, properties, and required fields
- **Models**: Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 2.5 Flash-Lite
- **Calling Modes**: AUTO (default), ANY (must call), NONE (prohibit)

## Next Steps
1. Create the new `llm_tools` Django app
2. Implement core tool endpoints following the command pattern
3. Create tool definition schemas for each LLM provider
4. Add authentication and rate limiting
5. Test with each LLM provider's API
6. Document the API endpoints and tool definitions