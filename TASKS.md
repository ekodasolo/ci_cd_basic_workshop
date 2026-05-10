# TASKS.md — タスク管理

## 進捗サマリー

| タスク | ステータス |
|---|---|
| T1: SAMアプリケーション実装 | [ ] 未着手 |
| T2: ユニットテスト実装 | [ ] 未着手 |
| T3: buildspec.yml作成 | [ ] 未着手 |
| T4: 事前構築用CloudFormationテンプレート作成 | [ ] 未着手 |
| T5: ハンズオン手順書作成 | [ ] 未着手 |

## タスク一覧

### T1: SAMアプリケーション実装 [ ]

SAMテンプレートとLambda関数を実装する。
都市情報APIのエンドポイント（GET /cities、GET /cities/{city_id}）を動作させる。

- ステアリングファイル：`steering-t1-sam-app.md`
- 成果物：`template.yaml`, `src/cities/app.py`, `src/cities/data.py`

### T2: ユニットテスト実装 [ ]

pytestによるユニットテストを実装する。
Lambdaハンドラーの正常系・異常系を検証する。

- ステアリングファイル：`steering-t2-tests.md`
- 成果物：`tests/test_cities.py`, `tests/requirements.txt`

### T3: buildspec.yml作成 [ ]

CodeBuild用のbuildspec.ymlを作成する。
完成版と、受講者向けの骨格版の2種類を用意する。

- ステアリングファイル：`steering-t3-buildspec.md`
- 成果物：`buildspec.yml`（骨格版）, `buildspec_complete.yml`（完成版）

### T4: 事前構築用CloudFormationテンプレート作成 [ ]

ハンズオン環境の事前構築に使用するCloudFormationテンプレートを作成する。
CodeCommitリポジトリ、S3バケット、IAMロール等を一括作成する。

- ステアリングファイル：`steering-t4-setup.md`
- 成果物：`setup/setup.yaml`

### T5: ハンズオン手順書作成 [ ]

Step 1〜5の手順書を作成する。
受講者がマネジメントコンソールを操作してパイプラインを構築する手順を記述する。

- ステアリングファイル：`steering-t5-handson-docs.md`
- 成果物：`docs/handson/step1.md` 〜 `step5.md`
