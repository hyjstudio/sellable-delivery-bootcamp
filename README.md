# Excel/CSV Weekly Report Generator

一个可交付 MVP：批量清洗 Excel/CSV，并自动生成按周汇总的销售周报。

## 目标
- 批量读取 `data/raw/` 下的 `.csv`, `.xlsx`, `.xls` 文件
- 自动清洗：
  - 标准化列名
  - 解析日期、数值字段
  - 去重
  - 过滤无效行
- 输出结果：
  - 全量清洗明细：`data/output/cleaned_rows.csv`
  - 周报汇总：`data/output/weekly_report.csv`
  - 周报 Markdown：`data/output/weekly_report.md`
  - 质检报告：`data/output/quality_report.json`、`data/output/quality_report.md`

## 快速上手
1. 安装依赖
```bash
cd /Users/zhoufangming/Developer/learning/sellable-delivery-bootcamp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. 把你的原始文件放到 `data/raw/`
3. 运行
```bash
python -m src.weekly_report
```

可选参数：
```bash
python -m src.weekly_report \
  --input-dir data/raw \
  --output-dir data/output \
  --date-format %Y-%m-%d
```

可选参数（可结合 `field-map.<profile>.json` 中 `quality` 段落覆盖默认阈值）：
```bash
python -m src.weekly_report \
  --max-invalid-row-rate 0.2 \
  --max-duplicate-order-rate 0.05 \
 --fail-on-quality
```

说明：
- `--max-invalid-row-rate`：可接受的无效行比例上限（0~1）
- `--max-duplicate-order-rate`：可接受的重复订单行比例上限（0~1）
- `--fail-on-quality`：超过阈值时以非 0 码退出，适合交付链路自动化。

最小回归测试：
```bash
python -m pip install pytest
python -m pytest
```

测试覆盖：
- `load_dataframe` 的无效行统计与错误样例返回
- CLI 产物（`quality_report.md/json`）包含每文件错误样例

## 字段映射规则
我们新增了“可售版本”字段映射模板：`field-map.json`。

脚本会先读取映射文件（默认 `field-map.json`）中的 `profiles`，再按 `--map-profile` 选择对应客户模板。

```bash
python -m src.weekly_report --map-profile cn_ops_template_a
```

如果映射文件不存在会回退到内置规则。你也可以临时指定其他映射文件：

```bash
python -m src.weekly_report --field-map /path/to/field-map.json --map-profile client_a
```

字段映射样例（同一份文件里可放多个客户）：
- 默认 profile：`default`
- 自定义 profile：`cn_ops_template_a`

### 多客户交付包（推荐）

我们提供 `scripts/client_delivery_pack.py`：

1) 按客户创建模板（自动生成 `field-map.<client>.json`）

```bash
python scripts/client_delivery_pack.py create "acme-shop"
```

会生成：`field-map.acme-shop.json`

2) 一键按客户模板跑周报

```bash
python scripts/client_delivery_pack.py run acme-shop
```

脚本会自动用该客户文件和对应 profile 执行：

```bash
python -m src.weekly_report --field-map field-map.acme-shop.json --map-profile acme-shop
```

你也可以在客户交付时快速改参数：

```bash
python scripts/client_delivery_pack.py run acme-shop --input-dir data/raw --output-dir data/output/acme-shop
```

如果要覆盖已有模板，添加 `--overwrite`。

## 现有内置字段映射
- 日期列：`date`, `日期`, `order_date`, `order date`, `交易日期`
- 金额列：`revenue`, `sales`, `amount`, `total`, `金额`, `销售额`
- 订单号列：`order_id`, `order`, `订单号`

如果你文件的字段名更特殊，请按 `field-map.json` 新增或修改对应 profile。可用同义词越多，适配不同源数据越快。


## 交付口径说明（第一版）
- 周期按周一为一周起点（ISO 一周）
- 统计总销售额、订单数、客单价（销售额/订单数）、有销量行数
