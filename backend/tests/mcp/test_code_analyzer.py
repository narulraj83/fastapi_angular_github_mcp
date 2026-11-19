from mcp_server.services.code_analyzer import CodeAnalyzer


def test_unused_import_detection():
    source = "import os\n\ndef add(a, b):\n    return a + b\n"
    result = CodeAnalyzer.analyze_python(source, "example.py")
    findings = result["verified_static_findings"]
    assert any(f["category"] == "unused_import" and f["line"] == 1 for f in findings)


def test_todo_detection():
    matches = CodeAnalyzer.find_todos("# TODO: improve\nprint('ok')", "example.py")
    assert matches == [{"file": "example.py", "line": 1, "text": "# TODO: improve"}]
