from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from src.weekly_report import load_dataframe, load_profile


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_load_dataframe_collects_invalid_row_samples() -> None:
    aliases, _ = load_profile(PROJECT_ROOT / "field-map.json", "default")
    sample_csv = PROJECT_ROOT / "data/raw/sample_sales.csv"

    df, report = load_dataframe(sample_csv, "%Y-%m-%d", aliases)

    assert report.source_file == "sample_sales.csv"
    assert report.input_rows == 10
    assert report.kept_rows == 8
    assert report.invalid_row_count == 2
    assert len(df) == 8
    assert len(report.invalid_row_samples) == 2

    sample_rows = {sample["row_number"] for sample in report.invalid_row_samples}
    assert sample_rows == {6, 10}
    assert all({"row_number", "date", "order_id", "amount", "reasons"} <= sample.keys() for sample in report.invalid_row_samples)
    assert any("invalid_amount" in sample["reasons"] for sample in report.invalid_row_samples)


def test_quality_markdown_and_json_include_invalid_samples(tmp_path: Path) -> None:
    sample_csv = PROJECT_ROOT / "data/raw/sample_sales.csv"
    work_raw = tmp_path / "raw"
    work_out = tmp_path / "output"
    work_raw.mkdir()
    work_out.mkdir()

    shutil.copy(sample_csv, work_raw / "sample_sales.csv")

    cmd = [
        sys.executable,
        "-m",
        "src.weekly_report",
        "--input-dir",
        str(work_raw),
        "--output-dir",
        str(work_out),
        "--field-map",
        str(PROJECT_ROOT / "field-map.json"),
        "--map-profile",
        "default",
        "--date-format",
        "%Y-%m-%d",
    ]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

    quality_md = (work_out / "quality_report.md").read_text(encoding="utf-8")
    quality_json = json.loads((work_out / "quality_report.json").read_text(encoding="utf-8"))

    assert "错误样例行：sample_sales.csv" in quality_md
    assert "| 6 |" in quality_md
    assert "| 10 |" in quality_md

    file_reports = quality_json["files"]
    assert len(file_reports) == 1
    file_summary = file_reports[0]
    assert "invalid_row_samples" in file_summary
    assert len(file_summary["invalid_row_samples"]) == 2
    assert file_summary["invalid_row_samples"][0]["row_number"] == 6
