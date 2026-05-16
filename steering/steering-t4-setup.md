# steering-t4-setup.md — T4: 事前構築用CloudFormationテンプレート作成

## 要求内容

### 変更・追加する機能の説明

ハンズオン環境の事前構築用CloudFormationテンプレート `setup/setup.yaml` を作成する。
講師がワークショップ前に1回デプロイすることで、受講者が CodePipeline / CodeBuild の構築に集中できる土台が整う状態にする。

作成するリソース（`docs/DESIGN.md` 事前構築リソース設計に準拠）：

| リソース | 用途 |
|---|---|
| CodeCommitリポジトリ | ワークショップアプリのソースコード管理 |
| S3バケット | SAMアーティファクト格納（`sam package` の出力先） |
| IAMロール（CodeBuild用） | CodeBuildジョブが引き受ける |
| IAMロール（CodePipeline用） | CodePipelineが引き受ける |
| IAMロール（CloudFormation用） | デプロイ実行時にCloudFormationが引き受ける |

### 受け入れ条件

- `aws cloudformation deploy --template-file setup/setup.yaml --stack-name <name> --capabilities CAPABILITY_NAMED_IAM` 1コマンドで全リソースが作成できる
- 受講者が手順書のStep 2〜4で参照する情報（CodeCommitクローンURL、S3バケット名、各IAMロールARN）が Outputs に出力される
- CodeCommitリポジトリは空の状態で作成され、受講者が後から `git push` でアプリコードを入れられる
- 各IAMロールに `AssumeRolePolicyDocument` が適切に設定され、対応するAWSサービスから引き受け可能
- ワークショップ終了後、S3バケットを空にすればスタック削除でクリーンアップできる

### 制約事項

- CloudFormation テンプレート形式（YAML）
- 環境（dev/prod）はワークショップでは1つの講師AWSアカウント内に作るので、setup.yaml はその両方を共通インフラとして1つで賄う
- 絵文字は使用しない
- リソース命名は ProjectName / StackName 由来にして受講者が混乱しないようにする
- S3バケット名はグローバル一意のため、アカウントID＋リージョンを含めて衝突を避ける

## 変更内容の設計

### 実装アプローチ

#### パラメータ設計

| パラメータ | 型 | デフォルト | 用途 |
|---|---|---|---|
| `ProjectName` | String | `cities-api` | CodeCommitリポジトリ名、リソース命名のベース |

`Environment` パラメータは setup.yaml には不要。setup.yaml で作るのは「共通インフラ」で、環境分離は SAM テンプレート側の `Environment` パラメータで制御するため。

#### リソースの命名規則

- CodeCommitリポジトリ：`${ProjectName}`
- S3バケット：`${ProjectName}-artifacts-${AWS::AccountId}-${AWS::Region}`
- IAMロール（呼称はワークショップ全体で統一）：
  - **build-role**：`${ProjectName}-build-role`（CodeBuildが引き受ける）
  - **pipeline-role**：`${ProjectName}-pipeline-role`（CodePipelineが引き受ける）
  - **deploy-role**：`${ProjectName}-deploy-role`（CloudFormationが引き受け、SAM変換結果をデプロイする）

#### IAMロール設計

IAMポリシーの基本方針は **AWS Managed Policy を主体としつつ、必要部分のみ Inline Policy で補完**。理由：

- ワークショップの主眼はCI/CDパイプラインの構築・運用であり、IAM最小権限の設計演習ではない
- 一方で、`AdministratorAccess` だけだと「IAMで権限を絞れる」という事実を学習者に見せられない
- AWS Managed Policy で「サービス単位の権限」、Inline Policy で「リソース単位の権限」を見せるバランスを取る

##### build-role（CodeBuild用）

| 種別 | ポリシー | 用途 |
|---|---|---|
| AssumeRole | `codebuild.amazonaws.com` | CodeBuildが引き受け |
| Managed | `CloudWatchLogsFullAccess` | ビルドログ出力 |
| Inline | `s3:GetObject`, `s3:PutObject`, `s3:ListBucket` on artifact bucket | `sam package` の出力先 |

`sam build` 自体は CodeBuild の作業ディレクトリで完結するので AWS API は不要。`sam package` 時のみ S3 アップロードが必要。

##### pipeline-role（CodePipeline用）

| 種別 | ポリシー | 用途 |
|---|---|---|
| AssumeRole | `codepipeline.amazonaws.com` | CodePipelineが引き受け |
| Inline | CodeCommit: `GetBranch`, `GetCommit`, `GetUploadArchiveStatus`, `UploadArchive`, `GitPull` | Sourceステージでのコード取得 |
| Inline | CodeBuild: `BatchGetBuilds`, `StartBuild` | Buildステージのトリガ |
| Inline | S3: `GetObject`, `PutObject`, `GetObjectVersion`, `ListBucket` on artifact bucket | アーティファクト授受 |
| Inline | CloudFormation: `CreateStack`, `UpdateStack`, `DeleteStack`, `DescribeStacks`, `CreateChangeSet`, `ExecuteChangeSet`, `DeleteChangeSet`, `DescribeChangeSet`, `SetStackPolicy` | Deployステージ |
| Inline | `iam:PassRole` on deploy-role | CloudFormationスタック実行時にロールを渡す |

CodeCommit にもManaged Policyはあるが（`AWSCodeCommitPowerUser` 等）、CodePipeline が必要なのは限定的なオペレーションだけなので Inline でリソース指定する形を選ぶ。学習素材として「リソースARNでスコープを絞る」が見える。

##### deploy-role（CloudFormation用）

| 種別 | ポリシー | 用途 |
|---|---|---|
| AssumeRole | `cloudformation.amazonaws.com` | CloudFormationが引き受け |
| Managed | `AWSLambda_FullAccess` | Lambda関数の作成・更新 |
| Managed | `AmazonAPIGatewayAdministrator` | API Gatewayの作成・更新 |
| Managed | `AWSCloudFormationFullAccess` | スタック内のネストリソース管理 |
| Inline | S3: `GetObject` on artifact bucket | packaged.yaml の取得 |
| Inline | IAM: アクションを以下に列挙、Resource: `*` | SAMがLambda実行ロールを動的生成するため |

deploy-role の IAM Inline Policy のアクション一覧（`IAMFullAccess` ではなく明示列挙）：

```
iam:CreateRole, iam:DeleteRole, iam:GetRole, iam:PassRole,
iam:AttachRolePolicy, iam:DetachRolePolicy,
iam:PutRolePolicy, iam:DeleteRolePolicy,
iam:TagRole, iam:UntagRole,
iam:UpdateAssumeRolePolicy
```

Resource は `*`（SAMが動的生成するLambda実行ロール名が事前に決まらないため）。Action 側で絞ることで「IAMでも個別アクションを列挙してスコープを絞れる」が学習素材として見える。

#### S3バケット設計

- バージョニング：有効（CodePipeline がアーティファクトのバージョンを使うため）
- 暗号化：S3標準（SSE-S3）
- パブリックアクセス：すべてブロック
- ライフサイクル：90日後に旧バージョン削除（ワークショップ後のクリーンアップを意識）
- DeletionPolicy: `Delete`（手順書で「バケットを空にしてからスタック削除」を案内）

#### CodeCommit設計

- リポジトリ名：`${ProjectName}`
- 初期コミット：なし（受講者が `git push` するため）
- DeletionPolicy: `Delete`

#### Outputs

受講者が手順書で参照する情報を出力：

| 出力名 | 値 |
|---|---|
| `CodeCommitCloneUrlHttp` | CodeCommitのHTTPSクローンURL |
| `CodeCommitRepositoryName` | リポジトリ名 |
| `ArtifactsBucketName` | S3バケット名 |
| `BuildRoleArn` | build-role の ARN |
| `PipelineRoleArn` | pipeline-role の ARN |
| `DeployRoleArn` | deploy-role の ARN |

### 変更するコンポーネント

| 区分 | パス | 種別 |
|---|---|---|
| 新規 | `setup/setup.yaml` | CloudFormationテンプレート |

### データ構造の変更

なし。既存ファイルには手を入れない。

### 影響範囲の分析

- T1〜T3成果物への影響：なし
- T5（手順書）への影響：
  - Step 1の前段で「講師が事前に setup.yaml をデプロイした」という前提を書く
  - Step 2 で CodeCommit クローン → push 手順がOutputs の CloneURL を参照する
  - Step 3 で CodeBuildプロジェクト作成時、本タスクで作る `CodeBuildRoleArn` と `ArtifactsBucketName` を `S3_BUCKET` 環境変数に設定する
  - Step 3/4 で CodePipeline 作成時、`CodePipelineRoleArn`、`CloudFormationRoleArn` を使う

## タスクリスト

### 詳細実装タスク

- [x] T4-1: `setup/` ディレクトリを作成
- [x] T4-2: `setup/setup.yaml` のスケルトン（Parameters / Resources / Outputs セクション）を作成
- [x] T4-3: CodeCommitリポジトリリソースを実装
- [x] T4-4: S3バケットリソースを実装（バージョニング・暗号化・パブリックアクセスブロック・ライフサイクル）
- [x] T4-5: build-role を実装
- [x] T4-6: pipeline-role を実装
- [x] T4-7: deploy-role を実装（IAMアクションは列挙形式で絞り込む）
- [x] T4-8: Outputs を実装
- [x] T4-9: `cfn-lint` で静的検証
- [-] T4-10: `aws cloudformation validate-template` はAWS SSOセッション期限切れのためスキップ（Yoheiの環境で再認証後に確認）
- [x] T4-11: `docs/TASKS.md` のT4ステータスを `[!]` レビュー待ちに更新

### 検証結果（2026-05-16）

| 検証 | 結果 |
|---|---|
| `cfn-lint setup/setup.yaml` | エラー・警告なし |
| `aws cloudformation validate-template` | AWS SSOセッション期限切れのためスキップ（Yoheiの環境で再認証後に実施推奨） |

### 補足

- `safe_load` での YAML パース確認は CFN intrinsic タグ（`!GetAtt` 等）を解釈できないためスキップし、`cfn-lint` での検証に統一した
- `cfn-lint` は CloudFormation スキーマ・ベストプラクティスを含めて検証するため、純粋な YAML 構文確認より強い保証になっている

### 完了条件

- 上記すべてのタスクが完了している
- `validate-template` が成功する
- Yoheiのレビューで承認を得ている
- 実際のAWSアカウントへのデプロイテストは Yohei が必要に応じて別途実施（CodeCommit作成等が伴い、コスト・残骸の観点で本タスクの完了条件には含めない）

## 設計判断の決定事項（2026-05-16 Yoheiレビュー）

| 論点 | 決定 |
|---|---|
| IAMポリシーの粒度方針 | AWS Managed Policy 主体 + 必要部分のみ Inline |
| 環境分離（dev/prod）リソースの扱い | 共通インフラ1セット（CodeBuildロール・S3バケットもdev/prod共通） |
| CodeCommitリポジトリ名のパラメータ化 | `ProjectName` パラメータ（デフォルト `cities-api`） |
| S3バケットのクリーンアップ方針 | `DeletionPolicy: Delete` + 手順書で空化を案内 |
| deploy-role の IAM権限の広さ | `IAMFullAccess` は使わず、必要なIAMアクションを列挙する Inline Policy で絞る |
| IAMロールの呼称 | build-role / pipeline-role / deploy-role（プロジェクト全体で統一） |
