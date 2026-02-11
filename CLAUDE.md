# CLAUDE.md

このファイルはClaude Code (claude.ai/code) がこのリポジトリで作業する際のガイドラインです。

## プロジェクト概要

**ぼくの読書きろく** — 小学校低学年（6〜8歳）の子供が読んだ本を記録・管理するためのWebアプリケーション。バーコードスキャンまたはISBN手動入力で本を登録し、外部APIから書籍情報を取得する。

## 技術スタック

| 項目 | 技術 | ポート |
|------|------|--------|
| フロントエンド | React (Node 18-alpine) | 3000 |
| バックエンド | Django (Python 3.11-slim) | 8000 |
| データベース | PostgreSQL 15 | 5432 |
| コンテナ管理 | Docker Compose | - |

## よく使うコマンド

```bash
# 全コンテナ一括起動
docker-compose up -d

# 全コンテナ一括停止
docker-compose down

# コード変更後の再ビルド
docker-compose build

# 特定コンテナの再ビルド＆起動
docker-compose up -d --build [frontend|backend]

# ログ確認
docker-compose logs -f [frontend|backend|db]

# Djangoマイグレーション実行
docker-compose exec backend python manage.py migrate

# Djangoマイグレーション作成
docker-compose exec backend python manage.py makemigrations

# Django管理コマンド
docker-compose exec backend python manage.py [command]

# DBバックアップ
docker exec db pg_dump -U user books_db > backup_$(date +%Y%m%d).sql

# DBリストア
cat backup_YYYYMMDD.sql | docker exec -i db psql -U user books_db
```

## ディレクトリ構成

```
ReadingManagementApp/
├── docker-compose.yml          # コンテナオーケストレーション
├── frontend/                   # Reactアプリ
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── components/         # 各画面コンポーネント
│       ├── services/           # API通信モジュール
│       └── App.js
├── backend/                    # Djangoアプリ
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/                 # Djangoプロジェクト設定
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── books/                  # booksアプリケーション
│       ├── models.py           # Bookモデル
│       ├── views.py            # APIビュー
│       ├── serializers.py
│       ├── urls.py
│       └── services.py         # 外部API連携ロジック
├── requirement_spec.md
└── CLAUDE.md
```

## アーキテクチャ

### 書籍登録フロー
```
フロントエンド                    バックエンド                       外部API
    │                                │                                │
    │ ISBN送信 (POST /api/books/)    │                                │
    │──────────────────────────────→ │                                │
    │                                │ ISBN検索                       │
    │                                │──────────────────────────────→ │ NDLサーチAPI
    │                                │ ← 書籍情報（タイトル等）       │
    │                                │                                │
    │                                │ [表紙画像なしの場合]            │
    │                                │──────────────────────────────→ │ Google Books API
    │                                │ ← 表紙画像URL                  │
    │                                │                                │
    │                                │ DB保存                         │
    │ ← 登録結果                     │                                │
```

### 外部API

| API | エンドポイント | 用途 |
|-----|---------------|------|
| NDLサーチ OpenSearch | `https://ndlsearch.ndl.go.jp/api/opensearch` | ISBN→書籍情報（メイン） |
| Google Books API | `https://www.googleapis.com/books/v1/volumes` | 表紙画像取得（フォールバック） |

### データモデル（Bookテーブル）

| カラム | 型 | 制約 |
|--------|-----|------|
| id | INTEGER | PRIMARY KEY, AUTO INCREMENT |
| isbn | VARCHAR(13) | UNIQUE, NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| cover_image_url | TEXT | NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() |

### 画面構成と遷移

```
メニュー画面
├── 本の登録（バーコード） → 登録完了 → メニュー
├── 本の登録（手動入力）   → 登録完了 → メニュー
├── 本の一覧             → 削除確認 → 一覧更新
└── 検索                 → 結果表示
```

## デザイン制約（必須遵守）

- **UIテキストは全てひらがな表記**：ボタン・ラベル・エラーメッセージ全て（例:「とうろくする」「さくじょ」「みつかりませんでした」）。APIから取得した書籍タイトル・著者名はそのまま表示。
- **パステルカラー基調**：子供向けの優しい色合い。
- **大きなボタン**：小学校低学年が操作しやすいサイズ。
- **レスポンシブ対応**：スマートフォン・タブレット・PCで動作。
- **認証なし**：家庭内LANのみで使用するため、ログイン機能は不要。

### エラーメッセージ一覧

| 状況 | メッセージ |
|------|-----------|
| 書籍が見つからない | 「みつかりませんでした」 |
| APIタイムアウト | 「みつかりませんでした」 |
| バーコード読み取り失敗 | 「もういちどためしてください」 |
| ネットワークエラー | 「つながりませんでした」 |
| データベースエラー | 「エラーがおきました」 |

---

## 開発フェーズとタスク

### Phase 1: Docker環境構築・DB設計

| # | タスク | 詳細 |
|---|--------|------|
| 1-1 | ✅ docker-compose.yml作成 | frontend / backend / db の3コンテナ定義、app-network作成、postgres-dataボリューム定義 |
| 1-2 | ✅ backend用Dockerfile作成 | python:3.11-slim ベース、requirements.txt インストール、manage.py 起動設定 |
| 1-3 | ✅ frontend用Dockerfile作成 | node:18-alpine ベース、npm install、開発サーバー起動設定 |
| 1-4 | ✅ Djangoプロジェクト初期化 | `django-admin startproject config .` でプロジェクト作成、settings.pyでPostgreSQL接続設定 |
| 1-5 | ✅ booksアプリ作成 | `python manage.py startapp books`、INSTALLED_APPSへの登録 |
| 1-6 | ✅ Bookモデル定義 | isbn / title / cover_image_url / created_at カラム定義 |
| 1-7 | ✅ マイグレーション実行 | makemigrations → migrate でテーブル作成 |
| 1-8 | ✅ Docker環境動作確認 | `docker-compose up` で3コンテナが正常に起動し通信できることを確認 |

### Phase 2: バックエンドAPI開発

| # | タスク | 詳細 |
|---|--------|------|
| 2-1 | ✅ Django REST Framework導入 | requirements.txtへの追加、settings.py設定 |
| 2-2 | ✅ Bookシリアライザー作成 | BookSerializer定義（全フィールド） |
| 2-3 | ✅ NDLサーチAPI連携サービス作成 | ISBNでNDL OpenSearch APIを呼び出し、XMLレスポンスからタイトル・表紙画像URLを抽出 |
| 2-4 | ✅ Google Books API連携サービス作成 | ISBNでGoogle Books APIを呼び出し、表紙画像URLを取得するフォールバック処理 |
| 2-5 | ✅ 書籍登録APIエンドポイント作成 | `POST /api/books/` — ISBN受取→外部API検索→DB保存→結果返却 |
| 2-6 | ✅ 書籍一覧APIエンドポイント作成 | `GET /api/books/` — 並び順パラメータ対応（登録日時順 / タイトル50音順） |
| 2-7 | ✅ 書籍削除APIエンドポイント作成 | `DELETE /api/books/{id}/` — 指定IDの書籍を削除 |
| 2-8 | ✅ 書籍検索APIエンドポイント作成 | `GET /api/books/search/?q=` — タイトル部分一致検索 |
| 2-9 | ✅ エラーハンドリング実装 | APIタイムアウト(5秒)、書籍未発見、ネットワークエラー、DB エラーの各ケース |
| 2-10 | ✅ CORS設定 | django-cors-headers導入、フロントエンド(port 3000)からのアクセス許可 |

### Phase 3: フロントエンド開発

| # | タスク | 詳細 |
|---|--------|------|
| 3-1 | ✅ Reactプロジェクト初期化 | Create React App またはViteでプロジェクト作成 |
| 3-2 | ✅ ルーティング設定 | React Routerで5画面のルート定義 |
| 3-3 | ✅ 共通スタイル設定 | パステルカラーのテーマ定義、大きなボタンの共通CSS、レスポンシブ対応 |
| 3-4 | ✅ API通信モジュール作成 | axios等でバックエンドAPI呼び出しの共通処理を定義 |
| 3-5 | ✅ メニュー画面実装 | タイトル表示、4つのナビゲーションボタン（ひらがな表記） |
| 3-6 | ✅ 本の登録画面（手動入力）実装 | ISBN入力フォーム（数字のみ）、登録ボタン、結果メッセージ表示、メニューへの遷移 |
| 3-7 | ✅ 本の登録画面（バーコード）実装 | カメラ起動・バーコードスキャンライブラリ(QuaggaJS/html5-qrcode)統合、ISBN読み取り→登録処理 |
| 3-8 | ✅ 本の一覧画面実装 | 書籍リスト表示（表紙画像+タイトル）、並び替え切替（あたらしいじゅん/あいうえおじゅん）、削除ボタン+確認ダイアログ |
| 3-9 | ✅ 検索画面実装 | 検索ボックス、検索結果リスト表示、該当なしメッセージ |
| 3-10 | ✅ エラーハンドリングUI実装 | ひらがなエラーメッセージ表示、「メニューにもどる」ボタン |

### Phase 4: 統合テスト・デバッグ

| # | タスク | 詳細 |
|---|--------|------|
| 4-1 | ✅ バックエンド単体テスト | 各APIエンドポイントのテスト（正常系・異常系） |
| 4-2 | ✅ 外部API連携テスト | NDLサーチAPI・Google Books APIの実際のレスポンス確認、フォールバック動作テスト |
| 4-3 | ✅ フロントエンド・バックエンド結合テスト | 画面操作→API呼び出し→DB保存の一連のフロー確認 |
| 4-4 | バーコードスキャンテスト | 実機（スマートフォン・タブレット）でのカメラ起動・バーコード読み取りテスト |
| 4-5 | レスポンシブ表示テスト | スマートフォン・タブレット・PCそれぞれでのUI表示確認 |
| 4-6 | エラーケーステスト | 全エラーパターン（書籍未発見、タイムアウト、ネットワークエラー等）の動作確認 |

### Phase 5: Docker Compose最適化・最終確認

| # | タスク | 詳細 |
|---|--------|------|
| 5-1 | コンテナ間通信の最適化 | ネットワーク設定の見直し、ヘルスチェック設定追加 |
| 5-2 | 環境変数の整理 | DB接続情報等を.envファイルに外出し |
| 5-3 | 本番ビルド設定 | フロントエンドのプロダクションビルド対応 |
| 5-4 | データ永続化確認 | コンテナ再起動後のデータ保持確認 |
| 5-5 | 起動・停止手順の最終確認 | `docker-compose up/down` の動作確認、README作成 |

---

完了したタスクは更新する
