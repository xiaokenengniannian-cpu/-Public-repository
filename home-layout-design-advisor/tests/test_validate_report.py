import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_report.py"
SPEC = importlib.util.spec_from_file_location("validate_report", VALIDATOR_PATH)
validate_report = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validate_report)


HEADINGS = [
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


def build_report(headings=HEADINGS, feng_shui_label=True):
    sections = []
    for heading in headings:
        body = "传统文化参考：不参与专业评分。" if heading == "住宅风水文化建议" and feng_shui_label else "内容"
        sections.append(f"## {heading}\n\n{body}")
    return "\n\n".join(sections) + "\n"


class ValidateReportTests(unittest.TestCase):
    def test_accepts_valid_report(self):
        self.assertEqual([], validate_report.validate_text(build_report()))

    def test_rejects_missing_heading(self):
        errors = validate_report.validate_text(build_report(HEADINGS[:-1]))
        self.assertTrue(any("缺少" in error for error in errors), errors)

    def test_rejects_wrong_order(self):
        headings = HEADINGS.copy()
        headings[3], headings[4] = headings[4], headings[3]
        errors = validate_report.validate_text(build_report(headings))
        self.assertTrue(any("顺序" in error for error in errors), errors)

    def test_rejects_duplicate_heading(self):
        headings = HEADINGS.copy()
        headings.insert(4, HEADINGS[3])
        errors = validate_report.validate_text(build_report(headings))
        self.assertTrue(any("重复" in error for error in errors), errors)

    def test_rejects_missing_feng_shui_label(self):
        errors = validate_report.validate_text(build_report(feng_shui_label=False))
        self.assertTrue(any("传统文化参考" in error for error in errors), errors)

    def test_rejects_headings_inside_fenced_code_blocks(self):
        for fence in ("```", "~~~"):
            with self.subTest(fence=fence):
                report = f"{fence}markdown\n{build_report()}{fence}\n"
                errors = validate_report.validate_text(report)
                self.assertTrue(errors, "fenced headings must not satisfy the report contract")


if __name__ == "__main__":
    unittest.main()
