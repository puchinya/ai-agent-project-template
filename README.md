# AI Agent Project Template

GitHub Issues を中心に、AIコーディングエージェントで要求整理・仕様策定・設計・実装・セルフレビュー・PRレビューまで進めるための汎用プロジェクトテンプレートです。

elwindui の agent workflow の考え方をベースにしつつ、Rust 固有のルールをプロジェクトプロファイルへ分離しています。Rust / Node.js / Python / .NET / 複数技術の混在プロジェクトを初期化時に最適化できます。

## Core principles

- `AGENTS.md` を全AIエージェント共通の正本にする。
- リポジトリ変更タスクは GitHub Issue と紐付けてから詳細調査・編集へ進む。
- フェーズを `requirements -> design -> ready -> implementation -> review` で管理する。
- 永続文書の責務を `specs -> design -> code -> status` に分離する。
- 仕様書は「何を保証するか」、設計書は「どう実現するか」を記述する。
- コードを正として、仕様書・設計書を実装後に後付けしない。
- Issueごとの一時状態は `.agent-state/issues/<issue>/` に保存してGit管理しない。
- 技術依存処理は `.agent/project.json` の hooks へ集約する。
- macOS/Linux と Windows PowerShell で共通の Python コアを使用する。
- 最終PR前に Issue 固有 Reviewer Checklist をコミット済み HEAD に対して検証する。

## First-time setup

必要なもの:

- Git
- GitHub CLI (`gh`)
- Python 3.10+
- 利用技術に応じたSDK/ツールチェーン

```bash
gh auth login
./scripts/agent/init-project.sh
./scripts/agent/setup-github.sh
```

PowerShell:

```powershell
gh auth login
.\scripts\agent\init-project.ps1
.\scripts\agent\setup-github.ps1
```

`init-project` は `Cargo.toml`, `package.json`, `pyproject.toml`, `requirements.txt`, `*.sln`, `*.csproj` などを見て技術スタックを検出し、`.agent/project.json` と `docs/agents/project.md` を生成します。

```bash
# auto-detect
./scripts/agent/init-project.sh

# explicit mixed stack
./scripts/agent/init-project.sh --stack rust,node

# Rustで実際にfeature branchへ切り替えた時だけ cargo clean
./scripts/agent/init-project.sh --stack rust --cargo-clean on

# version -> GitHub Milestone synchronization
./scripts/agent/init-project.sh --version-milestones on
```

初期化後は `.agent/project.json` と `docs/agents/project.md` をレビューしてコミットしてください。

## Documentation model

```text
docs/specs/   normative public / observable contract
      |
      v
docs/design/  durable internal architecture
      |
      v
source code   implementation
      |
      v
docs/status/  concise current state / gaps / verification state
```

仕様書・設計書の品質基準:

- `docs/standards/specification.md`
- `docs/standards/design.md`
- `docs/standards/documentation-sync.md`

雛形:

- `docs/templates/spec-template.md`
- `docs/templates/design-template.md`
- `docs/templates/status-template.md`

テンプレート準拠文書は次で検証できます。

```bash
./scripts/agent/validate-docs.sh
```

## Workflow usage

詳しい使い方は [`README.AGENTS_WORKFLOW.md`](README.AGENTS_WORKFLOW.md) を参照してください。


## Template updates for active projects

テンプレート改善を開発中の既存プロジェクトへ反映するため、managed-file manifest と `update-template` を含めています。

```bash
./scripts/agent/update-template.sh --source ../ai-agent-project-template
```

初回導入済みで state がない既存プロジェクトでは次を使います。

```bash
./scripts/agent/update-template.sh --source ../ai-agent-project-template --adopt
```

詳細は `docs/standards/template-update.md` を参照してください。

## Presentation

資料単体で目的から運用まで理解できる31枚の説明資料を `docs/presentations/ai-agent-project-template-introduction.pptx` に同梱しています。導入効果、事前準備・動作環境、workflow、仕様/設計の具体例、新規/既存projectへの導入、template更新・衝突解消、troubleshootingまで含みます。
