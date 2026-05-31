# 客户演示包：示例客户每周销售报表

## 演示定位

这个目录是一份面向中文客户的真实交付样例。

适用场景：

- 小商家、运营人员或外包服务方提供原始销售表。
- 我方负责清洗表格、生成每周销售报表，并标出有风险的数据行。
- 客户最终拿到可直接查看的周报，以及一份说明数据问题的质量报告。

## 客户问题

客户手里有销售数据，但原始文件通常不能直接用于周报。

常见问题：

- 表头命名不统一。
- 日期或金额存在错误值。
- 订单号可能缺失或重复。
- 每周人工统计重复、耗时，并且容易前后口径不一致。

## 我们交付什么

标准交付包包含：

- `cleaned_rows.csv`：清洗后的明细表
- `weekly_report.csv`：可继续处理的周报数据
- `weekly_report.md`：客户可直接阅读的周报
- `quality_report.json`：结构化质量结果
- `quality_report.md`：客户可读的质量报告，包含错误样例行
- `delivery-note.md`：可直接发给客户的交付说明

## 演示命令

运行正常样例：

```bash
python3 -m src.weekly_report \
  --input-dir demo/input/clean \
  --output-dir demo/output/clean
```

运行质量告警样例：

```bash
python3 -m src.weekly_report \
  --input-dir demo/input/chaos \
  --output-dir demo/output/chaos_fail \
  --max-invalid-row-rate 0.05 \
  --max-duplicate-order-rate 0.01 \
  --fail-on-quality
```

使用这个示例客户配置运行：

```bash
python3 scripts/client_delivery_pack.py run sample-client \
  --input-dir demo/input/clean \
  --output-dir data/output/sample-client
```

## 给客户展示哪些文件

快速演示时优先展示这些文件：

- `demo/input/clean/sample_clean_sales.csv`
- `demo/output/clean/weekly_report.md`
- `demo/output/clean/quality_report.md`
- `demo/input/chaos/sample_chaos_sales.csv`
- `demo/output/chaos_fail/quality_report.md`
- `data/output/sample-client/weekly_report.md`
- `data/output/sample-client/quality_report.md`

## 服务边界

这份演示不是完整财务系统。

它是一套轻量交付工具，适合：

- 重复生成每周销售报表
- 做基础表格清洗
- 在正式交付前发现数据质量问题
- 针对不同客户做字段映射

它不替代最终财务复核、税务申报或经营判断。
