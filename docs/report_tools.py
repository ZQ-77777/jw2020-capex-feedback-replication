"""
Helpers for docs/build_report_zh.py: pull exact source excerpts (with real line numbers) out of the
package, so every formula in the report points at the code that implements it.
"""
from __future__ import annotations

import ast
import html
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG = "zh"          # "zh" or "en": only changes the "lines a-b" labels


def set_lang(lang: str) -> None:
    global LANG
    LANG = lang


def _lines_label(a: int, b: int | None = None) -> str:
    if LANG == "en":
        return f"line {a}" if b is None or b == a else f"lines {a}–{b}"
    return f"第 {a} 行" if b is None or b == a else f"第 {a}–{b} 行"


@lru_cache(maxsize=None)
def _lines(file: str) -> list[str]:
    return (ROOT / file).read_text(encoding="utf-8").splitlines()


def func_span(file: str, name: str) -> tuple[int, int]:
    tree = ast.parse("\n".join(_lines(file)))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            return node.lineno, node.end_lineno
    raise KeyError(f"{name} not found in {file}")


def region_span(file: str, start: str, end: str | None) -> tuple[int, int]:
    """Lines from the first line containing `start` to the line before the next line containing `end`
    (or to the end of the enclosing block if end is None)."""
    L = _lines(file)
    a = next(i for i, x in enumerate(L) if start in x)
    if end is None:
        b = a
    else:
        b = next(i for i in range(a + 1, len(L)) if end in L[i]) - 1
    while b > a and not L[b].strip():
        b -= 1
    return a + 1, b + 1


def line_of(file: str, needle: str, nth: int = 1) -> int:
    hits = [i + 1 for i, x in enumerate(_lines(file)) if needle in x]
    if len(hits) < nth:
        raise KeyError(f"{needle!r} not found in {file}")
    return hits[nth - 1]


def text(file: str, a: int, b: int) -> str:
    L = _lines(file)[a - 1:b]
    ind = min((len(x) - len(x.lstrip()) for x in L if x.strip()), default=0)
    return "\n".join(x[ind:] for x in L)


def code_block(file: str, a: int, b: int, title: str = "", anchor: str = "") -> str:
    body = html.escape(text(file, a, b))
    aid = f' id="{anchor}"' if anchor else ""
    return (f'<figure class="code"{aid}><figcaption><code>{file}</code> · {_lines_label(a, b)}'
            f'{" · " + html.escape(title) if title else ""}</figcaption><pre><code>{body}</code></pre></figure>')


def ref(file: str, a: int, b: int | None = None, anchor: str = "") -> str:
    inner = f"<code>{file}</code> {_lines_label(a, b)}"
    return f'<a href="#{anchor}">{inner}</a>' if anchor else inner


def one_line(file: str, needle: str, nth: int = 1) -> str:
    n = line_of(file, needle, nth)
    return (f'<div class="codeline"><span><code>{file}</code> {_lines_label(n)}</span>'
            f'<pre><code>{html.escape(_lines(file)[n - 1].strip())}</code></pre></div>')


def js_notes(js_file: Path, var: str) -> dict[str, str]:
    """Read a `var X={"KEY|n":"text",...};` object from the study guide's script."""
    s = js_file.read_text(encoding="utf-8")
    m = re.search(r"var " + re.escape(var) + r"=\{(.*?)\};", s, re.S)
    if not m:
        return {}
    return {k: v for k, v in re.findall(r'"([A-Za-z_0-9]+\|?\d*)":"((?:[^"\\]|\\.)*)"', m.group(1))}
