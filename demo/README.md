# Demo Package

本目录为公开演示用素材，供客户/访客 5 分钟复现实操。

## 输入样例
- `input/clean/sample_clean_sales.csv`：干净样本，用于演示正常输出
- `input/chaos/sample_chaos_sales.csv`：脏数据样本，用于演示质量红线

## 输出样例
- `output/clean/*`：通过版输出
- `output/chaos_fail/*`：质量告警版输出（配合 `--fail-on-quality`）

## 推荐复现流程
1. 跑通过版
```bash
python3 -m src.weekly_report --input-dir demo/input/clean --output-dir demo/output/clean
```
2. 跑告警版
```bash
python3 -m src.weekly_report --input-dir demo/input/chaos --output-dir demo/output/chaos_fail --max-invalid-row-rate 0.05 --fail-on-quality
```

## 对外展示建议
- README 保留 5 分钟上手命令
- 把 `quality_report.md` 的“错误样例行”截图给客户看（最有说服力）
- 用 `weekly_report.md` 做最终提交件
- 展示页素材在 `demo/showcase/`，可直接用其中占位图替代真实截图后上线
