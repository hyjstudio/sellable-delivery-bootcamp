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

高级版（无手工录屏）：

```bash
# 安装（按需）
brew install asciinema ffmpeg
npm install -g asciinema-agg
```

```bash
asciinema rec demo/showcase/assets/demo-workflow.cast
# 在录屏中执行 5 分钟上手命令
# 退出 rec 后再转码为 gif（按终端终端大小可调）
agg demo/showcase/assets/demo-workflow.cast demo/showcase/assets/demo-workflow.gif
```

> 如未安装工具，不影响项目交付；当前素材已足够先把仓库发布成可浏览版本，后续可替换为更高质量截图/录屏。

## 在 README 的嵌入建议
将图片改写成你自己的链接路径：

```markdown
![示例输入](./showcase/assets/clean-input.png)
![通过版输出](./showcase/assets/clean-output.png)
![告警质检](./showcase/assets/quality-alert.png)
![演示 GIF](./showcase/assets/demo-workflow.gif)
```
