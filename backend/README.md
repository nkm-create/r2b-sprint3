# 学習塾時間割最適化システム - Backend (FastAPI)

## プロジェクト説明

FastAPI + PostgreSQL による REST API サーバー

## セットアップ

### 1. 依存パッケージをインストール

```bash
cd backend
uv sync
```

### 2. 環境変数を設定

```bash
cp .env.example .env
# .env を編集
```

### 3. 開発サーバー起動

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API ドキュメント

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## ディレクトリ構造

```
backend/
├── app/
│   ├── api/v1/           # エンドポイント定義
│   │   ├── endpoints/    # 各エンドポイント
│   │   └── schemas/      # Pydantic models
│   ├── core/             # 設定・依存注入・セキュリティ
│   ├── models/           # ORM models
│   ├── services/         # ビジネスロジック
│   ├── repositories/     # Data Access Layer
│   └── middleware/       # ミドルウェア
├── tests/                # テストファイル
│   ├── unit/
│   └── integration/
└── scripts/              # ユーティリティスクリプト
```

## 開発時の留意点

- 3レイヤーアーキテクチャを遵守（API → Service → Repository）
- TDD で実装
- パスワードは bcrypt (cost=12) でハッシュ化
- JWT + HttpOnly Cookie 認証

## テスト実行

```bash
uv run pytest
```

## OpenAPI スキーマ出力

```bash
uv run python scripts/export_openapi.py -o openapi.json
```
