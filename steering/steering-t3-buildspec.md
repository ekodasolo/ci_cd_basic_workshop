# steering-t3-buildspec.md — T3: buildspec.yml作成

## 要求内容

### 変更・追加する機能の説明

CodeBuild がパイプラインから呼ばれた際に実行する `buildspec.yml` を作成する。
受講者の写経用骨格版と、講師参考用の完成版の2ファイルを用意する。

実装する処理（`docs/DESIGN.md` buildspec.yml 設計に準拠）：

| フェーズ | 責務 |
|---|---|
| `install` | Pythonランタイムの指定 |
| `pre_build` | テスト用依存パッケージのインストール、ユニットテストの実行 |
| `build` | SAMビルド、SAMパッケージ（アーティファクトを `S3_BUCKET` 環境変数のバケットへ出力） |

ビルド成果物として `packaged.yaml`（`sam package` の出力）をアーティファクトに含め、後続のCloudFormationデプロイアクションが参照できるようにする。

### 受け入れ条件

- `buildspec_complete.yml`（完成版）
  - CodeBuild上で正常に走る構文・コマンド体系
  - `pre_build` でテストが失敗するとビルドも失敗する（パイプラインで止まる挙動）
  - `build` の最後で `packaged.yaml` がワークディレクトリに生成される
  - 出力アーティファクトに `packaged.yaml` が含まれる
- `buildspec.yml`（骨格版）
  - YAML として valid（CodeBuildで読み込めるレベル）
  - 各フェーズの構造とコメントによって、受講者が「ここに何を書けば良いか」読み取れる
  - 写経対象のコマンドはプレースホルダ（`echo "TODO: ..."` 等）にする。フェーズが空だとCodeBuildがエラーにするため
- 完成版と骨格版の差分が「写経で埋めるべき部分」と一致する（受講者のゴール体験と整合）

### 制約事項

- buildspec のバージョン：`0.2`（最新かつ標準）
- ランタイム：Python 3.12（SAMテンプレートと同じ）
- 環境変数 `S3_BUCKET` は受講者が CodeBuild プロジェクト作成時に設定する前提（buildspec 内では参照のみ）
- アーティファクト出力ファイル名：`packaged.yaml`
- 絵文字は使用しない
- CodeBuild のキャッシュ機構（pipキャッシュなど）は導入しない（ワークショップの学習対象から外れるため）

## 変更内容の設計

### 実装アプローチ

#### 完成版（buildspec_complete.yml）

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

設計判断のポイント：

- **`sam build --use-container` は使わない**：Docker起動のオーバーヘッドが大きく、Python標準ランタイムのLambdaなら `sam build` 単独で十分。ワークショップのフィードバックループを短くする
- **`sam package` の `--s3-prefix` は指定しない**：シンプルさ優先。バケット直下にアップされるが学習目的なら問題ない
- **`pip install` に `--upgrade` や `--no-cache-dir` を付けない**：CodeBuild の実行環境は使い捨てなので不要
- **アーティファクトに `packaged.yaml` のみ**：CloudFormationデプロイステージが必要とするのはこのファイル。`src/` や `template.yaml` 自体を含める必要はない

#### 骨格版（buildspec.yml）

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      # TODO: Pythonランタイムのバージョンを指定する
      python: 3.12

  pre_build:
    commands:
      # TODO: テスト用依存パッケージをインストールする
      # TODO: ユニットテストを実行する
      - echo "TODO: write pre_build commands here"

  build:
    commands:
      # TODO: SAM build を実行する
      # TODO: SAM package を実行し、S3 にアップロードして packaged.yaml を出力する
      - echo "TODO: write build commands here"

artifacts:
  files:
    # TODO: ビルド成果物としてパッケージ済みテンプレートを指定する
    - packaged.yaml
```

設計判断のポイント：

- **`python: 3.12` だけは骨格版にも含める**：ここは「写経対象」ではなく「設定値」で、講師が事前に与える情報という位置づけ。受講者が3.12 / 3.11 などの選択に迷う必要はない
- **空 `commands:` を避け `echo "TODO: ..."` を入れる**：CodeBuild は空 `commands:` を許容しないため。プレースホルダがあれば、写経前に「とりあえず走らせる→失敗を見る→修正していく」体験も可能
- **`artifacts.files` には完成版のファイル名を残す**：buildspec の構造としての見本になり、骨格版でも `artifacts` セクションが意味ある形で示せる。手順書（T5）でも「ここはこのままでよい」と説明できる
- **コメントは `# TODO: ...` 形式で統一**：受講者が `TODO` を検索して埋めるべき場所を一覧できる

#### 写経の差分（受講者が手順書を見て埋める部分）

| 場所 | 骨格版 | 完成版 |
|---|---|---|
| `pre_build.commands` | `echo "TODO: ..."` | `pip install -r tests/requirements.txt` + `python -m pytest tests/` |
| `build.commands` | `echo "TODO: ..."` | `sam build` + `sam package --s3-bucket ${S3_BUCKET} --output-template-file packaged.yaml` |

その他（`version`、`runtime-versions`、`artifacts.files`）は骨格と完成版で共通にして、受講者の負荷を「写経すべきコマンド」に集中させる。

### 変更するコンポーネント

| 区分 | パス | 種別 |
|---|---|---|
| 新規 | `buildspec.yml` | CodeBuild骨格版 |
| 新規 | `buildspec_complete.yml` | CodeBuild完成版 |

### データ構造の変更

なし。既存ファイルには手を入れない。

### 影響範囲の分析

- T1（SAM）・T2（pytest）成果物への影響：なし。本タスクはそれらを呼び出すだけ
- T4（setup.yaml）への影響：
  - `S3_BUCKET` 環境変数の存在は CodeBuild プロジェクト側の設定。setup.yaml が S3 バケットを作るので、その出力名がここで参照される `S3_BUCKET` の値と紐づく（受講者が手動で繋ぐ）
- T5（手順書）への影響：Step 3 の「buildspec.yml を完成させる」セクションで本タスクの骨格⇄完成の差分が写経対象になる

## タスクリスト

### 詳細実装タスク

- [x] T3-1: `buildspec_complete.yml`（完成版）を作成
- [x] T3-2: `buildspec.yml`（骨格版）を作成
- [x] T3-3: 両ファイルが YAML として valid であることをローカルで確認
- [x] T3-4: 完成版の `pre_build` フェーズ相当のコマンドをローカルで走らせ、テストが通ることを確認
- [x] T3-5: 完成版の `build` フェーズ相当の `sam build` をローカルで走らせて成功確認
- [x] T3-6: `docs/TASKS.md` のT3ステータスを `[!]` レビュー待ちに更新

### 検証結果（2026-05-16）

| 検証 | 結果 |
|---|---|
| YAML構文 | `buildspec.yml` / `buildspec_complete.yml` ともに valid（`yaml.safe_load`） |
| `pre_build` 相当 | `pip install -r tests/requirements.txt` 成功 / `pytest` 3 passed |
| `build` 相当 | `sam build` 成功（`.aws-sam/build/` 生成） |
| `sam package` | 実S3バケット必須のためローカル検証はスキップ（CodeBuild実行時に検証） |

### 完了条件

- 上記すべてのタスクが完了している
- `buildspec.yml` と `buildspec_complete.yml` の差分が「写経対象」と一致している
- Yoheiのレビューで承認を得ている

## 設計判断の決定事項（2026-05-16 Yoheiレビュー）

| 論点 | 決定 |
|---|---|
| 骨格版の `runtime-versions` を埋めておくか | 埋めておく（写経対象は「コマンド」に集中） |
| `pre_build` 失敗時のビルド停止挙動 | `pytest` の exit code に依存（明示的 `set -e` は不要） |
| `sam package` の `--s3-prefix` 指定 | 指定しない |
| CodeBuildキャッシュの導入 | 導入しない |
