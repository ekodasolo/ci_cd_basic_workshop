# SPEC.md — ワークショップ仕様

## 概要

AWS CodeCommit / CodeBuild / CodePipeline を使ったCI/CDハンズオンワークショップ。
Python + AWS SAM で構築したサーバーレスAPIを題材に、パイプラインの構築と運用を体験する。

## ワークショップ構成

- 所要時間：4時間（座学1時間 + ハンズオン3時間）
- 形式：手順書ベースのハンズオン
- 対象者：CI/CDの基礎を学びたいエンジニア
- 手順書形式：マークダウン（スクリーンショットは後日追加）

### 座学パート（1時間）

1. SDLCの導入：なぜ素早いリリースと品質を両立させる仕組みが必要なのか
2. CI/CDプロセスの概要
3. CI: ビルド、テスト
4. CD: デプロイ
5. CI/CDパイプラインを実現するAWSサービスの説明
6. CodeCommitの基本機能
7. CodePipelineの基本機能

### 受講者の作業環境

- EC2上のCode Serverにリポジトリをクローンして作業する
- AWSアカウントは講師が事前に準備する

### 複数ユーザー共存

- 講師と受講者は同一AWSアカウント・同一リージョンで作業する想定
- リソース名衝突を避けるため、受講者ごとに `UserName`（英小文字＋数字、8文字以内）を決め、全リソース名のサフィックスとして付与する
- 事前構築テンプレート（setup.yaml）、SAMテンプレート（template.yaml）、および受講者が手で命名するリソース（CodeBuild プロジェクト / CodePipeline / デプロイ先 CFN スタック等）すべてで同じ `UserName` を使う

## アプリケーション仕様

### 都市情報API

都市の基本情報を返すREST API。レスポンスは固定のJSONデータ（DB不使用）。

- エンドポイント：`GET /cities` — 都市一覧を取得
- エンドポイント：`GET /cities/{city_id}` — 指定都市の情報を取得
- レスポンス例：

```json
{
  "city_id": "tokyo",
  "name": "東京",
  "population": 14000000,
  "region": "関東"
}
```

### 都市データ（段階的に追加）

ハンズオンの進行に合わせて都市を増やしていく：

1. 初期状態：東京、大阪
2. 開発パイプライン体験時に追加：名古屋
3. 本番パイプライン体験時に追加：福岡、札幌

### 技術スタック

- 言語：Python
- フレームワーク：AWS SAM（サーバーレス）
- ランタイム：API Gateway + Lambda
- テスト：pytest（ユニットテスト）

## パイプライン構成

### 開発パイプライン

```
CodeCommit (develop ブランチ push)
  → CodeBuild
      1. ユニットテスト実行（pytest）
      2. SAM build
      3. SAM package
  → CloudFormation デプロイ → 開発環境
```

### 本番パイプライン

```
CodeCommit (main ブランチ push)
  → CodeBuild
      1. ユニットテスト実行（pytest）
      2. SAM build
      3. SAM package
  → 手動承認
  → CloudFormation デプロイ → 本番環境
```

## ハンズオンの流れ

### Step 1：SAMアプリをローカルで動かす

- SAMプロジェクトの構成を理解する
- `sam local start-api` でローカル実行
- pytestでユニットテストを実行する

### Step 2：CodeCommitにpushする

- 事前準備済みのCodeCommitリポジトリにコードをpush
- ブランチ戦略（develop / main）を確認

### Step 3：開発パイプラインを構築する

- マネジメントコンソールでCodeBuildプロジェクトを作成
- CodePipelineで開発パイプラインを構築
- developブランチへのpushで自動デプロイされることを確認

### Step 4：本番パイプラインを構築する

- 手動承認ステージ付きの本番パイプラインを構築
- mainブランチへのpushでパイプラインが起動
- 承認フローを体験する

### Step 5：パイプラインの効果を体験する

- 都市データを追加してpush → 開発環境に自動反映
- わざとテストを失敗させて、パイプラインが止まることを確認
- テストを修正して再push → パイプラインが成功することを確認

## 事前準備（受講者の環境に構築済み）

- SAMアプリケーションのソースコード
- CodeCommitリポジトリ
- パイプライン用IAMロール等の基盤リソース
- buildspec.ymlの骨格（コメントとセクション構造のみ）

## 受講者が構築するもの

- buildspec.yml（骨格をベースに、手順書を見ながら写経で完成させる）
- CodeBuildプロジェクト（マネジメントコンソールで作成）
- CodePipeline（開発用・本番用、マネジメントコンソールで作成）
