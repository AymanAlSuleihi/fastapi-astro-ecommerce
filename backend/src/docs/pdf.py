"""PDF generation for documents using weasyprint + Jinja2."""

from io import BytesIO
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

_templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
)


def generate_pdf(document: dict) -> bytes:
    """Render a document dict to a PDF via HTML template."""
    html_str = _templates.get_template("document.html").render(doc=document)
    out = BytesIO()
    HTML(string=html_str).write_pdf(out)
    return out.getvalue()
