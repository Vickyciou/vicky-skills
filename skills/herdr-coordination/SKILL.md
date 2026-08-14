---
name: herdr-coordination
description: 在 herdr 多 pane 開多個 Claude session,協調同一 workspace 內多個 repo 的工作
disable-model-invocation: true
---

# herdr-coordination

在 herdr 各 pane 各開一個 Claude Code session(都在 workspace 上層開),由**這個 session 當主控**,協調其他 session(worker)在同一 workspace 的多個 repo 上平行工作。適用於「主 SDK + 週邊 repo + 消費端 app」併在一層的多 repo 專案。

呼叫此 skill 後,你(這個 session)即為主控,依下面運作。

## 先做:認識這個 workspace

主控動工前,從 workspace 自己的 `CLAUDE.md` / `AGENTS.md` 讀出、並記住三件事(**以該檔為準,不要背**):

1. **有哪些 repo、各自的基準**(哪個分支 / tag;子 repo 或 submodule 關係)。
2. **整合迴圈的指令**——打包 / 建置 / 跑起消費端 app(模擬器)的 skill 或命令。
3. **跨 repo 的生效規則**(例:改了 SDK 要重打包、二進位同步到哪個 repo 才生效)。

再用 `ListAgents` 看有哪些 peer session、誰 idle。

## 角色

- **主控(這個 session)**:讀全貌、拆票、派工、驗收、串接整合迴圈。**自己不直接改 code。**
- **worker**:認領一張票,做完回報主控。

## 開新 worker

在新 pane 執行 `ccc work` 啟動(會自動登入 Claude Code),再由主控 `SendMessage` 指派。

## 管道

- `ListAgents` — 看 peer session 與 idle/busy 狀態
- `SendMessage({to: "<session名>", message: "..."})` — 派工、回報、追問

派工與回報一律走 `SendMessage`;狀態落在 task board(見下),session 重開也不遺失。

## 運作迴圈

1. 讀全貌,把需求拆成盡量不重疊的票,填進 board。
2. `SendMessage` 派給 idle worker,附上「派工單」(見下)。
3. worker 回報 done + 分支名 + 摘要 → 主控 review diff。
4. 要跑進 app 驗證 → 依「整合迴圈」串行執行。
5. 通過 → 在該 repo commit(或交回人類決定);不通過 → 退回同一 worker。清掉用完的 worktree。

## 派工單(SendMessage 給 worker 時附上)

- **票號 / 目標**:一句話說明要達成什麼
- **repo 與範圍**:哪個 repo、哪些檔案/模組
- **基準分支**、**驗收標準**
- **是否開 worktree**(見下)
- 一句:「先讀 workspace 的 `CLAUDE.md` 慣例再動手」

## worktree 政策

- **會改動 code 的任務 → 預設開 worktree**,在該 repo 內隔離:
  ```
  git worktree add ../.worktrees/<repo>-<taskid> -b task/<taskid>
  ```
  worktree 放 workspace 的 `.worktrees/`(記得 gitignore),驗收 land 後移除。
- **唯讀 / 調查型任務 → 不開 worktree**,直接讀。
- **零星、確定不重疊的小改**:可就地改,但遵守防撞規則。

## 防撞規則

worktree 已隔離各 worker,所以**同一 repo 可多人平行**,不必鎖模組。要顧的只有 land 時的檔案重疊:

1. 派工時盡量別把**同一批檔案**同時交給兩人;真重疊到了,land 時解 merge 衝突即可。
2. worker 動工前 `git status` 確認乾淨,做完只留自己那張票的改動。
3. 跨 repo 的一件事(例:改 SDK API 又要改 app 呼叫端)**拆成兩張票**,分派或序列做。

## 整合迴圈:序列,不可平行

打包 / 建置 / 跑模擬器會動到共用二進位與同一台模擬器,**同一時間只能一人做**,預設由主控跑(也可指派給單一 worker,但主控保證同時只有一人在整合)。

> ⚠️ **SDK 改動 + worktree 的接縫**:若建置會把產物依相對路徑同步進 sibling repo,而 SDK 改動在別處的 worktree,同步會對不到目標。
> 因此 SDK 類任務要跑進 app 驗證時,**先把 worktree 分支 land 回主 checkout,再從主 checkout 跑整合迴圈**,保持 sibling 路徑不變。
> app-only 改動可直接在 worktree 內建置/執行,無此問題。

## Task board

主控維護,一票一列:

| id | repo | 範圍 | 認領 | 狀態 | 產出(分支) |
|:---|:---|:---|:---|:---|:---|

狀態:`todo` → `doing` → `done`(驗收後 `landed`)。
