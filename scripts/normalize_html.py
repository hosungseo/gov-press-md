#!/usr/bin/env python3
"""Utilities for converting policy-briefing HTML fragments into readable Markdown-ish text."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser


class _HTMLTextExtractor(HTMLParser):
    BLOCK_TAGS = {
        'p', 'div', 'section', 'article', 'header', 'footer', 'aside',
        'ul', 'ol', 'table', 'tr', 'tbody', 'thead', 'tfoot', 'blockquote'
    }
    LIST_ITEM_TAGS = {'li'}
    HEADING_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self.hrefs: list[tuple[str, str]] = []
        self._current_href: str | None = None
        self._current_anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)
        if tag == 'br':
            self.parts.append('\n')
        elif tag in self.BLOCK_TAGS:
            self.parts.append('\n\n')
        elif tag in self.LIST_ITEM_TAGS:
            self.parts.append('\n- ')
        elif tag in self.HEADING_TAGS:
            self.parts.append('\n\n')
        elif tag == 'a':
            self._current_href = (attrs_dict.get('href') or '').strip() or None
            self._current_anchor_text = []

    def handle_endtag(self, tag: str):
        if tag in self.BLOCK_TAGS or tag in self.HEADING_TAGS:
            self.parts.append('\n\n')
        if tag == 'a':
            text = _clean_ws(''.join(self._current_anchor_text))
            if self._current_href:
                self.hrefs.append((text or self._current_href, self._current_href))
            self._current_href = None
            self._current_anchor_text = []

    def handle_data(self, data: str):
        if self._current_href is not None:
            self._current_anchor_text.append(data)
        self.parts.append(data)

    def handle_entityref(self, name: str):
        self.parts.append(html.unescape(f'&{name};'))

    def handle_charref(self, name: str):
        self.parts.append(html.unescape(f'&#{name};'))


def _clean_ws(text: str) -> str:
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\r\n?', '\n', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


def clean_html(raw: str) -> str:
    if not raw:
        return ''
    parser = _HTMLTextExtractor()
    parser.feed(raw)
    parser.close()
    text = html.unescape(''.join(parser.parts))
    text = _clean_ws(text)
    text = re.sub(r'\n-\s*\n', '\n', text)
    return text


def extract_links(raw: str) -> list[tuple[str, str]]:
    if not raw:
        return []
    parser = _HTMLTextExtractor()
    parser.feed(raw)
    parser.close()

    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for label, href in parser.hrefs:
        href = href.strip()
        if not href or href in seen:
            continue
        seen.add(href)
        out.append((_clean_ws(label) or href, href))
    return out
