# CI/CDハンズオン

AWS CodeCommit / CodeBuild / CodePipeline を使って、Python + AWS SAM 製の都市情報APIを継続的にデプロイするパイプラインを構築・運用するハンズオンです。

## このハンズオンで体験すること

- ローカルでSAMアプリを動かしテストする
- CodeCommitにコードをpushし、ブランチで開発環境と本番環境を分離する
- 開発パイプライン（develop → 開発環境への自動デプロイ）を構築する
- 本番パイプライン（main → 手動承認 → 本番環境）を構築する
- 都市データの追加・テスト失敗・テスト修正を通じてパイプラインの効果を体感する

## 全体構成と所要時間

| Step | 内容 | 所要時間目安 |
|---|---|---|
| [Step 1](step1.md) | SAMアプリをローカルで動かす | 約30分 |
| [Step 2](step2.md) | CodeCommitにpushする | 約20分 |
| [Step 3](step3.md) | 開発パイプラインを構築する | 約60分 |
| [Step 4](step4.md) | 本番パイプラインを構築する | 約40分 |
| [Step 5](step5.md) | パイプラインの効果を体験する | 約30分 |
| 合計 | | 約180分 |

ハンズオン完了後は [cleanup.md](cleanup.md) に従い、作成したAWSリソースを必ずクリーンアップしてください。

## 前提

- 受講者はEC2上のCode Server（または同等の作業環境）にアクセスできること
- 講師が事前に `setup.yaml` をデプロイし、CodeCommitリポジトリ、S3バケット、IAMロール3種を作成していること
- AWS CLI、SAM CLI、Python 3.12、Docker、Git が作業環境にインストールされていること

## 事前構築リソースの確認

ハンズオンを始める前に、以下の情報を講師から受け取るか、CloudFormationの事前構築スタックの **Outputs** タブから確認してください。各Stepで参照します。

| 項目 | 取得元（Outputs名） |
|---|---|
| CodeCommitクローンURL | `CodeCommitCloneUrlHttp` |
| CodeCommitリポジトリ名 | `CodeCommitRepositoryName` |
| アーティファクトS3バケット名 | `ArtifactsBucketName` |
| build-role の ARN | `BuildRoleArn` |
| pipeline-role の ARN | `PipelineRoleArn` |
| deploy-role の ARN | `DeployRoleArn` |

## 用語

| 用語 | 意味 |
|---|---|
| **build-role** | CodeBuild が引き受けるIAMロール |
| **pipeline-role** | CodePipeline が引き受けるIAMロール |
| **deploy-role** | CloudFormation がデプロイ実行時に引き受けるIAMロール |
| **開発環境** | developブランチへのpushでデプロイされるAWS環境（リソース名サフィックス `-dev`） |
| **本番環境** | mainブランチへのpushでデプロイされるAWS環境（リソース名サフィックス `-prod`） |
