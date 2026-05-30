# 🎬 Demo Video

## 演示卡片（可直接放到作品页）

<div align="center">

[![CLI 演示：Excel/CSV 清洗 + 质检告警](./assets/demo-workflow.gif)](./assets/demo-workflow.gif)

</div>

> 本页 GIF 为真实终端会话录屏结果：
> `demo/showcase/assets/demo-workflow.cast`（原始会话）
> `demo/showcase/assets/demo-workflow.gif`（展示图）

### 一键体验脚本（同根目录可复现）

```bash
cd /Users/zhoufangming/Developer/learning/sellable-delivery-bootcamp
python3 -m src.weekly_report --input-dir demo/input/clean --output-dir demo/output/clean
python3 -m src.weekly_report \
  --input-dir demo/input/chaos \
  --output-dir demo/output/chaos_fail \
  --max-invalid-row-rate 0.05 \
  --max-duplicate-order-rate 0.01 \
  --fail-on-quality
```

### 复用录屏素材

- 录屏源：`demo/showcase/assets/demo-workflow.cast`
- 展示图：`demo/showcase/assets/demo-workflow.gif`
- 想要替换素材：保留同名文件直接覆盖即可，`demo-video` 页面和主 README 会自动引用更新后的版本。

### 作品页级发布建议

- 把这页加入 README 的 `Launch Demo`，用户点击后直接看到流程卡片。
- 在公开渠道（公众号/Notion/私域）可直接复用本页第一段 `图片链接`。

