"""Client delivery helpers for quick profile packaging and one-click runs.

Usage:
  python scripts/client_delivery_pack.py create <client_name>
  python scripts/client_delivery_pack.py run <client_name> [--input-dir ...]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from subprocess import run
from typing import Dict, List


def normalize_client_name(name: str) -> str:
    # Keep unicode-friendly names (例如中文客户名) in filenames.
    raw = re.sub(r"[^\w-]+", "-", name.strip().lower(), flags=re.UNICODE)
    raw = re.sub(r"-+", "-", raw).strip("-_")
    return raw if raw else "client"


def default_aliases() -> Dict[str, List[str]]:
    return {
        "date": [
            "date",
            "日期",
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


def read_profile_aliases(field_map_file: Path, profile: str) -> Dict[str, List[str]]:
    with field_map_file.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict):
        raise ValueError(f"字段映射文件格式不对: {field_map_file}")

    if "profiles" in payload and isinstance(payload["profiles"], dict):
        profiles = payload["profiles"]
        if profile in profiles:
            return profiles[profile]
        raise ValueError(f"映射文件内未找到 profile={profile}: {field_map_file}")

    if all(k in payload for k in ("date", "amount", "order_id")):
        return {k: payload[k] for k in ("date", "amount", "order_id")}

    raise ValueError(f"字段映射文件缺少 profile 或 date/amount/order_id 三类字段: {field_map_file}")


def create_template(client_name: str, base_map: str, base_profile: str, overwrite: bool) -> Path:
    client_slug = normalize_client_name(client_name)
    out_file = Path(f"field-map.{client_slug}.json")

    if out_file.exists() and not overwrite:
        raise SystemExit(
            f"已存在 {out_file}。使用 --overwrite 覆盖，或先清理旧文件。"
        )

    aliases = default_aliases()
    base_path = Path(base_map)
    if base_path.exists():
        with base_path.open("r", encoding="utf-8") as f:
            base_payload = json.load(f)

        if "profiles" in base_payload and isinstance(base_payload["profiles"], dict):
            if base_profile in base_payload["profiles"]:
                aliases = read_profile_aliases(base_path, base_profile)
        elif all(k in base_payload for k in ("date", "amount", "order_id")):
            aliases = {
                "date": base_payload["date"],
                "amount": base_payload["amount"],
                "order_id": base_payload["order_id"],
            }

    payload = {
        "profiles": {
            client_slug: aliases
        },
        "meta": {
            "customer": client_name,
            "slug": client_slug,
            "base_profile": base_profile,
            "source_map": str(base_path),
        },
    }

    with out_file.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return out_file


def resolve_client_profile_from_file(client_file: Path, profile_hint: str) -> str:
    with client_file.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if "profiles" in payload and isinstance(payload["profiles"], dict):
        profiles = payload["profiles"]
        if profile_hint in profiles:
            return profile_hint
        if len(profiles) == 1:
            return next(iter(profiles.keys()))

    raise ValueError(
        f"文件 {client_file} 内未发现可识别 profile，预期包含 profiles 字段。\n"
        f"请先用 create 命令生成模板。")


def run_for_client(client_name: str, date_format: str, input_dir: str, output_dir: str, execute: bool) -> int:
    client_slug = normalize_client_name(client_name)
    client_file = Path(f"field-map.{client_slug}.json")

    if not client_file.exists():
        raise SystemExit(
            f"未找到 {client_file}。先运行:\n"
            f"python3 scripts/client_delivery_pack.py create \"{client_name}\""
        )

    profile = resolve_client_profile_from_file(client_file, client_slug)
    cmd = [
        sys.executable,
        "-m",
        "src.weekly_report",
        "--field-map",
        str(client_file),
        "--map-profile",
        profile,
        "--date-format",
        date_format,
        "--input-dir",
        input_dir,
        "--output-dir",
        output_dir,
    ]

    command = " ".join(cmd)
    if not execute:
        print("预览命令（未执行）:")
        print(command)
        return 0

    print("执行命令：")
    print(command)
    result = run(cmd)
    return result.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="client delivery workflow helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    create = sub.add_parser("create", help="生成 field-map.<client>.json 模板")
    create.add_argument("client_name")
    create.add_argument("--base-map", default="field-map.json", help="复制映射基准文件")
    create.add_argument("--base-profile", default="default", help="基准文件中的 profile 名称")
    create.add_argument("--overwrite", action="store_true", help="覆盖已存在的模板")

    run_cmd = sub.add_parser("run", help="用指定客户模板一键运行周报")
    run_cmd.add_argument("client_name")
    run_cmd.add_argument("--input-dir", default="data/raw", help="输入目录")
    run_cmd.add_argument("--output-dir", default="data/output", help="输出目录")
    run_cmd.add_argument("--date-format", default="%Y-%m-%d", help="日期格式")
    run_cmd.add_argument("--dry-run", action="store_true", help="只打印命令不执行")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.cmd == "create":
        out_file = create_template(args.client_name, args.base_map, args.base_profile, args.overwrite)
        print(f"已生成：{out_file}")
        return

    if args.cmd == "run":
        code = run_for_client(
            client_name=args.client_name,
            date_format=args.date_format,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            execute=not args.dry_run,
        )
        raise SystemExit(code)


if __name__ == "__main__":
    main()
