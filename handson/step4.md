# Step 4: 本番パイプラインを構築する

## このStepの目的

`main` ブランチへのpushをトリガに、本番環境（`cities-api-prod-<UserName>`）へデプロイする本番パイプラインを構築します。Step 3 の開発パイプラインとの大きな違いは、デプロイ前に **手動承認ステージ** が入る点で、本番反映を人間の判断で制御する仕組みを体験します。

## 所要時間

約40分

## 前提

- Step 3 が完了し、開発パイプラインが動作している
- `main` ブランチに Step 2 でpushしたコードが揃っている

## このStepのゴール

- 本番用のCodeBuildプロジェクトを作成している
- 手動承認ステージを含む本番CodePipelineを作成している
- `main` ブランチへのpushでパイプラインが起動し、承認待ち状態になる
- 承認を行うと本番環境にデプロイされ、curlで応答が確認できる

## 手順

### 1. develop ブランチの変更を main にマージする

Step 3 で `buildspec.yml` を完成させた変更が `develop` にのみ反映されています。本番パイプラインで使えるよう `main` にもマージします：

```bash
git switch main
git merge develop
git push origin main
```

この時点ではまだ本番パイプラインを作っていないので、pushしてもデプロイは走りません。

### 2. CodeBuildプロジェクトを作成する（本番環境用）

Step 3 の手順とほぼ同じですが、名前とブランチが異なります。

1. AWSマネジメントコンソールで **CodeBuild** → **Create project**
2. 以下を設定（Step 3 と異なる箇所のみ太字）：
   - **Project name**: **`cities-api-build-prod-<UserName>`**
   - **Source provider**: AWS CodeCommit
   - **Repository**: `cities-api-<UserName>`
   - **Branch**: **`main`**
   - **Environment image**: Step 3 と同じ Amazon Linux 2 / Standard / 最新イメージ
   - **Service role**: Existing service role → `cities-api-build-role-<UserName>`
   - **Environment variables**:
     - Name: `S3_BUCKET` / Value: Outputsの `ArtifactsBucketName` の値
   - **Buildspec name**: `buildspec.yml`
   - **Artifacts**: No artifacts
3. **Create build project** をクリック

build-role / S3バケットは開発環境と共通なので、新しいIAMロールやバケットを作る必要はありません。

### 3. CodePipeline（本番パイプライン）を作成する

1. AWSマネジメントコンソールで **CodePipeline** → **Create pipeline**

   **Step 1: Choose pipeline settings**
   - **Pipeline name**: `cities-api-pipeline-prod-<UserName>`
   - **Service role**: Existing service role → `cities-api-pipeline-role-<UserName>`
   - **Artifact store**: Custom location → Outputsの `ArtifactsBucketName` の値

   **Step 2: Add source stage**
   - **Source provider**: AWS CodeCommit
   - **Repository name**: `cities-api-<UserName>`
   - **Branch name**: **`main`**

   **Step 3: Add build stage**
   - **Build provider**: AWS CodeBuild
   - **Project name**: **`cities-api-build-prod-<UserName>`**

   **Step 4: Add deploy stage**
   - **Deploy provider**: AWS CloudFormation
   - **Action mode**: Create or update a stack
   - **Stack name**: **`cities-api-prod-<UserName>`**
   - **Artifact name**: BuildArtifact
   - **Template file**: `packaged.yaml`
   - **Capabilities**: `CAPABILITY_IAM`
   - **Role name**: `cities-api-deploy-role-<UserName>`
   - **Parameter overrides**: **`{ "Environment": "prod", "UserName": "<UserName>" }`**

2. **Create pipeline** をクリック

### 4. 手動承認ステージを追加する

パイプライン作成直後はSource → Build → Deployの3ステージしかありません。Build と Deploy の間に手動承認ステージを差し込みます。

1. 作成した `cities-api-pipeline-prod-<UserName>` の画面で右上の **Edit** をクリック
2. Build ステージと Deploy ステージの間にある **+ Add stage** をクリック
3. **Stage name**: `Approval` を入力 → **Add stage**
4. 新しいApprovalステージの中で **+ Add action group** をクリック
5. 以下を設定：
   - **Action name**: `ManualApproval`
   - **Action provider**: Manual approval
   - **Comments**（任意）: `本番デプロイの承認をお願いします`
6. **Done** → 画面上部の **Save** をクリック

<!-- screenshot: パイプライン編集画面で手動承認ステージを追加した直後の構成図 -->

### 5. main ブランチに push してパイプラインを起動する

軽い変更を加えてpushしてみます。たとえば README の末尾に1行追加するなど、機能に影響しない変更で構いません：

```bash
echo "" >> README.md
git add README.md
git commit -m "Trigger prod pipeline"
git push origin main
```

`cities-api-pipeline-prod-<UserName>` 画面に戻ると：

- **Source**: Succeeded
- **Build**: 実行中 → Succeeded
- **Approval**: **In Progress**

### 6. 承認して本番デプロイを実行する

1. Approval ステージの **ManualApproval** をクリック
2. ダイアログで **Approve** を選択（必要ならコメントを入力）
3. **Submit** をクリック

承認後、Deploy ステージが動き出し、CloudFormation が `cities-api-prod-<UserName>` スタックを作成します。

<!-- screenshot: 手動承認ダイアログ（Approve/Reject選択画面） -->

### 7. 本番環境のAPIエンドポイントを確認する

1. **CloudFormation** → `cities-api-prod-<UserName>` スタック → **Outputs** タブ
2. `ApiEndpoint` の値をコピー
3. curlで動作確認：

```bash
curl https://yyyy.execute-api.region.amazonaws.com/prod/cities
curl https://yyyy.execute-api.region.amazonaws.com/prod/cities/tokyo
```

開発環境とは別のURLで同じレスポンスが返れば本番デプロイ成功です。

## 開発パイプラインとの違い

| 項目 | 開発パイプライン | 本番パイプライン |
|---|---|---|
| Source ブランチ | develop | main |
| CodeBuildプロジェクト | cities-api-build-dev-&lt;UserName&gt; | cities-api-build-prod-&lt;UserName&gt; |
| CloudFormationスタック | cities-api-dev-&lt;UserName&gt; | cities-api-prod-&lt;UserName&gt; |
| Environment パラメータ | dev | prod |
| UserName パラメータ | 自分のUserName | 自分のUserName（同じ値） |
| 手動承認ステージ | なし | あり |

「人間の判断を挟むかどうか」だけで、自動化のメリットを残しつつ本番反映の安全性を高められるのが手動承認ステージの効用です。

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| Approvalステージで承認ボタンが押せない | 承認担当者のIAMユーザーに `codepipeline:PutApprovalResult` 権限がない | 自分のIAMユーザーに該当ポリシーを付与（講師に相談） |
| Approval後にDeployが `AccessDenied` | deploy-role の権限不足 | 事前構築スタックのIAM設定を講師に確認 |
| `cities-api-prod-<UserName>` スタックがロールバックされる | SAMテンプレートのリソース命名衝突（dev/prodで同名リソース、または他ユーザーのリソース名と衝突） | `template.yaml` の `FunctionName` などに `${Environment}` と `${UserName}` の両方が含まれているか、また `Parameter overrides` で正しい `UserName` を渡しているか確認 |
| Parameter overrides が反映されない | `Environment`/`UserName` のスペルミス、引用符の付け方、または JSON 構文エラー | `{ "Environment": "prod", "UserName": "<UserName>" }` の形式を再確認（キーは大文字小文字一致、`UserName` は自分の値に置換） |

## Stepのまとめ

- 本番用のCodeBuildプロジェクトとCodePipelineを構築しました
- 手動承認ステージを追加し、本番反映を人間が制御できるようにしました
- `main` ブランチへのpush → 承認 → 本番反映の流れを体験しました

次は [Step 5](step5.md) で、構築したパイプラインの「効果」を体験する3つのシナリオを実施します。
