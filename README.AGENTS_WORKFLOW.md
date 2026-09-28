# AI Agent Workflow — 使い方

この文書は、このリポジトリテンプレートを使った日常運用と、既存プロジェクトへの導入方法を説明します。


## 0. 事前準備・動作環境

このテンプレートは **GitHub上のリポジトリ + ローカルGit作業環境** を前提にしています。AIエージェント自体は特定製品に固定せず、`AGENTS.md` を読めるコーディングエージェントであれば同じworkflowを利用できます。

### 対応環境

| 項目 | 対応 / 前提 |
|---|---|
| OS | macOS / Linux / Windows |
| Shell | macOS/Linux: Bash系、Windows: PowerShell |
| Git | ローカルrepository操作に必須 |
| GitHub | Issue / Pull Request / labels を利用するため必須 |
| GitHub CLI | `gh`。Issue/PR/label/milestone操作に使用 |
| Python | Python 3.10+ 推奨。共通ロジック `scripts/agent/agent_tool.py` の実行に使用 |
| AI agent | Codex、Claude Code、Gemini系など。共通ルールは `AGENTS.md` を正本とする |
| Network | GitHub操作、push/pull、依存取得が必要な処理では必要 |

Shellごとの実行入口は同じ機能を提供します。

```text
macOS / Linux : scripts/agent/<command>.sh
Windows        : scripts/agent/<command>.ps1
```

`.sh` / `.ps1` は薄いwrapperで、主要ロジックはPythonへ集約しています。OSごとに別実装を持たないことで、workflowの挙動差を抑えています。

### 必須ツールの確認

macOS / Linux:

```bash
git --version
gh --version
python3 --version
gh auth status
```

Windows PowerShell:

```powershell
git --version
gh --version
python --version
gh auth status
```

`gh auth status` が失敗する場合は、先に次を実行します。

```bash
gh auth login
```

### GitHub側で必要な権限

最低限、対象repositoryに対して次の操作ができる必要があります。

- Issueの作成・編集
- labelsの参照・更新
- Pull Requestの作成・参照
- branchのpush
- `setup-github` を使う場合はlabelsの作成・更新
- version milestoneを有効にする場合はmilestoneの参照・作成・Issueへの設定

組織ポリシー、branch protection、required checks、GitHub Appの権限制限がある場合は、それらが優先されます。テンプレートは保護ルールを回避しません。

### 技術スタック別の追加要件

`init-project` は利用技術を検出して初期hookを生成しますが、実際のbuild/testにはその技術のSDK・package managerが必要です。

| Stack | 検出例 | 代表的な追加ツール | 生成されるhook例 |
|---|---|---|---|
| Rust | `Cargo.toml` | Rust toolchain / Cargo | `cargo check`, `cargo test`, 必要なら `cargo clean` |
| Node.js | `package.json` | Node.js / npm | `npm run typecheck`, `npm run lint`, `npm test` |
| Python | `pyproject.toml`, `requirements.txt` | Python環境 / project dependencies | `python -m pytest` 等 |
| .NET | `*.sln`, `*.csproj` | .NET SDK | `dotnet build`, `dotnet test` |
| Mixed | 上記が複数存在 | 各stackのtoolchain | 複数stackのhookを順に実行 |

自動検出は **安全な初期値の生成** が目的です。最終的な `verify_quick` / `verify_final` は、対象プロジェクトのCIやrelease gateと一致するよう `.agent/project.json` をレビューしてください。

### リポジトリ状態の前提

多くのhelperは、次の状態を前提にします。

- ローカルディレクトリがGit repositoryである
- `origin` が対象GitHub repositoryを指している
- `gh` がそのrepositoryへアクセスできる
- branch作成前にworktreeがcleanである
- Issue番号を使う操作では対象Issueが存在する

`start-feature-branch` は意図しない変更を巻き込まないため、dirty worktreeでは停止します。

### セキュリティとローカル状態

- GitHub tokenやAPI keyをrepositoryへ保存しない。認証は `gh` や各toolchainの標準credential storeを利用する。
- `.agent-state/` はIssue単位の一時状態、logs、contract mirror、self-reviewを置くため `.gitignore` 対象とする。
- checkpointやlogsに秘密情報、個人情報、不要な絶対パスを残さない。
- Implementation Contractのmirrorはローカル保存し、SHA-256で内容の取り違えを検出する。

### 対応範囲

このテンプレートはGitHub Issue / Pull Requestをworkflowの状態管理に使用します。そのため、GitLab等で同じ考え方を利用する場合は、`gh`を使うhelperとIssue/PR操作部分のadapterが必要です。仕様書・設計書・phase model・hook model自体は再利用できます。

## 1. 新規プロジェクトで使う

GitHub の Template Repository から新しいリポジトリを作成した後、最初にプロジェクト固有設定を生成します。

macOS / Linux:

```bash
./scripts/agent/init-project.sh
./scripts/agent/setup-github.sh
```

Windows PowerShell:

```powershell
.\scripts\agent\init-project.ps1
.\scripts\agent\setup-github.ps1
```

`init-project` は利用技術を検出して `.agent/project.json` を生成します。自動検出結果が意図と違う場合は明示します。

```bash
./scripts/agent/init-project.sh --stack rust
./scripts/agent/init-project.sh --stack node
./scripts/agent/init-project.sh --stack rust,node
```

Rust では、ディスク容量やビルドキャッシュ方針に応じて branch switch 後の `cargo clean` を設定できます。

```bash
./scripts/agent/init-project.sh --stack rust --cargo-clean on
```

この設定は `start-feature-branch` の **実際の branch switch が発生した時だけ** `branch_switch` hook として実行されます。同一branchでの再実行では clean しません。

初期化後に確認するファイル:

- `.agent/project.json`
- `docs/agents/project.md`
- `.gitignore`

## 2. 既存プロジェクトへ導入する

既存リポジトリへ追加する場合は、最初から既存のルールを上書きしません。

1. このテンプレートから `docs/agent-workflow/`, `docs/standards/`, `docs/templates/`, `scripts/agent/`, `.agent/` をコピーする。
2. 既存 `AGENTS.md` がある場合は破棄せず、プロジェクト固有ルールを `docs/agents/project.md` または関連ガイドへ移し、共通入口を `AGENTS.md` に統合する。
3. `CLAUDE.md` / `GEMINI.md` は共通ルールを複製せず `AGENTS.md` へのルータにする。
4. 既存の `docs/` 構造がある場合は、文書責務を確認して `specs`, `design`, `status` のどれに相当するかを明示する。無理に一括移動しない。
5. `init-project` を実行して技術プロファイルを生成する。
6. `setup-github` で workflow labels を作る。
7. `validate-docs` を実行する。
8. 導入作業自体を1つのIssue/PRとしてレビューする。

既存のCI・lint・testコマンドは `.agent/project.json` の `hooks.verify_quick` / `hooks.verify_final` に設定します。ワークフロー文書へコマンドを重複記載しないことを推奨します。

## 3. 新しい機能・修正をAIエージェントへ依頼する

ユーザーは通常の言葉で依頼して構いません。

```text
CSV exportを追加して
```

エージェントは `AGENTS.md` に従い、リポジトリ変更であれば先に owning Issue を特定します。存在しなければ `phase:requirements` Issue を作成してから詳細調査へ進みます。

### Requirements phase

目的は「実装方法を考えること」ではなく、「何を満たせば完了か」を明確にすることです。

Issueには少なくとも以下を整理します。

- Background
- Objective
- Functional requirements
- Non-goals
- Constraints
- Acceptance criteria
- Unresolved questions
- Document impact

Document impactはspecification、design、status/evidenceごとに、既存ownerの更新、新しい文書の正確な将来パス、または不要とする具体的理由を記録します。既存ownerはMarkdownリンクで示します。

公開・観測可能な契約が変わる場合は対応する[specification owner](docs/specs/README.md)を更新します。

### Design phase

要求承認後、`phase:design` へ進みます。

新しい機能やdurable architecture変更では、Issueのメモだけで終わらせず、Document Architecture Gateを通します。

- 変更するobservable ruleにはspecification ownerを一つ定める。
- durable architecture decisionにはdesign ownerを一つ定める。
- 新しい文書や分割した文書は[specification index](docs/specs/README.md)または[design index](docs/design/README.md)からリンクする。
- task-only decisionはIssue/PR、実装詳細はcode/tests、実際の進捗や検証結果はstatus/evidenceに置く。
- navigational Markdown referencesはクリック可能にする。
- schema-2の品質topicは適用するか、具体的な理由とともにN/Aとする。

1つの文書が不要な場合は、requirements/IssueのDocument impactに理由を残します。新規の非自明な機能では通常specificationとdesignの両方を検討します。

仕様書は[specification template](docs/templates/spec-template.md)、設計書は[design template](docs/templates/design-template.md)を起点にし、[specification standard](docs/standards/specification.md)と[design standard](docs/standards/design.md)に従います。

新規文書は helper から作成できます。ファイル名はエディタのタブでも種類を判別しやすいよう `-spec.md`, `-design.md`, `-status.md` 接尾辞になります。

```bash
./scripts/agent/new-doc.sh specification export/csv --issue 123 --title "CSV Export"
./scripts/agent/new-doc.sh design export/csv --issue 123 --title "CSV Export"
./scripts/agent/new-doc.sh status export/csv --issue 123 --title "CSV Export"
```

設計承認前に、実装後のセルフレビューで使う `## Reviewer Checklist` をIssueへ固定します。

### Implementation phase

実装開始時:

```bash
./scripts/agent/prepare-self-review.sh <issue-number>
./scripts/agent/start-feature-branch.sh <issue-number> "short english description"
```

PowerShell:

```powershell
.\scripts\agent\prepare-self-review.ps1 <issue-number>
.\scripts\agent\start-feature-branch.ps1 <issue-number> "short english description"
```

実装中は狭い検証を優先します。

```bash
./scripts/agent/run-hook.sh verify_quick
```

コードを安定させた後、最終検証を実行します。

```bash
./scripts/agent/run-hook.sh verify_final
./scripts/agent/validate-docs.sh
```

## 4. セルフレビュー

`prepare-self-review` は Issue の `## Reviewer Checklist` と、存在する場合は保存済み Implementation Contract の checklist を統合し、次を生成します。

```text
.agent-state/issues/<issue>/
  reviewer-checklist.md
  reviewer-checklist.sha256
  self-review.md
```

`self-review.md` の各項目を `PASS`, `N/A`, `FAIL` のいずれかで埋めます。`PASS` には `Evidence:`、`N/A` には `Reason:` が必要です。

変更をコミットした後、`Reviewed-HEAD` を現在の commit SHA に設定し、次を実行します。

```bash
./scripts/agent/validate-self-review.sh <issue-number>
```

新しいcommitが入った時点で以前のセルフレビューは stale です。再レビューします。

## 5. Pull Requestとレビュー

PRはIssueの全文を複製せず、差分中心にします。

推奨構成:

```text
## Purpose / impact
## Delta
## Design deviations
## Verification
## Untested / residual risk
## Reviewer focus
Closes #<issue>
```

PR作成後、Issueを `phase:review` にします。

レビュー修正でコードが変わった場合は:

1. 修正
2. focused verification
3. commit
4. complete diff self-review
5. `validate-self-review`
6. 必要なら final verification
7. 再レビュー依頼

Issueの完了はPR作成時ではなく、mergeとacceptance criteria達成で判断します。

## 6. 中断・再開

中断前:

```bash
./scripts/agent/save-work-checkpoint.sh <issue-number>
```

再開時:

```bash
./scripts/agent/resume-work.sh <issue-number>
./scripts/agent/agent-context.sh <issue-number>
```

checkpointは短く保ちます。思考過程、秘密情報、巨大ログは保存しません。

## 7. Implementation Contractを渡す

別のAIや人間がdecision-completeな実装指示書を作成済みの場合:

```bash
./scripts/agent/save-implementation-contract.sh <issue-number> instruction.md
```

保存先:

```text
.agent-state/issues/<issue>/implementation-contract.md
.agent-state/issues/<issue>/implementation-contract.sha256
```

Contractはworkflow bypassではありません。Issue ownership、既存spec/designとの整合、セルフレビューは引き続き必要です。

## 8. 技術スタックごとの最適化

`.agent/project.json` の `hooks` がプロジェクト固有実行規則です。

例: Rust

```json
{
  "hooks": {
    "branch_switch": ["cargo clean"],
    "verify_quick": ["cargo check --workspace"],
    "verify_final": [
      "cargo fmt --all -- --check",
      "cargo test --workspace"
    ]
  }
}
```

Node.js では `npm test`, `npm run lint`, `npm run typecheck` など、.NETでは `dotnet build`, `dotnet test`、Pythonでは `pytest` 等へ置き換えられます。

自動検出は初期値を作るだけです。プロジェクトの正しいCIゲートに合わせて調整してください。

## 9. 仕様書と設計書を維持する

仕様書と設計書を同じ内容の言い換えにしないことが重要です。

schema 2ではOverviewから詳細へ読み進められるようにし、一つのdurable ruleにつきsemantic ownerを一つにします。documentは現在の要求・architectureを記述し、完了したIssue/PRの経緯や単発の検証結果は残しません。文書分割はsemantic ownershipと変更境界で決め、50 KiBはreview warningであって分割条件ではありません。

文書間を案内するMarkdown referencesはクリック可能にし、broken relative `.md` targetを修正します。大きなrepositoryではnested ownership indexesを使えます。

仕様書:

- 外部・利用者・他モジュールから観測可能な契約
- MUST / MUST NOT / SHOULD 等で曖昧さを減らす
- 入出力、状態遷移、エラー、互換性、境界条件
- acceptance criteriaとの対応

設計書:

- 仕様を満たす内部構造
- component/module responsibility
- data/event flow
- ownership/lifecycle
- concurrency/async
- error propagation/recovery
- persistence/cache
- platform差
- test strategy
- alternatives considered / rejected

仕様書ではsecurity/privacy、performance/scalability、user-facing behaviorのaccessibility/usability、compatibility/versioning、portability/platform behaviorを検討します。設計書ではfailure/recovery、ownership/lifecycle/cleanup、cancellation/reentrancy/repeated calls、security、resource/performance、observability/supportability、compatibility/migration、platform/backend differencesを検討します。適用しないtopicは具体的な理由付きでN/Aとします。

詳しい基準は[Specification standard](docs/standards/specification.md)、[Design standard](docs/standards/design.md)、[Documentation synchronization standard](docs/standards/documentation-sync.md)にあります。

## 10. 最小の日常コマンド

```bash
# project context
./scripts/agent/agent-context.sh <issue>

# start implementation
./scripts/agent/prepare-self-review.sh <issue>
./scripts/agent/start-feature-branch.sh <issue> "short description"

# verification
./scripts/agent/run-hook.sh verify_quick
./scripts/agent/run-hook.sh verify_final
./scripts/agent/validate-docs.sh

# pause/resume
./scripts/agent/save-work-checkpoint.sh <issue>
./scripts/agent/resume-work.sh <issue>

# final self-review
./scripts/agent/validate-self-review.sh <issue>
```


## 11. テンプレート改善を開発中プロジェクトへ反映する

このテンプレートは `.agent/template-files.json` に template-managed files を持ちます。開発中プロジェクト側では `.agent/template-state.json` が前回同期したテンプレートのハッシュを保持します。

### 初回導入済みプロジェクトへ反映する

既存プロジェクトがまだ `template-state.json` を持っていない場合:

```bash
./scripts/agent/update-template.sh --source ../ai-agent-project-template --adopt
```

PowerShell:

```powershell
.\scripts\agent\update-template.ps1 --source ..\ai-agent-project-template --adopt
```

`--adopt` は既存ファイルをいきなり上書きしません。衝突がある場合は `<file>.incoming-template` を作成し、手動merge対象として報告します。

### テンプレート更新後に再同期する

```bash
git checkout -b chore/update-agent-template
./scripts/agent/update-template.sh --source ../ai-agent-project-template
./scripts/agent/validate-docs.sh
./scripts/agent/run-hook.sh verify_final
```

template manifestの `documentation_schema_version` が上がると、`update-template` はschemaが古いdurable spec/design文書を `MIGRATION_REQUIRED` として列挙し、終了コード `3` を返します。終了コード `2` はmanaged-file conflictです。終了コード `3` の場合も安全なmanaged-file更新は適用済みで、template-stateは記録されています。

Project-specific specs/design/statusはmanaged filesではなく、updaterは書き換えません。対象文書を人が意味的にschema 2へ移行し、ownership indexとリンクを直してから、同じtemplate-update Issue/PR内でupdaterを再実行します。終了コード `0`、`validate-docs`、project final verification、self-review、review phaseまで終わる前にtemplate-update PRを完了扱いにしません。自動の見出し挿入や機械的な意味移行は行いません。

衝突が出た場合:

1. `<file>.incoming-template` を確認する。
2. 既存ファイルへ必要な内容を手動mergeする。
3. `.incoming-template` を削除する。
4. `update-template` を再実行する。
5. 差分をPRでレビューする。

### 管理対象と非管理対象

管理対象は `.agent/template-files.json` に列挙された共通workflowファイルです。プロジェクト固有の `.agent/project.json`、`docs/agents/project.md`、個別仕様書・設計書・status、source code は上書き対象にしません。

## 12. 導入説明資料

`docs/presentations/ai-agent-project-template-introduction.pptx` に以下を含む説明資料を同梱しています。

- 導入効果
- 導入手順
- 日常運用
- テンプレート更新手順
- 既存プロジェクトへの反映方針
