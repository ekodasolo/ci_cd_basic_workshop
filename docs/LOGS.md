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

## 2026-05-16

### 実施内容

- T1（SAMアプリケーション実装）を `feature/t1-sam-app` ブランチで実施
- ステアリングファイル `steering-t1-sam-app.md` を作成し、設計判断3点をYoheiレビューで決定
- `template.yaml`、`src/cities/{__init__.py,app.py,data.py}` を実装
- ローカル環境にSAM CLI／Python 3.12 venv／Docker を準備してもらい、SAM CLI実機検証を実施
- `sam validate --lint` / `sam build` / `sam local start-api` + curl 3パターンで動作確認、すべてパス

### 決定事項

- Lambda関数の構成：エンドポイントごとに別関数（`ListCitiesFunction` / `GetCityFunction`）。「1関数1責務」原則を受講者に伝えやすいことを優先
- 初期データ：東京・大阪のみ。名古屋・福岡・札幌はハンズオン中に受講者が追加する流れ（SPEC.mdに従う）
- API Gateway ステージ名：`${Environment}`（dev / prod）をそのまま使用
- コード配置：2関数とも `CodeUri: src/cities/` を共有し `Handler` だけ変える。`data.py` を関数間で共有しつつ Lambda Layer を導入しない（ワークショップの学習対象から外れるノイズを避けるため）
- `sam local start-api` ハマりポイント：AWS SSOセッション期限切れ時、SAM CLIがLambdaコンテナへcredentials注入で失敗し502。今回のLambdaはAWS APIを呼ばないので、`AWS_ACCESS_KEY_ID=dummy AWS_SECRET_ACCESS_KEY=dummy` を渡して回避可能。T5手順書での扱いは別途検討
- `.gitignore` に `.aws-sam/`、`__pycache__/`、`*.pyc` を追加（ビルド生成物・キャッシュ）

### 実施内容（プロジェクト構造の整理）

- T2以降で増えるファイルに備えてルート直下を整理（`feature/restructure-docs` ブランチ）
- `SPEC/DESIGN/TASKS/LOGS.md` を `docs/` 配下に移動
- `steering-t1-sam-app.md` を `steering/` 配下に移動
- 受講者向けコンテンツ置き場を `docs/handson/` から `handson/`（リポジトリ直下）に変更（実体はT5で作成）
- `CLAUDE.md` にドキュメント配置セクションを新設し、各ファイル参照のパスを更新
- `docs/DESIGN.md` のリポジトリ構造定義（ツリー・役割・配置ルール）を刷新

### 決定事項（プロジェクト構造）

- プロジェクト製作者向けドキュメント（仕様・設計・タスク・ログ）は `docs/` 配下に集約
- ワークショップ受講者向けコンテンツ（ハンズオン手順書）は `handson/` 配下に配置。製作者向けと受講者向けを別ディレクトリで明確に分離する方針
- 個別タスクのステアリングファイルは `steering/` 配下に集約（`tasks/` 案より、内容と一致する `steering/` を採用）
- `CLAUDE.md` だけは Claude Code が自動読み込みする都合上ルート配置を維持

### 実施内容（T2: ユニットテスト実装）

- T2 を `feature/t2-tests` ブランチで実施
- ステアリングファイル `steering/steering-t2-tests.md` を作成し、設計判断3点をYoheiレビューで決定
- `pytest.ini`、`tests/{__init__.py,requirements.txt,test_cities.py}` を実装
- `pytest -v` で 3 passed を確認

### 決定事項（T2）

- pytest設定ファイルは `pytest.ini` を採用（`pyproject.toml` 等は導入しない）
- pytest が `app.py` をインポートできるよう `pytest.ini` に `pythonpath = src/cities` を宣言
- 都市数のアサートは `> 0` でゆるく見る。ワークショップでのテストの主眼は仕組み・考え方に慣れることで網羅性ではない（受講者が `nagoya` 等を追加してもテストが壊れない設計）
- テスト依存パッケージは `pytest` のみ。バージョンピンせず最新を取り込む
- `.gitignore` に `.pytest_cache/` を追加

### 実施内容（T3: buildspec.yml作成）

- T3 を `feature/t3-buildspec` ブランチで実施
- ステアリングファイル `steering/steering-t3-buildspec.md` を作成し、設計判断4点をYoheiレビューで決定
- `buildspec_complete.yml`（完成版）と `buildspec.yml`（骨格版）を実装
- 両ファイルの YAML valid を確認、`pip install + pytest` / `sam build` のローカル実行で動作確認

### 決定事項（T3）

- buildspec のバージョンは `0.2`、Pythonランタイムは 3.12（SAMテンプレートと同じ）
- 完成版コマンド: `pip install -r tests/requirements.txt` → `pytest tests/` → `sam build` → `sam package --s3-bucket ${S3_BUCKET} --output-template-file packaged.yaml`
- 骨格版の `runtime-versions` は埋めておく（受講者の写経対象は「コマンド」に集中させる）
- 骨格版の空 `commands:` は CodeBuild が許容しないため `echo "TODO: ..."` プレースホルダを置く
- `pre_build` 失敗時のビルド停止は `pytest` の exit code に任せる（明示的な `set -e` は導入しない）
- `sam package` の `--s3-prefix` は指定しない、CodeBuild のキャッシュ機構は導入しない（学習対象から外れるため）
- アーティファクト出力は `packaged.yaml` のみ（CloudFormationデプロイステージが参照）

### 実施内容（T4: 事前構築用CloudFormationテンプレート作成）

- T4 を `feature/t4-setup` ブランチで実施
- ステアリングファイル `steering/steering-t4-setup.md` を作成し、設計判断6点をYoheiレビューで決定
- `setup/setup.yaml` を実装（CodeCommit / S3 / build-role / pipeline-role / deploy-role / Outputs）
- `cfn-lint` で静的検証クリーン（AWS server-side validate-template はSSO期限切れでスキップ）
- DESIGN.md 事前構築リソース設計テーブルもロール呼称統一に合わせて更新

### 決定事項（T4）

- IAMロールの呼称は **build-role / pipeline-role / deploy-role** でプロジェクト全体統一（メモリにも記録）
- IAMポリシーの粒度：AWS Managed Policy 主体 + 必要部分のみ Inline。ワークショップの主眼から外れないバランス
- 環境分離：setup.yaml は dev/prod 共通インフラ1セット（ロールもS3バケットも共通）
- パラメータ：`ProjectName`（デフォルト `cities-api`）のみ。`Environment` は SAM テンプレート側で制御
- S3バケット名：`${ProjectName}-artifacts-${AWS::AccountId}-${AWS::Region}`（グローバル一意性）
- S3クリーンアップ：`DeletionPolicy: Delete` + 手順書で空化案内（T5で扱う）
- deploy-role の IAM権限：`IAMFullAccess` は使わず、SAM が動的生成する Lambda 実行ロール操作に必要な11アクションを列挙する Inline Policy で絞った
- pipeline-role の `iam:PassRole` は deploy-role の ARN にスコープ（ロールチェーンの正しい設計として明示）

### 実施内容（T5: ハンズオン手順書作成）

- T5 を `feature/t5-handson-docs` ブランチで実施
- ステアリングファイル `steering/steering-t5-handson-docs.md` を作成し、設計判断6点をYoheiレビューで決定
- `handson/{README, step1〜5, cleanup}.md` の7ファイルを作成（合計約42KB）
- 各Step共通の章立てテンプレ（目的/所要時間/前提/ゴール/手順/トラブルシューティング/まとめ）を採用
- スクリーンショットは後日追加するためHTMLコメント形式（`<!-- screenshot: ... -->`）でプレースホルダ7箇所を埋め込み
- DESIGN.md のリポジトリ構造定義に `README.md` / `cleanup.md` を追記
- Yoheiレビューで、CodeCommit認証部分を「IAMユーザーのHTTPS Git Credentials発行」から「EC2インスタンスロール + git credential.helper」方式に書き換え

### 決定事項（T5）

- ファイル構成：7ファイル（README + step1〜5 + cleanup）。step5にcleanupを埋め込むより独立ファイルの方が「忘れずにクリーンアップ」を強調できる
- 言語スタイル：です・ます調（受講者向けで丁寧さを保つ）
- スクリーンショットプレースホルダ：`<!-- screenshot: ... -->`（マークダウン上不可視、`grep screenshot:` で全件抽出可能）
- Step 5 のバグ仕込みシナリオ：`app.py` の `get_city_handler` で `CITIES.get("typo_" + city_id)` に書き換えるロジック改ざん方式
- 承認体験：承認ボタンを押すだけのシンプル体験（SNS通知や複数承認者は時間オーバーリスクで採用せず）
- CodeBuild / CodePipeline 構築方法：マネジメントコンソール手動（SPEC.md準拠）
- CodeCommit認証方式：EC2インスタンスロール + `git config --global credential.helper '!aws codecommit credential-helper $@'`。個別IAMユーザーのHTTPS Git Credentials発行は不要（メモリにも記録）

## プロジェクト完了

T1〜T5 のすべてのタスクが完了し、ワークショップ教材一式が揃った：

- SAMアプリ（template.yaml、src/cities/）
- ユニットテスト（pytest.ini、tests/）
- buildspec（buildspec.yml骨格 + buildspec_complete.yml）
- 事前構築テンプレート（setup/setup.yaml）
- ハンズオン手順書（handson/README + step1〜5 + cleanup）

未対応の残作業：

- 各Stepのスクリーンショット撮影・追加（後日Yoheiが対応）
- 講師AWSアカウントで setup.yaml をデプロイした実機検証
- ワークショップ本番運用での受講者フィードバック取り込み

## 2026-05-18

### 実施内容

- T6（複数ユーザー共存対応）を `feature/multi-user-coexistence` ブランチで実施
- 講師と受講者が同一AWSアカウント・同一リージョンで並立できるよう、全リソース名に `UserName` サフィックスを付与
- `setup/setup.yaml` と `template.yaml` に `UserName` パラメータを追加し、CodeCommit / S3 / IAMロール3種 / Lambda関数 / API Gateway の名前を更新
- handson 全ファイル（README、step1〜5、cleanup）のリソース名参照を `<UserName>` サフィックス付きに書き換え、CFN Deploy アクションの `Parameter overrides` にも `UserName` を追加
- `sam validate --lint` で両テンプレートを検証

### 決定事項

- `UserName` の制約：英小文字＋数字、1〜8文字（`^[a-z0-9]+$`、S3バケット名のグローバル一意制約に合わせた文字種、IAMロール名 64 文字制限のマージン確保のための長さ制限）
- 命名位置：サフィックス（既存リソース名の末尾に `-${UserName}` を付ける）。`Environment`（dev/prod）サフィックスがある場合は、`<Environment>` の後ろに `<UserName>` を置く（ユーザー名は常に末尾）
- `UserName` パラメータに Default は設けない：明示入力を必須化し、複数ユーザー運用を意識させる
- 受講者環境のEC2インスタンスロール（CodeCommit権限）は影響なし：リポジトリARN指定ではなく `*` 想定との Yohei 確認による
- 既存の事前構築済みCloudFormationスタックがある場合は新仕様でデプロイし直しが必要。buildspec.yml は環境変数 `S3_BUCKET` で受け取るため変更不要
