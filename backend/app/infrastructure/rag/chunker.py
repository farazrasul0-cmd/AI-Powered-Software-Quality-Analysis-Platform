"""Grammar-Aware Semantic AST Chunker for Python and TypeScript/JavaScript.

Decomposes source code files into semantically cohesive chunks aligned with
syntactic AST boundaries (classes, functions, methods, interfaces) while
preserving enclosing scopes, parameter signatures, and structural metadata.
"""

import ast
import hashlib
import re
from dataclasses import dataclass, field


@dataclass
class CodeChunk:
    """Represents a syntactically cohesive code unit."""

    chunk_id: str
    file_path: str
    language: str
    symbol_name: str
    symbol_type: str  # FUNCTION, METHOD, CLASS, INTERFACE, MODULE_TOP_LEVEL
    scope_path: list[str]
    start_line: int
    end_line: int
    content: str
    docstring: str | None = None
    parameters: list[str] = field(default_factory=list)
    return_type: str | None = None
    imported_symbols: list[str] = field(default_factory=list)


def generate_chunk_id(file_path: str, symbol_name: str, start_line: int, end_line: int) -> str:
    """Generates a deterministic SHA256 identifier for a code chunk."""
    raw = f"{file_path}:{symbol_name}:{start_line}:{end_line}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class PythonSemanticChunker:
    """AST-driven semantic chunker for Python source files."""

    @classmethod
    def chunk(cls, file_path: str, content: str) -> list[CodeChunk]:
        """Parses Python source code and extracts AST enclosing scope chunks."""
        chunks: list[CodeChunk] = []
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError:
            # Fallback for invalid syntax
            chunk_id = generate_chunk_id(file_path, "module", 1, max(1, total_lines))
            return [
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=file_path,
                    language="python",
                    symbol_name="module",
                    symbol_type="MODULE_TOP_LEVEL",
                    scope_path=["module"],
                    start_line=1,
                    end_line=max(1, total_lines),
                    content=content,
                )
            ]

        # 1. Collect module-level imports
        imported_symbols: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_symbols.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imported_symbols.append(f"{mod}.{alias.name}" if mod else alias.name)

        # 2. Extract Class and Function Definitions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                cls._extract_class(node, file_path, lines, imported_symbols, chunks)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cls._extract_function(
                    node, file_path, lines, imported_symbols, chunks, parent_scope=[]
                )

        # If no function or class chunks were found, treat entire file as module chunk
        if not chunks and content.strip():
            chunk_id = generate_chunk_id(file_path, "module", 1, total_lines)
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=file_path,
                    language="python",
                    symbol_name="module",
                    symbol_type="MODULE_TOP_LEVEL",
                    scope_path=["module"],
                    start_line=1,
                    end_line=total_lines,
                    content=content,
                    imported_symbols=imported_symbols,
                )
            )

        return chunks

    @classmethod
    def _extract_class(
        cls,
        node: ast.ClassDef,
        file_path: str,
        lines: list[str],
        imported_symbols: list[str],
        chunks: list[CodeChunk],
    ) -> None:
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)
        content = "".join(lines[start_line - 1 : end_line])
        docstring = ast.get_docstring(node)

        chunk_id = generate_chunk_id(file_path, node.name, start_line, end_line)
        class_chunk = CodeChunk(
            chunk_id=chunk_id,
            file_path=file_path,
            language="python",
            symbol_name=node.name,
            symbol_type="CLASS",
            scope_path=[node.name],
            start_line=start_line,
            end_line=end_line,
            content=content,
            docstring=docstring,
            imported_symbols=imported_symbols,
        )
        chunks.append(class_chunk)

        # Extract member methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cls._extract_function(
                    item,
                    file_path,
                    lines,
                    imported_symbols,
                    chunks,
                    parent_scope=[node.name],
                )

    @classmethod
    def _extract_function(
        cls,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
        lines: list[str],
        imported_symbols: list[str],
        chunks: list[CodeChunk],
        parent_scope: list[str],
    ) -> None:
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)
        content = "".join(lines[start_line - 1 : end_line])
        docstring = ast.get_docstring(node)

        # Extract parameters
        params: list[str] = []
        for arg in node.args.args:
            arg_name = arg.arg
            if arg.annotation:
                arg_name += f": {ast.unparse(arg.annotation)}"
            params.append(arg_name)

        # Extract return type
        ret_type: str | None = None
        if node.returns:
            ret_type = ast.unparse(node.returns)

        symbol_name = (
            f"{parent_scope[0]}.{node.name}" if parent_scope else node.name
        )
        symbol_type = "METHOD" if parent_scope else "FUNCTION"
        scope_path = parent_scope + [node.name]

        chunk_id = generate_chunk_id(file_path, symbol_name, start_line, end_line)
        chunks.append(
            CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                language="python",
                symbol_name=symbol_name,
                symbol_type=symbol_type,
                scope_path=scope_path,
                start_line=start_line,
                end_line=end_line,
                content=content,
                docstring=docstring,
                parameters=params,
                return_type=ret_type,
                imported_symbols=imported_symbols,
            )
        )


class TypeScriptSemanticChunker:
    """Syntax-aware semantic chunker for TypeScript and JavaScript files."""

    @classmethod
    def chunk(cls, file_path: str, content: str) -> list[CodeChunk]:
        """Extracts top-level classes, interfaces, and functions using balanced block traversal."""
        chunks: list[CodeChunk] = []
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)
        if total_lines == 0:
            return chunks

        # 1. Collect imports
        imported_symbols: list[str] = []
        import_pattern = re.compile(r"import\s+(?:\{([^}]+)\}|([a-zA-Z0-9_$]+))\s+from\s+['\"]([^'\"]+)['\"]")
        for line in lines:
            m = import_pattern.search(line)
            if m:
                if m.group(1):
                    for sym in m.group(1).split(","):
                        s = sym.strip().split(" as ")[0].strip()
                        if s:
                            imported_symbols.append(s)
                elif m.group(2):
                    imported_symbols.append(m.group(2).strip())

        # 2. Block definitions detector
        pattern = re.compile(
            r"^(?:export\s+)?(?:async\s+)?(?:default\s+)?(class|interface|function|const|let|var)\s+([a-zA-Z0-9_$]+)",
            re.MULTILINE,
        )

        matches = list(pattern.finditer(content))
        for i, match in enumerate(matches):
            kind = match.group(1)
            name = match.group(2)

            start_char = match.start()
            start_line = content[:start_char].count("\n") + 1

            # Determine end line: find balanced brace or next match
            brace_count = 0
            found_open = False
            end_char = len(content)

            for char_idx in range(match.end(), len(content)):
                c = content[char_idx]
                if c == "{":
                    brace_count += 1
                    found_open = True
                elif c == "}":
                    brace_count -= 1
                    if found_open and brace_count == 0:
                        end_char = char_idx + 1
                        break
                elif c == ";" and not found_open and kind in ("const", "let", "var"):
                    end_char = char_idx + 1
                    break

            # If not balanced, fall back to next match or end of file
            if not found_open and i + 1 < len(matches):
                end_char = matches[i + 1].start()

            end_line = content[:end_char].count("\n") + 1
            chunk_content = "".join(lines[start_line - 1 : end_line])

            symbol_type = (
                "CLASS"
                if kind == "class"
                else "INTERFACE"
                if kind == "interface"
                else "FUNCTION"
            )

            chunk_id = generate_chunk_id(file_path, name, start_line, end_line)
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=file_path,
                    language="typescript",
                    symbol_name=name,
                    symbol_type=symbol_type,
                    scope_path=[name],
                    start_line=start_line,
                    end_line=end_line,
                    content=chunk_content,
                    imported_symbols=imported_symbols,
                )
            )

        if not chunks and content.strip():
            chunk_id = generate_chunk_id(file_path, "module", 1, total_lines)
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=file_path,
                    language="typescript",
                    symbol_name="module",
                    symbol_type="MODULE_TOP_LEVEL",
                    scope_path=["module"],
                    start_line=1,
                    end_line=total_lines,
                    content=content,
                    imported_symbols=imported_symbols,
                )
            )

        return chunks


class UnifiedSemanticChunker:
    """Universal router for syntax-aware code chunking across languages."""

    @classmethod
    def chunk_file(cls, file_path: str, content: str, language: str | None = None) -> list[CodeChunk]:
        """Routes file to language-specific semantic chunker."""
        lower_path = file_path.lower()

        if language == "python" or lower_path.endswith((".py", ".pyw")):
            return PythonSemanticChunker.chunk(file_path, content)

        if language in ("typescript", "javascript") or lower_path.endswith(
            (".ts", ".tsx", ".js", ".jsx", ".mjs")
        ):
            return TypeScriptSemanticChunker.chunk(file_path, content)

        # Fallback for generic text/configuration
        lines = content.splitlines(keepends=True)
        total_lines = max(1, len(lines))
        chunk_id = generate_chunk_id(file_path, "generic_module", 1, total_lines)
        return [
            CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                language=language or "generic",
                symbol_name="generic_module",
                symbol_type="MODULE_TOP_LEVEL",
                scope_path=["module"],
                start_line=1,
                end_line=total_lines,
                content=content,
            )
        ]
