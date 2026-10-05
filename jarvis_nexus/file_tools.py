"""Tool definitions and registrations for File and Data Intelligence in JARVIS Nexus."""

from typing import Any, Dict, List, Optional
from jarvis_nexus.file_manager import FileManager


def register_file_tools(tool_registry: Any, file_manager: Optional[FileManager] = None) -> None:
    """Register file intelligence tools into the ToolRegistry."""
    fm = file_manager or FileManager()

    def list_files() -> Dict[str, Any]:
        """List all available files in the workspace directory."""
        files = fm.list_files()
        return {"count": len(files), "files": files}

    tool_registry.register(
        name="list_files",
        description="List all available files in the workspace directory.",
        parameters={"type": "object", "properties": {}, "required": []},
        func=list_files
    )

    def read_file(filename: str, max_lines: int = 100) -> Dict[str, Any]:
        """Read a text or Markdown file from the workspace."""
        return fm.read_file(filename, max_lines)

    tool_registry.register(
        name="read_file",
        description="Read the contents of a text (.txt) or markdown (.md) file.",
        parameters={
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Name or relative path of the file to read."},
                "max_lines": {"type": "integer", "description": "Maximum number of lines to read (default 100)."}
            },
            "required": ["filename"]
        },
        func=read_file
    )

    def inspect_csv(filename: str, sample_rows: int = 5) -> Dict[str, Any]:
        """Inspect a CSV file in the workspace."""
        return fm.inspect_csv(filename, sample_rows)

    tool_registry.register(
        name="inspect_csv",
        description="Inspect a CSV file (row count, columns, sample rows, and numeric statistics).",
        parameters={
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Name or relative path of the CSV file."},
                "sample_rows": {"type": "integer", "description": "Number of sample rows to return (default 5)."}
            },
            "required": ["filename"]
        },
        func=inspect_csv
    )

    def inspect_json(filename: str) -> Dict[str, Any]:
        """Inspect a JSON file in the workspace."""
        return fm.inspect_json(filename)

    tool_registry.register(
        name="inspect_json",
        description="Inspect a JSON file structure, keys, item count, and content summary.",
        parameters={
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Name or relative path of the JSON file."}
            },
            "required": ["filename"]
        },
        func=inspect_json
    )

    def search_files(query: str, extension: Optional[str] = None) -> Dict[str, Any]:
        """Search text/markdown files in the workspace for a phrase."""
        results = fm.search_files(query, extension)
        return {"query": query, "extension": extension, "results": results, "count": len(results)}

    tool_registry.register(
        name="search_files",
        description="Search workspace files for a text phrase or keyword snippet.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword or phrase."},
                "extension": {"type": "string", "description": "Optional extension filter (e.g. '.md' or '.txt')."}
            },
            "required": ["query"]
        },
        func=search_files
    )
