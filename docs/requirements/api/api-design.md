# API設計書

> 学習塾時間割最適化システム API設計書
> DB設計書・要件定義書v2・IPO一覧から作成

---

## 目次

1. [概要](#1-概要)
2. [認証・認可](#2-認証認可)
3. [共通仕様](#3-共通仕様)
4. [API一覧](#4-api一覧)
5. [エンドポイント詳細](#5-エンドポイント詳細)
6. [エラーハンドリング](#6-エラーハンドリング)

---

## 1. 概要

### 1.1 基本情報

| 項目 | 内容 |
|------|------|
| ベースURL | `https://api.example.com/api` |
| APIバージョン | v1（URLに含めない） |
| データ形式 | JSON（UTF-8） |
| 文字コード | UTF-8 |
| 日時形式 | ISO 8601（例: `2025-03-24T10:00:00Z`） |

### 1.2 API統計

| カテゴリ | エンドポイント数 |
|---------|-----------------|
| 認証（P001） | 5 |
| ダッシュボード（P002） | 7 |
| マネジメントダッシュボード（P003） | 4 |
| 教室設定（P004） | 8 |
| 講師管理（P005） | 7 |
| 生徒管理（P006） | 7 |
| 希望データ（P007） | 5 |
| 条件設定（P008） | 7 |
| 時間割作成（P009） | 11 |
| 振替対応（P010） | 5 |
| ターム管理（P011） | 6 |
| ユーザー管理（P012） | 5 |
| 教室マスタ管理（P013） | 4 |
| 共通機能 | 6 |
| **合計** | **87** |

---

## 2. 認証・認可

### 2.1 認証方式

| 項目 | 内容 |
|------|------|
| 認証方式 | JWT（Bearer Token） |
| アクセストークン有効期限 | 1時間 |
| リフレッシュトークン有効期限 | 7日間 |
| パスワードハッシュ | bcrypt（cost=12） |
| アカウントロック | 5回失敗で30分ロック |

### 2.2 トークン取得

```
POST /api/auth/login

Authorization: なし（公開エンドポイント）
```

### 2.3 認証ヘッダー

```
Authorization: Bearer {access_token}
```

### 2.4 ロールと権限

| ロール | 説明 | 主な権限 |
|--------|------|---------|
| `system_admin` | システム管理者 | 全機能へのアクセス |
| `area_manager` | エリアマネジャー | 担当エリアの教室参照 |
| `classroom_manager` | 教室長 | 担当教室の全機能 |

### 2.5 アクセス制御マトリクス

| 機能 | 教室長 | エリアマネジャー | システム管理者 |
|------|--------|----------------|---------------|
| 教室設定 | 自教室のみ | 参照のみ | 全権限 |
| 講師管理 | 自教室のみ | 参照のみ | 全権限 |
| 生徒管理 | 自教室のみ | 参照のみ | 全権限 |
| 時間割作成 | 自教室のみ | 参照のみ | 全権限 |
| ユーザー管理 | × | × | 全権限 |
| 教室マスタ管理 | × | × | 全権限 |

---

## 3. 共通仕様

### 3.1 リクエスト形式

#### ヘッダー

```
Content-Type: application/json
Authorization: Bearer {access_token}
Accept: application/json
```

#### クエリパラメータ規則

| パラメータ | 形式 | 例 |
|-----------|------|-----|
| 検索 | `q={検索文字列}` | `?q=田中` |
| フィルター | `filter[{field}]={value}` | `?filter[status]=active` |
| ソート | `sort={field}` または `sort=-{field}` | `?sort=-created_at` |
| ページネーション | `page={n}&per_page={n}` | `?page=1&per_page=20` |

### 3.2 レスポンス形式

#### 成功レスポンス（単一リソース）

```json
{
  "data": {
    "id": "uuid",
    "type": "teacher",
    "attributes": { ... }
  }
}
```

#### 成功レスポンス（リスト）

```json
{
  "data": [ ... ],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}
```

#### エラーレスポンス

```json
{
  "error": {
    "code": "VAL_001",
    "message": "メールアドレスの形式が正しくありません",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### 3.3 HTTPステータスコード

| コード | 意味 | 使用場面 |
|--------|------|---------|
| 200 | OK | 取得・更新成功 |
| 201 | Created | 新規作成成功 |
| 204 | No Content | 削除成功 |
| 400 | Bad Request | バリデーションエラー |
| 401 | Unauthorized | 認証エラー |
| 403 | Forbidden | 権限エラー |
| 404 | Not Found | リソース未検出 |
| 409 | Conflict | 重複・競合エラー |
| 500 | Internal Server Error | システムエラー |

---

## 4. API一覧

### 4.1 認証（P001）

| # | メソッド | エンドポイント | 機能ID | 機能名 | 認証 |
|---|---------|---------------|--------|--------|------|
| 1 | POST | `/api/auth/login` | F001 | ログイン | × |
| 2 | POST | `/api/auth/password-reset/request` | F002 | パスワードリセット要求 | × |
| 3 | POST | `/api/auth/password-reset/execute` | F002 | パスワードリセット実行 | × |
| 4 | POST | `/api/auth/refresh` | F003 | トークンリフレッシュ | × |
| 5 | POST | `/api/auth/password/change` | F004 | 初回パスワード変更 | ○ |

### 4.2 ダッシュボード - 教室長（P002）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 6 | GET | `/api/classrooms/{classroom_id}/dashboard` | F010 | ダッシュボード表示 |
| 7 | GET | `/api/classrooms/{classroom_id}/dashboard/fulfillment` | F011 | 充足率サマリー取得 |
| 8 | GET | `/api/classrooms/{classroom_id}/dashboard/heatmap` | F012 | 人員状況ヒートマップ取得 |
| 9 | GET | `/api/classrooms/{classroom_id}/dashboard/subject-coverage` | F013 | 科目別カバー率取得 |
| 10 | GET | `/api/classrooms/{classroom_id}/dashboard/supply-demand` | F014 | 需給バランス取得 |
| 11 | GET | `/api/users/{user_id}/notifications` | F015 | 通知一覧取得 |
| 12 | PATCH | `/api/notifications/{notification_id}/read` | F015 | 通知既読更新 |

### 4.3 マネジメントダッシュボード（P003）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 13 | GET | `/api/areas/{area_id}/dashboard` | F020 | マネジメントダッシュボード表示 |
| 14 | GET | `/api/areas/{area_id}/classrooms` | F021 | 教室別充足率一覧取得 |
| 15 | GET | `/api/areas/{area_id}/alerts` | F023 | 問題教室アラート取得 |
| 16 | GET | `/api/areas/{area_id}/compare` | F024 | 教室比較データ取得 |

### 4.4 教室設定（P004）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 17 | GET | `/api/classrooms/{classroom_id}/time-slots` | F030 | 時間枠設定取得 |
| 18 | PUT | `/api/classrooms/{classroom_id}/time-slots` | F030 | 時間枠設定更新 |
| 19 | PUT | `/api/classrooms/{classroom_id}/settings/operating-days` | F031 | 営業曜日設定更新 |
| 20 | PUT | `/api/classrooms/{classroom_id}/settings/capacity` | F032 | キャパシティ設定更新 |
| 21 | POST | `/api/classrooms/{classroom_id}/settings/apply-default` | F033 | デフォルト設定適用 |
| 22 | POST | `/api/classrooms/{classroom_id}/google-form-connections` | F034 | Google Form連携設定 |
| 23 | GET | `/api/auth/google/authorize` | F034 | Google OAuth認証開始 |
| 24 | GET | `/api/auth/google/callback` | F034 | Google OAuthコールバック |

### 4.5 講師管理（P005）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 25 | GET | `/api/classrooms/{classroom_id}/teachers` | F040 | 講師一覧表示 |
| 26 | POST | `/api/classrooms/{classroom_id}/teachers` | F041 | 講師新規登録 |
| 27 | PUT | `/api/classrooms/{classroom_id}/teachers/{teacher_id}` | F042 | 講師情報編集 |
| 28 | DELETE | `/api/classrooms/{classroom_id}/teachers/{teacher_id}` | F043 | 講師削除 |
| 29 | POST | `/api/classrooms/{classroom_id}/teachers/import` | F044 | 講師CSVインポート（プレビュー） |
| 30 | POST | `/api/classrooms/{classroom_id}/teachers/import/execute` | F044 | 講師CSVインポート（実行） |
| 31 | GET | `/api/classrooms/{classroom_id}/teachers/export` | F046 | 講師CSVエクスポート |

### 4.6 生徒管理（P006）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 32 | GET | `/api/classrooms/{classroom_id}/students` | F050 | 生徒一覧表示 |
| 33 | POST | `/api/classrooms/{classroom_id}/students` | F051 | 生徒新規登録 |
| 34 | PUT | `/api/classrooms/{classroom_id}/students/{student_id}` | F052 | 生徒情報編集 |
| 35 | DELETE | `/api/classrooms/{classroom_id}/students/{student_id}` | F053 | 生徒削除 |
| 36 | POST | `/api/classrooms/{classroom_id}/students/import` | F054 | 生徒CSVインポート（プレビュー） |
| 37 | POST | `/api/classrooms/{classroom_id}/students/import/execute` | F054 | 生徒CSVインポート（実行） |
| 38 | GET | `/api/classrooms/{classroom_id}/students/export` | F056 | 生徒CSVエクスポート |

### 4.7 希望データ（P007）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 39 | GET | `/api/classrooms/{classroom_id}/terms/{term_id}/preferences` | F060 | 希望データマトリクス表示 |
| 40 | PUT | `/api/classrooms/{classroom_id}/terms/{term_id}/preferences` | F062 | 希望データ編集 |
| 41 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/preferences/sync` | F063 | Google Form同期 |
| 42 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/preferences/sync/confirm` | F063 | Google Form同期確認 |
| 43 | GET | `/api/classrooms/{classroom_id}/terms/{term_id}/preferences/unanswered` | F064 | 未回答者確認 |

### 4.8 条件設定（P008）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 44 | POST | `/api/classrooms/{classroom_id}/terms` | F070 | ターム作成 |
| 45 | GET | `/api/classrooms/{classroom_id}/terms/{term_id}/master-status` | F071 | マスタ反映状況確認 |
| 46 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/constraints` | F072 | ターム固有調整設定 |
| 47 | PUT | `/api/classrooms/{classroom_id}/terms/{term_id}/policies` | F073 | 全体ポリシー設定 |
| 48 | POST | `/api/classrooms/{classroom_id}/policy-templates` | F074 | ポリシーテンプレート保存 |
| 49 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/apply-template` | F074 | テンプレート適用 |
| 50 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/copy-from` | F074 | 前タームからコピー |

### 4.9 時間割作成（P009）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 51 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/schedules/analyze` | F080 | 問題分析・戦略決定 |
| 52 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/schedules/generate` | F081 | 時間割生成（一発求解） |
| 53 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/schedules/regenerate` | F081 | 緩和適用後の再生成 |
| 54 | GET | `/api/schedules/{schedule_id}/explanation` | F082 | 結果説明取得 |
| 55 | POST | `/api/schedules/{schedule_id}/what-if` | F082 | What-if分析 |
| 56 | GET | `/api/schedules/{schedule_id}/calendar-view` | F083 | カレンダービュー表示 |
| 57 | GET | `/api/schedules/{schedule_id}/slots/{slot_id}/movable-targets` | F085 | 移動可能先確認 |
| 58 | PUT | `/api/schedules/{schedule_id}/slots/{slot_id}/move` | F085 | コマ移動 |
| 59 | POST | `/api/schedules/{schedule_id}/confirm` | F086 | 時間割確定 |
| 60 | POST | `/api/schedules/{schedule_id}/export` | F087 | PDF/CSV出力 |
| 61 | WS | `/api/schedules/{schedule_id}/progress` | F081 | 生成進捗通知（WebSocket） |

### 4.10 振替対応（P010）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 62 | GET | `/api/classrooms/{classroom_id}/schedules/{schedule_id}/slots` | F090 | 対象者コマ一覧取得 |
| 63 | POST | `/api/classrooms/{classroom_id}/absences` | F090 | 欠席登録 |
| 64 | GET | `/api/classrooms/{classroom_id}/absences/{absence_id}/reschedule-candidates` | F091 | 振替候補提案 |
| 65 | POST | `/api/classrooms/{classroom_id}/absences/{absence_id}/reschedule` | F092 | 振替確定 |
| 66 | GET | `/api/classrooms/{classroom_id}/absences` | F093 | 欠席・振替履歴表示 |

### 4.11 ターム管理（P011）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 67 | GET | `/api/classrooms/{classroom_id}/terms` | F100 | ターム一覧表示 |
| 68 | GET | `/api/classrooms/{classroom_id}/terms/{term_id}` | F101 | ターム詳細確認 |
| 69 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/duplicate` | F102 | ターム複製 |
| 70 | PUT | `/api/classrooms/{classroom_id}/terms/{term_id}` | F103 | ターム編集 |
| 71 | DELETE | `/api/classrooms/{classroom_id}/terms/{term_id}` | F104 | ターム削除 |
| 72 | POST | `/api/classrooms/{classroom_id}/terms/{term_id}/archive` | F104 | タームアーカイブ化 |

### 4.12 ユーザー管理（P012）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 73 | GET | `/api/users` | F110 | ユーザー一覧表示 |
| 74 | POST | `/api/users` | F111 | ユーザー新規作成 |
| 75 | PUT | `/api/users/{user_id}` | F112 | ユーザー情報編集 |
| 76 | DELETE | `/api/users/{user_id}` | F113 | ユーザー削除 |
| 77 | POST | `/api/users/{user_id}/reset-password` | F114 | パスワードリセット（管理者） |

### 4.13 教室マスタ管理（P013）

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 78 | GET | `/api/classrooms` | F120 | 教室一覧表示 |
| 79 | POST | `/api/classrooms` | F121 | 教室新規作成 |
| 80 | PUT | `/api/classrooms/{classroom_id}` | F122 | 教室情報編集 |
| 81 | DELETE | `/api/classrooms/{classroom_id}` | F123 | 教室削除 |

### 4.14 共通機能

| # | メソッド | エンドポイント | 機能ID | 機能名 |
|---|---------|---------------|--------|--------|
| 82 | GET | `/api/{resource}?q={検索文字列}` | FC01 | テキスト検索 |
| 83 | GET | `/api/{resource}?filter[field]=value` | FC02 | フィルタリング |
| 84 | GET | `/api/{resource}?sort={field}` | FC03 | ソート |
| 85 | GET | `/api/{resource}?page={n}&per_page={n}` | FC04 | ページネーション |
| 86 | POST | `/api/{resource}/{id}/restore` | FC05 | 削除取消（管理者のみ） |
| 87 | GET | `/api/{resource}/export?format=csv` | FC06 | CSV出力 |

---

## 5. エンドポイント詳細

### 5.1 認証 API

#### POST /api/auth/login

- **機能ID**: F001
- **目的**: ユーザー認証とJWTトークン発行
- **認証**: 不要
- **対応テーブル**: users, refresh_tokens, audit_logs

**リクエスト**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| email | string | Yes | メールアドレス（RFC 5322準拠） |
| password | string | Yes | パスワード（8〜72文字） |

```json
{
  "email": "user@example.com",
  "password": "********"
}
```

**レスポンス（成功: 200 OK）**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "山田 太郎",
    "role": "classroom_manager",
    "force_password_change": false
  }
}
```

**エラー**

| ステータス | コード | メッセージ |
|-----------|--------|----------|
| 401 | AUTH_001 | メールアドレスまたはパスワードが正しくありません |
| 401 | AUTH_002 | このアカウントは無効です |
| 401 | AUTH_003 | アカウントがロックされています。{N}分後に再試行してください |

---

#### POST /api/auth/refresh

- **機能ID**: F003
- **目的**: アクセストークンの更新
- **認証**: 不要（リフレッシュトークン使用）
- **対応テーブル**: refresh_tokens, users

**リクエスト**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**レスポンス（成功: 200 OK）**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**エラー**

| ステータス | コード | メッセージ |
|-----------|--------|----------|
| 401 | AUTH_006 | セッションが無効です。再ログインしてください |

---

#### POST /api/auth/password/change

- **機能ID**: F004
- **目的**: 初回パスワード変更
- **認証**: 必須
- **対応テーブル**: users

**リクエスト**

```json
{
  "current_password": "********",
  "new_password": "********"
}
```

**レスポンス（成功: 200 OK）**

```json
{
  "message": "パスワードを変更しました"
}
```

**エラー**

| ステータス | コード | メッセージ |
|-----------|--------|----------|
| 401 | AUTH_005 | 現在のパスワードが正しくありません |
| 400 | VAL_003 | 新パスワードは8文字以上で入力してください |
| 400 | VAL_004 | 新パスワードは英字と数字を含めてください |

---

### 5.2 ダッシュボード API

#### GET /api/classrooms/{classroom_id}/dashboard

- **機能ID**: F010
- **目的**: 教室長ダッシュボードの全データ取得
- **認証**: 必須
- **権限**: classroom_manager（自教室）, area_manager（担当エリア）, system_admin
- **対応テーブル**: schedules, schedule_slots, teachers, students, notifications, terms

**レスポンス（成功: 200 OK）**

```json
{
  "fulfillment_summary": {
    "current_rate": 85.3,
    "target_rate": 85.0,
    "one_to_two_slots": 136,
    "one_to_one_slots": 58,
    "unassigned_slots": 0,
    "trend": "up",
    "change_from_last_week": 2.1
  },
  "heatmap": {
    "mon": {
      "1": { "supply": 6, "demand": 5, "status": "sufficient" },
      "2": { "supply": 5, "demand": 7, "status": "shortage" }
    }
  },
  "subject_coverage": [
    { "subject_id": "JHS_MATH_PUB", "subject_name": "中学数学（公立）", "coverage_rate": 95, "status": "sufficient" },
    { "subject_id": "JHS_ENG", "subject_name": "中学英語", "coverage_rate": 78, "status": "warning" }
  ],
  "supply_demand": {
    "total_supply": 150,
    "total_demand": 142,
    "balance": 8
  },
  "alerts": [
    {
      "type": "low_coverage",
      "message": "中学英語のカバー率が78%です",
      "severity": "warning"
    }
  ],
  "current_term": {
    "term_id": "uuid",
    "term_name": "2025年4月期",
    "status": "draft"
  }
}
```

---

### 5.3 講師管理 API

#### GET /api/classrooms/{classroom_id}/teachers

- **機能ID**: F040
- **目的**: 講師一覧の取得（検索・フィルター対応）
- **認証**: 必須
- **権限**: classroom_manager（自教室）, area_manager（参照のみ）, system_admin
- **対応テーブル**: teachers, teacher_subjects, teacher_grades, subjects

**パスパラメータ**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| classroom_id | UUID | Yes | 教室ID |

**クエリパラメータ**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| q | string | No | 検索文字列（氏名・講師コード部分一致） |
| filter[status] | string | No | ステータス（active/inactive/all） |
| filter[gender] | string | No | 性別（male/female） |
| filter[subject_id] | string | No | 担当科目ID |
| sort | string | No | ソート項目（teacher_name/-created_at） |
| page | integer | No | ページ番号（デフォルト: 1） |
| per_page | integer | No | 1ページあたり件数（デフォルト: 20、最大: 100） |

**レスポンス（成功: 200 OK）**

```json
{
  "data": [
    {
      "teacher_id": "T001",
      "teacher_version_id": "550e8400-e29b-41d4-a716-446655440001",
      "teacher_name": "田村 悠樹",
      "gender": "male",
      "min_slots_per_week": 2,
      "max_slots_per_week": 5,
      "max_consecutive_slots": 3,
      "is_current": true,
      "subjects": [
        {"subject_id": "JHS_MATH_PUB", "subject_name": "中学数学（公立）", "level": "A"}
      ],
      "grades": ["JHS1", "JHS2", "JHS3"],
      "created_at": "2025-03-01T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "per_page": 20,
    "total_pages": 2
  }
}
```

---

#### POST /api/classrooms/{classroom_id}/teachers

- **機能ID**: F041
- **目的**: 講師の新規登録
- **認証**: 必須
- **権限**: classroom_manager（自教室）, system_admin
- **対応テーブル**: teachers, teacher_subjects, teacher_grades, ng_relations, audit_logs

**リクエスト**

```json
{
  "teacher_id": "T026",
  "teacher_name": "鈴木 一郎",
  "gender": "male",
  "min_slots_per_week": 2,
  "max_slots_per_week": 5,
  "max_consecutive_slots": 3,
  "subjects": [
    {"subject_id": "JHS_MATH_PUB", "level": "A"},
    {"subject_id": "JHS_ENG", "level": "B"}
  ],
  "grades": ["JHS1", "JHS2", "JHS3"],
  "ng_student_ids": ["S005", "S010"]
}
```

**レスポンス（成功: 201 Created）**

```json
{
  "teacher_id": "T026",
  "teacher_version_id": "550e8400-e29b-41d4-a716-446655440026",
  "message": "講師を登録しました"
}
```

**エラー**

| ステータス | コード | メッセージ |
|-----------|--------|----------|
| 400 | VAL_040 | 講師氏名は必須です |
| 400 | VAL_041 | 最小コマ数は最大コマ数以下で設定してください |
| 400 | VAL_042 | 担当科目を1つ以上選択してください |
| 409 | VAL_043 | この講師コードは既に使用されています |

---

#### PUT /api/classrooms/{classroom_id}/teachers/{teacher_id}

- **機能ID**: F042
- **目的**: 講師情報の編集（新バージョン作成）
- **認証**: 必須
- **権限**: classroom_manager（自教室）, system_admin
- **対応テーブル**: teachers, teacher_subjects, teacher_grades, ng_relations, audit_logs

**リクエスト**

```json
{
  "teacher_name": "鈴木 一郎",
  "max_slots_per_week": 6,
  "subjects": [
    {"subject_id": "JHS_MATH_PUB", "level": "A"},
    {"subject_id": "JHS_ENG", "level": "A"}
  ]
}
```

**レスポンス（成功: 200 OK）**

```json
{
  "teacher_id": "T026",
  "teacher_version_id": "550e8400-e29b-41d4-a716-446655440027",
  "version_number": 2,
  "message": "講師情報を更新しました"
}
```

**備考**: 講師コード（teacher_id）は変更不可

---

### 5.4 生徒管理 API

#### GET /api/classrooms/{classroom_id}/students

- **機能ID**: F050
- **目的**: 生徒一覧の取得（検索・フィルター対応）
- **認証**: 必須
- **権限**: classroom_manager（自教室）, area_manager（参照のみ）, system_admin
- **対応テーブル**: students, student_subjects, subjects, teachers

**クエリパラメータ**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| q | string | No | 検索文字列（氏名・生徒コード部分一致） |
| filter[status] | string | No | ステータス（active/inactive/all） |
| filter[grade] | string | No | 学年 |
| filter[subject_id] | string | No | 受講科目ID |
| sort | string | No | ソート項目 |
| page | integer | No | ページ番号 |
| per_page | integer | No | 1ページあたり件数 |

**レスポンス（成功: 200 OK）**

```json
{
  "data": [
    {
      "student_id": "S001",
      "student_version_id": "550e8400-e29b-41d4-a716-446655440101",
      "student_name": "山田 花子",
      "grade": "JHS2",
      "gender": "female",
      "school_type": "public",
      "max_consecutive_slots": 2,
      "preferred_teacher_id": "T001",
      "preferred_teacher_name": "田村 悠樹",
      "preferred_teacher_gender": "male",
      "is_current": true,
      "subjects": [
        {"subject_id": "JHS_MATH_PUB", "subject_name": "中学数学（公立）", "slots_per_week": 2}
      ],
      "total_slots_per_week": 4,
      "created_at": "2025-03-01T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 80,
    "page": 1,
    "per_page": 20,
    "total_pages": 4
  }
}
```

---

### 5.5 希望データ API

#### GET /api/classrooms/{classroom_id}/terms/{term_id}/preferences

- **機能ID**: F060, F061
- **目的**: 希望データマトリクスの取得
- **認証**: 必須
- **対応テーブル**: teacher_shift_preferences, student_preferences, teachers, students, time_slots

**クエリパラメータ**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| type | string | Yes | teacher / student |
| page | integer | No | ページ番号 |
| per_page | integer | No | 1ページあたり件数 |

**レスポンス（成功: 200 OK）**

```json
{
  "type": "teacher",
  "matrix": [
    {
      "person_id": "T001",
      "person_name": "田村 悠樹",
      "slots": [
        {"day_of_week": "mon", "slot_number": 1, "value": "available", "is_manually_edited": false},
        {"day_of_week": "mon", "slot_number": 2, "value": "unavailable", "is_manually_edited": true}
      ]
    }
  ],
  "time_slots": {
    "weekday": [
      {"slot_number": 1, "start_time": "16:00", "end_time": "17:20"}
    ],
    "saturday": []
  },
  "pagination": {}
}
```

---

#### POST /api/classrooms/{classroom_id}/terms/{term_id}/preferences/sync

- **機能ID**: F063
- **目的**: Google Formからの希望データ同期
- **認証**: 必須
- **対応テーブル**: teacher_shift_preferences, student_preferences, google_form_connections

**リクエスト**

```json
{
  "type": "teacher",
  "overwrite_manual_edits": false
}
```

**レスポンス（成功: 200 OK）**

```json
{
  "message": "同期が完了しました",
  "summary": {
    "added": 15,
    "updated": 8,
    "skipped": 3,
    "skipped_reason": "手動編集済みのためスキップ"
  },
  "last_sync_at": "2025-03-24T10:00:00Z"
}
```

**競合がある場合（200 OK with conflicts）**

```json
{
  "message": "同期を完了しましたが、一部競合があります",
  "summary": {},
  "conflicts": [
    {
      "person_id": "T001",
      "person_name": "田村 悠樹",
      "day_of_week": "mon",
      "slot_number": 1,
      "current_value": "available",
      "new_value": "unavailable",
      "is_manually_edited": true
    }
  ],
  "require_confirmation": true
}
```

---

### 5.6 条件設定 API

#### POST /api/classrooms/{classroom_id}/terms/{term_id}/constraints

- **機能ID**: F072
- **目的**: ターム固有調整の設定
- **認証**: 必須
- **対応テーブル**: term_constraints, audit_logs

**リクエスト**

```json
{
  "target_type": "teacher",
  "target_id": "T001",
  "constraints": [
    {"constraint_type": "max_slots", "value": {"value": 3}},
    {"constraint_type": "subject_limit", "value": {"subject_ids": ["JHS_MATH_PUB"]}}
  ]
}
```

**レスポンス（成功: 201 Created）**

```json
{
  "message": "制約を保存しました",
  "constraint_ids": ["uuid1", "uuid2"]
}
```

---

#### PUT /api/classrooms/{classroom_id}/terms/{term_id}/policies

- **機能ID**: F073
- **目的**: 全体ポリシーの設定
- **認証**: 必須
- **対応テーブル**: policies

**リクエスト**

```json
{
  "policies": [
    {
      "policy_type": "P001",
      "is_enabled": true,
      "parameters": {
        "level_A": ["A"],
        "level_B": ["A", "B"],
        "level_C": ["A", "B", "C"]
      }
    },
    {
      "policy_type": "P005",
      "is_enabled": true,
      "parameters": {
        "target_rate": 85
      }
    }
  ]
}
```

**レスポンス（成功: 200 OK）**

```json
{
  "message": "ポリシーを保存しました"
}
```

---

### 5.7 時間割作成 API

#### POST /api/classrooms/{classroom_id}/terms/{term_id}/schedules/analyze

- **機能ID**: F080
- **目的**: 問題分析・戦略決定（Analyzer）
- **認証**: 必須
- **対応テーブル**: terms, teachers, students, teacher_shift_preferences, student_preferences, policies

**レスポンス（成功: 200 OK）**

```json
{
  "analysis": {
    "scale": "medium",
    "scale_details": {
      "teacher_count": 33,
      "student_count": 92,
      "weekly_slots": 320
    },
    "difficulty": "high",
    "difficulty_reasons": [
      "土曜に需要集中（供給10コマ、需要15コマ）",
      "中受算数の講師不足"
    ],
    "bottlenecks": [
      {
        "type": "time_slot",
        "day_of_week": "sat",
        "slot_number": 3,
        "demand": 15,
        "supply": 10,
        "gap": -5
      }
    ]
  },
  "recommended_strategy": {
    "initial_strategy": "standard",
    "timeout": 30,
    "reason": "中規模問題、標準戦略で求解可能と推定"
  }
}
```

---

#### POST /api/classrooms/{classroom_id}/terms/{term_id}/schedules/generate

- **機能ID**: F081
- **目的**: 時間割生成（一発求解）
- **認証**: 必須
- **対応テーブル**: schedules, schedule_slots, schedule_generation_logs, audit_logs
- **備考**: 非同期処理。進捗はWebSocket (`/api/schedules/{schedule_id}/progress`) で通知

**リクエスト**

```json
{
  "options": {
    "target_fulfillment_rate": 85,
    "max_timeout_seconds": 60
  }
}
```

**レスポンス（成功: 201 Created）**

```json
{
  "schedule_id": "550e8400-e29b-41d4-a716-446655440200",
  "version": 1,
  "status": "draft",
  "solution_status": "optimal",
  "result": {
    "fulfillment_rate": 87.5,
    "soft_constraint_rate": 82.0,
    "one_to_two_rate": 78.5,
    "unplaced_students": 0
  },
  "solver_stats": {
    "strategy_used": "standard",
    "solve_time_ms": 12500,
    "solutions_found": 8,
    "optimality_gap": 0.02,
    "termination_reason": "target_achieved"
  },
  "orchestrator_decisions": [
    {
      "time_ms": 5000,
      "decision": "continue",
      "current_rate": 72.5,
      "reason": "改善中"
    },
    {
      "time_ms": 12000,
      "decision": "stop",
      "current_rate": 87.5,
      "reason": "目標達成（87.5% ≥ 85%）"
    }
  ],
  "next_action": "confirm_or_adjust"
}
```

**部分成功レスポンス（201 Created）**

```json
{
  "schedule_id": "550e8400-e29b-41d4-a716-446655440200",
  "solution_status": "partial",
  "result": {
    "fulfillment_rate": 75.0,
    "unplaced_students": 3,
    "unplaced_details": [
      {
        "student_id": "S001",
        "student_name": "山田 太郎",
        "subject": "中受算数",
        "reason": "希望時間帯に対応可能な講師がいません"
      }
    ]
  },
  "solver_stats": {
    "strategies_attempted": [
      {"strategy": "standard", "result": "no_solution", "time_ms": 30000},
      {"strategy": "relaxed", "result": "no_solution", "time_ms": 20000},
      {"strategy": "partial", "result": "feasible", "time_ms": 15000}
    ],
    "termination_reason": "strategy_fallback"
  },
  "next_actions": [
    {
      "action_id": "accept_partial",
      "label": "この部分解を採用",
      "description": "未配置3名は手動で調整"
    },
    {
      "action_id": "relax_constraints",
      "label": "制約を緩和して再生成"
    }
  ]
}
```

**実行不可能レスポンス（200 OK）**

```json
{
  "schedule_id": null,
  "solution_status": "infeasible",
  "infeasibility_analysis": {
    "conflicting_constraints": [
      {
        "constraint_type": "H003",
        "description": "講師出勤可能時間",
        "affected_students": ["S001", "S002"],
        "detail": "土曜午前に中受算数を教えられる講師がいません"
      }
    ]
  },
  "relaxation_suggestions": [
    {
      "suggestion_id": 1,
      "title": "山田太郎さんの希望時間帯を拡大",
      "constraint_to_relax": "S004",
      "impact": "本人の希望度が下がる",
      "affected_count": 1
    }
  ],
  "next_action": "select_relaxation"
}
```

---

#### POST /api/classrooms/{classroom_id}/terms/{term_id}/schedules/regenerate

- **機能ID**: F081
- **目的**: 緩和適用後の再生成
- **認証**: 必須
- **対応テーブル**: schedules, schedule_slots, term_constraints, schedule_generation_logs

**リクエスト**

```json
{
  "relaxations": [
    {"suggestion_id": 1}
  ],
  "fixed_slots": [
    {
      "student_id": "S005",
      "day_of_week": "sat",
      "slot_number": 1
    }
  ]
}
```

**レスポンス**: `/schedules/generate` と同様

---

#### WebSocket /api/schedules/{schedule_id}/progress

- **機能ID**: F081
- **目的**: 生成進捗のリアルタイム通知
- **認証**: 必須（接続時にトークン検証）

**メッセージ形式（サーバー→クライアント）**

```json
// 進捗通知
{
  "type": "progress",
  "solutions_found": 5,
  "current_rate": 78.0,
  "elapsed_ms": 8000,
  "strategy": "standard"
}

// 戦略切り替え通知
{
  "type": "strategy_switch",
  "from": "standard",
  "to": "relaxed",
  "reason": "30秒経過で解なし"
}

// 完了通知
{
  "type": "complete",
  "status": "optimal",
  "final_rate": 87.5,
  "termination_reason": "target_achieved"
}
```

---

#### GET /api/schedules/{schedule_id}/explanation

- **機能ID**: F082
- **目的**: 結果説明の取得（Explainer Agent - LLM）
- **認証**: 必須
- **対応テーブル**: schedules, schedule_slots, schedule_generation_logs

**レスポンス（成功: 200 OK）**

```json
{
  "summary": {
    "overall": "87.5%の充足率で最適解が見つかりました。これは数学的にこれ以上改善できない解です。",
    "key_points": [
      "土曜午前の講師配置が効率的に行われました",
      "1対2率は78.5%で目標の85%を下回っています"
    ]
  },
  "bottleneck_explanation": {
    "main_bottleneck": "土曜3限の講師不足",
    "detail": "土曜3限は需要15コマに対し供給10コマのため、5名が他の時間帯に配置されました。",
    "structural_cause": true
  },
  "trade_offs": [
    {
      "description": "田中先生を土曜に4コマ配置（上限3コマ超過）すれば充足率89%に改善可能",
      "pros": ["充足率+1.5%", "1対2率+3%"],
      "cons": ["S002違反（連続コマ上限超過）"],
      "recommendation": "not_recommended"
    }
  ]
}
```

---

#### POST /api/schedules/{schedule_id}/what-if

- **機能ID**: F082
- **目的**: What-if分析（Explainer Agent - LLM）
- **認証**: 必須
- **対応テーブル**: schedules, schedule_slots

**リクエスト**

```json
{
  "question": "山田太郎を土曜1限に固定したらどうなりますか？"
}
```

**レスポンス（成功: 200 OK）**

```json
{
  "analysis": {
    "feasible": true,
    "impact": {
      "fulfillment_rate_change": -0.5,
      "soft_constraint_violations_added": 1
    },
    "explanation": "山田太郎を土曜1限に固定すると、鈴木花子を別の時間帯に移動する必要があり、充足率が0.5%低下します。"
  }
}
```

---

#### POST /api/schedules/{schedule_id}/confirm

- **機能ID**: F086
- **目的**: 時間割の確定
- **認証**: 必須
- **対応テーブル**: schedules, audit_logs

**レスポンス（成功: 200 OK）**

```json
{
  "schedule_id": "550e8400-e29b-41d4-a716-446655440200",
  "status": "confirmed",
  "confirmed_at": "2025-03-24T15:30:00Z",
  "confirmed_by": "山田 太郎",
  "final_metrics": {
    "fulfillment_rate": 85.3,
    "one_to_two_slots": 136,
    "one_to_one_slots": 58,
    "total_slots": 194
  },
  "message": "時間割を確定しました"
}
```

---

### 5.8 振替対応 API

#### POST /api/classrooms/{classroom_id}/absences

- **機能ID**: F090
- **目的**: 欠席登録
- **認証**: 必須
- **対応テーブル**: absences, schedule_slots, audit_logs

**リクエスト**

```json
{
  "schedule_slot_id": "550e8400-e29b-41d4-a716-446655440300",
  "absence_type": "student",
  "person_id": "S001",
  "reason": "体調不良",
  "requires_reschedule": true
}
```

**レスポンス（成功: 201 Created）**

```json
{
  "absence_id": "550e8400-e29b-41d4-a716-446655440400",
  "status": "pending_reschedule",
  "affected_slot": {
    "date": "2025-03-25",
    "day_of_week": "tue",
    "slot_number": 2,
    "teacher_name": "田村 悠樹",
    "subject_name": "中学数学（公立）"
  },
  "message": "欠席を登録しました。振替候補を確認してください。"
}
```

---

#### GET /api/classrooms/{classroom_id}/absences/{absence_id}/reschedule-candidates

- **機能ID**: F091
- **目的**: 振替候補の提案
- **認証**: 必須
- **対応テーブル**: absences, schedule_slots, student_preferences, teacher_shift_preferences, teachers

**レスポンス（成功: 200 OK）**

```json
{
  "absence_id": "550e8400-e29b-41d4-a716-446655440400",
  "original_slot": {
    "date": "2025-03-25",
    "day_of_week": "tue",
    "slot_number": 2
  },
  "candidates": [
    {
      "candidate_id": "cand_001",
      "date": "2025-03-27",
      "day_of_week": "thu",
      "slot_number": 3,
      "teacher_id": "T001",
      "teacher_name": "田村 悠樹",
      "match_score": 95,
      "is_same_teacher": true,
      "student_preference": "preferred",
      "available_booths": 3
    }
  ]
}
```

---

### 5.9 ユーザー管理 API

#### POST /api/users

- **機能ID**: F111
- **目的**: ユーザーの新規作成
- **認証**: 必須
- **権限**: system_admin のみ
- **対応テーブル**: users, user_classrooms, audit_logs

**リクエスト**

```json
{
  "name": "田中 次郎",
  "email": "tanaka@example.com",
  "role": "classroom_manager",
  "classroom_ids": ["550e8400-e29b-41d4-a716-446655440500"],
  "is_active": true
}
```

**レスポンス（成功: 201 Created）**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440600",
  "message": "ユーザーを作成しました。初期パスワードをメールで送信しました。"
}
```

**エラー**

| ステータス | コード | メッセージ |
|-----------|--------|----------|
| 400 | VAL_110 | 氏名は必須です |
| 400 | VAL_112 | メールアドレスの形式が正しくありません |
| 409 | VAL_113 | このメールアドレスは既に使用されています |
| 400 | VAL_114 | 担当教室を選択してください |

---

### 5.10 教室マスタ管理 API

#### POST /api/classrooms

- **機能ID**: F121
- **目的**: 教室の新規作成
- **認証**: 必須
- **権限**: system_admin のみ
- **対応テーブル**: classrooms, classroom_settings, time_slots, audit_logs

**リクエスト**

```json
{
  "classroom_name": "新宿教室",
  "classroom_code": "SJK001",
  "area_id": "tokyo",
  "address": "東京都新宿区...",
  "phone_number": "03-9876-5432",
  "status": "operating"
}
```

**レスポンス（成功: 201 Created）**

```json
{
  "classroom_id": "550e8400-e29b-41d4-a716-446655440700",
  "message": "教室を作成しました"
}
```

**備考**: 教室作成時に以下が自動生成される
- classroom_settings（デフォルト値）
- time_slots（デフォルト時間枠）

---

## 6. エラーハンドリング

### 6.1 エラーコード体系

| プレフィックス | カテゴリ | 例 |
|---------------|---------|-----|
| AUTH_ | 認証エラー | AUTH_001（認証失敗） |
| VAL_ | バリデーションエラー | VAL_040（必須項目なし） |
| BIZ_ | ビジネスルールエラー | BIZ_110（自己役割変更不可） |
| GF_ | Google Form連携エラー | GF_001（認証エラー） |
| SYS_ | システムエラー | SYS_001（内部エラー） |

### 6.2 認証エラー

| コード | メッセージ | HTTPステータス |
|--------|----------|---------------|
| AUTH_001 | メールアドレスまたはパスワードが正しくありません | 401 |
| AUTH_002 | このアカウントは無効です | 401 |
| AUTH_003 | アカウントがロックされています | 401 |
| AUTH_004 | トークンが無効または期限切れです | 401 |
| AUTH_005 | 現在のパスワードが正しくありません | 401 |
| AUTH_006 | セッションが無効です | 401 |

### 6.3 バリデーションエラー

| コード | 画面 | メッセージ |
|--------|------|----------|
| VAL_030 | P004 | 時間枠の開始時刻は終了時刻より前に設定してください |
| VAL_031 | P004 | 時間枠が重複しています |
| VAL_040 | P005 | 講師氏名は必須です |
| VAL_041 | P005 | 最小コマ数は最大コマ数以下で設定してください |
| VAL_042 | P005 | 担当科目を1つ以上選択してください |
| VAL_043 | P005 | この講師コードは既に使用されています |
| VAL_050 | P006 | 生徒氏名は必須です |
| VAL_060 | P007 | 無効な希望値です |
| VAL_070 | P008 | ターム名は必須です |
| VAL_071 | P008 | 開始日は終了日より前に設定してください |
| VAL_110 | P012 | 氏名は必須です |
| VAL_112 | P012 | メールアドレスの形式が正しくありません |
| VAL_113 | P012 | このメールアドレスは既に使用されています |
| VAL_120 | P013 | 教室名は必須です |
| VAL_123 | P013 | この教室コードは既に使用されています |

### 6.4 ビジネスルールエラー

| コード | 画面 | メッセージ |
|--------|------|----------|
| BIZ_040 | P005 | 確定済みの時間割がある講師は削除できません |
| BIZ_050 | P006 | 確定済みの時間割がある生徒は削除できません |
| BIZ_060 | P007 | Google Form連携が設定されていません |
| BIZ_061 | P007 | 確定済みタームの希望データは編集できません |
| BIZ_070 | P008 | このタームには確定済み時間割があるため、制約を変更できません |
| BIZ_080 | P009 | ハード制約に違反しています |
| BIZ_110 | P012 | 自分自身の役割は変更できません |
| BIZ_111 | P012 | 最後のシステム管理者の役割は変更できません |
| BIZ_112 | P012 | このユーザーは他のデータで参照されているため削除できません |
| BIZ_113 | P012 | 最後のシステム管理者は削除できません |
| BIZ_120 | P013 | 教室コードは変更できません |

### 6.5 Google Form連携エラー

| コード | メッセージ | 対処 |
|--------|----------|------|
| GF_001 | 再認証が必要です | OAuth再認証 |
| GF_002 | スプレッドシートが見つかりません | URL確認 |
| GF_003 | シートが見つかりません | シート名確認 |
| GF_004 | アクセス権限がありません | 共有設定確認 |
| GF_005 | しばらく待ってから再試行してください | レート制限 |
| GF_006 | カラムマッピングが不正です | マッピング再設定 |

---

## 更新履歴

| 日付 | 更新内容 |
|------|---------|
| 2026-03-25 | 初版作成（81エンドポイント定義、DB設計書・要件定義書v2・IPO一覧に基づく） |
| 2026-03-25 | P009時間割作成API改訂: Phase1/Phase2方式を廃止、一発求解方式に変更。optimize/apply-proposalを削除し、explanation/what-if/regenerate/WebSocket progressを追加（83エンドポイント） |
