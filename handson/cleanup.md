# ハンズオン後のクリーンアップ手順

ハンズオンで作成したAWSリソースは、課金や残骸を避けるため必ず削除してください。
削除する順番が重要です。依存関係の下流（アプリスタック）から削除し、最後に事前構築スタックを削除します。

## 削除順序の全体像

```
1. CodePipeline（dev/prod）              - 受講者が手動作成
2. CodeBuildプロジェクト（dev/prod）     - 受講者が手動作成
3. cities-api-dev-<UserName> / cities-api-prod-<UserName> スタック - パイプラインがデプロイしたCFNスタック
4. S3アーティファクトバケットの中身を空にする
5. 事前構築スタック（setup.yaml で作ったもの）  - 講師管理
```

注：`<UserName>` は自分のユーザー名に読み替えてください（[README](README.md#ユーザー名usernameの決定) 参照）。

## 1. CodePipelineを削除する

1. AWSマネジメントコンソールで **CodePipeline** を開きます
2. 左ナビ：**Pipelines** で以下を1つずつ削除します
   - `cities-api-pipeline-dev-<UserName>`
   - `cities-api-pipeline-prod-<UserName>`
3. 各パイプラインを開き、右上の **Delete pipeline** → 確認ダイアログで名前を入力 → **Delete**

## 2. CodeBuildプロジェクトを削除する

1. AWSマネジメントコンソールで **CodeBuild** を開きます
2. 左ナビ：**Build projects** で以下を削除します
   - `cities-api-build-dev-<UserName>`
   - `cities-api-build-prod-<UserName>`
3. 各プロジェクトを選択し、右上の **Delete build project** → 確認ダイアログで名前を入力 → **Delete**

## 3. アプリケーション用CloudFormationスタックを削除する

`cities-api-dev-<UserName>` と `cities-api-prod-<UserName>` スタックを削除すると、Lambda関数・API Gateway・実行ロール等が一括削除されます。

1. AWSマネジメントコンソールで **CloudFormation** を開きます
2. 以下のスタックを1つずつ削除します
   - `cities-api-dev-<UserName>`
   - `cities-api-prod-<UserName>`
3. 各スタックを選択 → **Delete** → 確認ダイアログで **Delete**
4. 削除完了を待ちます（数分かかります）

## 4. S3アーティファクトバケットの中身を空にする

事前構築スタックを削除する前に、S3バケットを空にする必要があります（バケットが空でないとスタック削除が失敗します）。

1. AWSマネジメントコンソールで **S3** を開きます
2. バケット一覧から `cities-api-artifacts-<AccountID>-<Region>-<UserName>` を選択
3. 右上の **Empty** をクリック
4. 確認テキスト（`permanently delete`）を入力 → **Empty** をクリック
5. 全オブジェクト（旧バージョン含む）の削除完了を待ちます

## 5. 事前構築スタックを削除する（講師管理）

受講者が個人アカウントでハンズオンを行った場合のみ、自分で事前構築スタックを削除してください。共有アカウントで講師が事前構築している場合は、講師にお任せします。

1. AWSマネジメントコンソールで **CloudFormation** を開きます
2. 事前構築スタック（例：`cities-api-setup-<UserName>` など、講師が指定した名前）を選択
3. **Delete** → 確認ダイアログで **Delete**

これで CodeCommitリポジトリ、S3バケット、build-role / pipeline-role / deploy-role がすべて削除されます。

## クリーンアップ確認

すべての削除が完了したら、以下を確認します：

- **CodePipeline** の Pipelines が空になっている
- **CodeBuild** の Build projects が空になっている
- **CloudFormation** にハンズオン関連のスタックが残っていない
- **S3** にハンズオン関連のバケットが残っていない
- **CodeCommit** にリポジトリが残っていない

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| 事前構築スタックの削除が `BucketNotEmpty` で失敗 | S3バケットの中身が空になっていない（オブジェクトの旧バージョンが残っている） | S3コンソールでバケットを開き **Empty** を再実行 |
| `cities-api-dev-<UserName>` スタック削除が `Resource cannot be deleted` で失敗 | Lambda実行ロールに何かがアタッチされている | CloudFormation 画面でエラー詳細を確認、必要に応じて手動でリソースを削除してから再試行 |
| CodeCommitリポジトリが削除できない | 事前構築スタック側で管理されているため | 事前構築スタックを削除すると一緒に消える |
