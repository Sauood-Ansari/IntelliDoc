import ast
import os
import tokenize
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ExtractedFunction:
    name: str
    line_number: int
    signature: str
    parameters: list[str]
    docstring: Optional[str] = None
    has_return_value: bool = False
    is_method: bool = False
    is_async: bool = False
    is_generator: bool = False
    source_code: str = ""
    qualified_name: str = ""
    receiver: Optional[str] = None

@dataclass
class ExtractedSourceFile:
    relative_path: str
    parse_status: str
    error_message: Optional[str] = None
    functions: list[ExtractedFunction] = field(default_factory=list)

class ASTCodebaseParser:
    IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}

    @classmethod
    def discover_python_files(cls, base_dir):
        result = []
        for root, dirs, files in os.walk(base_dir, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in cls.IGNORED_DIRS and not d.startswith(".")
                             and not os.path.islink(os.path.join(root, d)))
            for name in sorted(files):
                path = os.path.join(root, name)
                if name.endswith(".py") and not os.path.islink(path):
                    result.append((os.path.relpath(path, base_dir).replace(chr(92), "/"), path))
        return result

    @classmethod
    def parse_file(cls, relative_path, full_path):
        try:
            with tokenize.open(full_path) as stream:
                source = stream.read()
            tree = ast.parse(source, filename=relative_path)
            return ExtractedSourceFile(relative_path, "Parsed", functions=cls._extract_functions_from_tree(tree, source))
        except (SyntaxError, UnicodeError, ValueError, OSError, RecursionError) as exc:
            return ExtractedSourceFile(relative_path, "Failed", f"{type(exc).__name__}: {exc}")

    @classmethod
    def _extract_functions_from_tree(cls, tree, source=""):
        result = []
        class Returns(ast.NodeVisitor):
            value = False
            generator = False
            def visit_Return(self, node):
                if node.value is not None and not (isinstance(node.value, ast.Constant) and node.value.value is None):
                    self.value = True
            def visit_Yield(self, node):
                self.generator = True
            visit_YieldFrom = visit_Yield
            def visit_FunctionDef(self, node):
                pass
            visit_AsyncFunctionDef = visit_FunctionDef
            visit_ClassDef = visit_FunctionDef
            visit_Lambda = visit_FunctionDef

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.stack = []
            def visit_ClassDef(self, node):
                self.stack.append((node.name, "class"))
                self.generic_visit(node)
                self.stack.pop()
            def visit_FunctionDef(self, node):
                args = node.args
                positional = args.posonlyargs + args.args
                params = [a.arg for a in positional]
                if args.vararg:
                    params.append("*" + args.vararg.arg)
                params.extend(a.arg for a in args.kwonlyargs)
                if args.kwarg:
                    params.append("**" + args.kwarg.arg)
                method = bool(self.stack and self.stack[-1][1] == "class")
                static = any(isinstance(d, ast.Name) and d.id == "staticmethod" for d in node.decorator_list)
                receiver = positional[0].arg if method and not static and positional else None
                returns = Returns()
                for statement in node.body:
                    returns.visit(statement)
                async_ = isinstance(node, ast.AsyncFunctionDef)
                signature = ("async " if async_ else "") + f"def {node.name}({ast.unparse(args)})"
                if node.returns:
                    signature += " -> " + ast.unparse(node.returns)
                result.append(ExtractedFunction(
                    name=node.name, qualified_name=".".join([p[0] for p in self.stack] + [node.name]),
                    line_number=node.lineno, signature=signature, parameters=params,
                    docstring=ast.get_docstring(node), has_return_value=returns.value,
                    is_method=method, is_async=async_, is_generator=returns.generator,
                    receiver=receiver, source_code=ast.get_source_segment(source, node) if source else ast.unparse(node)))
                self.stack.append((node.name, "function"))
                self.generic_visit(node)
                self.stack.pop()
            visit_AsyncFunctionDef = visit_FunctionDef
        Visitor().visit(tree)
        return result

