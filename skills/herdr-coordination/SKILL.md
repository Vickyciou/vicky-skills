---
name: herdr-coordination
description: 在 herdr 建立專用 worker panes，協調同一 workspace 內多個 repo 的平行工作
disable-model-invocation: true
---

# herdr-coordination

在 herdr workspace 中由**這個 session 當主控**，建立專用的 Claude Code 或 Codex worker sessions，協調「主 SDK + 周邊 repo + 消費端 app」等多 repo 工作。

呼叫此 skill 後，你（這個 session）即為主控，依下面運作。

## 先認識 workspace

動工前，從 workspace 的 `CLAUDE.md`／`AGENTS.md` 讀出並記住三件事（**以檔案為準，不要背**）：

1. **有哪些 repo、各自的基準**：分支、tag、子 repo 或 submodule 關係。
2. **整合迴圈的指令**：打包、建置、啟動消費端 app 或模擬器的 skill／命令。
3. **跨 repo 的生效規則**：例如 SDK 改動後要重打包，以及產物要同步到哪個 repo。

同時讀取 workspace 是否指定 herdr worker launcher；沒有指定時才使用本 skill 的 fallback。

## 角色

- **主控**：讀全貌、拆票、建立 workers、派工、驗收、維護 task board、串接整合迴圈。主控不直接改 code。
- **worker**：認領一張票，在綁定的 pane 中完成工作並留下可供主控讀取的結案回報。

## Worker launcher

worker 的 agent 類型與主控的 agent 類型彼此獨立。依下列優先序決定 launcher：

1. 使用者在本次呼叫明確指定的 launcher。
2. Workspace `CLAUDE.md`／`AGENTS.md` 指定的預設 launcher。
3. 兩者皆未指定時，繼承主控的 agent 類型。

支援的 launcher：

- `claude-work`：在新 pane 執行 `ccc work`。
- `codex`：在新 pane 執行 `codex -C "<workspace>"`。

使用者可明確指定混合配置，例如 2 個 `claude-work` 加 2 個 `codex`。若無法從上述規則決定 launcher，在建立 pane 前詢問使用者。

## 建立專用 workers

**只使用本次由主控新建的 panes。** 呼叫本 skill 前已存在的 sessions，不論是 idle、working 或有無對話紀錄，都不列入 worker pool。

1. 先拆票，再依可平行的票數建立 workers；worker 上限為 **4 個**，不包含主控。
2. 用 `herdr pane split` 在 workspace 根目錄建立新 pane，記錄回傳的 pane ID。
3. 依 launcher 在新 pane 啟動全新的 agent session，等待 herdr 偵測到 agent ready。
4. 將 pane ID、launcher 與票號記入 task board，再派工。
5. 每個 worker 綁定一張票及其延續工作；已有 context 的 worker 不改派無關的新票。
6. 超過 4 張的票保留為 `todo`。若 4 個 workers 都已綁定，而新的無關工作需要空白 context，回報容量已滿並等使用者決定。

建立與啟動的命令形狀如下；方向與比例可依現有 layout 調整：

```sh
herdr pane split --current --direction right --cwd "<workspace>" --no-focus
herdr pane run <pane-id> ccc work
herdr pane run <pane-id> codex -C "<workspace>"
```

## 派工與回報管道

使用 herdr 的 agent-neutral 管道，讓 Claude Code 與 Codex workers 共用同一流程：

- `herdr agent prompt <pane-id> "<派工單>"`：派工或追問。
- `herdr agent wait <pane-id>`：等待 worker 進入 idle、done 或 blocked。
- `herdr agent read <pane-id>`：讀取進度與結案回報。

派工單必須要求 worker 在最後回報：狀態、分支名、修改摘要、驗證結果與未解問題。主控讀到回報後 review diff；資訊不足時回到同一 pane 追問。

## 運作迴圈

1. 讀全貌，把需求拆成盡量不重疊的票，填入 board。
2. 建立最多 4 個專用 workers，逐一綁定並派工。
3. worker 完成後，主控讀取結案回報並 review diff。
4. 要跑進 app 驗證時，依「整合迴圈」串行執行。
5. 通過後，在該 repo commit 或交回使用者決定；不通過則退回原 worker。

## 派工單

- **票號／目標**：一句話說明要達成什麼。
- **repo 與範圍**：哪個 repo、哪些檔案或模組。
- **基準分支**與**驗收標準**。
- **是否開 worktree**。
- 要求：「先讀 workspace 的 `CLAUDE.md`／`AGENTS.md` 慣例再動手。」
- 要求結案回報格式：狀態、分支、摘要、驗證、未解問題。

## Pane 保留政策

任務完成後，保留 worker pane、agent session 與 context，供驗收、追問或原任務的延續工作使用。只有使用者明確要求時，才能關閉、重啟或清空 panes。

## Worktree 政策

- **會改動 code 的任務 → 預設開 worktree**，在該 repo 內隔離：

  ```sh
  git worktree add ../.worktrees/<repo>-<taskid> -b task/<taskid>
  ```

  worktree 放 workspace 的 `.worktrees/`，並確保被 gitignore；驗收 land 後移除。
- **唯讀／調查型任務 → 不開 worktree**，直接讀。
- **零星且確定不重疊的小改**可就地修改，但仍遵守防撞規則。

## 防撞規則

worktree 已隔離 workers，同一 repo 可以平行工作。主控在派工與 land 時仍須處理下列邊界：

1. 盡量不要把同一批檔案同時交給兩個 workers；若仍重疊，land 時處理 merge conflict。
2. worker 動工前以 `git status` 確認基準，做完只留下該票的改動。
3. 跨 repo 的一件事，例如改 SDK API 又改 app 呼叫端，拆成兩張票分派或序列執行。

## 整合迴圈：序列，不可平行

打包、建置、跑模擬器會動到共用二進位與同一台模擬器，同一時間只能一人執行。預設由主控負責；也可指派單一 worker，但主控必須保證沒有第二個整合流程同時執行。

> **SDK 改動 + worktree 的接縫**：若建置會依相對路徑把產物同步進 sibling repo，而 SDK 改動位於其他 worktree，同步路徑可能對不到目標。SDK 類任務要跑進 app 驗證時，先把 worktree 分支 land 回主 checkout，再從主 checkout 執行整合迴圈，保持 sibling 路徑不變。app-only 改動可直接在 worktree 內建置與執行。

## Task board

主控維護，一票一列：

| id | repo | 範圍 | pane | launcher | 狀態 | 產出（分支） |
|:---|:---|:---|:---|:---|:---|:---|

狀態：`todo` → `doing` → `done`（驗收後 `landed`）。
