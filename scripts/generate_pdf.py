#!/usr/bin/env python3
"""
Nutanix Objects API Reference PDF Generator
Parses the nutanix-objects.json API specification and produces a professional PDF document.

Usage:
    python3 generate_pdf.py [--input ../nutanix-objects.json] [--output ../Nutanix-Objects-API-Reference.pdf]
"""

import argparse
import json
import re
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    NextPageTemplate,
)


class OpNameMarker(Flowable):
    """Zero-height flowable that sets the current operation name on the doc."""
    width = 0
    height = 0

    def __init__(self, op_name):
        super().__init__()
        self.op_name = op_name

    def draw(self):
        self.canv._current_op_name = self.op_name


class BookmarkAnchor(Flowable):
    """Zero-height flowable that registers a named PDF destination."""
    width = 0
    height = 0

    def __init__(self, key):
        super().__init__()
        self.key = key

    def draw(self):
        self.canv.bookmarkHorizontal(self.key, 0, 0)

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
NTNX_BLUE = colors.HexColor("#024DA1")
NTNX_DARK = colors.HexColor("#1A1F36")
NTNX_LIGHT_BG = colors.HexColor("#F5F7FA")
NTNX_ACCENT = colors.HexColor("#0070D2")
NTNX_CODE_BG = colors.HexColor("#F0F2F5")
NTNX_BORDER = colors.HexColor("#D8DDE6")
NTNX_MUTED = colors.HexColor("#6B7280")
NTNX_GREEN = colors.HexColor("#16A34A")
NTNX_RED = colors.HexColor("#DC2626")
NTNX_WHITE = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def build_styles():
    ss = getSampleStyleSheet()

    styles = {}
    styles["body"] = ParagraphStyle(
        "body",
        parent=ss["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=NTNX_DARK,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    styles["op_title"] = ParagraphStyle(
        "op_title",
        parent=ss["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=NTNX_BLUE,
        spaceAfter=10,
        spaceBefore=0,
    )
    styles["section"] = ParagraphStyle(
        "section",
        parent=ss["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=NTNX_DARK,
        spaceBefore=14,
        spaceAfter=6,
    )
    styles["subsection"] = ParagraphStyle(
        "subsection",
        parent=ss["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=NTNX_DARK,
        spaceBefore=8,
        spaceAfter=4,
    )
    styles["param_name"] = ParagraphStyle(
        "param_name",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=NTNX_BLUE,
        spaceBefore=8,
        spaceAfter=2,
    )
    styles["param_desc"] = ParagraphStyle(
        "param_desc",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=NTNX_DARK,
        leftIndent=12,
        spaceAfter=2,
    )
    styles["required_tag"] = ParagraphStyle(
        "required_tag",
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=NTNX_MUTED,
        leftIndent=12,
        spaceAfter=6,
    )
    styles["code"] = ParagraphStyle(
        "code",
        fontName="Courier",
        fontSize=8.5,
        leading=12,
        textColor=NTNX_DARK,
        spaceAfter=2,
        leftIndent=6,
    )
    styles["toc_entry"] = ParagraphStyle(
        "toc_entry",
        fontName="Helvetica",
        fontSize=10,
        leading=18,
        textColor=NTNX_DARK,
    )
    styles["toc_title"] = ParagraphStyle(
        "toc_title",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        textColor=NTNX_BLUE,
        spaceBefore=40,
        spaceAfter=20,
    )
    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=40,
        textColor=NTNX_WHITE,
        alignment=TA_LEFT,
    )
    styles["cover_sub"] = ParagraphStyle(
        "cover_sub",
        fontName="Helvetica",
        fontSize=14,
        leading=20,
        textColor=colors.HexColor("#B0C4DE"),
        alignment=TA_LEFT,
    )
    styles["footer"] = ParagraphStyle(
        "footer",
        fontName="Helvetica",
        fontSize=8,
        textColor=NTNX_MUTED,
    )
    styles["error_name"] = ParagraphStyle(
        "error_name",
        fontName="Courier-Bold",
        fontSize=9,
        leading=13,
        textColor=NTNX_RED,
        leftIndent=12,
        spaceBefore=4,
        spaceAfter=2,
    )
    styles["error_desc"] = ParagraphStyle(
        "error_desc",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=NTNX_DARK,
        leftIndent=24,
        spaceAfter=4,
    )
    styles["http_method"] = ParagraphStyle(
        "http_method",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=NTNX_GREEN,
        spaceBefore=4,
        spaceAfter=4,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        parent=styles["body"],
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=3,
    )
    styles["note_label"] = ParagraphStyle(
        "note_label",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#92400E"),
        spaceAfter=2,
    )
    styles["note_text"] = ParagraphStyle(
        "note_text",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#78350F"),
        alignment=TA_JUSTIFY,
    )
    return styles


# ---------------------------------------------------------------------------
# HTML / documentation helpers
# ---------------------------------------------------------------------------
_CDATA_RE = re.compile(r"<!\[CDATA\[|\]\]>")
_MULTI_WS = re.compile(r"\s+")
_NOTE_RE = re.compile(r"\s*<note>\s*(.*?)\s*</note>\s*", re.DOTALL | re.IGNORECASE)
_LINK_RE = re.compile(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")

_LINK_PLACEHOLDER_PREFIX = "\x00LINK"


def _strip_tags_keep_links(html):
    """Strip all HTML tags except <a href> links.

    Replaces <a href> links with reportlab-compatible markup while
    removing every other tag.  The returned string is already escaped
    for use inside a reportlab Paragraph (do NOT call para_escape on it).
    """
    placeholders = []

    def _stash_link(m):
        url = m.group(1)
        label = _TAG_RE.sub("", m.group(2)).strip()
        idx = len(placeholders)
        placeholders.append((url, label))
        return f"{_LINK_PLACEHOLDER_PREFIX}{idx}\x00"

    text = _LINK_RE.sub(_stash_link, html)
    text = _TAG_RE.sub(" ", text)
    text = _MULTI_WS.sub(" ", text).strip()
    text = para_escape(text)

    for idx, (url, label) in enumerate(placeholders):
        token = f"{_LINK_PLACEHOLDER_PREFIX}{idx}\x00"
        rl_link = (
            f'<a href="{url}" color="#024DA1">'
            f'<u>{para_escape(label)}</u></a>'
        )
        text = text.replace(token, rl_link)
    return text


def strip_html(text):
    """Remove HTML tags and normalise whitespace, preserving <a href> links."""
    if not text:
        return ""
    text = _CDATA_RE.sub("", text)
    return _strip_tags_keep_links(text)


def parse_documentation(text):
    """Split documentation into (main_markup, [note_markups]).

    Extracts <note>...</note> blocks.  Strips HTML from everything except
    <a href> links, which are converted to reportlab-compatible markup.
    Returns the body and a list of notes, both ready for Paragraph().
    """
    if not text:
        return "", []
    text = _CDATA_RE.sub("", text)
    notes = []
    for m in _NOTE_RE.finditer(text):
        note_html = m.group(1)
        note_clean = _strip_tags_keep_links(note_html)
        if note_clean:
            notes.append(note_clean)
    main_html = _NOTE_RE.sub(" ", text)
    main_clean = _strip_tags_keep_links(main_html)
    return main_clean, notes


def xml_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para_escape(text):
    """Escape text for use inside reportlab Paragraph XML."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


# ---------------------------------------------------------------------------
# JSON → structured data
# ---------------------------------------------------------------------------
class ApiSpec:
    def __init__(self, path):
        with open(path) as fh:
            self.raw = json.load(fh)
        self.metadata = self.raw.get("metadata", {})
        self.shapes = self.raw.get("shapes", {})
        self.operations = self.raw.get("operations", {})

    def supported_operations(self):
        ops = []
        for name, op in self.operations.items():
            if op.get("isNtnxSupported", True) is False:
                continue
            ops.append((name, op))
        ops.sort(key=lambda x: x[0])
        return ops

    def resolve_shape(self, shape_name):
        return self.shapes.get(shape_name, {})

    def shape_to_xml(self, shape_name, tag_name=None, indent=0, visited=None):
        """Recursively build XML representation of a shape."""
        if visited is None:
            visited = set()
        if shape_name in visited:
            prefix = "  " * indent
            t = tag_name or shape_name
            return [f"{prefix}<{t}>...</{t}>"]
        visited = visited | {shape_name}

        shape = self.resolve_shape(shape_name)
        stype = shape.get("type", "string")
        prefix = "  " * indent
        tag = tag_name or shape_name

        if stype == "blob":
            return []

        if stype in ("string", "integer", "long", "boolean", "timestamp"):
            value = self._primitive_placeholder(shape)
            return [f"{prefix}<{tag}>{value}</{tag}>"]

        if stype == "list":
            member_shape = shape.get("member", {}).get("shape", "")
            member_loc = shape.get("member", {}).get("locationName", member_shape)
            lines = self.shape_to_xml(member_shape, member_loc, indent, visited)
            return lines

        if stype == "structure":
            if shape.get("eventstream"):
                return [f"{prefix}<!-- Event stream response -->"]
            lines = [f"{prefix}<{tag}>"]
            body_children = []
            for mname, minfo in shape.get("members", {}).items():
                if minfo.get("isNtnxSupported", False) is False and "isNtnxSupported" in minfo:
                    continue
                loc = minfo.get("location", "")
                if loc in ("header", "headers", "uri", "querystring"):
                    continue
                child_shape_name = minfo.get("shape", "")
                child_shape = self.resolve_shape(child_shape_name)
                if child_shape.get("type") == "blob":
                    continue
                child_tag = minfo.get("locationName", mname)
                child_lines = self.shape_to_xml(child_shape_name, child_tag, indent + 1, visited)
                body_children.extend(child_lines)
            if not body_children:
                return []
            lines.extend(body_children)
            lines.append(f"{prefix}</{tag}>")
            return lines

        if stype == "map":
            lines = [f"{prefix}<{tag}>"]
            lines.append(f"{prefix}  <entry>")
            lines.append(f"{prefix}    <key>...</key>")
            lines.append(f"{prefix}    <value>...</value>")
            lines.append(f"{prefix}  </entry>")
            lines.append(f"{prefix}</{tag}>")
            return lines

        return [f"{prefix}<{tag}>...</{tag}>"]

    def _primitive_placeholder(self, shape):
        if shape.get("enum"):
            vals = shape["enum"]
            joined = "|".join(vals)
            if len(joined) > 80 and len(vals) > 4:
                return "|".join(vals[:3]) + "|..."
            return joined
        if shape.get("type") == "boolean":
            return "true|false"
        if shape.get("type") in ("integer", "long"):
            return "..."
        if shape.get("type") == "timestamp":
            return "..."
        return "..."

    def get_input_members(self, op):
        """Return (uri_params, query_params, header_params, body_shape_info) for an operation."""
        input_shape_name = op.get("input", {}).get("shape", "")
        if not input_shape_name:
            return [], [], [], None
        shape = self.resolve_shape(input_shape_name)
        required = set(shape.get("required", []))

        uri_params = []
        query_params = []
        header_params = []
        body_members = {}

        for mname, minfo in shape.get("members", {}).items():
            if minfo.get("isNtnxSupported", False) is False and "isNtnxSupported" in minfo:
                continue
            loc = minfo.get("location", "")
            entry = {
                "name": mname,
                "shape": minfo.get("shape", ""),
                "locationName": minfo.get("locationName", mname),
                "documentation": strip_html(minfo.get("documentation", "")),
                "required": mname in required,
            }
            if loc == "uri":
                uri_params.append(entry)
            elif loc == "querystring":
                query_params.append(entry)
            elif loc in ("header", "headers"):
                header_params.append(entry)
            else:
                body_members[mname] = minfo

        payload_name = shape.get("payload")
        body_info = None
        if payload_name and payload_name in body_members:
            body_info = {
                "payload": payload_name,
                "shape": body_members[payload_name].get("shape", ""),
            }
        elif body_members:
            body_info = {
                "payload": None,
                "shape": input_shape_name,
                "members": body_members,
            }
        return uri_params, query_params, header_params, body_info

    def get_output_members(self, op):
        """Return (header_params, body_xml_lines, has_body) for an operation."""
        output_shape_name = op.get("output", {}).get("shape", "")
        if not output_shape_name:
            return [], [], False

        shape = self.resolve_shape(output_shape_name)
        header_params = []
        body_member_names = []

        for mname, minfo in shape.get("members", {}).items():
            if minfo.get("isNtnxSupported", False) is False and "isNtnxSupported" in minfo:
                continue
            loc = minfo.get("location", "")
            if loc in ("header", "headers"):
                entry = {
                    "name": mname,
                    "shape": minfo.get("shape", ""),
                    "locationName": minfo.get("locationName", mname),
                    "documentation": strip_html(minfo.get("documentation", "")),
                    "required": False,
                }
                header_params.append(entry)
            else:
                body_member_names.append(mname)

        payload_name = shape.get("payload")
        xml_lines = []
        has_body = False

        if payload_name:
            payload_info = shape["members"].get(payload_name, {})
            payload_shape = payload_info.get("shape", "")
            payload_tag = payload_info.get("locationName", payload_name)
            resolved = self.resolve_shape(payload_shape)
            if resolved.get("type") == "blob":
                pass
            else:
                candidate_lines = self.shape_to_xml(payload_shape, payload_tag, 0)
                if candidate_lines:
                    has_body = True
                    xml_lines = candidate_lines
        elif body_member_names:
            has_body = True
            root_tag = output_shape_name.replace("Output", "Result")
            xml_lines = [f"<{root_tag}>"]
            for mname in body_member_names:
                minfo = shape["members"][mname]
                if minfo.get("isNtnxSupported", False) is False and "isNtnxSupported" in minfo:
                    continue
                child_shape = minfo.get("shape", "")
                child_tag = minfo.get("locationName", mname)
                child_lines = self.shape_to_xml(child_shape, child_tag, 1)
                xml_lines.extend(child_lines)
            xml_lines.append(f"</{root_tag}>")

        return header_params, xml_lines, has_body

    def get_response_params(self, op):
        """Gather all response parameter descriptions (headers + body members)."""
        output_shape_name = op.get("output", {}).get("shape", "")
        if not output_shape_name:
            return []
        shape = self.resolve_shape(output_shape_name)
        params = []
        for mname, minfo in shape.get("members", {}).items():
            if minfo.get("isNtnxSupported", False) is False and "isNtnxSupported" in minfo:
                continue
            doc, notes = parse_documentation(minfo.get("documentation", ""))
            child_shape = self.resolve_shape(minfo.get("shape", ""))
            child_doc, child_notes = parse_documentation(child_shape.get("documentation", ""))
            params.append({
                "name": mname,
                "documentation": doc or child_doc,
                "notes": notes or child_notes,
                "required": False,
            })
        return params

    def get_request_params(self, op):
        """Gather all request parameter descriptions."""
        input_shape_name = op.get("input", {}).get("shape", "")
        if not input_shape_name:
            return []
        shape = self.resolve_shape(input_shape_name)
        required_set = set(shape.get("required", []))
        params = []
        for mname, minfo in shape.get("members", {}).items():
            if minfo.get("isNtnxSupported", False) is False and "isNtnxSupported" in minfo:
                continue
            doc, notes = parse_documentation(minfo.get("documentation", ""))
            child_shape = self.resolve_shape(minfo.get("shape", ""))
            child_doc, child_notes = parse_documentation(child_shape.get("documentation", ""))
            params.append({
                "name": mname,
                "documentation": doc or child_doc,
                "notes": notes or child_notes,
                "required": mname in required_set,
            })
        return params

    def get_errors(self, op):
        """Return error shapes for the operation."""
        errs = []
        for err_info in op.get("errors", []):
            if err_info.get("isNtnxSupported", True) is False:
                continue
            shape_name = err_info.get("shape", "")
            shape = self.resolve_shape(shape_name)
            doc = strip_html(shape.get("documentation", ""))
            status_code = shape.get("error", {}).get("httpStatusCode", "")
            errs.append({
                "name": shape_name,
                "documentation": doc,
                "httpStatusCode": status_code,
            })
        return errs


# ---------------------------------------------------------------------------
# PDF Document Builder
# ---------------------------------------------------------------------------
class ApiPdfBuilder:
    def __init__(self, spec, output_path):
        self.spec = spec
        self.output_path = output_path
        self.styles = build_styles()
        self.story = []
        self.toc_entries = []
        self._current_op_name = ""
        self._page_count = 0

    def build(self):
        doc = BaseDocTemplate(
            self.output_path,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN,
            bottomMargin=MARGIN + 0.5 * cm,
            title="Nutanix Objects API Reference",
            author="Nutanix",
        )

        frame_cover = Frame(0, 0, PAGE_W, PAGE_H, id="cover", leftPadding=0,
                            rightPadding=0, topPadding=0, bottomPadding=0)
        frame_body = Frame(
            MARGIN, MARGIN,
            PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN - 0.5 * cm,
            id="body",
        )
        doc.addPageTemplates([
            PageTemplate(id="cover", frames=[frame_cover], onPage=self._draw_cover_bg),
            PageTemplate(id="content", frames=[frame_body], onPage=self._draw_page_decor),
        ])

        self._build_cover()
        self._build_toc_placeholder()
        self._build_operations()

        doc.build(self.story)
        print(f"PDF written to {self.output_path}")

    # ----- Cover Page -----
    def _build_cover(self):
        self.story.append(NextPageTemplate("cover"))
        self.story.append(Spacer(1, 8 * cm))

        cover_frame_inset = []
        cover_frame_inset.append(Spacer(1, 0))

        title_text = "Nutanix Objects<br/>API Reference"
        self.story.append(
            Paragraph(title_text, self.styles["cover_title"])
        )
        self.story.append(Spacer(1, 0.8 * cm))

        version = self.spec.metadata.get("apiVersion", "")
        date_str = datetime.now().strftime("%B %d, %Y")
        sub_text = f"Objects 1.0&nbsp;&nbsp;|&nbsp;&nbsp;{date_str}"
        self.story.append(
            Paragraph(sub_text, self.styles["cover_sub"])
        )
        self.story.append(NextPageTemplate("content"))
        self.story.append(PageBreak())

    def _draw_cover_bg(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NTNX_BLUE)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

        canvas.setFillColor(colors.HexColor("#013A7A"))
        canvas.rect(0, 0, PAGE_W, PAGE_H * 0.35, fill=1, stroke=0)

        canvas.setStrokeColor(colors.HexColor("#0360B8"))
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, PAGE_H * 0.35, PAGE_W - MARGIN, PAGE_H * 0.35)

        canvas.setFont("Helvetica", 10)
        canvas.setFillColor(colors.HexColor("#B0C4DE"))
        canvas.drawString(MARGIN + 0.5 * cm, 2 * cm,
                          "Confidential  |  Nutanix, Inc.")

        canvas.restoreState()

    # ----- Table of Contents -----
    def _build_toc_placeholder(self):
        self.story.append(OpNameMarker(""))
        self.story.append(Paragraph("Contents", self.styles["toc_title"]))
        self.story.append(Spacer(1, 0.4 * cm))

        ops = self.spec.supported_operations()
        for op_name, _ in ops:
            bookmark = f"op_{op_name}"
            link_text = (
                f'<a href="#{bookmark}" color="#024DA1">'
                f'{para_escape(op_name)}'
                f'</a>'
            )
            self.story.append(Paragraph(link_text, self.styles["toc_entry"]))

        self.story.append(PageBreak())

    # ----- Operations -----
    def _build_operations(self):
        ops = self.spec.supported_operations()
        for idx, (op_name, op) in enumerate(ops):
            self._build_single_operation(op_name, op)
            if idx < len(ops) - 1:
                self.story.append(PageBreak())

    def _build_single_operation(self, op_name, op):
        self._current_op_name = op_name
        self.story.append(OpNameMarker(op_name))
        bookmark = f"op_{op_name}"
        self.story.append(BookmarkAnchor(bookmark))

        title = Paragraph(
            para_escape(op_name),
            self.styles["op_title"],
        )
        self.story.append(title)

        http = op.get("http", {})
        method = http.get("method", "GET")
        uri = http.get("requestUri", "/")
        method_color = {
            "GET": "#16A34A", "PUT": "#D97706", "POST": "#2563EB",
            "DELETE": "#DC2626", "HEAD": "#7C3AED",
        }.get(method, "#374151")
        badge = (
            f'<font color="{method_color}"><b>{method}</b></font>'
            f'&nbsp;&nbsp;<font face="Courier" size="10">{para_escape(uri)}</font>'
        )
        self.story.append(Paragraph(badge, self.styles["http_method"]))
        self.story.append(Spacer(1, 4))

        self._add_separator()

        doc_text, doc_notes = parse_documentation(op.get("documentation", ""))
        if doc_text:
            self.story.append(Paragraph(doc_text, self.styles["body"]))
            self.story.append(Spacer(1, 4))
        for note in doc_notes:
            self._add_note_block(note)

        self._build_request_syntax(op)
        self._build_request_parameters(op)
        self._build_response_syntax(op)
        self._build_response_parameters(op)
        self._build_errors(op)

    def _add_separator(self):
        sep = Table(
            [[""]],
            colWidths=[PAGE_W - 2 * MARGIN],
            rowHeights=[1],
        )
        sep.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, NTNX_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        self.story.append(sep)

    # ----- Request Syntax -----
    def _build_request_syntax(self, op):
        self.story.append(Paragraph("Request Syntax", self.styles["section"]))

        http = op.get("http", {})
        method = http.get("method", "GET")
        uri = http.get("requestUri", "/")

        lines = [f"{method} {uri} HTTP/1.1"]
        lines.append("Host: {Bucket}.your.objects.domain.com")

        _, _, header_params, body_info = self.spec.get_input_members(op)
        for hp in header_params:
            lines.append(f"{hp['locationName']}: {hp['name']}")

        if body_info:
            payload_name = body_info.get("payload")
            if payload_name:
                resolved = self.spec.resolve_shape(body_info["shape"])
                if resolved.get("type") == "blob":
                    lines.append("")
                    lines.append("[Binary request body]")
                else:
                    xml_lines = self.spec.shape_to_xml(
                        body_info["shape"],
                        payload_name,
                        0,
                    )
                    if xml_lines:
                        lines.append("")
                        lines.extend(xml_lines)
            else:
                body_xml = []
                root_tag = body_info["shape"].replace("Request", "")
                body_xml.append(f"<{root_tag}>")
                for mname, minfo in body_info.get("members", {}).items():
                    if minfo.get("isNtnxSupported", False) is False and "isNtnxSupported" in minfo:
                        continue
                    child_shape_name = minfo.get("shape", "")
                    child_resolved = self.spec.resolve_shape(child_shape_name)
                    if child_resolved.get("type") == "blob":
                        continue
                    child_tag = minfo.get("locationName", mname)
                    child_lines = self.spec.shape_to_xml(child_shape_name, child_tag, 1)
                    body_xml.extend(child_lines)
                body_xml.append(f"</{root_tag}>")
                if len(body_xml) > 2:
                    lines.append("")
                    lines.extend(body_xml)

        self._add_code_block(lines)

    # ----- Request Parameters -----
    def _build_request_parameters(self, op):
        params = self.spec.get_request_params(op)
        if not params:
            return
        self.story.append(Paragraph("Request Parameters", self.styles["section"]))
        for p in params:
            self._add_param_entry(p)

    # ----- Response Syntax -----
    def _build_response_syntax(self, op):
        self.story.append(Paragraph("Response Syntax", self.styles["section"]))

        http = op.get("http", {})
        status_code = http.get("responseCode", 200)

        header_params, xml_lines, has_body = self.spec.get_output_members(op)

        if not op.get("output"):
            lines = [f"HTTP/1.1 {status_code}"]
            self._add_code_block(lines)
            return

        lines = [f"HTTP/1.1 {status_code}"]
        for hp in header_params:
            lines.append(f"{hp['locationName']}: {hp['name']}")

        if has_body and xml_lines:
            lines.append("")
            lines.extend(xml_lines)

        self._add_code_block(lines)

    # ----- Response Parameters -----
    def _build_response_parameters(self, op):
        params = self.spec.get_response_params(op)
        if not params:
            return
        self.story.append(Paragraph("Response Parameters", self.styles["section"]))
        for p in params:
            self._add_param_entry(p)

    # ----- Errors -----
    def _build_errors(self, op):
        errors = self.spec.get_errors(op)
        if not errors:
            return
        self.story.append(Paragraph("Errors", self.styles["section"]))
        for err in errors:
            status = err.get("httpStatusCode", "")
            status_suffix = f"  (HTTP {status})" if status else ""
            self.story.append(Paragraph(
                para_escape(err["name"] + status_suffix),
                self.styles["error_name"],
            ))
            if err.get("documentation"):
                self.story.append(Paragraph(
                    err["documentation"],
                    self.styles["error_desc"],
                ))

    # ----- Helpers -----
    def _add_param_entry(self, param):
        self.story.append(Paragraph(
            para_escape(param["name"]),
            self.styles["param_name"],
        ))
        doc = param.get("documentation") or ""
        notes = param.get("notes") or []
        if doc:
            self.story.append(Paragraph(
                doc,
                self.styles["param_desc"],
            ))
        for note in notes:
            self._add_note_block(note)
        req_text = "Required: yes" if param.get("required") else "Required: no"
        self.story.append(Paragraph(req_text, self.styles["required_tag"]))

    def _add_code_block(self, lines):
        """Render a code block as a shaded table."""
        text = "\n".join(lines)
        escaped = para_escape(text)
        escaped = escaped.replace("\n", "<br/>")
        para = Paragraph(escaped, self.styles["code"])

        available_w = PAGE_W - 2 * MARGIN - 12
        tbl = Table(
            [[para]],
            colWidths=[available_w],
        )
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NTNX_CODE_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, NTNX_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        self.story.append(tbl)
        self.story.append(Spacer(1, 6))

    def _add_note_block(self, note_text):
        """Render an S3-style note callout with amber left border."""
        NTNX_NOTE_BG = colors.HexColor("#FFFBEB")
        NTNX_NOTE_BORDER = colors.HexColor("#D97706")

        label = Paragraph("Note", self.styles["note_label"])
        body = Paragraph(note_text, self.styles["note_text"])

        available_w = PAGE_W - 2 * MARGIN - 16
        inner = Table(
            [[label], [body]],
            colWidths=[available_w - 6],
        )
        inner.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))

        tbl = Table(
            [[inner]],
            colWidths=[available_w],
        )
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NTNX_NOTE_BG),
            ("LINEBEFOREDECOR", (0, 0), (0, -1), 3, NTNX_NOTE_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        self.story.append(Spacer(1, 4))
        self.story.append(tbl)
        self.story.append(Spacer(1, 6))

    # ----- Page decorations -----
    def _draw_page_decor(self, canvas, doc):
        canvas.saveState()

        canvas.setStrokeColor(NTNX_BLUE)
        canvas.setLineWidth(2)
        canvas.line(MARGIN, PAGE_H - MARGIN + 6, PAGE_W - MARGIN, PAGE_H - MARGIN + 6)

        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(NTNX_BLUE)
        canvas.drawString(MARGIN, PAGE_H - MARGIN + 12, "Nutanix Objects API Reference")

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(NTNX_MUTED)
        page_str = f"Page {canvas.getPageNumber()}"
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 14, page_str)

        op_name = getattr(canvas, '_current_op_name', '')
        if op_name:
            footer_text = f"Objects  |  {op_name}"
            canvas.drawString(MARGIN, MARGIN - 14, footer_text)

        canvas.restoreState()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate Nutanix Objects API Reference PDF from JSON spec."
    )
    parser.add_argument(
        "--input", "-i",
        default="../nutanix-objects.json",
        help="Path to the API JSON specification (default: nutanix-objects.json)",
    )
    parser.add_argument(
        "--output", "-o",
        default="../Nutanix-Objects-API-Reference.pdf",
        help="Output PDF file path",
    )
    args = parser.parse_args()

    spec = ApiSpec(args.input)
    builder = ApiPdfBuilder(spec, args.output)
    builder.build()


if __name__ == "__main__":
    main()
