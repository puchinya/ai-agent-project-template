# Implementation Contract — Agent Workflow 全改善

対象: `puchinya/ai-agent-project-template`、Codex / Claude Code共通。調査基準: 2026-10-01 `main` `b32913b2f736c9abc544cf8c8b3e5579fbb26562`。着手前に最新HEAD/Issue/PRを再確認する。

> This document is an Implementation Contract. Do not redesign the architecture during implementation. If a requirement conflicts with repository reality or requires a material design change, do not silently choose an alternative. Report the exact conflict and continue only with independent valid work.

## 1. Repository Baseline

- [Issue #3](https://github.com/puchinya/ai-agent-project-template/issues/3) / [PR #4](https://github.com/puchinya/ai-agent-project-template/pull/4) は完了。変更は**新規Owning Issue**を `phase:requirements` から開始。`AGENTS.md` と `docs/agent-workflow/*.md` のIssue先行/承認/PR Gateを維持。
- 現行Owner: `docs/specs/agent-tooling-spec.md`（CLI・Docs/Template Update）、`docs/specs/project-profile-spec.md` / `docs/design/project-profile-context-design.md`（Schema 1/2、Context、Target、Hook）。不変条件は `specs→design→code/tests→status/evidence`、Owner一意、Schema 1互換、Host非永続、global→component→target順。
- `scripts/agent/agent_tool.py`: `cmd_context` (678–735) はIssueの `number,labels,url,body` だけ取得、`cmd_run_hook` (455–519) は逐次実行、`cmd_save_contract` (927–949) はローカルSHAミラー、`effective_checklist` / `cmd_validate_review` (797–925) はChecklistとReviewed-HEADを検査。実Evidenceの真偽は未検査。
- `.agent/project.json` はSchema 2、配布Starterは `initialized:false`（変更禁止）。`.agent/template-files.json` v0.5.0。既存 `scripts/agent/tests/test_{doc_validation,project_profile}.py`。PR #4は48件unittest成功と報告したがmacOS/arm64のみ。確認時 `.github/workflows/` とActions実行履歴はない。下流固有Profile/Spec/Design/Statusの上書きは禁止。

## 2. Architecture Decisions

**契約書の正本と節約:** Issue本文 `## Implementation Contract` には `Comment ID: <int>`、`SHA-256: <64hex>`、`State: approved` のみ。全文は当該Issueの**トップレベルコメント**1版1件。`.agent-state/issues/N/implementation-contract.md` は復元可能な検証済みミラー。コメント形式は `<!-- agent-contract:v1 issue=N sha256=64hex bytes=DECIMAL -->\n\n` + UTF-8原文。ハッシュ対象は原文bytes（改行も末尾も無断正規化禁止）、上限64KiB、NUL/明白な認証情報を拒否。Publish後に単一コメントをAPIで再取得し、所属Issue・長さ・SHAを検証してからIssueポインタ更新。Restoreも `gh api repos/OWNER/REPO/issues/comments/ID` **だけ**取得して検証後、一時ファイルからatomic replace。不正・不一致・既存ミラー衝突時はfail closed、既存bytes不変。通常 `agent-context` はコメント取得・全文出力なし（ポインタとローカルSHAのみ）。Legacyローカルのみは読み取り互換。

**版と競合:** 同一Issue+SHA publishは冪等。コメント作成後にポインタ更新が失敗してもコメントは残し、再試行で再利用。別SHAは承認済み原文を `--source PATH --supersede` で新コメントとして公開（旧版編集・削除禁止）。承認済みリモート版へのローカル更新は `restore --replace-stale` を明示し、旧ローカル版をSHA付きで退避してからatomic replace。Issue本文更新は直前再取得による競合検出と更新後readbackを行い、無関係セクションを保持する。GitHub側で厳密CAS不可なら同時Issue本文編集禁止と明記する。

**レビューとCI:** Self-review全文もPRの**トップレベル会話コメント**に公開。PR本文 `## Self-review` はComment ID/SHA/Reviewed-HEADのみ。公開前に既存 `validate-self-review` PASS必須、単一コメント取得で帰属/SHA/HEAD/Checklistを再確認する。新commitでstale、再レビュー・再公開。Evidenceはコード・テスト・CI run等を具体的に記すが、記入形式を真偽の証明と混同せず、別セッションのReviewerが独立検証する。CIは配布Starter未初期化のまま専用testを実行。PRイベントはread-only/Secretsなし。未信頼PRの任意Hookをwrite token付きで起動しない。Required Checks未設定/pending/failを成功扱いしない。

**TargetとContext:** Schema 2 Targetへ任意 `requirements:{architectures:string[],tools:string[],capabilities:string[]}` を追加。省略時は旧Schema 2互換。`runnable_on` OS→arch（AMD64/x86_64→x86_64、aarch64/arm64→arm64）→PATH上の `shutil.which`→明示 `--capability ID` の順に評価し、全条件一致時のみTarget Hook実行。不一致は `SKIPPED_TARGET_VERIFICATION component=... target=... reason=host_mismatch|architecture_mismatch|missing_tool|missing_capability`、非実行かつ未検証。Capability宣言は実機Evidenceの代用ではない。`run-hook verify_quick --issue N` はIssue `## Affected components` だけ、`--component` 併用不可。`verify_final` 無指定は全Component、Schema 1は従来どおり。`agent-context` はIssue `## Document impact` で**明示された同一Repo内** `docs/specs|design|status/*.md` の既存Ownerのみパス表示、予定は `planned_owner`、曖昧URLは診断。全文やコメント全件は展開しない。

**その他のGate:** `generic` は合法だがinit時に警告。Affected ComponentがgenericならPRに `Generic profile rationale:` の具体的確認理由を要求。Stack/HostからTypeを推測しない。Hookは信頼済み`.agent/project.json`にある任意Shellコマンドでありsandboxでないことを明記。Merge後closed Issueは `phase=closed` とし、merged/closed確認後に残る `phase:review` を冪等削除。既存完了Issueの一括修正は禁止。

拒否する方式: Issue/PR本文への全文貼付、コメント全件取得、外部DB/Gist必須化、要約Contractの正本化、Application Type別Workflow複製、未検証TargetのPASS化、Self-reviewを独立承認扱い。

## 3. Exact Change Set

`agent_tool.py` に以下のCLIを追加（既存CLIを破壊しない）。GitHubへの本文送信はJSON一時ファイルと引数配列で行い、原文をShell文字列に展開しない。

```text
save-implementation-contract N [path]      # 既存互換
publish-implementation-contract N [--source PATH] [--supersede]
restore-implementation-contract N [--replace-stale]
verify-implementation-contract N
publish-self-review N --pr P
validate-public-review N --pr P [--head 40hex]
delivery-check N --pr P --stage handoff|merged
finalize-merged-issue N --pr P
run-hook verify_quick --issue N [--capability ID ...]
run-hook verify_quick|verify_final [--component ID ...] [--capability ID ...]
```

- `delivery-check handoff`: 同一Repo/Issue、open/non-draft PR、本文 `Closes #N`、Issue `phase:review`、PR HEAD=公開Reviewed-HEAD、公開Checklist/SHA妥当、Verification/Untested欄記入、Required Checks greenを要求。`merged`: PR merged、Issue closed、旧phase labelなし。提出順は commit/push→Draft PR→Issue review→Self-review公開→Ready→CI green→handoff。PR作成は省略不可。
- `.github/workflows/template-ci.yml` 新規: `pull_request` と`main` push、Ubuntu Python 3.10/3.13、Windows/macOS Python 3.13。unittest、py_compile、validate-docs。PR metadata/Evidenceのread-only checkを別jobにし、DraftではReady用判定保留、Readyで必須。
- 新規 `docs/specs/agent-workflow-assurance-spec.md`（コメント/CLI/公開Evidence/Deliveryの観測契約）、`docs/design/agent-workflow-assurance-design.md`（正本/ミラー所有、失敗/版/競合、CI Trust Boundary）。Target/Owner routingは既存project-profile Spec/Designだけを更新。`agent-tooling-spec.md` は既存契約を保ち交差参照のみ。
- `AGENTS.md`、`docs/agent-workflow/{requirements,design,implementation,review,evidence,checkpoint}.md`、`README.AGENTS_WORKFLOW.md`、`scripts/agent/README.md` に運用順・復元・Trust・Context節約・Merge後処理を反映。Provider別 `CLAUDE.md` / `GEMINI.md` はRouter維持。新CLIの`.sh` / `.ps1` 薄いwrapperを対称追加。
- `.github/pull_request_template.md` にSelf-review/Generic rationale、`docs/{specs,design}/README.md` にOwner、`.agent/template-files.json` / `TEMPLATE_INVENTORY.md` に共有文書・wrapperを登録。下流固有 `.agent/project.json` / Spec/Design/Statusは管理対象に入れない。

## 4. Implementation Sequence

1. 新IssueへRequirements、Affected components、Document impact、Acceptance、第9節Checklistを登録。Spec→Designを承認・`validate-docs`後 `phase:ready`。
2. Contract codec/publish/restore、Contextポインタ/Owner、Issue Quickを実装。
3. PR Self-review公開・独立取得→Delivery→Merge後label処理を実装。
4. Target requirements・generic確認・Hook Trustを実装しSchema 1/旧Schema 2回帰。
5. 新Spec/Design、Wrapper、Docs、Manifest、Tests、CIを同期。Starter `initialized:false` 保持、下流 `update-template --check` で固有文書保護。
6. CI Matrix/Required Checksを実際に確認→commit/push→最新HEADでSelf-review再実施→PR Ready→Delivery Check。PR URLを提出。

## 5. Required Runtime Semantics

Publish部分失敗はコメントを保持して同SHAで再試行。API 403/404、所属/SHA不一致、ローカル衝突で既存ミラーは不変。Temp JSON/原文は成功・失敗・キャンセル時に清掃し、本文/Tokenを通常ログに出さない。同一Issueの公開操作は逐次、競合時停止。Target skipはHook非実行・未検証。新commitでReview stale。CI未実行はPASSにしない。`handoff` は実装完了、`merged` はIssue全体完了を判定する。

## 6. Non-goals / Forbidden Changes

Phase増設、Schema 1破壊、Hook順序変更、Host永続化、Application Type推測、常駐daemon/外部DB、コメント一括取得、全文/Logsの通常Context埋込、下流固有文書上書き、過去Issue一括修正は禁止。`pull_request_target` で未信頼PRコードをSecrets/write権限付き実行しない。

## 7. Concrete Tests

- 新 `scripts/agent/tests/test_contract_distribution.py`: UTF-8/CRLF/末尾改行byte一致、単一ID復元、同SHA冪等、コメント成功/ポインタ失敗から再試行、明示supersede、改変/別Issue/404/衝突時の**ミラー不変**、通常ContextのコメントAPI呼出し0。
- 新 `test_review_delivery.py`: Checklist変更・HEAD変更・公開SHA不正・Draft・`Closes`欠落・phase違い・Required Check未設定/pending/failを拒否、Valid handoff成功、merged後label清掃が反復安全。
- `test_project_profile.py`: Issue Quick限定、Final全体、排他、OS/arch/tool/capability mismatchで**コマンド実行0回**、capability明示時のみ実行、旧Schema 1/2互換、generic rationale有無。
- `test_doc_validation.py`: 新Schema 2文書、Owner Index、Manifest、Template Updateの固有文書保護。Fake gh/APIで試験しunit testはGitHub実書込を行わない。

## 8. Verification

```bash
python3 -B -m unittest discover -s scripts/agent/tests -p 'test_*.py'
python3 -m py_compile scripts/agent/agent_tool.py
python3 scripts/agent/agent_tool.py validate-docs
git diff --check
./scripts/agent/validate-self-review.sh <issue>
```

Windows PowerShell/macOS・Linux Bash wrapperも検証。`run-hook verify_final` は初期化済みfixtureで実行（Starterは未初期化）。CI Matrix実run、Required Check設定、未検証Platform/Targetを区別。VersionはIssueで確定し `refresh-template-manifest` を使う。

## 9. Reviewer Checklist（実装前に承認・公開。Issue側への同文重複は禁止）

- [ ] Issue先行、Spec→Design→Code→Evidence、Schema 1・既存CLI維持。
- [ ] Contract単一ID取得・原文byte/SHA/所属照合、失敗時ミラー不変、冪等・版更新・競合停止。
- [ ] 通常Contextにコメント全文/全件・大量Logsを含めず、Ownerは同一Repo内Pathのみ。
- [ ] 公開Self-reviewがChecklist/HEADと一致し、別セッションで検証可能。自己申告を独立承認扱いしない。
- [ ] CI Matrix/Required Checksの実効性、PR read-only/Secretsなし、未設定/pendingは失敗。
- [ ] Quick=Issue影響Component、Final既定=全Component、Target skipは非実行・未検証。
- [ ] generic確認、Hook Trust、Merge後phase清掃、Temp cleanup。
- [ ] Wrapper/Spec/Design/Index/Manifest/README/Tests整合、Starterと下流固有文書保護。
- [ ] 最新HEADで再レビューし、PR URL・CI結果・未検証環境を報告。

## 10. Completion Report / Gate

Issue URL、**PR URL（`Closes #N`）**、commit、変更ファイル、Checklist各結果/Evidence、全テスト/CI Matrix、Required Checks、未検証OS/Target、逸脱/残作業を報告。レビュー指摘は A=Contract違反、B=曖昧、C=新要件、D=任意改善で分類し、Cを無断追加しない。Commit/Push/PR/Issue `phase:review`/公開Self-review/Required Checks成功までImplementation未完了。Merge/Issue close/Label清掃まで全体未完了。認証・権限等の外部失敗は実CLI/APIエラーを示して **blocked** とする。
