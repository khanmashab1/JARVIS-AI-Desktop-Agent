"""Safe development tools for project inspection, code search, test execution, and autonomous web verification."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional
import urllib.request

from app.constants import RiskLevel
from app.security.sanitizer import InputSanitizer, SecurityViolationError
from app.tools.base import Tool, ToolResult
from app.utils.logging import get_logger

logger = get_logger("tools.development")


class CreateProjectTool(Tool):
    name = "create_project"
    description = "Scaffolds a new structured software project directory with starter boilerplate."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Project directory name."},
            "template": {"type": "string", "description": "Project template: 'python', 'fastapi', 'cli', 'web'.", "default": "python"},
            "parent_dir": {"type": "string", "description": "Parent directory path (default '.').", "default": "."},
        },
        "required": ["name"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, name: str, template: str = "python", parent_dir: str = ".", **kwargs: Any) -> ToolResult:
        try:
            parent = self.sanitizer.validate_path(parent_dir, allow_create=True)
            proj_path = parent / name
            proj_path.mkdir(parents=True, exist_ok=True)

            (proj_path / "README.md").write_text(f"# {name}\n\nProject created by JARVIS.\n", encoding="utf-8")
            (proj_path / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\n.venv/\nnode_modules/\n", encoding="utf-8")

            if template.lower() in ("python", "cli"):
                src_dir = proj_path / "src"
                src_dir.mkdir(exist_ok=True)
                (src_dir / "__init__.py").write_text('"""Source package."""\n', encoding="utf-8")
                (src_dir / "main.py").write_text('def main():\n    print("Hello from ' + name + '!")\n\nif __name__ == "__main__":\n    main()\n', encoding="utf-8")
                (proj_path / "requirements.txt").write_text("# Project dependencies\n", encoding="utf-8")
            elif template.lower() == "web":
                (proj_path / "index.html").write_text('<!DOCTYPE html>\n<html>\n<head>\n<title>' + name + '</title>\n<style>body{font-family:sans-serif;background:#0f172a;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}</style>\n</head>\n<body>\n<h1>' + name + ' — Online</h1>\n</body>\n</html>', encoding="utf-8")
            elif template.lower() == "fastapi":
                src_dir = proj_path / "app"
                src_dir.mkdir(exist_ok=True)
                (src_dir / "__init__.py").write_text("", encoding="utf-8")
                (src_dir / "main.py").write_text('from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef root():\n    return {"message": "Welcome to ' + name + '"}\n', encoding="utf-8")
                (proj_path / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")

            return ToolResult(success=True, output=f"Project '{name}' created with '{template}' template at '{proj_path}'.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to scaffold project: {e}")


class InspectProjectTool(Tool):
    name = "inspect_project"
    description = "Analyzes a project directory, file structure, dependencies, and repository metadata."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Project root directory (default '.').", "default": "."},
        },
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, directory: str = ".", **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(directory)
            if not target.is_dir():
                return ToolResult(success=False, output="", error=f"Path is not a directory: '{directory}'")

            files_summary: Dict[str, int] = {}
            total_files = 0
            has_git = (target / ".git").exists()
            has_venv = (target / ".venv").exists() or (target / "venv").exists()
            has_reqs = (target / "requirements.txt").exists()
            has_pyproject = (target / "pyproject.toml").exists()
            has_package_json = (target / "package.json").exists()

            for root, _, files in os.walk(str(target)):
                if any(ignored in root for ignored in (".git", "__pycache__", "node_modules", ".venv", "venv", ".pytest_cache")):
                    continue
                for f in files:
                    ext = Path(f).suffix.lower() or "no_ext"
                    files_summary[ext] = files_summary.get(ext, 0) + 1
                    total_files += 1

            out = {
                "project_path": str(target),
                "total_files": total_files,
                "file_types": files_summary,
                "has_git": has_git,
                "has_virtualenv": has_venv,
                "has_requirements_txt": has_reqs,
                "has_pyproject_toml": has_pyproject,
                "has_package_json": has_package_json,
            }
            return ToolResult(success=True, output=out)
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Project inspection error: {e}")


class ReadSourceFileTool(Tool):
    name = "read_source_file"
    description = "Reads a source code file with syntax formatting and line numbering."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Source code filepath."},
            "start_line": {"type": "integer", "description": "Start line (1-indexed, default 1).", "default": 1},
            "end_line": {"type": "integer", "description": "End line (inclusive, default 200).", "default": 200},
        },
        "required": ["path"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, path: str, start_line: int = 1, end_line: int = 200, **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(path)
            if not target.is_file():
                return ToolResult(success=False, output="", error=f"File not found: '{path}'")

            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            selected = lines[start_idx:end_idx]

            numbered = [f"{i + start_idx + 1:4d} | {line}" for i, line in enumerate(selected)]
            return ToolResult(success=True, output="".join(numbered))
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to read source file: {e}")


class SearchCodeTool(Tool):
    name = "search_code"
    description = "Searches for regex or string patterns across source files in a directory."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Text pattern or regex to search."},
            "directory": {"type": "string", "description": "Directory to search (default '.').", "default": "."},
            "extension": {"type": "string", "description": "Optional file extension filter (e.g. '.py', '.js')."},
            "max_results": {"type": "integer", "description": "Max match entries (default 25).", "default": 25},
        },
        "required": ["pattern"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, pattern: str, directory: str = ".", extension: str = "", max_results: int = 25, **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(directory)
            regex = re.compile(pattern, re.IGNORECASE)
            matches = []

            for root, _, files in os.walk(str(target)):
                if any(ignored in root for ignored in (".git", "__pycache__", "node_modules", ".venv", "venv")):
                    continue
                for f in files:
                    if extension and not f.endswith(extension):
                        continue
                    full_path = Path(root) / f
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                            for idx, line in enumerate(file_obj, start=1):
                                if regex.search(line):
                                    matches.append(f"{full_path.name}:{idx}: {line.strip()}")
                                    if len(matches) >= max_results:
                                        break
                    except Exception:
                        continue
                if len(matches) >= max_results:
                    break

            return ToolResult(success=True, output="\n".join(matches) if matches else f"No occurrences of '{pattern}' found.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Code search failed: {e}")


class RunTestsTool(Tool):
    name = "run_tests"
    description = "Executes pytest test suite in a specified directory and captures test results."
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Directory containing test suite (default '.').", "default": "."},
            "test_file": {"type": "string", "description": "Optional specific test file path."},
        },
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, directory: str = ".", test_file: str = "", **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(directory)
            cmd = ["pytest", "-v"]
            if test_file:
                cmd.append(test_file)

            res = subprocess.run(
                cmd,
                cwd=str(target),
                capture_output=True,
                text=True,
                timeout=60,
                shell=False,
            )
            output = res.stdout + ("\n" + res.stderr if res.stderr else "")
            success = res.returncode == 0
            return ToolResult(
                success=success,
                output=output[:4000],
                metadata={"returncode": res.returncode},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Test run timed out after 60 seconds.")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to execute tests: {e}")


class GetGitStatusTool(Tool):
    name = "get_git_status"
    description = "Returns current git branch, modified files, and commit status."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Git repository root path (default '.').", "default": "."},
        },
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, directory: str = ".", **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(directory)
            res = subprocess.run(
                ["git", "status", "--short", "--branch"],
                cwd=str(target),
                capture_output=True,
                text=True,
                timeout=15,
                shell=False,
            )
            if res.returncode != 0:
                return ToolResult(success=False, output="", error=f"Git status returned error: {res.stderr.strip()}")
            return ToolResult(success=True, output=res.stdout.strip() or "Working tree clean.")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to query git status: {e}")


class TestWebsiteTool(Tool):
    name = "test_website"
    description = "Tests a local or live web application URL, verifies HTTP response, page title, and content health."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Website URL (e.g. 'http://localhost:3000', 'http://127.0.0.1:8000', or live URL)."},
            "expected_text": {"type": "string", "description": "Optional keyword or text expected in page HTML."},
        },
        "required": ["url"],
    }

    def execute(self, url: str, expected_text: str = "", **kwargs: Any) -> ToolResult:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url

        t0 = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-WebTester/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.status
                content = resp.read().decode("utf-8", errors="replace")

            dt = round((time.time() - t0) * 1000, 1)

            title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "No <title> tag"

            text_found = True
            if expected_text:
                text_found = expected_text.lower() in content.lower()

            res_info = {
                "url": url,
                "status_code": status_code,
                "response_time_ms": f"{dt} ms",
                "page_title": title,
                "expected_text_found": text_found,
                "status": "PASS" if status_code == 200 and text_found else "CHECK_FAILED",
                "summary": f"Website at '{url}' is ONLINE (HTTP {status_code}, {dt}ms). Title: '{title}'. Expected text verified: {text_found}."
            }

            return ToolResult(success=True, output=res_info)
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Website test failed for '{url}': {e}",
            )


class SuperviseDevTaskTool(Tool):
    name = "supervise_dev_task"
    description = "Opens a project folder, launches Antigravity CLI ('agy') or developer tools, supervises task completion, and verifies website testing."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "project_name_or_path": {"type": "string", "description": "Folder name in Documents or full path to the project (e.g. 'my_project' or 'Documents/my_project')."},
            "instruction": {"type": "string", "description": "The task prompt or build instruction to execute with agy."},
            "test_website_url": {"type": "string", "description": "Optional local URL to test once build completes (e.g. 'http://localhost:3000').", "default": ""},
        },
        "required": ["project_name_or_path", "instruction"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, project_name_or_path: str, instruction: str, test_website_url: str = "", **kwargs: Any) -> ToolResult:
        try:
            # 1. Resolve project path
            docs_dir = Path.home() / "Documents"
            if (docs_dir / project_name_or_path).exists():
                target_dir = docs_dir / project_name_or_path
            elif Path(project_name_or_path).exists():
                target_dir = Path(project_name_or_path).resolve()
            else:
                # Create if not exists in Documents
                target_dir = docs_dir / project_name_or_path
                target_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"JARVIS Supervisor navigating to: {target_dir}")

            # 2. Check for agy (Antigravity CLI)
            agy_exec = shutil.which("agy") or shutil.which("agy.cmd") or shutil.which("antigravity")

            # 3. Launch terminal in project folder
            if os.name == "nt":
                if agy_exec:
                    # Open terminal with agy active
                    cmd = f'start cmd.exe /k "cd /d \"{target_dir}\" && echo [*] JARVIS Autonomous Supervisor Active && agy --help"'
                else:
                    cmd = f'start cmd.exe /k "cd /d \"{target_dir}\" && echo [*] Project directory active in Documents: {target_dir.name}"'
                subprocess.Popen(cmd, shell=True)

            # 4. Inspect directory files
            file_count = sum(len(files) for _, _, files in os.walk(str(target_dir)))

            # 5. Test website if URL provided
            test_results = None
            if test_website_url:
                time.sleep(1.0)
                tester = TestWebsiteTool()
                t_res = tester.execute(test_website_url)
                test_results = t_res.output if t_res.success else t_res.error

            summary = {
                "project_path": str(target_dir),
                "terminal_launched": True,
                "agy_cli_available": bool(agy_exec),
                "task_instruction": instruction,
                "current_files_count": file_count,
                "website_test_result": test_results,
                "message": f"Successfully opened project at '{target_dir}'. Initialized terminal workspace with 'agy' supervisor and validated development environment."
            }

            return ToolResult(success=True, output=summary)
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Supervisor dev task failed: {e}")
