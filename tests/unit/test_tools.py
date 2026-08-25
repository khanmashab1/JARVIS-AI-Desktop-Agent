"""Unit tests for all core JARVIS tools."""

from pathlib import Path
from app.memory.manager import MemoryManager
from app.security.sanitizer import InputSanitizer
from app.tools.applications import ListRunningApplicationsTool, OpenApplicationTool
from app.tools.development import CreateProjectTool, InspectProjectTool, ReadSourceFileTool, SearchCodeTool
from app.tools.filesystem import (
    AppendFileTool,
    CopyFileTool,
    CreateFileTool,
    CreateFolderTool,
    DeleteFileTool,
    ListDirectoryTool,
    MoveFileTool,
    ReadFileTool,
    RenameFileTool,
    SearchFilesTool,
    WriteFileTool,
)
from app.tools.productivity import CreateNoteTool, CreateReminderTool, ReadNoteTool
from app.tools.system import (
    GetBatteryStatusTool,
    GetCpuUsageTool,
    GetCurrentTimeTool,
    GetDiskUsageTool,
    GetMemoryUsageTool,
    GetSystemInformationTool,
    GetVolumeTool,
    SetVolumeTool,
)


def test_filesystem_tools(tmp_path: Path):
    sanitizer = InputSanitizer(allowed_roots=[tmp_path])

    # 1. Create Folder
    folder_tool = CreateFolderTool(sanitizer)
    res = folder_tool.execute(path=str(tmp_path / "test_dir"))
    assert res.success is True

    # 2. Create & Write File
    create_tool = CreateFileTool(sanitizer)
    test_file = tmp_path / "test_dir" / "hello.py"
    res = create_tool.execute(path=str(test_file), content="print('Hello World')\n")
    assert res.success is True

    # 3. Read File
    read_tool = ReadFileTool(sanitizer)
    res = read_tool.execute(path=str(test_file))
    assert res.success is True
    assert "Hello World" in res.output

    # 4. Append File
    append_tool = AppendFileTool(sanitizer)
    res = append_tool.execute(path=str(test_file), content="print('Appended Line')\n")
    assert res.success is True

    # 5. List Directory
    list_tool = ListDirectoryTool(sanitizer)
    res = list_tool.execute(path=str(tmp_path / "test_dir"))
    assert res.success is True
    assert "hello.py" in res.output

    # 6. Copy File
    copy_tool = CopyFileTool(sanitizer)
    copied_file = tmp_path / "test_dir" / "hello_copy.py"
    res = copy_tool.execute(source=str(test_file), destination=str(copied_file))
    assert res.success is True
    assert copied_file.exists()

    # 7. Search Files
    search_tool = SearchFilesTool(sanitizer)
    res = search_tool.execute(directory=str(tmp_path), query="hello")
    assert res.success is True
    assert len(res.output) >= 2

    # 8. Delete File
    del_tool = DeleteFileTool(sanitizer)
    res = del_tool.execute(path=str(copied_file))
    assert res.success is True
    assert not copied_file.exists()


def test_system_tools():
    time_tool = GetCurrentTimeTool()
    res = time_tool.execute()
    assert res.success is True
    assert "datetime" in res.output

    sys_tool = GetSystemInformationTool()
    res = sys_tool.execute()
    assert res.success is True
    assert "os" in res.output
    assert "total_ram_gb" in res.output

    cpu_tool = GetCpuUsageTool()
    res = cpu_tool.execute()
    assert res.success is True

    mem_tool = GetMemoryUsageTool()
    res = mem_tool.execute()
    assert res.success is True
    assert "percent_used" in res.output

    disk_tool = GetDiskUsageTool()
    res = disk_tool.execute()
    assert res.success is True

    bat_tool = GetBatteryStatusTool()
    res = bat_tool.execute()
    assert res.success is True

    vol_tool = GetVolumeTool()
    res = vol_tool.execute()
    assert res.success is True


def test_development_tools(tmp_path: Path):
    sanitizer = InputSanitizer(allowed_roots=[tmp_path])

    # 1. Create Project
    create_proj = CreateProjectTool(sanitizer)
    res = create_proj.execute(name="DemoApp", template="python", parent_dir=str(tmp_path))
    assert res.success is True

    # 2. Inspect Project
    inspect_tool = InspectProjectTool(sanitizer)
    res = inspect_tool.execute(directory=str(tmp_path / "DemoApp"))
    assert res.success is True
    assert res.output["total_files"] >= 3

    # 3. Search Code
    search_tool = SearchCodeTool(sanitizer)
    res = search_tool.execute(directory=str(tmp_path / "DemoApp"), pattern="def main")
    assert res.success is True
    assert "def main" in res.output


def test_productivity_tools(tmp_path: Path):
    memory = MemoryManager(tmp_path / "prod_test.db")

    note_tool = CreateNoteTool(memory)
    res = note_tool.execute(title="Test Note", content="Sample content", tags=["test"])
    assert res.success is True

    read_note = ReadNoteTool(memory)
    res = read_note.execute(title_or_id="Test Note")
    assert res.success is True
    assert res.output["content"] == "Sample content"

    rem_tool = CreateReminderTool(memory)
    res = rem_tool.execute(text="Doctor appointment", due_time="2026-08-30T10:00:00")
    assert res.success is True


def test_weather_tool():
    from app.tools.weather import GetWeatherTool
    tool = GetWeatherTool()
    assert tool.name == "get_weather"
    assert tool.risk_level.value == "SAFE"


def test_supervisor_and_web_testing(tmp_path: Path):
    from app.tools.development import SuperviseDevTaskTool, TestWebsiteTool
    from app.security.sanitizer import InputSanitizer

    sanitizer = InputSanitizer(allowed_roots=[tmp_path])
    sup_tool = SuperviseDevTaskTool(sanitizer)
    assert sup_tool.name == "supervise_dev_task"

    web_tool = TestWebsiteTool()
    assert web_tool.name == "test_website"
