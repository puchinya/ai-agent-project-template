# AI Agent Project Template

GitHub Issues を中心に、AIコーディングエージェントで要求整理・仕様策定・設計・実装・セルフレビュー・PRレビューまで進めるための汎用プロジェクトテンプレートです。

elwindui の agent workflow の考え方をベースにしつつ、Rust 固有のルールをプロジェクトプロファイルへ分離しています。Rust / Node.js / Python / .NET / 複数技術の混在プロジェクトを初期化時に最適化できます。

## Core principles

- `AGENTS.md` を全AIエージェント共通の正本にする。
- リポジトリ変更タスクは GitHub Issue と紐付けてから詳細調査・編集へ進む。
- フェーズを `requirements -> design -> ready -> implementation -> review` で管理する。
- 永続文書を人とAIの両方が使えるよう、specification / design / code-and-tests / status-evidence の責務を分ける。
- 仕様書は「何を保証するか」、設計書は「どう実現するか」を記述する。
- 仕様書・設計書は短いOverviewから詳細へ進め、各ルールの意味上のownerを一つにする。
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

schema 2では `component`（開発・検証単位）、`stack`（実装技術）、`application type`（追加の設計・仕様観点）、`target`（build/run対象）を別々に記録します。application typeは自動推論されません。省略時は `generic` になり、追加profileは適用されません。

```bash
# auto-detect
./scripts/agent/init-project.sh

# explicit mixed stack
./scripts/agent/init-project.sh --stack rust,node

# application behavior and build/run targets
./scripts/agent/init-project.sh --stack swift --application-type mobile,library --target ios-device,macos-arm64

# Rustで実際にfeature branchへ切り替えた時だけ cargo clean
./scripts/agent/init-project.sh --stack rust --cargo-clean on

# version -> GitHub Milestone synchronization
./scripts/agent/init-project.sh --version-milestones on
```

初期化後は `.agent/project.json` と `docs/agents/project.md` をレビューしてコミットしてください。

schema-2の `run-hook verify_quick` / `verify_final` はglobal hooks、component hooks、runtime hostで実行できるtarget hooksを順に実行します。`--component <id>` は繰り返し指定でき、省略すると全componentが選択されます。profileの詳細は [Project Profile and Agent Context Specification](docs/specs/project-profile-spec.md) を参照してください。

## Documentation model

Schema 2 gives specifications and designs a human-readable Overview, explicit semantic ownership, current-state-only content, and prompts for relevant commercial-quality concerns. Large files trigger a review warning at 50 KiB; size alone does not require a split.

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

- [Specification standard](docs/standards/specification.md)
- [Design standard](docs/standards/design.md)
- [Documentation synchronization standard](docs/standards/documentation-sync.md)

雛形:

- [Specification template](docs/templates/spec-template.md)
- [Design template](docs/templates/design-template.md)
- [Status template](docs/templates/status-template.md)

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

テンプレートmanifestの `documentation_schema_version` は、適用先の durable specification / design に必要なschemaを示します。更新でmigrationが必要になると、`update-template` は終了コード `3` と対象ファイル一覧を返します。文書は自動書き換えせず、同じtemplate-update Issue/PRで意味を保って移行します。

詳細は [Template update standard](docs/standards/template-update.md) を参照してください。

## Presentation

資料単体で目的から運用まで理解できる31枚の説明資料を `docs/presentations/ai-agent-project-template-introduction.pptx` に同梱しています。導入効果、事前準備・動作環境、workflow、仕様/設計の具体例、新規/既存projectへの導入、template更新・衝突解消、troubleshootingまで含みます。
