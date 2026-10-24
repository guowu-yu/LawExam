# 明律知境 · 2027 法考备考系统精讲站

一个面向 **2027 年度国家统一法律职业资格考试** 的静态学习网站。按学科顺序系统精讲，覆盖全部八科，并配套备考时间表与报名清单。

## 站点结构

八科系统精讲路线图（学习顺序）：

> 民法 → 刑法 → 民诉 → 刑诉 → 行政法 → 商经 → 理论法（法理/宪法/法治思想） → 三国法（国际公/私/经）

每科下设若干**子专题**细化讲义，父科页自动汇总「本章子专题」。

## 目录说明

```
2027PrepareLawExam/
├── build.py                 # 静态站生成器（Markdown → dist/）
├── src/                     # 模板与资源
│   ├── index.html           # 首页（八科路线图悬窗 + 进度勾选）
│   ├── topic.html           # 专题页模板
│   └── assets/              # CSS / JS / PDF
├── content/topics/          # 内容源（Markdown，在这里写笔记）
├── scripts/gen_subtopics.py # 子专题批量生成脚本（不覆盖已有文件）
├── dist/                    # 构建产物（被 .gitignore 忽略，CI 会重建）
└── .github/workflows/       # GitHub Pages 自动部署
```

## 本地使用

需要 Python 3 与 `markdown` 库：

```bash
pip install markdown
python build.py          # 生成 dist/
python -m http.server 8000 -d dist   # 本地预览
```

- 补笔记：直接编辑 `content/topics/*.md`，再运行 `build.py`。
- 新增子专题：在 `content/topics/` 新建 `.md` 并加 `parent: <八科slug>`，父科页会自动汇总。

## 部署

仓库已内置 GitHub Pages 工作流（`.github/workflows/deploy.yml`）：推送 `main` 分支即自动构建并发布。
在仓库 **Settings → Pages** 中将 Source 设为 **GitHub Actions** 即可。

> 注：本站内容仅供个人备考学习参考，具体报考政策与考试安排以司法部官方公告为准。
