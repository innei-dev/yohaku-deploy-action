#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
#
# --- How to run ---
# uv run tools/normalize_yohaku_signature.py "signature.svg" -o signature1.svg
# python tools/normalize_yohaku_signature.py "signature.svg" -o signature1.svg

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Final


SVG_NS: Final = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

STRIP_PREFIXES: Final = ("data-darkreader-",)
STRIP_ATTRS: Final = {
    "class",
    "style",
    "fill-rule",
    "font-size",
    "stroke",
    "fill",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "vector-effect",
}
YOHOKU_SIGNATURE_CLASS: Final = "signature-animated"
OUTPUT_FORMATS: Final = ("json", "yaml")


@dataclass(frozen=True, slots=True)
class NormalizeOptions:
    input_path: Path
    output_path: Path | None
    stroke_width: str
    svg_id: str
    group_id: str
    output_format: str


class SvgNormalizeError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


def parse_args(argv: list[str]) -> NormalizeOptions:
    parser = argparse.ArgumentParser(
        description="Normalize an SVG for Yohaku's native signature animation.",
    )
    parser.add_argument("input", type=Path, help="Source SVG file path")
    parser.add_argument("-o", "--output", type=Path, help="Write cleaned SVG here")
    parser.add_argument(
        "--stroke-width",
        default="1.35",
        help="Stroke width for all signature paths, default: 1.35",
    )
    parser.add_argument(
        "--svg-id",
        default="lipiston-signature",
        help="ID to set on the root svg element",
    )
    parser.add_argument(
        "--group-id",
        default="lipiston-signature-strokes",
        help="ID to set on the first group element",
    )
    parser.add_argument(
        "--format",
        choices=OUTPUT_FORMATS,
        default="json",
        help="Output format: json or yaml. Default: json",
    )
    args = parser.parse_args(argv)

    return NormalizeOptions(
        input_path=args.input,
        output_path=args.output,
        stroke_width=args.stroke_width,
        svg_id=args.svg_id,
        group_id=args.group_id,
        output_format=args.format,
    )


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalize_svg(source: str, options: NormalizeOptions) -> str:
    try:
        root = ET.fromstring(source)
    except ET.ParseError as error:
        raise SvgNormalizeError(f"Invalid SVG XML: {error}") from error

    if local_name(root.tag) != "svg":
        raise SvgNormalizeError("Input file root element is not <svg>.")

    root.set("id", options.svg_id)
    root.attrib.pop("style", None)
    root.set("class", YOHOKU_SIGNATURE_CLASS)

    group = first_group(root)
    group.set("id", options.group_id)
    group.set("stroke", "currentColor")
    group.set("fill", "none")
    group.set("stroke-linecap", "round")
    group.set("stroke-linejoin", "round")
    group.set("stroke-width", options.stroke_width)

    paths = [element for element in root.iter() if local_name(element.tag) == "path"]
    if not paths:
        raise SvgNormalizeError("No <path> elements found in SVG.")

    for element in root.iter():
        clean_common_attrs(element)

    for path in paths:
        clean_path(path)

    return ET.tostring(root, encoding="unicode", short_empty_elements=True)


def first_group(root: ET.Element) -> ET.Element:
    for element in root.iter():
        if local_name(element.tag) == "g":
            return element

    group = ET.Element(f"{{{SVG_NS}}}g")
    children = list(root)
    for child in children:
        root.remove(child)
        group.append(child)
    root.append(group)
    return group


def clean_path(path: ET.Element) -> None:
    for attr in list(path.attrib):
        if attr in STRIP_ATTRS or attr.startswith(STRIP_PREFIXES):
            path.attrib.pop(attr, None)


def clean_common_attrs(element: ET.Element) -> None:
    for attr in list(element.attrib):
        if attr.startswith(STRIP_PREFIXES):
            element.attrib.pop(attr, None)


def to_yaml_snippet(svg: str) -> str:
    indented_svg = "\n".join(f"        {line}" for line in svg.splitlines())
    return (
        "config:\n"
        "  module:\n"
        "    signature:\n"
        "      animated: true\n"
        "      svg: |\n"
        f"{indented_svg}\n"
    )


def to_json_object(svg: str) -> str:
    payload = {
        "config": {
            "module": {
                "signature": {
                    "svg": svg,
                    "animated": True,
                },
            },
        },
    }
    return f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"


def render_output(svg: str, output_format: str) -> str:
    match output_format:
        case "yaml":
            return to_yaml_snippet(svg)
        case "json":
            return to_json_object(svg)
        case unreachable:
            raise AssertionError(f"Unhandled output format: {unreachable}")


def run(options: NormalizeOptions) -> str:
    source = options.input_path.read_text(encoding="utf-8")
    svg = normalize_svg(source, options)
    return render_output(svg, options.output_format)


def main(argv: list[str]) -> int:
    options = parse_args(argv)
    try:
        output = run(options)
    except (OSError, SvgNormalizeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if options.output_path is None:
        print(output, end="")
        return 0

    options.output_path.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
