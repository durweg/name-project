[English](README.md) · 中文

# name-project

**一个 [Durweg](https://github.com/durweg/durweg) 工作流：让 AI agent（Claude Code、Codex、Antigravity）按固定的 6 步给你的项目起名字，让名字说出项目的特别之处，并且同一领域里没有活跃项目在用。**

agent 先和你一起填一个钻石（核心价值、两类竞争对手、只有你有的东西），找出竞争对手的名字都没占的方向，把看似无关的词拼成候选名字，逐个查重，最后给你一张短名单，请你只选一次。只有**同一领域里没有活跃项目在用**的名字才算通过；星数不算数。Durweg 这个名字就是用它起的。

一个真实的例子，一步一步看：**[给 stepaper 起名](https://claude.ai/artifact/CKh1BGrRvUDbokrhLAi58t#zh)**（中英文可以切换，默认英文；本仓库里也有一份：[case/stepaper-naming.html](case/stepaper-naming.html)）。

## 🧭 安装

先要装好 Durweg（[安装 Durweg](https://github.com/durweg/durweg/blob/main/README_cn.md)）。查重要搜索 GitHub，所以还需要一个 GitHub 账号和 GitHub 命令行工具 `gh`，并用 `gh auth login` 登录一次。

1. **打开终端**（同 Durweg “每天怎么用”第 1 步）。
2. **加进方法库：** `durweg library add https://github.com/musetee/name-project.git --name name-project`。
   它会把工作流下载到 `~/Durweg/workflows/name-project/` 并登记。这一步需要 git；没有 git 的话，在 GitHub 上点 **Code → Download ZIP**，解压到一个文件夹，再运行 `durweg library add <那个文件夹> --name name-project`。

看到 `added name-project`，并且 `durweg library list` 里有 `name-project`，就装好了。

## 📅 怎么用

在要起名字的项目文件夹里启动 agent，对它说：“用 durweg 运行 name-project”。

## 🪜 6 个步骤

| # | 步骤 | 交出什么 | 由你决定 |
| :--- | :--- | :--- | :---: |
| 1 | 钻石 | 核心价值、两类竞争对手、只有你有的东西，都用名词和动词 | ✅ |
| 2 | 空白地带 | 竞争对手的名字都没走的方向 | ✅ |
| 3 | 强制关联 | 10 到 20 个候选名字 | |
| 4 | 逐个查重 | 每个名字在 GitHub、PyPI、npm、crates.io 的情况，以及网上和商标搜索 | |
| 5 | 短名单，只选一次 | 几个名字和一个推荐；你选一次 | ✅ |
| 6 | 记录 | 选定的名字、理由和背后的查重结果 | |

## 🙋 我想……

| 我想 | 怎么做 |
| :--- | :--- |
| 看一次完整的运行，从钻石到最后的决定 | [案例：给 stepaper 起名](https://claude.ai/artifact/CKh1BGrRvUDbokrhLAi58t#zh) |
| 只查一个名字有没有人用 | 见下面的[单独查重](#-单独查重) |
| 改成我自己的做法 | 用 Durweg 的 write-your-method 做一个自己的版本，或者按[工作流格式](https://github.com/durweg/durweg/blob/main/docs/workflow-format_cn.md)改 `workflow.json` 和 `skills/name-project/SKILL.md` |
| 不再用它 | `durweg library remove name-project`，再删掉 `~/Durweg/workflows/name-project/` |

## 🔍 单独查重

```bash
python3 ~/Durweg/workflows/name-project/tools/namecheck.py sousbook coherd --inspect
```

```text
sousbook       CLEAN  repos 0 (same name 0, updated since 2025-10-31: 0)  account free  pypi free  npm free  crates free
coherd         TAKEN  repos 2 (same name 1, updated since 2025-10-31: 1)  account free  pypi free  npm free  crates free
    ! ye-c/coherd 0* pushed 2026-10-30:
      100+ commits, Python, created 2026-08-13: # coherd coherd 把多个 AI agent 组织成一个小团队 …
```

`CLEAN`：最近一年更新过的同名仓库里，没有一个的简介用到你这个领域的词（`--field`，默认 agent、ai、llm、workflow 等）。`TAKEN`：有（标 `!`）。`CHECK`：有最近一年更新过、却没写简介的同名仓库（标 `?`），加 `--inspect` 再跑一次，它会读那个仓库的 README。判断名字被占之前，一定要看 `!` 那几行。

测试：`python3 -m unittest discover -s tools -p 'test_*.py'`（不联网）。

---

MIT 许可证：[LICENSE](LICENSE)。
