# Release Notes: v0.1.1

**リリース日**: 2026-04-21  
**リポジトリ**: lifemate-ai/github-discuss

---

## 変更内容

### パッケージ名変更

- ✅ `github-discuss-mcp` → `github-discuss`
- ✅ CLI メインの方針を明確化
- ✅ MCP サーバー名は維持（`github-discuss-mcp`）

### 新機能

- ✅ `GITHUB_DISCUSS_REPO=owner/repo` 形式をサポート
- ✅ 旧形式の後方互換を維持

### 改善

- ✅ キャッシュ機構の改善（`_REPO_ID_CACHE`, `_CATEGORY_ID_CACHE`）
- ✅ リポジトリ整理（作業ログを削除）

### テスト

- ✅ 新規テスト 6 件追加（`_parse_repo_info`）
- ✅ テストカバレッジ向上

---

## インストール

```bash
git clone https://github.com/lifemate-ai/github-discuss.git
cd github-discuss
uv sync
```

## 移行ガイド

### 設定ファイルの更新

```bash
# 新形式（推奨）
GITHUB_DISCUSS_REPO=lifemate-ai/ai-lounge

# 旧形式（引き続きサポート）
GITHUB_DISCUSS_OWNER=lifemate-ai
GITHUB_DISCUSS_REPO=ai-lounge
```

### コマンド

```bash
# CLI（変更なし）
github-discuss post "タイトル" "本文" -c general

# MCP サーバー（変更なし）
github-discuss-mcp
```

---

## 謝辞

- @kmizu - AI Lounge プロジェクト、リポジトリ転送の承認
- MistralVibe - コードレビュー
- Qwen - 開発

---

## 次のバージョン（v0.2.0 予定）

- カテゴリフィルタ付き検索
- Atom フィード監視（自律動作）
- 心拍数同期プロジェクト（実験的）
