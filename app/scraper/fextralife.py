from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from app.core.config import settings


class FextralifeScraper:
    HEADING_TAGS = {"h2", "h3", "h4", "h5", "h6"}
    NAMESPACE_PREFIXES = ("File:", "Special:", "Category:", "Talk:", "User:", "Template:")

    def __init__(self, user_agent: str = settings.scraper_user_agent):
        self.user_agent = user_agent

    def fetch_html(self, url: str) -> str:
        resp = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=15)
        resp.raise_for_status()
        return resp.text

    def parse_page(self, html: str, allow_patterns: list[str] | None) -> str:
        content = self._get_content(html)
        blocks = self._split_into_heading_blocks(content)

        if allow_patterns is None:
            keep_flags = [True] * len(blocks)
        else:
            keep_flags = self._resolve_keep(blocks, allow_patterns)

        kept_sections: list[str] = []
        for (level, heading, tokens), keep in zip(blocks, keep_flags):
            if not keep:
                continue
            section_text = self._tokens_to_text(tokens)
            if section_text:
                kept_sections.append(f"## {heading}\n{section_text}")

        return "\n\n".join(kept_sections)

    def page_title(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        heading = soup.find("h1")
        return heading.get_text(strip=True) if heading else ""

    def extract_links(self, html: str, base_url: str) -> list[tuple[str, str]]:
        content = self._get_content(html)
        seen: set[str] = set()
        links: list[tuple[str, str]] = []

        for a in content.find_all("a", href=True):
            href = a["href"]
            if not self._is_wiki_link(href):
                continue

            url = urljoin(base_url, href)
            if url in seen:
                continue
            seen.add(url)
            links.append((url, a.get_text(strip=True)))

        return links

    @classmethod
    def _get_content(cls, html: str) -> Tag:
        soup = BeautifulSoup(html, "html.parser")
        content = soup.find("div", class_="mw-parser-output")
        if content is None:
            raise ValueError("could not find main content container (mw-parser-output)")
        return content

    @classmethod
    def _is_wiki_link(cls, href: str) -> bool:
        if not href or href.startswith("#") or href.startswith("http"):
            return False
        if "?" in href:
            return False
        path = href.lstrip("/")
        return not path.startswith(cls.NAMESPACE_PREFIXES)

    @staticmethod
    def _matches_allowlist(heading: str, patterns: list[str]) -> bool:
        heading_lower = heading.lower()
        return any(p in heading_lower for p in patterns)

    @classmethod
    def _tokenize(cls, node: Tag):
        for child in node.children:
            if isinstance(child, Tag):
                if child.name in cls.HEADING_TAGS:
                    level = int(child.name[1])
                    yield ("heading", level, child.get_text(strip=True))
                elif child.name == "table":
                    yield ("table", None, child)
                elif child.name in ("script", "style"):
                    continue
                else:
                    yield from cls._tokenize(child)
            else:
                text = str(child).strip()
                if text:
                    yield ("text", None, text)

    @classmethod
    def _split_into_heading_blocks(
        cls, content: Tag
    ) -> list[tuple[int, str, list[tuple[str, object]]]]:
        blocks: list[tuple[int, str, list[tuple[str, object]]]] = []
        current: tuple[int, str, list[tuple[str, object]]] | None = None

        for kind, level, value in cls._tokenize(content):
            if kind == "heading":
                if current is not None:
                    blocks.append(current)
                current = (level, value, [])
            elif current is not None:
                current[2].append((kind, value))

        if current is not None:
            blocks.append(current)

        return blocks

    @staticmethod
    def _resolve_keep(
        blocks: list[tuple[int, str, list[tuple[str, object]]]],
        allow_patterns: list[str],
    ) -> list[bool]:
        keep: list[bool] = [False] * len(blocks)
        stack: list[tuple[int, bool]] = []

        for i, (level, heading, _tokens) in enumerate(blocks):
            while stack and stack[-1][0] >= level:
                stack.pop()
            own_match = FextralifeScraper._matches_allowlist(heading, allow_patterns)
            ancestor_kept = stack[-1][1] if stack else False
            keep[i] = own_match or ancestor_kept
            stack.append((level, keep[i]))

        return keep

    @staticmethod
    def table_to_text(table: Tag) -> str:
        rows = table.find_all("tr")
        if not rows:
            return ""

        header_cells = rows[0].find_all("th")
        headers = [c.get_text(" ", strip=True) for c in header_cells]
        data_rows = rows[1:] if headers else rows

        lines: list[str] = []
        for row in data_rows:
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
            if not any(cells):
                continue
            if headers and len(cells) == len(headers):
                lines.append(", ".join(f"{h}: {v}" for h, v in zip(headers, cells) if v))
            elif len(cells) == 2:
                lines.append(f"{cells[0]}: {cells[1]}")
            else:
                lines.append(", ".join(c for c in cells if c))

        return "\n".join(lines)

    @classmethod
    def _tokens_to_text(cls, tokens: list[tuple[str, object]]) -> str:
        parts: list[str] = []
        for kind, value in tokens:
            if kind == "table":
                parts.append(cls.table_to_text(value))
            else:
                parts.append(value)
        return " ".join(p for p in parts if p).strip()
