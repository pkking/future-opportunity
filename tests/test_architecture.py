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
