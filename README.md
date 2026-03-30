# 学習塾 時間割最適化システム

個別指導塾（1:2 指導）の時間割作成を AI で自動化する Web アプリ。

月 30 時間かかっていた時間割作成を **3 時間以下**に、1:1 授業率を **5% 以下**に削減することを目標とする。

---

## 起動手順

### 前提条件

- Docker / Docker Compose
- Node.js 20+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

---

### 1. DB 起動（PostgreSQL）

```bash
docker compose up -d
```

| サービス | URL |
|---------|-----|
| PostgreSQL | `localhost:5432` |
| pgAdmin (DB管理UI) | http://localhost:5050 (admin@example.com / admin) |

---

### 2. バックエンド起動（FastAPI）

```bash
cd backend

# 環境変数を設定
cp .env.example .env
# .env の JWT_SECRET_KEY を任意の文字列に変更

# 依存パッケージをインストール
uv sync

# DB マイグレーション
uv run alembic upgrade head

# テストデータ投入（任意）
uv run python scripts/seed_subjects.py
uv run python scripts/seed_test_user.py

# サーバー起動
uv run uvicorn app.main:app --reload
```

| エンドポイント | 説明 |
|------------|------|
| http://localhost:8000 | API ルート |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/api/v1/health | ヘルスチェック |

---

### 3. フロントエンド起動（Next.js）

```bash
cd frontend

# 依存パッケージをインストール
npm install

# 開発サーバー起動
npm run dev
```

→ http://localhost:3000 でアクセス可能

---

### 4. ワイヤーフレームを見る

サーバー不要で全 13 画面のプロトタイプを確認できます。

```bash
open wireframe/index.html
```

---

## テスト実行

```bash
# バックエンド
cd backend
uv run pytest

# フロントエンド
cd frontend
npm test
```

---

## プロジェクト構成

```
r2b-sprint3/
├── backend/                    # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── api/v1/             # エンドポイント
│   │   ├── models/             # SQLAlchemy ORM モデル
│   │   ├── services/           # ビジネスロジック・最適化ソルバー
│   │   ├── repositories/       # DB アクセス層
│   │   └── core/               # 設定・認証・DB接続
│   ├── alembic/                # DB マイグレーション
│   ├── scripts/                # シードスクリプト
│   └── pyproject.toml
├── frontend/                   # Next.js 14 + Tailwind CSS
│   └── src/
│       ├── app/                # App Router（ページ）
│       ├── components/         # UI コンポーネント
│       ├── hooks/              # カスタム hooks
│       ├── stores/             # Zustand 状態管理
│       └── lib/api/            # API クライアント
├── infrastructure/terraform/   # AWS インフラ（ECS / RDS / VPC）
├── wireframe/index.html        # ブラウザで開くプロトタイプ
├── docs/requirements/          # 設計ドキュメント一式
└── docker-compose.yml          # PostgreSQL + pgAdmin
```

---

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | Next.js 14, Tailwind CSS, Radix UI, TanStack Query, Zustand |
| バックエンド | FastAPI, SQLAlchemy 2.0 (AsyncSession), Alembic |
| DB | PostgreSQL 16 |
| 認証 | JWT (httpOnly Cookie) |
| 最適化 | 遺伝的アルゴリズム / CSP / ILP / SA / Greedy など6種類 + LLM Agent |
| インフラ | AWS (ECS Fargate, RDS, VPC) / Terraform |
| パッケージ管理 | uv (Python), npm (Node.js) |

---

## 主な画面

| 画面 | 役割 |
|------|------|
| ログイン | JWT 認証 |
| ダッシュボード | 充足率・ヒートマップ表示 |
| 時間割作成 | AI による自動最適化・手動調整 |
| 講師・生徒管理 | CRUD + CSV インポート |
| 振替対応 | 欠席登録・代替案提示 |
| マネジメント | 複数教室の一括監視（エリアマネジャー用） |
