# AGENT.md - Hot Yoga Studios Backend

## Build/Test Commands
- Install dependencies: `uv sync` or `uv install`
- Run main script: `uv run python main.py` or `uv run python main.py --help`
- Run specific scripts: `uv run python scrape_hot_yoga_studios.py`, `uv run python database_operations.py`
- No formal test suite - test manually by running scripts with sample data

## Code Style Guidelines
- Python 3.12+ required
- Use type hints from `typing` module (Dict, List, Any, Optional, Tuple, Union)
- Import order: standard library, third-party, local modules with empty lines between groups
- Use `#!/usr/bin/env python3` shebang and docstrings for all main scripts
- Logging: use structured logging with handlers for both file (`logs/`) and console output
- Error handling: use try/except blocks, especially for external API calls and imports
- Use `os.makedirs("logs", exist_ok=True)` pattern for directory creation
- Variable names: snake_case, descriptive names (e.g., `coworking_places_data`)
- Functions: return type hints, handle Optional/None cases explicitly

## Project Rules
- For new files/logic changes: update `dev-docs/task-update.txt` (don't overwrite existing content)
- Use MCP servers: supabase, brave-search, fetch-mcp, context7, browser-tools
- Database: Supabase project ID `lkmyxcwmkgsmmkefelkl` in EU West region

## Dependencies
- Core: requests, pandas, python-dotenv, crawl4ai, tqdm, supabase, pycountry
- Use `uv` for all dependency management operations
