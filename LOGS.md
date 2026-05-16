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
