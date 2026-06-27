import ast

from ariadne_codegen.plugins.base import Plugin

PACKAGE_PREFIX = "networking.graphql_client"


class AbsoluteImportsPlugin(Plugin):
    def generate_client_import(self, import_: ast.ImportFrom) -> ast.ImportFrom:
        return _make_absolute(import_)

    def generate_client_method_import(self, import_: ast.ImportFrom) -> ast.ImportFrom:
        return _make_absolute(import_)

    def generate_result_import(self, import_: ast.ImportFrom) -> ast.ImportFrom:
        return _make_absolute(import_)

    def generate_init_import(self, import_: ast.ImportFrom) -> ast.ImportFrom:
        return _make_absolute(import_)


def _make_absolute(import_: ast.ImportFrom) -> ast.ImportFrom:
    # Only rewrite relative imports (level > 0 means "from .something import ...")
    if import_.level and import_.level > 0:
        relative_module = import_.module or ""
        absolute_module = f"{PACKAGE_PREFIX}.{relative_module}".rstrip(".")
        return ast.ImportFrom(
            module=absolute_module,
            names=import_.names,
            level=0,  # 0 = absolute
        )
    return import_
