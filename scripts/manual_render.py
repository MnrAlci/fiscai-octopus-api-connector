"""Huisstijl-renderer voor de handleidingen (PDF via Chrome/Chromium headless, DOCX via python-docx).

Minimalistische FISCALCI-huisstijl: alleen logo/zegel, FISCALCI, Accounting & Tax en de kleuren #092B47, #016BFC, #01D0FD.
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ATTR = "Powered by FISCALCI Accounting & Tax (Askin Alci)"
NAVY, BLUE, CYAN = "#092B47", "#016BFC", "#01D0FD"

CSS = """
@page { size: A4; margin: 26mm 20mm 24mm 24mm;
  @top-left { content: "FISCALCI"; background: url(%(img)s) no-repeat left center; background-size: 8mm 8mm; padding-left: 11mm; font-family: 'Marcellus', Georgia, serif; font-size: 12pt; letter-spacing: 3px; color: %(navy)s; border-bottom: 2px solid %(blue)s; vertical-align: middle; width: 55%%; padding-bottom: 3mm; }
  @top-right { content: "Accounting & Tax"; font-family: 'Poppins', Arial, sans-serif; font-size: 8pt; letter-spacing: 1px; color: %(blue)s; border-bottom: 2px solid %(blue)s; vertical-align: middle; padding-bottom: 3mm; }
  @bottom-left { content: "%(attr)s"; font-family: 'Poppins', Arial, sans-serif; font-size: 7.5pt; color: %(navy)s; border-top: 1px solid %(cyan)s; vertical-align: middle; width: 80%%; padding-top: 2mm; }
  @bottom-right { content: counter(page); font-family: 'Poppins', Arial, sans-serif; font-size: 7.5pt; color: %(navy)s; border-top: 1px solid %(cyan)s; vertical-align: middle; padding-top: 2mm; } }
@page :first { @top-left { content: none; border: 0; } @top-right { content: none; border: 0; } @bottom-left { content: none; border: 0; } @bottom-right { content: none; border: 0; } }
html { font-family: 'Poppins', 'Segoe UI', Arial, sans-serif; color: #1c2433; font-size: 10pt; line-height: 1.55; }
body { margin: 0; }
h1, h2, h3 { font-family: 'Marcellus', Georgia, serif; color: %(navy)s; font-weight: 400; }
h1 { font-size: 22pt; border-bottom: 2px solid %(blue)s; padding-bottom: 6px; margin-top: 0; }
h2 { font-size: 15pt; margin-top: 22px; border-bottom: 1px solid %(cyan)s; padding-bottom: 3px; page-break-after: avoid; }
h3 { font-size: 12pt; page-break-after: avoid; color: %(blue)s; }
a { color: %(blue)s; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.5pt; background: #eef4fb; padding: 1px 3px; border-radius: 3px; word-break: break-word; }
pre { background: #f3f7fc; border-left: 3px solid %(blue)s; padding: 8px 10px; font-size: 8pt; white-space: pre-wrap; word-break: break-word; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%%; margin: 8px 0 14px; font-size: 8.8pt; page-break-inside: auto; }
th { background: %(navy)s; color: #fff; text-align: left; padding: 5px 7px; }
td { border-bottom: 1px solid #dfe7f1; padding: 4px 7px; vertical-align: top; }
tr { page-break-inside: avoid; }
blockquote { border-left: 3px solid %(cyan)s; margin: 10px 0; padding: 2px 12px; color: #34475a; background: #f5fbfe; }
.cover { page-break-after: always; text-align: left; padding-top: 38mm; position: relative; height: 195mm; }
.cover img { width: 34mm; }
.cover .brand { font-family: 'Marcellus', Georgia, serif; letter-spacing: 6px; font-size: 20pt; color: %(navy)s; margin-top: 10mm; }
.cover .slogan { color: %(blue)s; letter-spacing: 2px; font-size: 11pt; }
.cover .rule { height: 4px; width: 60mm; background: linear-gradient(90deg, %(navy)s, %(blue)s, %(cyan)s); margin: 8mm 0; }
.cover h1 { border: 0; font-size: 26pt; }
.cover .by { position: absolute; bottom: 0; font-size: 8pt; color: %(navy)s; }
"""


def _css(img: str) -> str:
    return CSS % {"navy": NAVY, "blue": BLUE, "cyan": CYAN, "img": img, "attr": ATTR}


def _html(md_text: str, title: str, logo: Path, lang: str) -> str:
    import base64
    import markdown
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
    body = re.sub(r"^<h1>.*?</h1>", "", body, count=1, flags=re.S)
    b64 = base64.b64encode(logo.read_bytes()).decode()
    img = f"data:image/png;base64,{b64}"
    from PIL import Image
    import io
    im = Image.open(logo).convert("RGBA")
    im.thumbnail((40, 40), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    small = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    sub = "Accounting &amp; Tax"
    return (f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>{_css(small)}</style></head><body>"
            f"<div class='cover'><img src='{img}' alt='FISCALCI'><div class='brand'>FISCALCI</div><div class='slogan'>{sub}</div><div class='rule'></div><h1>{html.escape(title)}</h1><div class='by'>{ATTR}</div></div>"
            f"{body}</body></html>")


def build_pdf(md_text: str, title: str, logo: Path, out_pdf: Path, lang: str) -> bool:
    chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser") if subprocess.run(["which", c], capture_output=True).returncode == 0), None)
    if not chrome:
        print("WAARSCHUWING: geen Chrome/Chromium; PDF overgeslagen", file=sys.stderr)
        return False
    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "m.html"
        h.write_text(_html(md_text, title, logo, lang), encoding="utf-8")
        subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}", "--virtual-time-budget=4000", h.as_uri()],
                       check=True, capture_output=True, timeout=180)
    return out_pdf.is_file() and out_pdf.stat().st_size > 5000


def build_docx(md_text: str, title: str, logo: Path, out: Path) -> None:
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt, RGBColor
    rgb = lambda h: RGBColor.from_string(h.lstrip("#").upper())  # noqa: E731
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Mm(297), Mm(210)
    sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Mm(24), Mm(20), Mm(26), Mm(24)
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Poppins", Pt(10)
    hp = sec.header.paragraphs[0]
    hp.add_run().add_picture(str(logo), width=Mm(8))
    r = hp.add_run("  FISCALCI   ")
    r.font.size, r.font.color.rgb, r.font.name = Pt(12), rgb(NAVY), "Marcellus"
    r2 = hp.add_run("Accounting & Tax")
    r2.font.size, r2.font.color.rgb = Pt(8), rgb(BLUE)
    fp = sec.footer.paragraphs[0]
    fr = fp.add_run(ATTR)
    fr.font.size, fr.font.color.rgb = Pt(7.5), rgb(NAVY)
    # titelpagina
    p = doc.add_paragraph()
    p.add_run().add_picture(str(logo), width=Mm(34))
    p = doc.add_paragraph()
    rr = p.add_run("FISCALCI")
    rr.font.size, rr.font.color.rgb, rr.font.name = Pt(20), rgb(NAVY), "Marcellus"
    p = doc.add_paragraph()
    rr = p.add_run("Accounting & Tax")
    rr.font.size, rr.font.color.rgb = Pt(11), rgb(BLUE)
    p = doc.add_paragraph()
    rr = p.add_run(title)
    rr.font.size, rr.font.color.rgb, rr.font.name = Pt(24), rgb(NAVY), "Marcellus"
    doc.add_page_break()

    def inline(par, text: str) -> None:
        for tok in re.split(r"(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))", text):
            if not tok:
                continue
            if tok.startswith("`"):
                run = par.add_run(tok[1:-1])
                run.font.name, run.font.size = "Consolas", Pt(8.5)
            elif tok.startswith("**"):
                par.add_run(tok[2:-2]).bold = True
            elif tok.startswith("["):
                m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", tok)
                run = par.add_run(f"{m.group(1)} ({m.group(2)})")
                run.font.color.rgb = rgb(BLUE)
            else:
                par.add_run(tok.replace("<", "").replace(">", ""))

    lines = md_text.split("\n")
    i = 0
    first_h1 = True
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# "):
            if first_h1:
                first_h1 = False
                i += 1
                continue
        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            p = doc.add_paragraph()
            run = p.add_run("\n".join(buf))
            run.font.name, run.font.size = "Consolas", Pt(8)
            i += 1
            continue
        m = re.match(r"^(#{1,3}) (.*)", ln)
        if m:
            h = doc.add_heading(level=len(m.group(1)))
            run = h.add_run(m.group(2))
            run.font.color.rgb, run.font.name = rgb(NAVY if len(m.group(1)) < 3 else BLUE), "Marcellus"
            i += 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(set(c) <= set("-: ") for c in cells):
                    rows.append(cells)
                i += 1
            t = doc.add_table(rows=len(rows), cols=max(len(r) for r in rows))
            t.style = "Table Grid"
            for ri, row in enumerate(rows):
                for ci, c in enumerate(row):
                    cell = t.cell(ri, ci)
                    cell.paragraphs[0].text = ""
                    inline(cell.paragraphs[0], c)
                    for run in cell.paragraphs[0].runs:
                        run.font.size = Pt(8.5)
                        if ri == 0:
                            run.bold, run.font.color.rgb = True, RGBColor(255, 255, 255)
                    if ri == 0:
                        tcPr = cell._tc.get_or_add_tcPr()
                        shd = OxmlElement("w:shd")
                        shd.set(qn("w:val"), "clear")
                        shd.set(qn("w:fill"), NAVY.lstrip("#"))
                        tcPr.append(shd)
            doc.add_paragraph()
            continue
        mo = re.match(r"^(\d+)\. (.*)", ln)
        if mo:
            p = doc.add_paragraph(style="List Number")
            inline(p, mo.group(2))
            i += 1
            continue
        if ln.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            inline(p, ln[2:])
            i += 1
            continue
        if ln.startswith(">"):
            txt = ln.lstrip("> ").strip()
            if txt:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Mm(6)
                inline(p, txt)
                for run in p.runs:
                    run.italic = True
            i += 1
            continue
        if ln.strip():
            p = doc.add_paragraph()
            inline(p, ln)
        i += 1
    doc.core_properties.title, doc.core_properties.author = title, "FISCALCI Accounting & Tax"
    doc.save(str(out))


