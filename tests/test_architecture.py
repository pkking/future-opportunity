from pathlib import Path
import ast


FORBIDDEN_DOMAIN_IMPORT_PREFIXES = (
    "fastapi",
    "httpx",
    "psycopg",
    "ccxt",
    "sqlalchemy",
    "requests",
    "aiohttp",
)


def test_domain_layer_has_no_framework_or_exchange_sdk_dependencies() -> None:
    domain_root = Path("src/future_opportunity/domain")
    violations: list[str] = []

    for path in domain_root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]

            for module in modules:
                if module.startswith(FORBIDDEN_DOMAIN_IMPORT_PREFIXES):
                    violations.append(f"{path}: {module}")

    assert violations == []


def test_exchange_adapters_are_read_only_in_v0() -> None:
    exchange_root = Path("src/future_opportunity/adapters/exchanges")
    violations: list[str] = []
    mutating_methods = {"post", "put", "patch", "delete"}

    for path in exchange_root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if isinstance(node.func, ast.Attribute):
                if node.func.attr in mutating_methods:
                    violations.append(f"{path}: .{node.func.attr}(...)")
                    continue

                if node.func.attr == "request":
                    method: str | None = None
                    if node.args and isinstance(node.args[0], ast.Constant):
                        if isinstance(node.args[0].value, str):
                            method = node.args[0].value
                    for keyword in node.keywords:
                        if (
                            keyword.arg == "method"
                            and isinstance(keyword.value, ast.Constant)
                            and isinstance(keyword.value.value, str)
                        ):
                            method = keyword.value.value
                    if method and method.upper() != "GET":
                        violations.append(
                            f"{path}: request(method={method!r})"
                        )

    assert violations == []
