#!/usr/bin/env python3
import argparse
import re
import sys

import pymupdf
import pymupdf4llm

def clean_markdown(markdown: str) -> str:
    cleaned = markdown
    cleaned = re.sub(
        r"^\*\*==> picture \[\d+ x \d+\] intentionally omitted <==\*\*\n?",
        "",
        cleaned,
        flags=re.MULTILINE,
    )
    cleaned = re.sub(r"[ \t]+$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"(?m)^([ \t]*[-*+] .+)\n\n(?=[ \t]*[-*+] )", r"\1\n", cleaned)
    cleaned = re.sub(r"(?m)^([ \t]*\d+\. .+)\n\n(?=[ \t]*\d+\. )", r"\1\n", cleaned)
    cleaned = re.sub(r"(?m)^([ \t]*[-*+] )●\s+", r"\1", cleaned)
    return cleaned.strip() + "\n"


def extract_link_text(page: pymupdf.Page, link_rect: pymupdf.Rect) -> str:
    words = []
    for word in page.get_text("words"):
        word_rect = pymupdf.Rect(word[:4])
        if word_rect.is_empty:
            continue
        center = word_rect.tl + (word_rect.br - word_rect.tl) * 0.5
        if center in link_rect:
            words.append(word)
    if not words:
        return ""

    words.sort(key=lambda word: (word[5], word[6], word[7]))
    lines = {}
    for word in words:
        lines.setdefault((word[5], word[6]), []).append(word)

    candidates = []
    for line_words in lines.values():
        line_words.sort(key=lambda word: word[7])
        text = " ".join(word[4] for word in line_words).strip()
        if text:
            candidates.append(text)
    if not candidates:
        return ""
    return max(candidates, key=len)


def extract_markdown_links(pdf_path: str) -> list[tuple[str, str]]:
    document = pymupdf.open(pdf_path)
    markdown_links = []
    try:
        for page in document:
            for link in page.get_links():
                uri = link.get("uri")
                if not uri:
                    continue
                text = extract_link_text(page, link["from"])
                if len(text) < 4 or text == "-" or " / " in text:
                    continue
                if text.startswith("http://") or text.startswith("https://"):
                    continue
                markdown_links.append((text, uri))
    finally:
        document.close()

    markdown_links.sort(key=lambda item: len(item[0]), reverse=True)
    unique_links = []
    seen = set()
    for link in markdown_links:
        if link in seen:
            continue
        seen.add(link)
        unique_links.append(link)
    return unique_links


def apply_markdown_links(markdown: str, markdown_links: list[tuple[str, str]]) -> str:
    linked_markdown = markdown
    for text, uri in markdown_links:
        pattern = re.compile(rf"(?<!\[){re.escape(text)}(?!\]\()")
        linked_markdown = pattern.sub(f"[{text}]({uri})", linked_markdown, count=1)
    return linked_markdown


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path")
    arguments = parser.parse_args()

    markdown = pymupdf4llm.to_markdown(arguments.pdf_path)
    markdown_links = extract_markdown_links(arguments.pdf_path)
    markdown = apply_markdown_links(markdown, markdown_links)
    markdown = clean_markdown(markdown)
    sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
