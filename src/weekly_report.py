"""Batch report generator for CSV/Excel files.

Usage:
  python -m src.weekly_report [--input-dir data/raw] [--output-dir data/output]
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Any

try:
    import pandas as pd
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "缺少 pandas 依赖。请先执行: pip install -r requirements.txt"
    ) from exc


@dataclass
class ColumnMap:
    """Canonical columns used for report generation."""

    date: str
    amount: str
    order_id: str


@dataclass
class QualityResult:
    """Lightweight quality result for a single source file."""

    source_file: str
    input_rows: int
    kept_rows: int
    invalid_row_count: int
    dropped_duplicate_rows: int
    invalid_date_rows: int
    invalid_amount_rows: int
    negative_amount_rows: int
    missing_order_id_rows: int
    duplicated_order_id_rows: int
    duplicate_order_ratio: float
    invalid_row_samples: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_file": self.source_file,
            "input_rows": self.input_rows,
            "kept_rows": self.kept_rows,
            "invalid_row_count": self.invalid_row_count,
            "dropped_duplicate_rows": self.dropped_duplicate_rows,
            "invalid_date_rows": self.invalid_date_rows,
            "invalid_amount_rows": self.invalid_amount_rows,
            "negative_amount_rows": self.negative_amount_rows,
            "missing_order_id_rows": self.missing_order_id_rows,
            "duplicated_order_id_rows": self.duplicated_order_id_rows,
            "duplicate_order_ratio": self.duplicate_order_ratio,
            "invalid_row_samples": self.invalid_row_samples,
        }


DEFAULT_ALIASES: Dict[str, List[str]] = {
    "date": [
        "date",
        "订单日期",
        "order_date",
        "order date",
        "trade_date",
        "交易日期",
        "销售日期",
    ],
    "amount": [
        "amount",
        "revenue",
        "sales",
        "total",
        "total_amount",
        "金额",
        "销售额",
        "成交额",
    ],
    "order_id": [
        "order_id",
        "order",
        "订单号",
        "订单 ID",
        "id",
    ],
}

MAX_INVALID_SAMPLES = 5


@dataclass
class QualityThresholds:
    """Quality thresholds can be configured by CLI args or field-map profile."""

    max_invalid_row_ratio: float = 1.0
    max_duplicate_order_ratio: float = 1.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="batchly clean sales data and build weekly reports")
    parser.add_argument("--input-dir", default="data/raw", help="raw files directory")
    parser.add_argument("--output-dir", default="data/output", help="generated files directory")
    parser.add_argument("--date-format", default="%Y-%m-%d", help="date parse fallback format")
    parser.add_argument(
        "--field-map",
        default="field-map.json",
        help="field mapping config file",
    )
    parser.add_argument("--map-profile", default="default", help="selected profile in field-map.json")
    parser.add_argument(
        "--max-invalid-row-rate",
        type=float,
        default=1.0,
        help="最大可接受的无效行占比（0~1，1 表示不限制）",
    )
    parser.add_argument(
        "--max-duplicate-order-rate",
        type=float,
        default=1.0,
        help="最大可接受的重复订单号占比（0~1，1 表示不限制）",
    )
    parser.add_argument(
        "--fail-on-quality",
        action="store_true",
        help="当质量告警超过阈值时中止流程（默认仅产出质检报告）",
    )
    return parser.parse_args()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns
    ]
    return df


def detect_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    normalized = set(df.columns)
    for c in candidates:
        cc = str(c).strip().lower().replace(" ", "_").replace("-", "_")
        if cc in normalized:
            return cc
    return None


def load_profile(path: Path, profile: str) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    aliases = {k: list(v) for k, v in DEFAULT_ALIASES.items()}
    quality_policy: Dict[str, Any] = {}

    if not path.exists():
        print(f"未找到映射文件 {path}，使用内置字段映射")
        return aliases, quality_policy

    with path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    # 支持两种格式:
    # 1) {"profiles": {"default": {...}, "client_x": {...}}, "meta": {...}}
    # 2) {"date": [...], "amount": [...], "order_id": [...], "quality": {...}}
    if not isinstance(config, dict):
        raise ValueError(f"字段映射文件格式错误: {path}")

    profile_cfg: Dict[str, Any] | None = None
    if "profiles" in config and isinstance(config["profiles"], dict):
        profile_cfg = config["profiles"].get(profile)
        if profile_cfg is None:
            names = ", ".join(sorted(config["profiles"].keys()))
            raise ValueError(f"未找到 profile='{profile}'，可选: {names}")
    elif all(k in config for k in ("date", "amount", "order_id")):
        profile_cfg = config
    else:
        raise ValueError(f"字段映射文件缺少字段映射配置: {path}")

    for key, value in profile_cfg.items():
        if key == "quality":
            if not isinstance(value, dict):
                raise ValueError(f"字段映射文件中 quality 必须是对象: {path}")
            quality_policy = value
            continue
        if key not in aliases:
            continue
        if not isinstance(value, list):
            raise ValueError(f"字段映射的 {key} 必须是数组: {path}")
        aliases[key] = [str(v).strip() for v in value if str(v).strip()]

    return aliases, quality_policy


def resolve_columns(df: pd.DataFrame, aliases: Dict[str, List[str]]) -> ColumnMap:
    date_col = detect_column(df, aliases["date"])
    amount_col = detect_column(df, aliases["amount"])
    order_col = detect_column(df, aliases["order_id"])

    if date_col is None:
        raise ValueError("未识别日期列；支持字段示例: date/order_date/订单日期")
    if amount_col is None:
        raise ValueError("未识别金额列；支持字段示例: amount/revenue/金额")
    if order_col is None:
        # 如果订单号不存在，用行号代替，保证可继续生成周报
        order_col = "_tmp_order_id"

    return ColumnMap(date=date_col, amount=amount_col, order_id=order_col)


def _is_blank_series(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(str).str.strip().eq("")


def _read_datetime_series(df: pd.DataFrame, col: str, date_format: str) -> tuple[pd.Series, pd.Series]:
    parsed_primary = pd.to_datetime(df[col], format=date_format, errors="coerce")
    parsed_fallback = pd.to_datetime(df[col], errors="coerce")
    parsed = parsed_primary.fillna(parsed_fallback)
    return parsed, parsed_fallback.isna() & parsed_primary.isna()


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        raise ValueError(f"不支持的文件类型: {path.suffix}")
    return df


def _select_and_parse_rows(
    df: pd.DataFrame,
    cols: ColumnMap,
    date_format: str,
) -> tuple[pd.DataFrame, int, int, int, int, int, pd.Series, List[Dict[str, Any]]]:
    parsed_amount = pd.to_numeric(df[cols.amount], errors="coerce")
    parsed_date, date_invalid = _read_datetime_series(df, cols.date, date_format)
    date_is_blank = _is_blank_series(df[cols.date])
    order_series = df[cols.order_id].astype(str)
    missing_order_count = int(_is_blank_series(df[cols.order_id]).sum())
    invalid_date_count = int(date_invalid.sum())
    invalid_amount_count = int(parsed_amount.isna().sum())

    negative_amount_count = int((parsed_amount < 0).sum())
    invalid_rows_mask = date_is_blank | parsed_amount.isna() | parsed_date.isna()
    valid_rows = ~invalid_rows_mask
    invalid_rows_count = int((~valid_rows).sum())
    invalid_samples: List[Dict[str, Any]] = []
    invalid_rows = df.loc[~valid_rows]
    for row_idx in invalid_rows.index[:MAX_INVALID_SAMPLES]:
        raw_date = invalid_rows.at[row_idx, cols.date]
        raw_amount = invalid_rows.at[row_idx, cols.amount]
        raw_order = invalid_rows.at[row_idx, cols.order_id]
        reasons: List[str] = []
        if pd.isna(raw_date) or str(raw_date).strip() == "":
            reasons.append("missing_date")
        elif pd.isna(parsed_date.loc[row_idx]):
            reasons.append("invalid_date")
        if pd.isna(parsed_amount.loc[row_idx]):
            reasons.append("invalid_amount")
        if pd.isna(raw_order) or str(raw_order).strip() == "":
            reasons.append("missing_order_id")
        if not reasons:
            reasons.append("invalid_row")

        invalid_samples.append(
            {
                "row_number": int(row_idx) + 2,
                "date": None if pd.isna(raw_date) else str(raw_date),
                "order_id": "" if pd.isna(raw_order) else str(raw_order).strip(),
                "amount": None if pd.isna(raw_amount) else str(raw_amount).strip(),
                "reasons": reasons,
            }
        )

    parsed = pd.DataFrame(
        {
            "report_date": parsed_date.loc[valid_rows].reset_index(drop=True),
            "amount": parsed_amount.loc[valid_rows].reset_index(drop=True),
            "order_id": order_series.loc[valid_rows].astype(str).str.strip().reset_index(drop=True),
        }
    )

    return (
        parsed,
        invalid_rows_count,
        invalid_date_count,
        invalid_amount_count,
        negative_amount_count,
        missing_order_count,
        valid_rows,
        invalid_samples,
    )


def load_dataframe(path: Path, date_format: str, aliases: Dict[str, List[str]]) -> tuple[pd.DataFrame, QualityResult]:
    df = _read_table(path)

    df = normalize_columns(df)
    cols = resolve_columns(df, aliases)

    # 缺失订单号则补齐
    if cols.order_id not in df.columns:
        df[cols.order_id] = [f"row-{i}" for i in range(len(df))]

    raw_rows = len(df)

    (
        parsed_df,
        invalid_rows,
        date_invalid_count,
        amount_invalid_count,
        negative_amount_count,
        missing_order_count,
        valid_rows_mask,
        invalid_row_samples,
    ) = (
        _select_and_parse_rows(df, cols, date_format)
    )

    # 阶段 1：关键字段缺失/无效过滤后，仅保留有效记录
    df_valid = df.loc[valid_rows_mask].copy().reset_index(drop=True)
    parsed_df = parsed_df.reset_index(drop=True)

    # 阶段 2：构建标准列，避免中途重名导致 .dt 失效
    canonical = df_valid.drop(columns=[cols.date, cols.amount, cols.order_id], errors="ignore")
    canonical = pd.concat([canonical, parsed_df], axis=1)

    # 阶段 3：对有效集合做去重统计
    before_dedup = len(canonical)
    canonical = canonical.drop_duplicates()
    duplicate_rows = before_dedup - len(canonical)

    # 阶段 4：在有效集合上做订单号去重与质量统计
    order_values = canonical["order_id"].astype(str).str.strip()
    duplicate_order_count = int((order_values.duplicated() & ~order_values.eq("")).sum())
    duplicate_order_ratio = 0.0
    non_blank_order_total = max(int((~order_values.eq("")).sum()), 1)
    duplicate_order_ratio = duplicate_order_count / non_blank_order_total

    if "report_date" not in canonical.columns:
        raise RuntimeError("清洗结果缺失 report_date，无法计算周报")
    if "amount" not in canonical.columns:
        raise RuntimeError("清洗结果缺失 amount，无法计算周报")
    if "order_id" not in canonical.columns:
        raise RuntimeError("清洗结果缺失 order_id，无法计算周报")

    canonical["amount"] = canonical["amount"].fillna(0)
    canonical["report_week"] = canonical["report_date"].dt.to_period("W-MON").apply(lambda p: p.start_time)
    canonical["report_week"] = pd.to_datetime(canonical["report_week"]).dt.date

    report = QualityResult(
        source_file=path.name,
        input_rows=raw_rows,
        kept_rows=len(canonical),
        invalid_row_count=invalid_rows,
        dropped_duplicate_rows=duplicate_rows,
        invalid_date_rows=date_invalid_count,
        invalid_amount_rows=amount_invalid_count,
        negative_amount_rows=negative_amount_count,
        missing_order_id_rows=missing_order_count,
        duplicated_order_id_rows=duplicate_order_count,
        duplicate_order_ratio=duplicate_order_ratio,
        invalid_row_samples=invalid_row_samples,
    )

    return canonical, report


def summarize_weekly(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby("report_week", as_index=False)
        .agg(
            weekly_sales=("amount", "sum"),
            orders=("order_id", "nunique"),
            avg_order_value=("amount", "mean"),
            rows=("order_id", "count"),
        )
        .sort_values("report_week")
    )
    grouped["avg_order_value"] = grouped["avg_order_value"].round(2)
    grouped["weekly_sales"] = grouped["weekly_sales"].round(2)
    return grouped


def write_markdown_report(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Weekly Report\n\n")
        f.write("| Week Start | Weekly Sales | Orders | Avg Order Value | Rows |\n")
        f.write("| --- | ---: | ---: | ---: | ---: |\n")

        for _, row in df.iterrows():
            f.write(
                f"| {row['report_week']} | {row['weekly_sales']:.2f} | "
                f"{int(row['orders'])} | {row['avg_order_value']:.2f} | {int(row['rows'])} |\n"
            )

        total_sales = df["weekly_sales"].sum()
        total_orders = int(df["orders"].sum())
        total_rows = int(df["rows"].sum())
        f.write("\n")
        f.write(f"- Total sales: {total_sales:.2f}\n")
        f.write(f"- Total orders: {total_orders}\n")
        f.write(f"- Total rows: {total_rows}\n")


def _quality_thresholds(profile_policy: Dict[str, Any], args: argparse.Namespace) -> QualityThresholds:
    max_invalid = args.max_invalid_row_rate
    max_duplicate = args.max_duplicate_order_rate

    if isinstance(profile_policy.get("max_invalid_row_ratio"), (int, float)):
        max_invalid = float(profile_policy["max_invalid_row_ratio"])
    if isinstance(profile_policy.get("max_duplicate_order_ratio"), (int, float)):
        max_duplicate = float(profile_policy["max_duplicate_order_ratio"])

    return QualityThresholds(max_invalid_row_ratio=max_invalid, max_duplicate_order_ratio=max_duplicate)


def check_quality_thresholds(reports: List[QualityResult], thresholds: QualityThresholds, fail_on_quality: bool) -> List[str]:
    issues: List[str] = []

    total_input = sum(r.input_rows for r in reports)
    total_invalid = sum(r.invalid_row_count for r in reports)
    total_rows = sum(r.kept_rows for r in reports)
    total_duplicates = sum(r.dropped_duplicate_rows for r in reports)

    invalid_ratio = 0.0 if total_input == 0 else total_invalid / total_input
    if invalid_ratio > thresholds.max_invalid_row_ratio:
        issues.append(
            f"invalid_row_ratio={invalid_ratio:.2%} > threshold={thresholds.max_invalid_row_ratio:.2%}"
        )

    if total_rows:
        duplicate_ratio = total_duplicates / total_rows
        if duplicate_ratio > thresholds.max_duplicate_order_ratio:
            issues.append(
                f"duplicate_row_ratio={duplicate_ratio:.2%} > threshold={thresholds.max_duplicate_order_ratio:.2%}"
            )

    if fail_on_quality and issues:
        raise SystemExit("\n".join(["发现质量问题超过阈值:"] + issues))

    return issues


def write_quality_artifacts(reports: List[QualityResult], out_dir: Path, thresholds: QualityThresholds) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    quality_json = out_dir / "quality_report.json"
    quality_md = out_dir / "quality_report.md"

    total_input = sum(r.input_rows for r in reports)
    total_kept = sum(r.kept_rows for r in reports)
    total_invalid = sum(r.invalid_row_count for r in reports)
    total_duplicate_rows = sum(r.dropped_duplicate_rows for r in reports)
    total_negative = sum(r.negative_amount_rows for r in reports)

    summary = {
        "totals": {
            "input_rows": total_input,
            "kept_rows": total_kept,
            "invalid_rows": total_invalid,
            "invalid_row_ratio": 0.0 if total_input == 0 else total_invalid / total_input,
            "dropped_duplicates_rows": total_duplicate_rows,
            "negative_amount_rows": total_negative,
        },
        "thresholds": {
            "max_invalid_row_ratio": thresholds.max_invalid_row_ratio,
            "max_duplicate_order_ratio": thresholds.max_duplicate_order_ratio,
        },
        "files": [r.to_dict() for r in reports],
    }

    with quality_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with quality_md.open("w", encoding="utf-8") as f:
        f.write("# Data Quality Report\n\n")
        f.write("## Summary\n")
        f.write(f"- Input rows: {total_input}\n")
        f.write(f"- Kept rows: {total_kept}\n")
        f.write(f"- Invalid rows: {total_invalid}\n")
        f.write(f"- Invalid row ratio: {(0.0 if total_input == 0 else total_invalid / total_input):.2%}\n")
        f.write(f"- Dropped duplicate rows: {total_duplicate_rows}\n")
        f.write(f"- Negative amount rows: {total_negative}\n")
        f.write("\n## File Quality Details\n")
        f.write(
            "| File | Input Rows | Kept Rows | Invalid Rows | Invalid Date | Invalid Amount | "
            "Negative Amount | Duplicate Order IDs | Duplicate Order Rate |\n"
        )
        f.write(
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n"
        )
        for r in reports:
            f.write(
                f"| {r.source_file} | {r.input_rows} | {r.kept_rows} | {r.invalid_row_count} | "
                f"{r.invalid_date_rows} | {r.invalid_amount_rows} | {r.negative_amount_rows} | "
                f"{r.duplicated_order_id_rows} | {r.duplicate_order_ratio:.2%} |\n"
            )
            if r.invalid_row_samples:
                f.write(f"\n### 错误样例行：{r.source_file}\n")
                f.write("| Row | Date | Order ID | Amount | Reasons |\n")
                f.write("| --- | --- | --- | --- | --- |\n")
                for sample in r.invalid_row_samples:
                    reasons = "; ".join(sample["reasons"])
                    f.write(
                        f"| {sample['row_number']} | {sample['date']} | {sample['order_id']} | "
                        f"{sample['amount']} | {reasons} |\n"
                    )
            else:
                f.write(f"\n### 错误样例行：{r.source_file}\n")
                f.write("- 无无效样例\n")


def main() -> None:
    args = parse_args()
    aliases, quality_policy = load_profile(Path(args.field_map), args.map_profile)
    thresholds = _quality_thresholds(quality_policy, args)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("*"))
    allowed = {".csv", ".xlsx", ".xls"}
    target_files = [p for p in files if p.suffix.lower() in allowed]

    if not target_files:
        raise SystemExit(f"没有可处理文件。请确认 {input_dir} 下有 csv/xlsx/xls")

    all_frames: List[pd.DataFrame] = []
    quality_reports: List[QualityResult] = []

    for file in target_files:
        try:
            df, quality = load_dataframe(file, args.date_format, aliases)
            df.insert(0, "source_file", file.name)
            all_frames.append(df)
            quality_reports.append(quality)
        except Exception as exc:
            print(f"跳过 {file.name}: {exc}")

    if not all_frames:
        raise SystemExit("未成功读取到任何可用文件")

    merged = pd.concat(all_frames, ignore_index=True)
    merged = merged.sort_values(["report_week", "report_date", "order_id"])

    cleaned_path = output_dir / "cleaned_rows.csv"
    merged.to_csv(cleaned_path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    weekly = summarize_weekly(merged)
    report_csv = output_dir / "weekly_report.csv"
    report_md = output_dir / "weekly_report.md"
    weekly.to_csv(report_csv, index=False, encoding="utf-8-sig")
    write_markdown_report(weekly, report_md)

    write_quality_artifacts(quality_reports, output_dir, thresholds)
    quality_issues = check_quality_thresholds(quality_reports, thresholds, args.fail_on_quality)

    print("cleaned rows =>", cleaned_path)
    print("weekly csv =>", report_csv)
    print("weekly md  =>", report_md)
    print("quality json =>", output_dir / "quality_report.json")
    print("quality md  =>", output_dir / "quality_report.md")

    if quality_issues:
        print("质量告警:")
        for item in quality_issues:
            print(f"- {item}")


if __name__ == "__main__":
    main()
