import ast
from typing import Any


class CodeAnalyzer:
    @staticmethod
    def analyze_python(source: str, path: str) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as exc:
            return {"verified_static_findings": [{"file": path, "line": exc.lineno, "severity": "error", "description": f"SyntaxError: {exc.msg}"}], "ai_suggestions": []}

        imported_names: dict[str, int] = {}
        used_names: set[str] = set()
        functions: list[dict[str, Any]] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names[alias.asname or alias.name.split(".")[0]] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        imported_names[alias.asname or alias.name] = node.lineno
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1 + sum(isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.Match)) for n in ast.walk(node))
                functions.append({"name": node.name, "line": node.lineno, "complexity": complexity})

        for name, line in imported_names.items():
            if name not in used_names:
                findings.append({"file": path, "line": line, "severity": "warning", "description": f"Unused import: {name}", "category": "unused_import"})

        for function in functions:
            if function["complexity"] >= 10:
                findings.append({"file": path, "line": function["line"], "severity": "warning", "description": f"High complexity in {function['name']}", "category": "complexity", "complexity": function["complexity"]})

        return {"verified_static_findings": findings, "ai_suggestions": [], "functions": functions}

    @staticmethod
    def find_todos(source: str, path: str) -> list[dict[str, Any]]:
        matches = []
        for number, line in enumerate(source.splitlines(), start=1):
            upper = line.upper()
            if "TODO" in upper or "FIXME" in upper:
                matches.append({"file": path, "line": number, "text": line.strip()})
        return matches
