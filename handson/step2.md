# Step 2: CodeCommitにpushする

## このStepの目的

ローカルで動作確認したソースコードをCodeCommitリポジトリに登録します。`develop` と `main` の2ブランチを用意することで、後続Stepでブランチごとに別環境へデプロイするパイプラインを構築できる状態にします。

## 所要時間

約20分

## 前提

- Step 1 が完了している
- 講師から事前構築リソース（CloudFormationスタック）のOutputs情報を受け取っている
- 作業環境のEC2インスタンスに、CodeCommitへの読み書き権限を持つインスタンスロールが付与されている（個別のIAMユーザー認証情報は不要）

## このStepのゴール

- Git に AWS CodeCommit用のcredential helperが設定されている
- ローカルのソースコード一式が CodeCommitリポジトリの `develop` ブランチと `main` ブランチに push されている
- `git push` 時に認証が通ることを確認できている

## 手順

### 1. CodeCommitリポジトリ情報を確認する

CloudFormationの事前構築スタックの **Outputs** タブを開き、以下の値を控えます：

| Outputs名 | 用途 |
|---|---|
| `CodeCommitCloneUrlHttp` | リポジトリのHTTPSクローンURL |
| `CodeCommitRepositoryName` | リポジトリ名（`cities-api`） |

<!-- screenshot: CloudFormationスタック詳細のOutputsタブ -->

### 2. Git の AWS credential helper を設定する

作業環境のEC2インスタンスにはCodeCommitへの権限を持つインスタンスロールが付与されています。Gitに **AWS CLI のcredential helper** を使うよう設定すれば、インスタンスロールの認証情報を介してCodeCommitに認証されます。IAMユーザーで個別にGit Credentialsを発行する必要はありません。

ターミナルで以下を実行します：

```bash
git config --global credential.helper '!aws codecommit credential-helper $@'
git config --global credential.UseHttpPath true
```

設定の意味：

- `credential.helper`：認証要求時に `aws codecommit credential-helper` を呼び出す。AWS CLI が IMDS（インスタンスメタデータサービス）からインスタンスロールの一時認証情報を取得して使う
- `credential.UseHttpPath`：CodeCommit が要求するように、HTTPパスを認証スコープに含める

### 3. ローカルリポジトリをCodeCommitに紐づけてpushする

ターミナルで Step 1 のアプリのディレクトリに居ることを確認したうえで、以下を実行します：

```bash
git init
git add .
git commit -m "Initial commit"
```

リモートリポジトリを追加します（URLは Outputs の `CodeCommitCloneUrlHttp` を使用）：

```bash
git remote add origin <CodeCommitCloneUrlHttp の値>
```

`develop` ブランチを作って push します：

```bash
git checkout -b develop
git push -u origin develop
```

credential helper が裏で認証を済ませてくれるので、ユーザー名・パスワードを聞かれることなくpushできます。

次に `main` ブランチを作って push します：

```bash
git checkout -b main
git push -u origin main
```

### 4. CodeCommitコンソールでpushを確認する

1. AWSマネジメントコンソールで **CodeCommit** を開きます
2. 左ナビ：**Repositories** → `cities-api` をクリック
3. 画面上部のブランチセレクタで `develop` / `main` を切り替え、両方にコードがあることを確認

<!-- screenshot: CodeCommitリポジトリのコード一覧画面（developブランチ表示） -->

## ブランチ戦略の解説

このハンズオンでは2ブランチで開発・本番を分離します：

- **develop ブランチ**：開発環境（`cities-api-dev` スタック）へのデプロイをトリガ
- **main ブランチ**：本番環境（`cities-api-prod` スタック）へのデプロイをトリガ（手動承認あり）

実際のチーム開発ではここに feature ブランチや PR レビューが加わりますが、本ハンズオンの主眼は「ブランチによって異なる環境へデプロイされる」体験です。

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `git push` で `fatal: unable to access ... The requested URL returned error: 403` | EC2インスタンスロールにCodeCommitへの権限がない、またはcredential helperが効いていない | `aws sts get-caller-identity` でインスタンスロールが認識されているか、`git config --global --list \| grep credential` でhelper設定が入っているか確認 |
| `git push` で credential helper が呼ばれず認証ダイアログが出る | `git config` の設定が反映されていない | `git config --global --list` で `credential.helper` と `credential.UseHttpPath` が出力されるか確認、出ない場合は手順2を再実行 |
| クローンURLが `https://git-codecommit.region.amazonaws.com/v1/repos/cities-api` 形式でない | Outputsを取り違えた | CloudFormationスタックの正しいOutputs `CodeCommitCloneUrlHttp` を再確認 |

## Stepのまとめ

- GitにAWS CodeCommit用のcredential helperを設定し、EC2インスタンスロールの認証情報でpushできるようにしました
- ローカルコードを CodeCommit に push し、`develop` と `main` の両ブランチが揃いました
- ブランチごとに異なる環境へデプロイされるという、本ワークショップの土台ができました

次は [Step 3](step3.md) で、`develop` ブランチへのpushで開発環境にデプロイされるパイプラインを構築します。
