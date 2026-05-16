# LOGS.md — 作業ログ

## 2026-05-10

### 実施内容

- ワークショップの仕様をブレストで決定し、SPEC.mdを作成した
- SPEC.mdに基づきシステム設計を行い、DESIGN.mdを作成した
- セルフレビューを実施し、設計から実装詳細を分離する修正を行った
- TASKS.mdを作成し、5つのタスクに分割した

### 決定事項

- アプリケーション：Python + AWS SAM による都市情報API（固定JSON、DB不使用）
- 環境分離：SAMテンプレートの `Environment` パラメータ（dev / prod）で制御
- パイプライン構成：CodeBuildでテスト・ビルド・パッケージ → CloudFormationデプロイアクションで適用
- 本番パイプラインには手動承認ステージを設ける
- buildspec.yml：骨格を提供し受講者が写経で完成させる。S3_BUCKET環境変数は受講者がCodeBuildプロジェクト作成時に設定
- 受講者の作業環境：EC2上のCode Server（スコープ外、講師が別途準備）
- 手順書形式：マークダウン（スクリーンショットは後日Yoheiが追加）
- 事前構築リソース（setup.yaml）：CodeCommitリポジトリ、S3バケット、IAMロール群
- EC2/Code Serverの構築はこのプロジェクトのスコープ外
- CodeBuildプロジェクトは環境ごとに1つ（計2つ）
- ここまでの変更はすべてdevelopブランチにマージ済み。次回はdevelopからfeatureブランチを切って作業する

## 2026-05-16

### 実施内容

- T1（SAMアプリケーション実装）を `feature/t1-sam-app` ブランチで実施
- ステアリングファイル `steering-t1-sam-app.md` を作成し、設計判断3点をYoheiレビューで決定
- `template.yaml`、`src/cities/{__init__.py,app.py,data.py}` を実装
- ローカル環境にSAM CLI／Python 3.12 venv／Docker を準備してもらい、SAM CLI実機検証を実施
- `sam validate --lint` / `sam build` / `sam local start-api` + curl 3パターンで動作確認、すべてパス

### 決定事項

- Lambda関数の構成：エンドポイントごとに別関数（`ListCitiesFunction` / `GetCityFunction`）。「1関数1責務」原則を受講者に伝えやすいことを優先
- 初期データ：東京・大阪のみ。名古屋・福岡・札幌はハンズオン中に受講者が追加する流れ（SPEC.mdに従う）
- API Gateway ステージ名：`${Environment}`（dev / prod）をそのまま使用
- コード配置：2関数とも `CodeUri: src/cities/` を共有し `Handler` だけ変える。`data.py` を関数間で共有しつつ Lambda Layer を導入しない（ワークショップの学習対象から外れるノイズを避けるため）
- `sam local start-api` ハマりポイント：AWS SSOセッション期限切れ時、SAM CLIがLambdaコンテナへcredentials注入で失敗し502。今回のLambdaはAWS APIを呼ばないので、`AWS_ACCESS_KEY_ID=dummy AWS_SECRET_ACCESS_KEY=dummy` を渡して回避可能。T5手順書での扱いは別途検討
- `.gitignore` に `.aws-sam/`、`__pycache__/`、`*.pyc` を追加（ビルド生成物・キャッシュ）

### 実施内容（プロジェクト構造の整理）

- T2以降で増えるファイルに備えてルート直下を整理（`feature/restructure-docs` ブランチ）
- `SPEC/DESIGN/TASKS/LOGS.md` を `docs/` 配下に移動
- `steering-t1-sam-app.md` を `steering/` 配下に移動
- 受講者向けコンテンツ置き場を `docs/handson/` から `handson/`（リポジトリ直下）に変更（実体はT5で作成）
- `CLAUDE.md` にドキュメント配置セクションを新設し、各ファイル参照のパスを更新
- `docs/DESIGN.md` のリポジトリ構造定義（ツリー・役割・配置ルール）を刷新

### 決定事項（プロジェクト構造）

- プロジェクト製作者向けドキュメント（仕様・設計・タスク・ログ）は `docs/` 配下に集約
- ワークショップ受講者向けコンテンツ（ハンズオン手順書）は `handson/` 配下に配置。製作者向けと受講者向けを別ディレクトリで明確に分離する方針
- 個別タスクのステアリングファイルは `steering/` 配下に集約（`tasks/` 案より、内容と一致する `steering/` を採用）
- `CLAUDE.md` だけは Claude Code が自動読み込みする都合上ルート配置を維持

### 実施内容（T2: ユニットテスト実装）

- T2 を `feature/t2-tests` ブランチで実施
- ステアリングファイル `steering/steering-t2-tests.md` を作成し、設計判断3点をYoheiレビューで決定
- `pytest.ini`、`tests/{__init__.py,requirements.txt,test_cities.py}` を実装
- `pytest -v` で 3 passed を確認

### 決定事項（T2）

- pytest設定ファイルは `pytest.ini` を採用（`pyproject.toml` 等は導入しない）
- pytest が `app.py` をインポートできるよう `pytest.ini` に `pythonpath = src/cities` を宣言
- 都市数のアサートは `> 0` でゆるく見る。ワークショップでのテストの主眼は仕組み・考え方に慣れることで網羅性ではない（受講者が `nagoya` 等を追加してもテストが壊れない設計）
- テスト依存パッケージは `pytest` のみ。バージョンピンせず最新を取り込む
- `.gitignore` に `.pytest_cache/` を追加
