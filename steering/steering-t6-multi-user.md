# steering-t6-multi-user.md — T6: 複数ユーザー共存対応

## 要求内容

### 変更・追加する機能の説明

ハンズオンの実施時、同一AWSアカウント・同一リージョンに講師と受講者（1名以上）が同時に作業する場合でも、リソース名の衝突が起きないようにする。
具体的には、すべてのリソース名にユーザー名サフィックスを付けて、ユーザーごとに独立した一式が並立できる状態を作る。

### 受け入れ条件

- `setup/setup.yaml` に `UserName` パラメータが追加され、CodeCommit / S3 / IAMロール 3種すべての名前にサフィックスとして付く
- `template.yaml` に `UserName` パラメータが追加され、Lambda 関数名 / API Gateway 名にサフィックスとして付く
- 講師と受講者が異なる `UserName` で setup.yaml をデプロイすれば、同一アカウント・同一リージョンに 2 セット以上のリソースが並立できる
- ハンズオン手順書（README、step1〜5、cleanup）に「自分の `UserName` を決めて全リソース名に入れる」運用が反映されている
- 受講者が手で命名する CodeBuild プロジェクト / CodePipeline / デプロイ先 CFN スタックも `UserName` サフィックス付きの名前で案内されている

### 制約事項

- `UserName` の最大長は 8 文字（IAM ロール名 64 文字制限に対するマージンを確保するため）
- `UserName` は英小文字＋数字のみ（S3 バケット名のグローバル一意名の制約に合わせる）
- 命名位置は **サフィックス**（既存リソース名の末尾に `-${UserName}` を付ける）
- 既存の `Environment`（dev/prod）サフィックスより **後ろ** に `UserName` を置く（ユーザー名は常に末尾）
- 受講者環境の EC2 インスタンスロール（事前付与済み）の CodeCommit 権限は影響なし（CodeCommit 系の権限はリポジトリ ARN 指定ではなく `*` 想定との前提）

## 変更内容の設計

### 命名規約

#### setup.yaml が作るリソース

| リソース | 変更前 | 変更後 |
|---|---|---|
| CodeCommit リポジトリ | `cities-api` | `cities-api-<UserName>` |
| S3 バケット | `cities-api-artifacts-<Acct>-<Region>` | `cities-api-artifacts-<Acct>-<Region>-<UserName>` |
| build-role | `cities-api-build-role` | `cities-api-build-role-<UserName>` |
| pipeline-role | `cities-api-pipeline-role` | `cities-api-pipeline-role-<UserName>` |
| deploy-role | `cities-api-deploy-role` | `cities-api-deploy-role-<UserName>` |

#### template.yaml が作るリソース（SAM デプロイ）

| リソース | 変更前 | 変更後 |
|---|---|---|
| API Gateway Name | `cities-api-<Env>` | `cities-api-<Env>-<UserName>` |
| ListCities Lambda | `cities-list-<Env>` | `cities-list-<Env>-<UserName>` |
| GetCity Lambda | `cities-get-<Env>` | `cities-get-<Env>-<UserName>` |

#### 受講者が手で命名するリソース（handson 手順書）

| リソース | 変更前 | 変更後 |
|---|---|---|
| CodeBuild プロジェクト（dev） | `cities-api-build-dev` | `cities-api-build-dev-<UserName>` |
| CodeBuild プロジェクト（prod） | `cities-api-build-prod` | `cities-api-build-prod-<UserName>` |
| CodePipeline（dev） | `cities-api-pipeline-dev` | `cities-api-pipeline-dev-<UserName>` |
| CodePipeline（prod） | `cities-api-pipeline-prod` | `cities-api-pipeline-prod-<UserName>` |
| デプロイ先 CFN スタック（dev） | `cities-api-dev` | `cities-api-dev-<UserName>` |
| デプロイ先 CFN スタック（prod） | `cities-api-prod` | `cities-api-prod-<UserName>` |
| 事前構築用 CFN スタック | `cities-api-setup` 等 | `cities-api-setup-<UserName>` |

### パラメータ設計

```yaml
UserName:
  Type: String
  MaxLength: 8
  MinLength: 1
  AllowedPattern: '^[a-z0-9]+$'
  Description: ユーザー識別子（英小文字+数字、8文字以内）。同一AWSアカウント・同一リージョン内でリソースを共存させるためのサフィックスに使用
```

- Default は設けない（明示入力を必須化することで、複数ユーザー運用を意識させる）
- 制約パターン `^[a-z0-9]+$` は S3 バケット名互換

### 変更するコンポーネント

| 区分 | パス | 内容 |
|---|---|---|
| 変更 | `setup/setup.yaml` | `UserName` パラメータ追加、全リソース名にサフィックス付与 |
| 変更 | `template.yaml` | `UserName` パラメータ追加、Lambda / API 名にサフィックス付与 |
| 変更 | `docs/SPEC.md` | 「ワークショップ構成」に複数ユーザー共存要件を追記 |
| 変更 | `docs/DESIGN.md` | 命名規約セクションを追加、テンプレート設計に `UserName` を反映 |
| 変更 | `handson/README.md` | 「自分の `UserName` を決める」セクションを冒頭に追加 |
| 変更 | `handson/step1.md`〜`step5.md` | リソース名参照を `<UserName>` サフィックス付きに書き換え |
| 変更 | `handson/cleanup.md` | 削除対象リソース名を `<UserName>` サフィックス付きに書き換え |

### データ構造の変更

なし。

### 影響範囲の分析

- 既存の事前構築済みCloudFormationスタック（もし作成済みなら）には影響なし。ただし新仕様でデプロイし直しが必要
- buildspec.yml は環境変数 `S3_BUCKET` で受け取るため、影響なし（CodeBuild プロジェクト作成時のバケット名指定が変わるだけ）
- ユニットテストには影響なし

## タスクリスト

### 詳細実装タスク

- [x] T6-1: `setup/setup.yaml` に `UserName` パラメータを追加し、全リソース名にサフィックス付与
- [x] T6-2: `template.yaml` に `UserName` パラメータを追加し、Lambda / API 名にサフィックス付与
- [x] T6-3: `docs/SPEC.md` に複数ユーザー共存要件を追記
- [x] T6-4: `docs/DESIGN.md` に命名規約セクションを追記
- [x] T6-5: `handson/README.md` に `UserName` 設定セクションを追加
- [x] T6-6: `handson/step1.md`〜`step5.md`、`cleanup.md` のリソース名参照を更新
- [x] T6-7: `cfn-lint` で setup.yaml / template.yaml を静的検証
- [x] T6-8: `docs/TASKS.md` のT6ステータスを `[!]` レビュー待ちに更新

### 完了条件

- 上記すべてのタスクが完了している
- `cfn-lint` でエラーが出ない
- Yoheiのレビューで承認を得ている
