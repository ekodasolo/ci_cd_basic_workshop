# steering-t5-handson-docs.md — T5: ハンズオン手順書作成

## 要求内容

### 変更・追加する機能の説明

受講者がEC2上のCode Serverで作業しながら、マネジメントコンソールを操作してCI/CDパイプラインを構築・運用するハンズオン手順書を `handson/` 配下に作成する。

`docs/SPEC.md` のハンズオン構成（Step 1〜5、合計3時間）に従い、各Stepを1ファイルずつ・受講者がコピー＆ペーストでコマンドを実行できる粒度・スクリーンショット後追い前提で書く。

### 受け入れ条件

- 受講者が手順書を上から順に読み進めるだけで、Step 1〜5が完走できる
- 必要なAWS情報（CodeCommit URL、S3バケット名、IAMロールARN）は事前構築の `setup.yaml` Outputs を参照する形で具体的にプレースホルダ化されている
- 写経で完成させる `buildspec.yml` の埋め方が手順書からだけで理解できる
- Step 5 の「テストを失敗させる→パイプラインが止まる→修正→成功する」シナリオが、改ざんすべきファイル名・行・修正例まで明示されている
- ハンズオン後のクリーンアップ手順が含まれる（S3空化 → CloudFormationスタック削除）
- 全Stepでトラブルシューティング欄を持ち、よくあるハマりどころと回避策が書かれている

### 制約事項

- 形式：マークダウン
- 言語：日本語、です・ます調（受講者向けで丁寧さを保つ）
- スクリーンショットは後日Yoheiが追加するためプレースホルダ（HTMLコメント）を埋め込む
- 絵文字は使用しない
- ハンズオン総所要時間 3時間以内に収まる粒度（各Stepの所要時間目安を明記）
- 受講者の作業環境（EC2上のCode Server）はスコープ外。手順書では「お使いの環境のターミナル」と書く

## 変更内容の設計

### 実装アプローチ

#### ファイル構成

```
handson/
├── README.md         # ハンズオン全体ガイド（Stepへのリンク、所要時間、前提）
├── step1.md          # Step 1: SAMアプリをローカルで動かす
├── step2.md          # Step 2: CodeCommitにpushする
├── step3.md          # Step 3: 開発パイプラインを構築する
├── step4.md          # Step 4: 本番パイプラインを構築する
├── step5.md          # Step 5: パイプラインの効果を体験する
└── cleanup.md        # ハンズオン後のクリーンアップ
```

`README.md` と `cleanup.md` を別ファイルにする理由：

- `README.md` はハンズオン全体の入口として独立した方が、目次を見て全体像をつかみやすい
- `cleanup.md` を Step 5 の中に埋め込むと、Step 5 完了時点で「クリーンアップを忘れずに」を強調しにくい

#### 各Step共通の章立てテンプレ

```markdown
# Step N: <タイトル>

## このStepの目的

<このStepで何を体験するかの1〜2文>

## 所要時間

約X分

## 前提

- Step N-1 が完了していること
- <その他、必要に応じて>

## このStepのゴール

完了時に達成している状態を箇条書き

## 手順

### 1. <小見出し>

<手順本文、コマンド、コンソール操作>

### 2. <小見出>

...

## トラブルシューティング

| 症状 | 原因 | 対処 |

## Stepのまとめ

<このStepで体験したこと、次のStepへの繋ぎ>
```

#### スクリーンショットのプレースホルダ形式

スクリーンショット後追い前提で、以下のHTMLコメント形式で埋め込む：

```markdown
<!-- screenshot: CodeBuildプロジェクト作成画面 / 環境の編集セクション -->
```

理由：

- マークダウン上は不可視になる
- Yoheiが後で `grep screenshot:` で全プレースホルダを一覧できる
- 「何の画面か」を明記しておけば、撮り直しのときも迷わない

#### コンソール操作の記述形式

スクリーンショットがない段階でも操作が追えるよう、ナビゲーションと設定値をテキストで明示する：

```markdown
1. AWSマネジメントコンソールで CodeBuild を開きます
2. 左ナビ：**Build projects** をクリック
3. 右上の **Create build project** をクリック
4. 以下を設定します：
   - **Project name**: `cities-api-build-dev`
   - **Source provider**: AWS CodeCommit
   - **Repository**: `cities-api`
   - **Branch**: `develop`
   - **Service role**: 既存のロールを選択 → `cities-api-build-role`
   - **Environment variables**:
     - Name: `S3_BUCKET` / Value: `<setup.yaml Outputs の ArtifactsBucketName>`
5. **Create build project** をクリック
```

設定値で「事前構築物の名前」を参照する箇所は、setup.yaml のOutputs 名を明示し、受講者が CloudFormation スタックの Outputs タブを見れば値が拾える状態にする。

#### Step ごとの内容方針

##### Step 1: SAMアプリをローカルで動かす（約30分）

- SAMプロジェクト構成（`template.yaml`、`src/cities/`、`tests/`）の説明
- `pytest` を走らせて3テスト通ることを確認
- `sam build` → `sam local start-api` → curl 3パターン
- T1 で見つけた「AWS SSO期限切れ時の `AWS_ACCESS_KEY_ID=dummy ...` 回避」を Tips として記載

##### Step 2: CodeCommitにpushする（約20分）

- 事前構築の `setup.yaml` Outputs から CodeCommit クローンURLを取得
- IAM認証情報（Git Credential Helper）の設定 — 受講者のIAMユーザーで HTTPS Git Credentials を発行する手順
- `git clone` → ファイル配置 → `develop` / `main` 両ブランチへの push
- ブランチ戦略の解説（develop=開発環境、main=本番環境）

##### Step 3: 開発パイプラインを構築する（約60分）

- CodeBuildプロジェクト作成（dev用）
  - サービスロール：`cities-api-build-role`
  - 環境変数：`S3_BUCKET`
  - buildspec：リポジトリの `buildspec.yml`（このタイミングで写経完成）
- **buildspec.yml の写経** — 骨格の `echo "TODO: ..."` を完成形のコマンドに置き換える解説
- CodePipeline作成（develop ブランチをトリガ）
  - Source: CodeCommit develop
  - Build: 上で作った CodeBuild プロジェクト
  - Deploy: CloudFormation — packaged.yaml を使い、`cities-api-dev` スタックを CreateOrUpdate
- 開発環境エンドポイントへの curl で動作確認

##### Step 4: 本番パイプラインを構築する（約40分）

- 本番用 CodeBuild プロジェクト作成（環境変数のみ違う想定。実体としては dev とほぼ同じ）
- 本番 CodePipeline 作成（main ブランチをトリガ + 手動承認）
  - 手動承認ステージで「承認待ち」を体験
  - 承認 → 本番デプロイ
- 本番環境エンドポイントへの curl で動作確認

##### Step 5: パイプラインの効果を体験する（約30分）

シナリオ1：開発パイプラインで新都市追加

- `src/cities/data.py` に名古屋を追加 → develop へ push → 開発パイプライン自動起動 → 開発環境に反映

シナリオ2：テスト失敗による安全網の体験

- `src/cities/app.py` の `get_city_handler` で意図的にバグを入れる（具体例：`CITIES.get(city_id)` を `CITIES.get("typo_" + city_id)` に書き換える）
- develop へ push → 開発パイプラインが pytest 段階で失敗 → 本番環境は守られている
- バグを修正 → 再 push → 成功 → 本番にもリリース可能になる

##### cleanup.md

- 各環境スタック（`cities-api-dev`、`cities-api-prod`）の削除
- アーティファクトS3バケットの中身を空にする手順
- 事前構築スタックの削除
- CodePipelineの削除（pipelineスタックではなくコンソールで手動作成しているため、手動削除）
- CodeBuildプロジェクトの削除（同上）

#### 各Stepのトラブルシューティング欄

各Stepで想定されるハマりどころと対処を表形式で記載：

| Step | 想定ハマり |
|---|---|
| 1 | `sam local start-api` が AWS SSO期限切れで 502 |
| 1 | `pytest` が `ModuleNotFoundError: No module named 'app'`（→ `pytest.ini` 位置の確認） |
| 2 | `git push` で認証エラー（→ Git Credential Helper / HTTPS Git Credentials） |
| 3 | CodeBuild が S3 Access Denied で失敗（→ build-role の Inline Policy 確認） |
| 3 | CloudFormation デプロイで IAM 関連エラー（→ deploy-role の `CAPABILITY_IAM` 設定） |
| 4 | 手動承認をクリックしても進まない（→ 承認担当者のIAM権限） |
| 5 | テスト失敗のはずがビルド成功してしまう（→ buildspec の `pre_build` コマンドの順序確認） |

### 変更するコンポーネント

| 区分 | パス | 種別 |
|---|---|---|
| 新規 | `handson/README.md` | ハンズオン全体ガイド |
| 新規 | `handson/step1.md` | Step 1 手順書 |
| 新規 | `handson/step2.md` | Step 2 手順書 |
| 新規 | `handson/step3.md` | Step 3 手順書 |
| 新規 | `handson/step4.md` | Step 4 手順書 |
| 新規 | `handson/step5.md` | Step 5 手順書 |
| 新規 | `handson/cleanup.md` | クリーンアップ手順 |

### データ構造の変更

なし。

### 影響範囲の分析

- T1〜T4成果物への影響：なし（受講者向けの使い方ガイドのみ）
- DESIGN.md への影響：リポジトリ構造定義の `handson/` セクションに `README.md` と `cleanup.md` を追記する必要がある

## タスクリスト

### 詳細実装タスク

- [x] T5-1: `handson/` ディレクトリを作成
- [x] T5-2: `handson/README.md`（全体ガイド・目次）を作成
- [x] T5-3: `handson/step1.md` を作成
- [x] T5-4: `handson/step2.md` を作成
- [x] T5-5: `handson/step3.md` を作成
- [x] T5-6: `handson/step4.md` を作成
- [x] T5-7: `handson/step5.md` を作成
- [x] T5-8: `handson/cleanup.md` を作成
- [x] T5-9: 各Stepで参照しているリソース名・出力名の整合性確認、コンソールUIでのロール選択表現を統一
- [x] T5-10: DESIGN.md のリポジトリ構造定義に `README.md` / `cleanup.md` を反映
- [x] T5-11: `docs/TASKS.md` のT5ステータスを `[!]` レビュー待ちに更新

### 検証結果（2026-05-16）

- すべての handson/ ファイルを作成
- スクショプレースホルダ：`grep -r 'screenshot:' handson/` で全件抽出可能
- リソース名・Outputs名・コマンドはT1〜T4成果物と整合（突き合わせ完了）
- IAMロール参照箇所は「ロール名から選択」形式に統一（コンソールUIの実体に合わせる）

### 完了条件

- 上記すべてのタスクが完了している
- 各手順書のリソース名・コマンド・参照先がT1〜T4の成果物と整合している
- Yoheiのレビューで承認を得ている

## 設計判断の決定事項（2026-05-16 Yoheiレビュー）

| 論点 | 決定 |
|---|---|
| ファイル分割 | `README.md` + `step1〜5.md` + `cleanup.md` の7ファイル構成 |
| 言語スタイル | です・ます調 |
| スクリーンショットプレースホルダ形式 | `<!-- screenshot: ... -->`（HTMLコメント） |
| Step 5 のバグ仕込みシナリオ | `app.py` の `get_city_handler` を `CITIES.get("typo_" + city_id)` に書き換える |
| 承認体験の規模感 | 承認ボタンを押すだけのシンプル体験 |
| CodeBuild / CodePipeline 構築方法 | マネジメントコンソール手動（SPEC.md準拠） |
