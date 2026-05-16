# Step 1: SAMアプリをローカルで動かす

## このStepの目的

これから継続的にデプロイしていく都市情報APIのアプリケーション構造を理解し、ローカル環境でAPI動作とテストを確認します。CI/CDパイプラインに乗せる前に「動くもの」を手元で確認することで、後続Stepでパイプラインが失敗したときの切り分けが容易になります。

## 所要時間

約30分

## 前提

- 作業環境に Python 3.12 / AWS SAM CLI / Docker / git がインストール済み
- Docker Desktop（または同等のDocker環境）が起動している

## このStepのゴール

- アプリのディレクトリ構造を把握している
- `pytest` でユニットテスト3件をパスできる
- `sam build` が成功し、`sam local start-api` でAPIをローカル起動できる
- `curl` でAPIが期待どおりのレスポンスを返すことを確認できている

## 手順

### 1. アプリのソースコードを取得する

講師から配布されたソースコード一式を作業環境に展開してください（Step 2でCodeCommitにpushする対象になります）。

展開後のディレクトリ構造はおおよそ次のとおりです：

```
cities-api/
├── template.yaml          # SAMテンプレート
├── buildspec.yml          # CodeBuild用（骨格、Step 3で完成させます）
├── buildspec_complete.yml # CodeBuild用（完成版、参照用）
├── pytest.ini             # pytest設定
├── src/cities/
│   ├── __init__.py
│   ├── app.py             # Lambdaハンドラー
│   └── data.py            # 都市データ
├── tests/
│   ├── __init__.py
│   ├── requirements.txt
│   └── test_cities.py     # ユニットテスト
└── ...
```

ターミナルで展開先ディレクトリへ移動してください：

```bash
cd cities-api
```

### 2. Python仮想環境とテスト依存をセットアップする

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r tests/requirements.txt
```

### 3. ユニットテストを実行する

```bash
pytest -v
```

3件のテストが PASSED となれば成功です：

```
tests/test_cities.py::test_list_cities_returns_all_cities PASSED
tests/test_cities.py::test_get_city_returns_existing_city PASSED
tests/test_cities.py::test_get_city_returns_404_for_unknown_city PASSED

============================== 3 passed ==============================
```

このテストは、後でCodeBuildでも同じものが自動実行されます。

### 4. SAMアプリをビルドする

```bash
sam build
```

`.aws-sam/build/` 配下に成果物が生成されたら成功です。

### 5. ローカルでAPIを起動する

```bash
sam local start-api --port 3000
```

起動すると以下のような出力が出ます：

```
Mounting ListCitiesFunction at http://127.0.0.1:3000/cities [GET]
Mounting GetCityFunction at http://127.0.0.1:3000/cities/{city_id} [GET]
 * Running on http://127.0.0.1:3000
```

### 6. 別ターミナルでcurlでAPIを叩く

`sam local start-api` は起動したまま、別のターミナルで以下を実行します：

```bash
curl http://127.0.0.1:3000/cities
curl http://127.0.0.1:3000/cities/tokyo
curl http://127.0.0.1:3000/cities/unknown
```

それぞれ以下のような結果が返ればOKです：

- `GET /cities` → 200 / 東京・大阪を含む配列
- `GET /cities/tokyo` → 200 / 東京の情報
- `GET /cities/unknown` → 404 / `City not found`

確認できたら、`sam local start-api` のターミナルで `Ctrl+C` を押して停止します。

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `pytest` で `ModuleNotFoundError: No module named 'app'` | `pytest.ini` の `pythonpath` 設定が読まれていない | リポジトリルートで `pytest` を実行しているか確認 |
| `sam build` で `requirements.txt file not found` 警告 | Lambdaソースに外部依存がないため。エラーではない | そのまま進めてOK |
| `sam local start-api` 起動はOKだが curl が `502 Internal server error` を返す | AWS SSO等のセッション期限切れによりSAMがLambdaコンテナへcredentials注入で失敗 | `sam local` を一度停止し、`AWS_ACCESS_KEY_ID=dummy AWS_SECRET_ACCESS_KEY=dummy AWS_DEFAULT_REGION=ap-northeast-1 sam local start-api --port 3000` で再起動 |
| ポート3000が既に使用中 | 他プロセスが使用 | `--port 3001` 等で別ポート指定 |

## Stepのまとめ

- アプリの構造（SAMテンプレート + Lambdaハンドラー + テスト）を確認しました
- pytestでユニットテストが通ることを確認しました
- SAM CLI でローカルAPIを立ち上げ、curl で3パターンの応答を確認しました

このローカル動作確認が、後続Stepでパイプラインがうまく動かないときの「比較対象」になります。

次は [Step 2](step2.md) で、このコードをCodeCommitにpushしていきます。
