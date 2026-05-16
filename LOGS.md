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
