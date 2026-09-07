"""Small, accessible SVG vocabulary; external strings are always escaped."""
from html import escape
from xml.etree import ElementTree

STYLE = '''
svg { color: #292136; background: transparent; }
.bg { fill: #FAF8FF; stroke: #D9CFE7; }
.panel { fill: #F0EAFA; stroke: #D9CFE7; }
text { fill: #292136; font: 16px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.muted { fill: #655674; } .accent { fill: #6D28D9; }
.signal { fill: #6D28D9; } .line { stroke: #A898BE; fill: none; }
@media (prefers-color-scheme: dark) {
 .bg { fill: #171321; stroke: #493A5E; }
 .panel { fill: #211A30; stroke: #493A5E; }
 text { fill: #F2EDF9; } .muted { fill: #BDB0CF; }
 .accent { fill: #C4B5FD; } .signal { fill: #C4B5FD; }
 .line { stroke: #88749F; }
}
@keyframes breathe { 50% { opacity: .45; } }
.pulse { animation: breathe 4s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) { .pulse { animation: none; } }
'''


def text(x: float, y: float, value: object, css: str = '', size: int = 16) -> str:
    return f'<text x="{x}" y="{y}" class="{css}" style="font-size:{size}px">{escape(str(value))}</text>'


def line(x1: float, y1: float, x2: float, y2: float) -> str:
    return f'<path class="line" d="M{x1} {y1} L{x2} {y2}"/>'


def document(title: str, description: str, height: int, elements: list[str], source: str, width: int = 480) -> str:
    result = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<!-- AUTO-GENERATED FILE. Source: {source}. Do not edit manually. -->
<title id="title">{escape(title)}</title>
<desc id="desc">{escape(description)}</desc>
<style>{STYLE}</style>
<rect class="bg" x="1" y="1" width="{width-2}" height="{height-2}" rx="14"/>
{chr(10).join(elements)}
</svg>
'''
    ElementTree.fromstring(result)
    return result
