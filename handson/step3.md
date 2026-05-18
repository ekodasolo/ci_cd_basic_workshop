# Step 3: 開発パイプラインを構築する

## このStepの目的

`develop` ブランチへのpushをトリガに、テスト・SAMビルド・パッケージ・CloudFormationデプロイまでを自動実行する開発パイプラインを構築します。受講者がリポジトリ内の `buildspec.yml` を写経で完成させる工程も含みます。

## 所要時間

約60分

## 前提

- Step 2 が完了している（`develop` ブランチに push 済み）
- 事前構築リソース（build-role / pipeline-role / deploy-role、アーティファクトS3バケット）が作成済み

## このStepのゴール

- `buildspec.yml` の `pre_build` / `build` フェーズを写経で完成させ、developブランチにpushしている
- CodeBuildプロジェクト（開発環境用）を作成している
- CodePipelineの開発パイプライン（Source / Build / Deploy）を作成している
- `develop` ブランチへのpushでパイプラインが起動し、開発環境にデプロイされることを確認している
- 開発環境のAPIエンドポイントに curl して期待どおりのレスポンスを得ている

## 手順

### 1. buildspec.yml を写経で完成させる

Step 2 でpushした `buildspec.yml` は骨格版で、`pre_build` と `build` の commands が `echo "TODO: ..."` のままになっています。これを完成形に書き換えます。

完成形は同リポジトリの `buildspec_complete.yml` を参考にしてもよいですが、コマンドの意味を意識しながら手で書くのがおすすめです。

`buildspec.yml` を以下のように編集します：

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.12

  pre_build:
    commands:
      - pip install -r tests/requirements.txt
      - python -m pytest tests/

  build:
    commands:
      - sam build
      - sam package --s3-bucket ${S3_BUCKET} --output-template-file packaged.yaml

artifacts:
  files:
    - packaged.yaml
```

**各コマンドの意味：**

| コマンド | 役割 |
|---|---|
| `pip install -r tests/requirements.txt` | pytestをインストール |
| `python -m pytest tests/` | ユニットテストを実行。失敗するとビルドも失敗しパイプラインが止まる |
| `sam build` | Lambda関数のビルド成果物を `.aws-sam/build/` に生成 |
| `sam package --s3-bucket ${S3_BUCKET} --output-template-file packaged.yaml` | ビルド成果物をS3にアップロードし、デプロイ可能な`packaged.yaml`を出力 |

`${S3_BUCKET}` はCodeBuildプロジェクトの環境変数として後で設定します。

編集が終わったら develop ブランチにcommit & pushします：

```bash
git add buildspec.yml
git commit -m "Complete buildspec.yml"
git push origin develop
```

### 2. CodeBuildプロジェクトを作成する（開発環境用）

1. AWSマネジメントコンソールで **CodeBuild** を開きます
2. 左ナビ：**Build projects** → **Create project** をクリック
3. 以下を設定します：

   **Project configuration**
   - **Project name**: `cities-api-build-dev`
   - **Description**: （任意）

   **Source**
   - **Source provider**: AWS CodeCommit
   - **Repository**: `cities-api`
   - **Reference type**: Branch
   - **Branch**: `develop`

   **Environment**
   - **Provisioning model**: On-demand
   - **Environment image**: Managed image
   - **Operating system**: Amazon Linux
   - **Runtime(s)**: Standard
   - **Image**: 最新のaws/codebuild/amazonlinux2-x86_64-standardイメージを選択
   - **Service role**: **Existing service role** を選択 → ロール名から `cities-api-build-role` を選択
   - **Allow AWS CodeBuild to modify this service role so it can be used with this build project** のチェックを **外す**（既存ロールをそのまま使うため）

   **Additional configuration**（Environment内）
   - **Environment variables**:
     - Name: `S3_BUCKET` / Value: `ArtifactsBucketName`（Outputsの値）

   **Buildspec**
   - **Build specifications**: Use a buildspec file
   - **Buildspec name**: `buildspec.yml`（リポジトリルートの buildspec.yml）

   **Artifacts**
   - **Type**: No artifacts（CodePipelineが生成物を扱うため、ここではNo artifactsでOK）

   **Logs**
   - **CloudWatch logs**: 有効のまま

4. **Create build project** をクリック

<!-- screenshot: CodeBuildプロジェクト作成画面 / Environment変数セクション -->

### 3. CodePipeline（開発パイプライン）を作成する

1. AWSマネジメントコンソールで **CodePipeline** を開きます
2. **Create pipeline** をクリック
3. **Category**: Build costom pipeline を選んで次へ

   **Step 1: Choose pipeline settings**
   - **Pipeline name**: `cities-api-pipeline-dev`
   - **Service role**: **Existing service role** を選択 → ロール名から `cities-api-pipeline-role` を選択
   - **Advanced settings**を展開し、 **Artifact store**: **Custom location** を選択 → Bucket に `cities-api-artifacts-<AccountID>-<Region>`（Outputsの `ArtifactsBucketName` の値）

   **Step 2: Add source stage**
   - **Source provider**: AWS CodeCommit
   - **Repository name**: `cities-api`
   - **Branch name**: `develop`
   - **Detection mode**: Amazon CloudWatch Events（推奨）

   **Step 3: Add build stage**
   - **Build provider**: AWS CodeBuild
   - **Project name**: `cities-api-build-dev`

   **Step 4: Add deploy stage**
   - **Deploy provider**: AWS CloudFormation
   - **Action mode**: Create or update a stack
   - **Stack name**: `cities-api-dev`
   - **Artifact name**: BuildArtifact
   - **Template file**: `BuildArtifact`の`packaged.yaml`
   - **Capabilities**: `CAPABILITY_IAM`（SAMが Lambda 実行ロールを作成するため必須）
   - **Role name**: ロール名から `cities-api-deploy-role` を選択（Outputsの `DeployRoleArn` の値）
   - **Advanced** セクションを開く：
     - **Parameter overrides**: `{"Environment": "dev"}`

4. **Create pipeline** をクリック

作成と同時に1回目のパイプライン実行が走ります。

<!-- screenshot: CodePipeline作成完了直後のパイプライン画面（3ステージが動いている様子） -->

### 4. パイプラインの実行状況を確認する

CodePipeline画面で `cities-api-pipeline-dev` を開き、各ステージの進捗を確認します：

- **Source**: 数十秒で Succeeded
- **Build**: 数分かかります。失敗する場合は CodeBuild の `View logs` でログを確認
- **Deploy**: CloudFormation が `cities-api-dev` スタックを作成・更新します

すべて Succeeded（緑）になれば開発環境にデプロイ完了です。

### 5. 開発環境のAPIエンドポイントを確認する

1. **CloudFormation** を開き、`cities-api-dev` スタック → **Outputs** タブ
2. `ApiEndpoint` の値（`https://xxxx.execute-api.region.amazonaws.com/dev` の形式）をコピー
3. ターミナルで curl してみます：

```bash
curl https://xxxx.execute-api.region.amazonaws.com/dev/cities
curl https://xxxx.execute-api.region.amazonaws.com/dev/cities/tokyo
```

Step 1 でローカル実行したときと同じレスポンスが返ればデプロイ成功です。

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| Build ステージが `AccessDenied` で失敗（S3関連） | build-role の Inline Policy が `ArtifactsBucket` に届いていない | 事前構築スタック側のIAM設定を講師に確認 |
| Build ステージが `pytest` でテスト失敗 | buildspec の commands が正しく写経できていない | `buildspec.yml` と `buildspec_complete.yml` を diff で比較 |
| Build ステージが `sam package` で `bucket does not exist` | CodeBuild の環境変数 `S3_BUCKET` の値が誤っている | プロジェクト設定 → Environment → Environment variables を再確認 |
| Deploy ステージが `is not authorized to perform: iam:CreateRole` | パイプラインの **Capabilities** に `CAPABILITY_IAM` が指定されていない | Deploy アクションを編集して `CAPABILITY_IAM` を追加 |
| Deploy ステージが `Template format error` | アーティファクト指定が誤っている | Template file が `packaged.yaml`、Artifact name が `BuildArtifact` か確認 |

## Stepのまとめ

- `buildspec.yml` を写経で完成させ、CodeBuildが何をするのか理解しました
- 開発環境用のCodeBuildプロジェクト・CodePipelineを構築しました
- 自動でテスト・ビルド・パッケージ・デプロイが流れる開発パイプラインができました
- `develop` ブランチへのpushで開発環境が更新される基盤が整いました

次は [Step 4](step4.md) で、`main` ブランチをトリガとする本番パイプライン（手動承認付き）を構築します。
