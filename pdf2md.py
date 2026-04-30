#!/usr/bin/env python3
import argparse
import sys

import pymupdf4llm


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path")
    arguments = parser.parse_args()

    markdown = pymupdf4llm.to_markdown(arguments.pdf_path)
    sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
