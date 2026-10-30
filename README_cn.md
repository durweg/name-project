[English](README.md) · 中文

# naming-workflow

给项目起名字的工作流，适合用 coding agent（Claude Code、Codex、Antigravity）的人：agent 先和你一起弄清这个项目和别人有什么不同，为它找一个比喻，收集候选名字，逐个查重，最后给你一张短名单，请你只选一次。只有**同一领域里没有活跃项目在用**的名字才算通过；星数不算数。

## 安装

作为 [AIagents](https://github.com/musetee/aiagents) 插件（这个仓库目前是私有的）：

```bash
aiagent plugin install git@github.com:musetee/naming-workflow.git
```

不用 AIagents：克隆到任意位置，运行 `bash tools/install.sh`。之后 skill `name-project` 会链接到每个已安装的 agent，`~/.naming-workflow` 指向这个克隆。查重需要先登录 `gh`（`gh auth login`）。

## 怎么用

对 agent 说“帮这个项目起个名字”（或“X 这个名字有没有人用”）。它会照着 [`skills/name-project/SKILL.md`](skills/name-project/SKILL.md) 一步步做，只在需要你决定的地方问你。

查重也可以单独运行：

```bash
python3 ~/.naming-workflow/tools/namecheck.py sousbook coherd --inspect
```

`CLEAN`：最近一年更新过的同名仓库里，没有一个的简介用到你这个领域的词（`--field`，默认 agent、ai、llm、workflow 等）。`TAKEN`：有（标 `!`）。`CHECK`：有最近一年更新过、却没写简介的同名仓库（标 `?`），加 `--inspect` 再跑一次，它会读那个仓库的 README。判断名字被占之前，一定要看 `!` 那几行。

测试：`python3 -m unittest discover -s tools -p 'test_*.py'`（不联网）。
