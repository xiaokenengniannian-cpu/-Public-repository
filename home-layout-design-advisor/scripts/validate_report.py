#!/usr/bin/env python3
"""Validate the fixed section contract for home-layout-design-advisor reports."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


REQUIRED_HEADINGS = [
    "图纸信息识别",
    "信息缺失与待确认项",
    "户型总体评分",
    "主要问题及优先级",
    "硬装和空间改造建议",
    "动线、采光、通风及隐私分析",
    "软装风格建议",
    "收纳规划建议",
    "住宅风水文化建议",
    "风险、限制和专业复核事项",
    "方案A：低成本优化",
    "方案B：完整改造",
    "所调用的知识来源",
]

HEADING_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.MULTILINE)
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def _mask_fenced_code_blocks(text: str) -> str:
    """Blank fenced code while preserving offsets used for section slicing."""
    masked: list[str] = []
    fence_char: str | None = None
    fence_length = 0

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        is_fence_line = False

        if fence_char is None:
            opening = FENCE_OPEN_RE.match(content)
            if opening:
                fence = opening.group(1)
                fence_char = fence[0]
                fence_length = len(fence)
                is_fence_line = True
        else:
            candidate = content.lstrip(" ")
            indentation = len(content) - len(candidate)
            run_length = len(candidate) - len(candidate.lstrip(fence_char))
            remainder = candidate[run_length:]
            if indentation <= 3 and run_length >= fence_length and not remainder.strip(" \t"):
                is_fence_line = True
                fence_char = None
                fence_length = 0

        if fence_char is not None or is_fence_line:
            masked.append("".join(char if char in "\r\n" else " " for char in line))
        else:
            masked.append(line)

    return "".join(masked)


def validate_text(text: str) -> list[str]:
    """Return human-readable contract violations; an empty list means valid."""
    visible_text = _mask_fenced_code_blocks(text)
    matches = list(HEADING_RE.finditer(visible_text))
    headings = [match.group(1) for match in matches]
    errors: list[str] = []

    if len(headings) != len(REQUIRED_HEADINGS):
        errors.append(
            f"二级标题数量错误：应为 {len(REQUIRED_HEADINGS)}，实际为 {len(headings)}。"
        )

    counts = Counter(headings)
    duplicates = [heading for heading, count in counts.items() if count > 1]
    if duplicates:
        errors.append(f"存在重复二级标题：{'、'.join(duplicates)}。")

    missing = [heading for heading in REQUIRED_HEADINGS if heading not in counts]
    if missing:
        errors.append(f"缺少必需二级标题：{'、'.join(missing)}。")

    unexpected = [heading for heading in headings if heading not in REQUIRED_HEADINGS]
    if unexpected:
        errors.append(f"二级标题名称不正确：{'、'.join(unexpected)}。")

    if headings != REQUIRED_HEADINGS and not missing and not duplicates and not unexpected:
        errors.append("二级标题顺序错误。")

    feng_shui_heading = "住宅风水文化建议"
    if feng_shui_heading in headings:
        index = headings.index(feng_shui_heading)
        section_start = matches[index].end()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(visible_text)
        if "传统文化参考" not in visible_text[section_start:section_end]:
            errors.append("第9节必须包含“传统文化参考”标签。")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Markdown report to validate")
    args = parser.parse_args()

    try:
        text = args.report.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL: 无法读取报告：{exc}")
        return 2

    errors = validate_text(text)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: report structure is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
