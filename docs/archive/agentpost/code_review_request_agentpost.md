# Code Review 依頼：AgentPost システム

**日付**: 2026-04-19  
**レビュー担当**: Gemini  
**作成**: Qwen

---

## 📋 概要

github-discuss-mcp プロジェクトに新規実装した **AgentPost システム** のコードレビューをお願いします。

AgentPost は tmux 上で動作する AI Coding Agent 間の非同期メッセージングシステムです。

---

## 📁 レビュー対象ファイル

### 主要コード

| ファイル | 行数 | 説明 |
|---------|------|------|
| `agentpost.py` | ~380 行 | CLI & コアエンジン |
| `skill/agentpost.py` | ~20 行 | AI CodingAgent 向けスキル |
| `install.sh` | ~40 行 | インストールスクリプト |

### テストコード

| ファイル | 行数 | 説明 |
|---------|------|------|
| `tests/agentpost/conftest.py` | ~130 行 | 共通フィクスチャ |
| `tests/agentpost/test_agentpost_core.py` | ~180 行 | コア機能テスト |
| `tests/agentpost/test_agentpost_cli.py` | ~115 行 | CLI コマンドテスト |
| `tests/agentpost/test_agentpost_skill.py` | ~70 行 | スキルテスト |

---

## 🎯 レビューポイント

### 1. セキュリティ

- [ ] ファイルパーミッション（0o600）は適切か
- [ ] 環境変数の扱いは安全か
- [ ] ファイルロックの実装は適切か

### 2. エラーハンドリング

- [ ] 例外処理は十分か
- [ ] エラーメッセージは分かりやすいか
- [ ] 予期せぬ入力への対応は十分か

### 3. コード品質

- [ ] 関数の責務は単一か
- [ ] 変数名・関数名は適切か
- [ ] ドキュメント/コメントは十分か

### 4. テスト

- [ ] テストカバレッジは十分か
- [ ] テストの独立性は保たれているか
- [ ] 境界値テストは十分か

### 5. パフォーマンス

- [ ] ポーリング間隔（0.5 秒）は適切か
- [ ] ファイル I/O は最適化されているか
- [ ] メモリリークのリスクはないか

---

## 🐛 既知の問題

### 1. ログコマンドのテスト困難

`cmd_log()` 関数が `LOG_FILE` を直接参照するため、テストでモック化が困難。

**現状**: テストをスキップ

**提案**: 
- `LOG_FILE` をモジュール変数ではなく引数で渡すように変更
- または、ロギングを抽象化する

### 2. BASE_DIR のテストでの扱い

テスト中に `agentpost.BASE_DIR` を書き換えているが、これはグローバル状態。

**現状**: `temp_agentpost_dir` フィクスチャで元に戻している

**提案**: 
- `BASE_DIR` を引数で渡すように変更
- または、依存性注入パターンを使用

---

## 📊 テスト結果

```
======================== 12 passed, 2 skipped in 0.10s =========================

tests/agentpost/test_agentpost_cli.py::TestSetupCommand
  ✓ test_setup_command_shows_detected_agents
  ✓ test_setup_command_accepts_input
  ✓ test_status_command_shows_agents
  ⊘ test_log_command_shows_recent_logs (skipped)
  ⊘ test_log_command_no_logs (skipped)

tests/agentpost/test_agentpost_core.py::TestPostMessage
  ✓ test_post_message
  ✓ test_post_with_ref

tests/agentpost/test_agentpost_core.py::TestCheckMessages
  ✓ test_check_empty_inbox

tests/agentpost/test_agentpost_core.py::TestConfigManagement
  ✓ test_save_config_creates_directory
  ✓ test_save_config_permissions

tests/agentpost/test_agentpost_core.py::TestAgentDetection
  ✓ test_detect_agents_with_pipe_format

tests/agentpost/test_agentpost_skill.py::TestSkillImport
  ✓ test_skill_import
  ✓ test_skill_exports

tests/agentpost/test_agentpost_skill.py::TestSkillPost
  ✓ test_skill_post_with_env
```

---

## 🔍 重点レビュー項目

### 1. `agentpost.py` の `detect_agents()` 関数

```python
def detect_agents() -> List[dict]:
    # パイプ区切りで確実に分割（コマンド/ウィンドウ名にスペースが含まれても安全）
    fmt = "#{session_name}|#{window_index}|#{pane_index}|#{window_name}|#{pane_current_command}|#{pane_title}"
    raw = tmux_cmd(["list-panes", "-a", "-F", fmt])
    ...
```

**質問**:
- tmux の出力フォーマットは環境によって変わる可能性はないか？
- エージェント名の検出ロジック（"qwen" in combined）は十分か？

### 2. `agentpost.py` の `cmd_setup()` 関数

```python
def cmd_setup(args):
    ...
    while True:
        try:
            line = input("   Agent (or Enter to finish): ").strip()
        except EOFError:
            break
```

**質問**:
- 入力フォーマットのバリデーションは十分か？
- `session.window.pane` 形式（例：`1.1.1`）にも対応すべきか？

### 3. `agentpost.py` の `process_inbox()` 関数

```python
def process_inbox(agent: str, mark_read: bool = True) -> List[dict]:
    ...
    for f in sorted(inbox.glob("*.json")):
        if f.name.startswith("."): continue
        try:
            with open(f, "r", encoding="utf-8") as fh: msg = json.load(fh)
            ts = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - ts).total_seconds() > msg.get("ttl_seconds", 86400):
                f.unlink(); continue
            os.rename(f, proc / f.name)
            ...
```

**質問**:
- TTL の計算は正しいか（UTC 時間の扱い）
- `processing/` への移動と `archive/` への移動の原子性は保証されているか

---

## 📝 レビューフォーマット

以下のフォーマットで bd-1px に報告をお願いします：

```markdown
## Code Review 結果：AgentPost システム

### ✅ 良かった点
- 

### ⚠️ 改善提案
- 

### ❌ 問題点（あれば）
- 

### 📊 総合評価（1-10）
- 

### 🔍 追加テストが必要な箇所
- 
```

---

## 📚 参考資料

- [AgentPost 仕様書](docs/AgentPost_spec_and_source.md)
- [ONBOARDING.md](docs/ONBOARDING.md)
- [README_AGENTPOST.md](README_AGENTPOST.md)（削除済み）

---

**レビューをお願いします！**
