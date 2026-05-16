# Step 5: パイプラインの効果を体験する

## このStepの目的

ここまでで構築したCI/CDパイプラインが「実際にどんな価値を生むか」を、3つの具体的シナリオで体験します。

1. 新機能の素早い反映（都市追加）
2. テストによる安全網（不具合のあるコードがpushされた時にパイプラインが止まる）
3. 修正の素早い反映（再push）

## 所要時間

約30分

## 前提

- Step 3 / Step 4 が完了し、開発パイプラインと本番パイプラインが両方とも動作している
- `develop` / `main` の両ブランチが揃っている

## このStepのゴール

- 開発環境に名古屋を追加して、developパイプラインで反映されることを確認している
- 意図的にバグを入れたコードをpushして、テスト失敗でパイプラインが止まることを確認している
- バグを修正して再pushし、パイプラインが成功に戻ることを確認している

## シナリオ1：新都市の追加

ハンズオン仕様で、初期データは東京・大阪のみです。新しい都市「名古屋」を追加して、それが開発パイプラインで自動デプロイされることを体験します。

### 1. data.py を編集する

`src/cities/data.py` を以下のように編集します。`osaka` の後ろに `nagoya` を追加します：

```python
CITIES = {
    "tokyo": {
        "city_id": "tokyo",
        "name": "東京",
        "population": 14000000,
        "region": "関東",
    },
    "osaka": {
        "city_id": "osaka",
        "name": "大阪",
        "population": 8800000,
        "region": "近畿",
    },
    "nagoya": {
        "city_id": "nagoya",
        "name": "名古屋",
        "population": 2300000,
        "region": "中部",
    },
}
```

### 2. ローカルでテストを実行する

```bash
pytest -v
```

3件すべてpassすることを確認します（テストは「件数 > 0」で見るので、データを増やしても通ります）。

### 3. develop ブランチに push する

```bash
git checkout develop
git add src/cities/data.py
git commit -m "Add nagoya to cities"
git push origin develop
```

### 4. 開発パイプラインの実行を確認する

CodePipeline画面で `cities-api-pipeline-dev` を開き、Source → Build → Deploy が順に Succeeded になることを確認します。

完了後、開発環境のAPIに名古屋が含まれていることを確認：

```bash
curl https://xxxx.execute-api.region.amazonaws.com/dev/cities
curl https://xxxx.execute-api.region.amazonaws.com/dev/cities/nagoya
```

`/cities/nagoya` で名古屋の情報が返れば成功です。

## シナリオ2：テストによる安全網

ここで意図的にバグを仕込んでpushします。テストが正しく落ち、パイプラインが止まり、開発環境が壊れない様子を確認します。

### 1. app.py に意図的なバグを入れる

`src/cities/app.py` の `get_city_handler` を以下のように書き換えます。`city_id` の参照を破壊的に変更します：

```python
def get_city_handler(event, context):
    city_id = event["pathParameters"]["city_id"]
    city = CITIES.get("typo_" + city_id)  # ←ここに意図的なバグを仕込む
    if city is None:
        return _response(404, {"error": "City not found", "city_id": city_id})
    return _response(200, city)
```

このバグだと、どのcity_idで呼んでも常に404が返るようになります。

### 2. ローカルで pytest を実行して落ちることを確認する

```bash
pytest -v
```

`test_get_city_returns_existing_city` が FAILED となるはずです：

```
FAILED tests/test_cities.py::test_get_city_returns_existing_city
- assert 404 == 200
```

これがあるからこそ、後続のCI/CDで安全網になります。

### 3. 意図的に develop ブランチに push する

```bash
git add src/cities/app.py
git commit -m "BAD: introduce bug for demo"
git push origin develop
```

### 4. 開発パイプラインの失敗を確認する

CodePipeline画面を見ると、Build ステージが **Failed**（赤）になります。

- **View logs** をクリックして CloudWatch のビルドログを確認
- `pre_build` フェーズの `pytest` のところで `1 failed` のログがあるはず
- Build が失敗したので Deploy は実行されず、**開発環境は前のバージョンのまま守られている**

これがCI/CDの安全網としての価値です。テストを書いていれば、壊れたコードを本番に届ける前に止められます。

curl で開発環境のAPIを叩いてみると、まだ正常に動いていることが確認できます：

```bash
curl https://xxxx.execute-api.region.amazonaws.com/dev/cities/tokyo
# → 200 / 東京の情報（壊れたコードはデプロイされていない）
```

<!-- screenshot: CodePipelineでBuildステージがFailedになっている画面 -->

## シナリオ3：修正して再デプロイする

バグを直して再pushすれば、パイプラインがまた通って開発環境が更新されます。

### 1. app.py のバグを修正する

`src/cities/app.py` の `get_city_handler` を元に戻します：

```python
def get_city_handler(event, context):
    city_id = event["pathParameters"]["city_id"]
    city = CITIES.get(city_id)  # 修正
    if city is None:
        return _response(404, {"error": "City not found", "city_id": city_id})
    return _response(200, city)
```

### 2. ローカルでテストを通す

```bash
pytest -v
```

3件すべてpassすることを再度確認します。

### 3. develop ブランチに push する

```bash
git add src/cities/app.py
git commit -m "Fix: restore correct city lookup"
git push origin develop
```

### 4. パイプラインが成功して開発環境が更新される

CodePipeline画面で `cities-api-pipeline-dev` を確認すると、今度は Source → Build → Deploy すべて Succeeded になります。

curl で開発環境を確認：

```bash
curl https://xxxx.execute-api.region.amazonaws.com/dev/cities/tokyo
# → 200 / 東京の情報（正常に戻った）
```

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| シナリオ1で名古屋を追加したのに `/cities` のレスポンスに反映されない | パイプラインが完了する前にcurlした、もしくはAPI Gatewayのキャッシュ | 1-2分待ってから再度curl |
| シナリオ2でpushしたのに Build が成功してしまう | `buildspec.yml` の `pre_build` で `pytest` が実行されていない（写経漏れ） | `buildspec.yml` を `buildspec_complete.yml` と diff で比較 |
| シナリオ2の Build ログを開いてもエラー内容が見えない | ログのフィルタが厳しい | CloudWatch Logs Insights で `/aws/codebuild/cities-api-build-dev` を直接開くと全文見える |

## このハンズオン全体のまとめ

ここまでの体験で得たもの：

- **継続的インテグレーション**: pushされた変更を自動でテスト・ビルドする仕組み
- **継続的デリバリー**: テストを通った変更を自動でデプロイする仕組み
- **環境分離**: ブランチごとに異なる環境（dev/prod）へデプロイする運用
- **手動承認**: 自動化と人間の判断のバランス（本番反映）
- **テストの効果**: 意図しない変更が本番に届かない安全網

実際の業務開発では、ここにフィーチャーフラグ・カナリアリリース・複数のテスト層（統合・E2E）・運用監視連携などが加わりますが、いずれも今回学んだ「コミット → 自動処理 → 環境反映」の基本パターンの応用です。

## 後片付け

ハンズオンで作成したAWSリソースは、課金や残骸を避けるため必ず削除してください。

詳細手順は [cleanup.md](cleanup.md) を参照してください。
