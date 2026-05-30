# Showcase Assets（展示页素材）

这个文件用于把项目从“README 文档”升级到“公开售卖页”可复用资产。

## 目标
- 提供 3 张图片 + 1 段 GIF 的标准化素材
- 方便你直接放到 GitHub README、公众号、Notion、私域海报中

## 当前展示文件
- `demo/showcase/assets/clean-input.png`
- `demo/showcase/assets/clean-output.png`
- `demo/showcase/assets/quality-alert.png`
- `demo/showcase/assets/demo-workflow.gif`

文件均为当前工程真实运行结果导出的展示素材；若你喜欢终端原生截图，可直接替换为同名文件。

## 推荐拍摄流程

### A. 真实截图（推荐，最快）
1. 按 README 的 5 分钟命令跑通过版与告警版
2. 用系统截图录制三类关键页面：
   - 输入样本（`demo/input/clean/sample_clean_sales.csv`）
   - 通过版输出（`demo/output/clean/weekly_report.md`）
   - 告警版质检（`demo/output/chaos_fail/quality_report.md`）
3. 将截图保存为：
   - `demo/showcase/assets/clean-input.png`
   - `demo/showcase/assets/clean-output.png`
   - `demo/showcase/assets/quality-alert.png`

### B. 生成短 GIF（演示 CLI 链路）

当前仓库已提供 `demo/showcase/assets/demo-workflow.gif`；
你可以继续用更高质量的录屏（同路径替换）覆盖它。

建议安装方式：

```bash
python3 -m pip install --user asciinema

# 如果 asciinema 不在 PATH，可用：
# ASCIINEMA_BIN="$(python3 -m site --user-base)/bin/asciinema"
```

录制 `.cast` 并回放文本（按你实际设备路径替换）：

```bash
asciinema rec demo/showcase/assets/demo-workflow.cast -c "bash -lc 'cd /Users/zhoufangming/Developer/learning/sellable-delivery-bootcamp; python3 -m src.weekly_report --input-dir demo/input/clean --output-dir demo/output/clean; python3 -m src.weekly_report --input-dir demo/input/chaos --output-dir demo/output/chaos_fail --max-invalid-row-rate 0.05 --max-duplicate-order-rate 0.01 --fail-on-quality || true'"

asciinema cat demo/showcase/assets/demo-workflow.cast
```

> 当前仓库的 `demo-workflow.gif` 由 `.cast` 会话在本地脚本中渲染生成；你可以直接替换 `.cast` 或 `.gif`，无需改文档链接。

## 演示视频页（作品页入口）

除了静态截图，仓库新增了单独页面用于“作品页级”展示：

- `demo/showcase/demo-video.md`（演示流程 + 命令片段）

建议把该页面放到主 README 的 “Launch Demo” 中对外曝光，点击即可直接进入视频演示页。

## 终端演示卡片（可直接引用）

```markdown
[![Terminal Demo](./assets/demo-workflow.gif)](./demo-video.md)
```

`./assets/demo-workflow.gif` 替换为你录制的终端录屏 GIF 后，作品页会立即变得更“可销售”。

## 在 README 的嵌入建议
将图片改写成你自己的链接路径：

```markdown
![示例输入](./showcase/assets/clean-input.png)
![通过版输出](./showcase/assets/clean-output.png)
![告警质检](./showcase/assets/quality-alert.png)
![演示 GIF](./showcase/assets/demo-workflow.gif)
```
