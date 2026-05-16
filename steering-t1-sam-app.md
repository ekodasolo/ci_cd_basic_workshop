# steering-t1-sam-app.md — T1: SAMアプリケーション実装

## 要求内容

### 変更・追加する機能の説明

都市情報APIのバックエンドとなるSAMアプリケーションを新規実装する。
ハンズオン受講者が `sam local start-api` でローカル実行でき、後続のCI/CDパイプラインによってAWSへデプロイ可能な状態にする。

実装する機能：

- `GET /cities` — 都市一覧を返す
- `GET /cities/{city_id}` — 指定都市の情報を返す（存在しない場合は404）

### 受け入れ条件

- `sam build` がローカルで成功する
- `sam local start-api` 起動後、curlで以下が成功する
  - `GET /cities` → 200 / `cities` 配列を含むJSON
  - `GET /cities/tokyo` → 200 / `city_id: "tokyo"` のJSON
  - `GET /cities/unknown` → 404 / `error: "City not found"` を含むJSON
- SAMテンプレートに `Environment` パラメータ（dev / prod）が存在し、リソース名に環境名が付与される
- 初期データは **東京・大阪のみ**（名古屋・福岡・札幌はハンズオン中に受講者が追加するため含めない）

### 制約事項

- 言語：Python 3.12
- フレームワーク：AWS SAM
- 外部依存：標準ライブラリのみ（pytest等のテスト用依存はT2で扱う）
- 都市データはDBを使わず、Pythonモジュール内の固定データとして保持
- レスポンスはJSON、文字コードはUTF-8、日本語は `ensure_ascii=False` で出力
- 絵文字は使用しない（CLAUDE.md ルール）
- リポジトリ構造は DESIGN.md の定義に従う

## 変更内容の設計

### 実装アプローチ

#### Lambda関数の構成

**エンドポイントごとに別Lambda関数** で実装する（Yoheiの判断による決定）。

- `ListCitiesFunction` — `GET /cities` を処理
- `GetCityFunction` — `GET /cities/{city_id}` を処理

理由：

- 「1関数1責務」の原則を受講者に伝えやすい
- CloudWatch Logs / メトリクスがエンドポイント単位で分かれるため、運用観点の学習素材としても良い
- 一方の関数だけ更新するシナリオ（特定エンドポイントだけ修正してデプロイ）が示しやすい

#### コード配置と共有

DESIGN.md のリポジトリ構造（`src/cities/` 配下にコードを集約）はそのまま維持し、`app.py` 内に2つのハンドラー関数を定義する：

- `app.list_cities_handler`
- `app.get_city_handler`

SAMテンプレートでは、両関数とも `CodeUri: src/cities/` を共有し `Handler` だけ変える。共通の都市データ（`data.py`）はパッケージに同梱され、両関数から `from data import CITIES` でインポートできる。

理由：

- 関数ごとにディレクトリを分けると `data.py` を複製するか Lambda Layer を導入する必要があり、ワークショップの学習対象（CI/CDパイプライン）から外れたノイズが増える
- 1つの `CodeUri` を共有することで、`sam build` の出力もシンプルになり、`buildspec.yml`（T3）の構造が複雑化しない

#### SAMテンプレートのパラメータ設計

- `Environment` パラメータ（AllowedValues: `dev`, `prod`、Default: `dev`）
- Lambda関数名は `cities-list-${Environment}` / `cities-get-${Environment}`
- API Gateway のステージ名も `${Environment}`

#### 都市データの構造

`src/cities/data.py` に `CITIES` 辞書として保持：

```python
CITIES = {
    "tokyo": {"city_id": "tokyo", "name": "東京", "population": 14000000, "region": "関東"},
    "osaka": {"city_id": "osaka", "name": "大阪", "population": 8800000,  "region": "近畿"},
}
```

`city_id` をキーにすることで `GET /cities/{city_id}` のルックアップが O(1) になり、受講者にも構造が読みやすい。

#### Lambdaハンドラーの構造

```python
# src/cities/app.py
from data import CITIES

def list_cities_handler(event, context):
    return _response(200, {"cities": list(CITIES.values())})

def get_city_handler(event, context):
    city_id = event["pathParameters"]["city_id"]
    city = CITIES.get(city_id)
    if city is None:
        return _response(404, {"error": "City not found", "city_id": city_id})
    return _response(200, city)

def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }
```

各ハンドラーは責務が小さく、テストもエンドポイント単位で書きやすい（T2の設計と整合）。

### 変更するコンポーネント

| 区分 | パス | 種別 |
|---|---|---|
| 新規 | `template.yaml` | SAMテンプレート |
| 新規 | `src/cities/__init__.py` | 空ファイル（Pythonパッケージ化） |
| 新規 | `src/cities/app.py` | Lambdaハンドラー |
| 新規 | `src/cities/data.py` | 都市データ定義 |

### データ構造の変更

新規プロジェクトのため既存データ構造の変更はなし。
`CITIES` 辞書のフォーマットは DESIGN.md の「都市データ一覧」テーブルに準拠（`city_id` / `name` / `population` / `region`）。

### 影響範囲の分析

- 後続タスクへの影響
  - T2（ユニットテスト）：本タスクで定義する `lambda_handler` のインターフェース（event形式、レスポンス形式）に依存する
  - T3（buildspec.yml）：`sam build` / `sam package` を呼び出すため、`template.yaml` の存在が前提
  - T4（setup.yaml）：直接の依存はなし
  - T5（手順書）：`sam local start-api` の動作・APIレスポンスの確認手順で参照される
- ドキュメントへの影響：DESIGN.md のリポジトリ構造定義に沿うので変更不要

## タスクリスト

### 詳細実装タスク

- [x] T1-1: ディレクトリ構造の作成（`src/cities/`）と `__init__.py` の配置
- [x] T1-2: `src/cities/data.py` を実装（東京・大阪の `CITIES` 辞書）
- [x] T1-3: `src/cities/app.py` を実装（`list_cities_handler` / `get_city_handler` / `_response` ヘルパー）
- [x] T1-4: `template.yaml` を実装（`Environment` パラメータ、`ListCitiesFunction` / `GetCityFunction`、API Gateway 暗黙定義、Outputs）
- [x] T1-5: ローカル動作確認（Python `ast` 構文チェック + ハンドラーの直接呼び出しスモークテスト）
- [x] T1-6: TASKS.md のT1ステータスを `[!]` レビュー待ちに更新

### 検証結果

#### Python ハンドラーの直接呼び出しスモークテスト（2026-05-16）

| ケース | event | 期待 | 結果 |
|---|---|---|---|
| 都市一覧取得 | `{}` | 200, `cities` 配列 | 200, 東京・大阪を含む配列 ✓ |
| 個別都市取得（正常） | `{"pathParameters": {"city_id": "tokyo"}}` | 200, `city_id: "tokyo"` | 200, 東京の情報 ✓ |
| 個別都市取得（異常） | `{"pathParameters": {"city_id": "unknown"}}` | 404, エラー本文 | 404, `City not found` ✓ |

日本語が `ensure_ascii=False` で正しく出力されることも確認済み。

#### SAM CLI による検証（2026-05-16）

| 検証 | 結果 |
|---|---|
| `sam validate --lint` | ✓ valid SAM Template |
| `sam build` | ✓ Build Succeeded（`requirements.txt` なしのため依存解決スキップ） |
| `sam local start-api` 起動 | ✓ ListCitiesFunction / GetCityFunction が `/cities`, `/cities/{city_id}` にマウントされた |
| `GET /cities` | ✓ 200, `cities` 配列に東京・大阪 |
| `GET /cities/tokyo` | ✓ 200, 東京の情報 |
| `GET /cities/unknown` | ✓ 404, `City not found` |

#### 補足：SAM local 起動時の注意

YoheiのAWS SSOセッション期限切れ状態で `sam local start-api` を起動すると、SAM CLIがLambdaコンテナへcredentials注入を試み `LoginRefreshRequired` で 502 になる。本ワークショップのLambdaはAWS APIを呼ばないため、以下いずれかで回避可能：

- `aws sso login` などで認証セッションを更新する
- ダミー認証を環境変数で渡して起動する（`AWS_ACCESS_KEY_ID=dummy AWS_SECRET_ACCESS_KEY=dummy sam local start-api`）

ハンズオン手順書（T5）でこの点に触れるかは別途検討。

### 完了条件

- 上記すべてのタスクが完了している
- 「受け入れ条件」セクションの3つのcurlコマンドが期待どおりのレスポンスを返す
- Yoheiのレビューで承認を得ている

## 設計判断の決定事項（2026-05-16 Yoheiレビュー）

| 論点 | 決定 |
|---|---|
| Lambda関数の構成 | エンドポイントごとに別関数（`ListCitiesFunction` / `GetCityFunction`） |
| 初期データに含める都市 | 東京・大阪のみ（名古屋・福岡・札幌はハンズオン中に受講者が追加） |
| API Gateway ステージ名 | `${Environment}`（dev / prod）をそのまま使用 |
