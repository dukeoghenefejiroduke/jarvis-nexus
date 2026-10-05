"""Safe file and data intelligence manager for JARVIS Nexus workspace isolation."""

import os
import csv
import json
import statistics
from typing import Any, Dict, List, Optional


class FileManager:
    """Manages secure file inspection within a controlled workspace directory."""

    def __init__(self, workspace_dir: Optional[str] = None, max_file_size_bytes: int = 10 * 1024 * 1024) -> None:
        self.workspace_dir = os.path.abspath(workspace_dir or "data/workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)
        self.max_file_size_bytes = max_file_size_bytes

    def _sanitize_path(self, filename: str) -> str:
        """Safely resolve path and enforce workspace containment, preventing path traversal."""
        # Clean filename/path
        if os.path.isabs(filename):
            # If absolute, check if it's within workspace
            abs_path = os.path.abspath(filename)
        else:
            abs_path = os.path.abspath(os.path.join(self.workspace_dir, filename))

        # Enforce workspace containment using commonpath
        common = os.path.commonpath([self.workspace_dir, abs_path])
        if common != self.workspace_dir:
            raise ValueError(f"Security Error: Access denied for path '{filename}' outside workspace.")

        # Check for symbolic link escaping
        if os.path.islink(abs_path):
            real_path = os.path.realpath(abs_path)
            common_real = os.path.commonpath([self.workspace_dir, real_path])
            if common_real != self.workspace_dir:
                raise ValueError(f"Security Error: Symbolic link escapes workspace for '{filename}'.")

        return abs_path

    def list_files(self) -> List[Dict[str, Any]]:
        """List all available files within the controlled workspace directory."""
        results = []
        try:
            for root, _, files in os.walk(self.workspace_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    try:
                        rel_path = os.path.relpath(full_path, self.workspace_dir)
                        stat = os.stat(full_path)
                        results.append({
                            "name": rel_path,
                            "size_bytes": stat.st_size,
                            "modified_at": stat.st_mtime,
                            "extension": os.path.splitext(file)[1].lower()
                        })
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error listing files: {e}")
        return results

    def read_file(self, filename: str, max_lines: int = 100) -> Dict[str, Any]:
        """Read a text or Markdown file with line truncation limits."""
        try:
            safe_path = self._sanitize_path(filename)
            if not os.path.exists(safe_path):
                return {"status": "error", "message": f"File '{filename}' not found."}
            
            if os.path.getsize(safe_path) > self.max_file_size_bytes:
                return {"status": "error", "message": f"File '{filename}' exceeds maximum allowed size."}

            ext = os.path.splitext(safe_path)[1].lower()
            if ext not in ['.txt', '.md', '.csv', '.json']:
                return {"status": "error", "message": f"Unsupported file extension '{ext}'. Supported: .txt, .md, .csv, .json"}

            lines = []
            with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip('\n'))

            content = "\n".join(lines)
            return {
                "status": "success",
                "filename": filename,
                "lines_read": len(lines),
                "truncated": len(lines) >= max_lines,
                "content": content
            }
        except ValueError as ve:
            return {"status": "error", "message": str(ve)}
        except Exception as e:
            return {"status": "error", "message": f"Error reading file: {str(e)}"}

    def inspect_csv(self, filename: str, sample_rows: int = 5) -> Dict[str, Any]:
        """Inspect CSV files: rows count, columns, column names, sample rows, numeric stats."""
        try:
            safe_path = self._sanitize_path(filename)
            if not os.path.exists(safe_path):
                return {"status": "error", "message": f"File '{filename}' not found."}

            if os.path.getsize(safe_path) > self.max_file_size_bytes:
                return {"status": "error", "message": f"File '{filename}' exceeds maximum allowed size."}

            rows = []
            with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                try:
                    header = next(reader)
                except StopIteration:
                    return {"status": "success", "filename": filename, "rows": 0, "columns": 0, "column_names": [], "samples": []}
                
                for row in reader:
                    rows.append(row)

            row_count = len(rows)
            col_count = len(header) if header else 0
            samples = rows[:sample_rows]

            # Calculate basic numeric statistics for numeric columns
            stats = {}
            if header and rows:
                for col_idx, col_name in enumerate(header):
                    col_values = []
                    for row in rows:
                        if col_idx < len(row):
                            val_str = row[col_idx].strip()
                            try:
                                # Try float conversion
                                val = float(val_str)
                                col_values.append(val)
                            except ValueError:
                                pass
                    if len(col_values) > 0:
                        stats[col_name] = {
                            "min": min(col_values),
                            "max": max(col_values),
                            "mean": statistics.mean(col_values),
                            "count": len(col_values)
                        }

            return {
                "status": "success",
                "filename": filename,
                "row_count": row_count,
                "column_count": col_count,
                "column_names": header,
                "sample_rows": samples,
                "numeric_statistics": stats
            }
        except ValueError as ve:
            return {"status": "error", "message": str(ve)}
        except Exception as e:
            return {"status": "error", "message": f"Error inspecting CSV: {str(e)}"}

    def inspect_json(self, filename: str) -> Dict[str, Any]:
        """Inspect JSON files: structure summary, keys, list/object info, safe summary."""
        try:
            safe_path = self._sanitize_path(filename)
            if not os.path.exists(safe_path):
                return {"status": "error", "message": f"File '{filename}' not found."}

            if os.path.getsize(safe_path) > self.max_file_size_bytes:
                return {"status": "error", "message": f"File '{filename}' exceeds maximum allowed size."}

            with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)

            data_type = type(data).__name__
            keys = list(data.keys()) if isinstance(data, dict) else None
            length = len(data) if isinstance(data, (dict, list)) else None

            # Safe summary preview (truncated if large)
            preview = json.dumps(data, indent=2)
            if len(preview) > 2000:
                preview = preview[:2000] + "\n... [truncated]"

            return {
                "status": "success",
                "filename": filename,
                "data_type": data_type,
                "top_level_keys": keys,
                "item_count": length,
                "preview": preview
            }
        except ValueError as ve:
            return {"status": "error", "message": str(ve)}
        except json.JSONDecodeError as jde:
            return {"status": "error", "message": f"Invalid JSON format: {str(jde)}"}
        except Exception as e:
            return {"status": "error", "message": f"Error inspecting JSON: {str(e)}"}

    def search_files(self, query: str, extension: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search text and Markdown files for a phrase, returning matching snippets with line numbers."""
        results = []
        try:
            files = self.list_files()
            for file_info in files:
                fname = file_info["name"]
                ext = file_info["extension"]
                if extension and ext != extension.lower():
                    continue
                if ext in ['.txt', '.md', '.csv', '.json']:
                    safe_path = self._sanitize_path(fname)
                    try:
                        with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if query.lower() in line.lower():
                                    results.append({
                                        "filename": fname,
                                        "line_number": line_num,
                                        "snippet": line.strip()
                                    })
                                    if len(results) >= 50:  # limit total snippets
                                        return results
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error searching files: {e}")
        return results
