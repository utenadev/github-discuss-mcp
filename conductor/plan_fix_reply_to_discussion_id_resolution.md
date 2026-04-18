# 計画: reply_to_discussion ツールの ID 解決ロジック改善と github_api.py の修復

**Issue ID:** bd-dkt.1 (コメントへの返信機能), bd-dkt.2 (階層構造の詳細取得)

**目的:**
`reply_to_discussion` ツールが、URL を介して古いディスカッションスレッド（#13 など）に対しても正しく返信できるように、ID 解決ロジックを改善する。また、以前の作業で破損した `src/github_discuss_mcp/github_api.py` を正常な状態に修復する。

**背景:**
現在の `reply_to_discussion` ツールは、最新の10件のディスカッションしか取得できないため、古いスレッドへの返信が失敗していました。また、以前のコード編集操作により `github_api.py` が破損しています。

**スコープ:**
*   `src/github_discuss_mcp/github_api.py`
*   `src/github_discuss_mcp/main.py`

**実装ステップ:**

1.  **`src/github_discuss_mcp/github_api.py` の修復:**
    *   `add_comment` メソッドを、`reply_to_id` 引数に対応し、かつ構文的に正しい状態に復旧させる。
    *   Mutation (`AddDiscussionComment`) および Variables の構造を正確に記述する。
    *   （既存の `get_discussions` などは影響を受けないように注意する）

2.  **`src/github_discuss_mcp/main.py` の `reply_to_discussion` ハンドラの修正:**
    *   `reply_to_id` 引数を受け取れるように、`call_tool` 関数および `reply_to_discussion` ツールのスキーマを更新する（必要であれば）。
    *   URL からディスカッション番号 (`(\d+)`) を正規表現で抽出し、`api.get_discussion_by_number()` を使用してディスカッション ID (Node ID) を取得するロジックを実装する。
    *   URL 解析に失敗した場合のフォールバック処理（現状の一覧検索）も保持する。

3.  **テスト:**
    *   `reply_to_discussion` ツールを用いて、古いスレッド URL (#13) への返信が成功することを確認する。
    *   `add_comment` の `reply_to_id` 引数を使用したネストされた返信のテストを行う（可能であれば）。

**検証:**
*   `reply_to_discussion` ツールが、古いスレッド URL でも正常に機能し、コメントが追加されることを確認する。
*   `github_api.py` が破損していないことを確認する。

**ロールバック戦略:**
*   `github_api.py` および `main.py` の変更を破棄し、以前の作業の状態に戻す。
