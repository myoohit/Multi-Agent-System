"""
Converts the finished report (+ critique) into a styled, downloadable
PDF. Uses xhtml2pdf: it takes HTML + CSS and produces a real vector PDF
(selectable text, small file size) — not a screenshot of the page.
"""

import markdown as md
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime

# All styling lives in this one template. xhtml2pdf only understands a
# subset of CSS, so this is deliberately simple: serif body type, a
# violet accent for headings, and page numbers in the footer — the
# "research paper" look, without anything fancy that could fail to render.
PDF_TEMPLATE = """
<html>
<head>
<style>
  @page {{
    size: A4;
    margin: 2.4cm 2.2cm;
    @frame footer_frame {{
      -pdf-frame-content: footer_content;
      bottom: 1cm;
      margin-left: 2.2cm;
      margin-right: 2.2cm;
      height: 1cm;
    }}
  }}
  body {{
    font-family: "Times New Roman", Times, serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #1a1a1a;
  }}
  .eyebrow {{
    font-family: Helvetica, sans-serif;
    font-size: 8.5pt;
    letter-spacing: 2px;
    color: #7a5cff;
  }}
  h1.title {{ font-size: 21pt; margin: 6px 0 2px; }}
  .meta {{
    font-family: Helvetica, sans-serif;
    font-size: 9pt;
    color: #666666;
    margin-bottom: 18px;
    border-bottom: 1pt solid #cccccc;
    padding-bottom: 12px;
  }}
  h2 {{
    font-size: 14pt;
    color: #3d2f8f;
    margin-top: 22px;
    margin-bottom: 6px;
    border-bottom: 0.5pt solid #dddddd;
    padding-bottom: 4px;
  }}
  h3 {{ font-size: 12pt; margin-top: 14px; }}
  p {{ margin: 0 0 10px; text-align: justify; }}
  ul, ol {{ margin: 0 0 10px; padding-left: 20px; }}
  li {{ margin-bottom: 4px; }}
  strong {{ color: #3d2f8f; }}
  .section-label {{
    font-family: Helvetica, sans-serif;
    font-size: 9pt;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #999999;
    margin-top: 30px;
    margin-bottom: 8px;
  }}
  #footer_content {{
    font-family: Helvetica, sans-serif;
    font-size: 8pt;
    color: #999999;
    text-align: center;
  }}
</style>
</head>
<body>
  <div class="eyebrow">AUTONOMOUS RESEARCH PIPELINE</div>
  <h1 class="title">{topic}</h1>
  <div class="meta">Generated on {date}</div>

  {report_html}
  {critique_section}

  <div id="footer_content">Page <pdf:pagenumber /> of <pdf:pagecount /></div>
</body>
</html>
"""


def build_report_pdf(topic: str, report_markdown: str, critique_markdown: str = None) -> bytes:
    """Takes the raw markdown from the writer/critic chains, returns PDF bytes."""
    report_html = md.markdown(report_markdown)

    critique_section = ""
    if critique_markdown:
        critique_html = md.markdown(critique_markdown)
        critique_section = f'<div class="section-label">Critic\'s Review</div>{critique_html}'

    html = PDF_TEMPLATE.format(
        topic=topic,
        date=datetime.now().strftime("%B %d, %Y"),
        report_html=report_html,
        critique_section=critique_section,
    )

    output = BytesIO()
    pisa.CreatePDF(html, dest=output)
    return output.getvalue()