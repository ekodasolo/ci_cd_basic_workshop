# steering-t2-tests.md — T2: ユニットテスト実装

## 要求内容

### 変更・追加する機能の説明

T1で実装した都市情報APIのLambdaハンドラーに対するユニットテストを pytest で実装する。
このテストは後続のT3で `buildspec.yml` から呼び出され、CI/CDパイプライン上で自動実行される。

実装するテスト（`docs/DESIGN.md` ユニットテスト設計に準拠）：

| No. | テストケース | 検証内容 |
|---|---|---|
| 1 | 都市一覧取得 | `list_cities_handler` が 200 を返し、レスポンスに `cities` 配列が含まれる |
| 2 | 個別都市取得（正常） | `get_city_handler(city_id=tokyo)` が 200 を返し、`city_id` が `tokyo` である |
| 3 | 個別都市取得（異常） | `get_city_handler(city_id=unknown)` が 404 を返し、エラーメッセージが含まれる |

### 受け入れ条件

- ローカルで `pytest` を実行すると、3つのテストケースがすべてパスする
- `tests/requirements.txt` を `pip install -r` するだけでテスト実行に必要な依存が揃う
- T3 で `buildspec.yml` から `python -m pytest tests/` を呼び出すだけでテストが実行できる構成になっている
- テストはLambdaハンドラーを直接呼び出す（`sam local` などのコンテナ起動を必要としない）
- 仕様変更時にメンテしやすいよう、テストのアサーションは「何を確認したいか」が読み取れる粒度にする

### 制約事項

- フレームワーク：pytest（最新版）
- Python：3.12（プロジェクト全体と同じ）
- 外部依存はpytest本体のみ（プラグインは原則使わない。必要が出たら別途相談）
- テストは `tests/` 直下に `test_` プレフィックス で配置（`docs/DESIGN.md` のファイル配置ルール）
- 絵文字は使用しない

## 変更内容の設計

### 実装アプローチ

#### Lambdaハンドラーを直接呼び出す方式

`src/cities/app.py` の `list_cities_handler` / `get_city_handler` を Python から直接importして呼び出す。SAM CLI / Docker は不要。

理由：

- ユニットテストの責務は「ハンドラー関数のロジックが期待どおりか」を確かめること。API Gateway や Lambda ランタイムの統合は責務外
- Dockerが要らないので、CodeBuild上でも高速に走り、CI/CD体験のフィードバックループを短く保てる（ワークショップ趣旨と合致）

#### Pythonインポートパス問題の解消

`app.py` は `from data import CITIES` という形で同階層の `data.py` をimportしている。Lambda上ではこれで動くが、pytestをリポジトリルートから走らせると `src/cities/` 配下が `sys.path` に入っておらず ImportError になる。

これを以下の `pytest.ini` をリポジトリルートに置くことで解消：

```ini
[pytest]
pythonpath = src/cities
testpaths = tests
```

理由：

- `conftest.py` で `sys.path.insert` するより、設定ファイルでpythonpathを宣言する方が宣言的かつIDEのテストランナーとも整合する
- `testpaths = tests` で `pytest` 単独実行時にも `tests/` だけが対象になり、誤検出（`src/` 直下の名前衝突など）を避けられる

#### テストファイルの構造

`tests/test_cities.py` に3関数として実装：

```python
import json
from app import list_cities_handler, get_city_handler


def test_list_cities_returns_all_cities():
    response = list_cities_handler({}, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "cities" in body
    assert isinstance(body["cities"], list)
    assert len(body["cities"]) > 0


def test_get_city_returns_existing_city():
    event = {"pathParameters": {"city_id": "tokyo"}}
    response = get_city_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["city_id"] == "tokyo"


def test_get_city_returns_404_for_unknown_city():
    event = {"pathParameters": {"city_id": "unknown"}}
    response = get_city_handler(event, None)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "error" in body
```

- 都市データ追加（名古屋・福岡・札幌）に強いテストにするため、件数は `> 0` でアサート。「具体的に2件」と固定するとハンズオン中の都市追加でテストが壊れてしまう
- レスポンスボディが JSON 文字列であることに注意し、`json.loads` でデコードしてからアサート

#### requirements.txt

```
pytest
```

依存は pytest 本体のみ。バージョンピンしない（学習用なので最新を取り込む方が学習機会が増える）。

### 変更するコンポーネント

| 区分 | パス | 種別 |
|---|---|---|
| 新規 | `pytest.ini` | pytest設定 |
| 新規 | `tests/__init__.py` | パッケージ化（pytestのテスト自動収集と相性が良い） |
| 新規 | `tests/test_cities.py` | ユニットテスト本体 |
| 新規 | `tests/requirements.txt` | テスト用依存（pytest） |

### データ構造の変更

なし。既存の `src/cities/app.py` / `src/cities/data.py` には手を入れない。

### 影響範囲の分析

- T1成果物への影響：なし（読み取り専用でimportするのみ）
- T3（buildspec.yml）への影響：本タスクで定義する `pytest.ini` の存在と `pip install -r tests/requirements.txt` を前提とする
- T5（ハンズオン手順書）への影響：Step 1 で「ローカルでpytestを実行する」手順を書く際に、本タスクで決めたコマンド体系を参照する
- ハンズオン中の都市データ追加への影響：「件数 > 0」のアサートにしておくことで、受講者が `nagoya` 等を追加してもテストが壊れない

## タスクリスト

### 詳細実装タスク

- [x] T2-1: `pytest.ini` をリポジトリルートに作成（`pythonpath = src/cities`, `testpaths = tests`）
- [x] T2-2: `tests/__init__.py` を作成（空ファイル）
- [x] T2-3: `tests/requirements.txt` を作成（pytest）
- [x] T2-4: `tests/test_cities.py` を実装（3テストケース）
- [x] T2-5: ローカルで `pytest` を実行し、3テスト全パスを確認
- [x] T2-6: `docs/TASKS.md` のT2ステータスを `[!]` レビュー待ちに更新

### 検証結果

#### pytest 実行結果（2026-05-16）

```
============================= test session starts ==============================
platform darwin -- Python 3.12.10, pytest-9.0.3, pluggy-1.6.0
configfile: pytest.ini
testpaths: tests
collected 3 items

tests/test_cities.py::test_list_cities_returns_all_cities PASSED         [ 33%]
tests/test_cities.py::test_get_city_returns_existing_city PASSED         [ 66%]
tests/test_cities.py::test_get_city_returns_404_for_unknown_city PASSED  [100%]

============================== 3 passed in 0.01s ===============================
```

3テストすべてパス。`pytest.ini` の `pythonpath` 設定により `from app import ...` が解決され、リポジトリルートから `pytest` を叩くだけで実行できる構成になっている。

### 完了条件

- 上記すべてのタスクが完了している
- `pytest` 実行で「3 passed」を確認できる
- Yoheiのレビューで承認を得ている

## 設計判断の決定事項（2026-05-16 Yoheiレビュー）

| 論点 | 決定 |
|---|---|
| pytest設定ファイルの形式 | `pytest.ini` を採用（`pyproject.toml` は導入しない） |
| テストの粒度（都市数のアサート） | `> 0` でゆるく見る。テストの主眼は仕組み・考え方に慣れることで網羅性ではない |
| `tests/__init__.py` を置くか | 置く |
