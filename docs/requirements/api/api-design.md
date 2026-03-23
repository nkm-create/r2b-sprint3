# API仕様書

## 1. 概要

### 1.1 基本情報

| 項目 | 値 |
|------|-----|
| ベースURL | `https://api.example.com/v1` |
| 認証方式 | JWT Bearer Token |
| Content-Type | application/json |
| 文字コード | UTF-8 |

### 1.2 共通仕様

#### リクエストヘッダー

```
Authorization: Bearer {jwt_token}
Content-Type: application/json
X-Request-ID: {uuid}
```

#### レスポンス形式

**成功時**
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2025-04-01T10:00:00Z",
    "request_id": "uuid"
  }
}
```

**エラー時**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ",
    "details": [ ... ]
  },
  "meta": {
    "timestamp": "2025-04-01T10:00:00Z",
    "request_id": "uuid"
  }
}
```

#### ページネーション

```json
{
  "data": [ ... ],
  "pagination": {
    "total": 92,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}
```

#### HTTPステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 |
| 201 | 作成成功 |
| 204 | 削除成功（レスポンスボディなし） |
| 400 | バリデーションエラー |
| 401 | 認証エラー |
| 403 | 権限エラー |
| 404 | リソースが見つからない |
| 409 | 競合（重複など） |
| 422 | 処理不可能なエンティティ |
| 500 | サーバーエラー |

---

## 2. システム API

### GET /health

ヘルスチェック（認証不要）

**Response 200**
```json
{
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2025-04-01T10:00:00Z",
    "services": {
      "database": "healthy",
      "cache": "healthy",
      "queue": "healthy"
    }
  }
}
```

**Response 503** (サービス異常時)
```json
{
  "data": {
    "status": "unhealthy",
    "services": {
      "database": "unhealthy",
      "cache": "healthy",
      "queue": "healthy"
    }
  }
}
```

---

## 3. 認証 API

### POST /auth/login

ログイン処理

**Request**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response 200**
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "name": "山田太郎",
      "email": "user@example.com",
      "role": "classroom_manager",
      "classroom_id": "uuid"
    }
  }
}
```

**Error 401**
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "メールアドレスまたはパスワードが正しくありません"
  }
}
```

### POST /auth/refresh

トークンリフレッシュ

**Request**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 200**
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600
  }
}
```

### POST /auth/logout

ログアウト

**Response 204** No Content

### POST /auth/password-reset/request

パスワードリセット要求

**Request**
```json
{
  "email": "user@example.com"
}
```

**Response 200**
```json
{
  "data": {
    "message": "パスワードリセットメールを送信しました"
  }
}
```

### POST /auth/password-reset/confirm

パスワードリセット確定

**Request**
```json
{
  "token": "reset_token",
  "new_password": "newPassword123"
}
```

**Response 200**
```json
{
  "data": {
    "message": "パスワードを変更しました"
  }
}
```

---

## 4. エリア API

### GET /areas

エリア一覧取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| search | string | 名前で検索 |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "東京エリア",
      "code": "TKY",
      "classrooms_count": 5
    }
  ]
}
```

### GET /areas/{id}

エリア詳細取得

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "name": "東京エリア",
    "code": "TKY",
    "classrooms": [
      { "id": "uuid", "name": "渋谷教室", "code": "SBY001", "status": "active" },
      { "id": "uuid", "name": "新宿教室", "code": "SJK001", "status": "active" }
    ]
  }
}
```

### POST /areas

エリア新規作成

**Request**
```json
{
  "name": "神奈川エリア",
  "code": "KNG"
}
```

**Response 201**
```json
{
  "data": {
    "id": "uuid",
    "name": "神奈川エリア",
    "code": "KNG"
  }
}
```

### PUT /areas/{id}

エリア更新

**Request**
```json
{
  "name": "神奈川エリア（更新）"
}
```

### DELETE /areas/{id}

エリア削除（配下に教室がある場合はエラー）

---

## 5. 教室 API

### GET /classrooms

教室一覧取得（管理者用）

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| area_id | string | エリアでフィルター |
| status | string | ステータスでフィルター |
| search | string | 名前で検索 |
| page | number | ページ番号 |
| per_page | number | 1ページあたり件数 |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "渋谷教室",
      "code": "SBY001",
      "area": {
        "id": "uuid",
        "name": "東京エリア"
      },
      "status": "active",
      "address": "東京都渋谷区...",
      "phone": "03-1234-5678"
    }
  ],
  "pagination": { ... }
}
```

### GET /classrooms/{id}

教室詳細取得

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "name": "渋谷教室",
    "code": "SBY001",
    "area": { "id": "uuid", "name": "東京エリア" },
    "status": "active",
    "address": "東京都渋谷区...",
    "phone": "03-1234-5678",
    "settings": {
      "operating_days": ["mon", "tue", "wed", "thu", "fri", "sat"],
      "capacity": 8
    },
    "time_slots": {
      "weekday": [
        { "slot_number": 1, "start_time": "16:00", "end_time": "17:20" },
        { "slot_number": 2, "start_time": "17:30", "end_time": "18:50" },
        { "slot_number": 3, "start_time": "19:00", "end_time": "20:20" },
        { "slot_number": 4, "start_time": "20:30", "end_time": "21:50" }
      ],
      "saturday": [
        { "slot_number": 0, "start_time": "13:00", "end_time": "14:20" },
        { "slot_number": 1, "start_time": "14:30", "end_time": "15:50" },
        { "slot_number": 2, "start_time": "16:00", "end_time": "17:20" },
        { "slot_number": 3, "start_time": "17:30", "end_time": "18:50" },
        { "slot_number": 4, "start_time": "19:00", "end_time": "20:20" }
      ]
    }
  }
}
```

### POST /classrooms

教室新規作成

**Request**
```json
{
  "name": "新宿教室",
  "code": "SJK001",
  "area_id": "uuid",
  "address": "東京都新宿区...",
  "phone": "03-9876-5432"
}
```

**Response 201**
```json
{
  "data": {
    "id": "uuid",
    "name": "新宿教室",
    "code": "SJK001",
    ...
  }
}
```

### PUT /classrooms/{id}

教室更新

### DELETE /classrooms/{id}

教室削除（論理削除）

### PUT /classrooms/{id}/settings

教室設定更新

**Request**
```json
{
  "operating_days": ["mon", "tue", "wed", "thu", "fri", "sat"],
  "capacity": 10,
  "time_slots": {
    "weekday": [
      { "slot_number": 1, "start_time": "16:00", "end_time": "17:20" },
      ...
    ],
    "saturday": [ ... ]
  }
}
```

---

## 6. 講師 API

### GET /classrooms/{classroom_id}/teachers

講師一覧取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| subject_id | string | 指導可能科目でフィルター |
| grade | string | 指導可能学年でフィルター |
| gender | string | 性別でフィルター |
| status | string | ステータスでフィルター |
| search | string | 氏名で検索 |
| include_versions | boolean | バージョン履歴を含める |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "display_id": "T001",
      "version": {
        "id": "uuid",
        "version_number": 3,
        "name": "佐藤一郎",
        "gender": "male",
        "subjects": [
          { "id": "uuid", "name": "中受算数" },
          { "id": "uuid", "name": "中受理科" }
        ],
        "grades": ["elementary_4", "elementary_5", "elementary_6"],
        "min_slots_per_week": 4,
        "max_slots_per_week": 8,
        "max_consecutive_slots": 3,
        "university_rank": "A",
        "has_junior_high_exam_exp": true,
        "has_high_school_exam_exp": false,
        "status": "active"
      }
    }
  ],
  "pagination": { ... }
}
```

### GET /classrooms/{classroom_id}/teachers/{id}

講師詳細取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| include_versions | boolean | バージョン履歴を含める |
| version_id | string | 特定バージョンを取得 |

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "display_id": "T001",
    "current_version": {
      "id": "uuid",
      "version_number": 3,
      "name": "佐藤一郎",
      ...
    },
    "versions": [
      {
        "id": "uuid",
        "version_number": 3,
        "valid_from": "2025-04-01T00:00:00Z",
        "valid_to": null,
        "is_current": true,
        "change_reason": "コマ数上限変更"
      },
      {
        "id": "uuid",
        "version_number": 2,
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_to": "2025-03-31T23:59:59Z",
        "is_current": false,
        "change_reason": "科目追加"
      }
    ],
    "ng_students": [
      { "id": "uuid", "display_id": "S005", "name": "田中花子" }
    ]
  }
}
```

### POST /classrooms/{classroom_id}/teachers

講師新規登録

**Request**
```json
{
  "name": "鈴木次郎",
  "gender": "male",
  "subject_ids": ["uuid", "uuid"],
  "grades": ["junior_high_1", "junior_high_2", "junior_high_3"],
  "min_slots_per_week": 3,
  "max_slots_per_week": 6,
  "max_consecutive_slots": 2,
  "university_rank": "B",
  "has_junior_high_exam_exp": false,
  "has_high_school_exam_exp": true
}
```

**Response 201**
```json
{
  "data": {
    "id": "uuid",
    "display_id": "T010",
    "version": { ... }
  }
}
```

### PUT /classrooms/{classroom_id}/teachers/{id}

講師情報更新（新バージョン作成）

**Request**
```json
{
  "name": "佐藤一郎",
  "max_slots_per_week": 10,
  "change_reason": "コマ数上限変更"
}
```

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "display_id": "T001",
    "version": {
      "id": "new-version-uuid",
      "version_number": 4,
      ...
    }
  }
}
```

### DELETE /classrooms/{classroom_id}/teachers/{id}

講師削除（論理削除）

### POST /classrooms/{classroom_id}/teachers/import

講師CSVインポート

**制限**: 最大30件/回

**Request** (multipart/form-data)
- file: CSVファイル

**Response 200**
```json
{
  "data": {
    "preview": [
      {
        "row": 1,
        "data": { "name": "山田太郎", ... },
        "status": "valid"
      },
      {
        "row": 2,
        "data": { "name": "鈴木次郎", ... },
        "status": "error",
        "errors": ["指導可能科目が存在しません"]
      }
    ],
    "valid_count": 8,
    "error_count": 2
  }
}
```

### POST /classrooms/{classroom_id}/teachers/import/confirm

CSVインポート確定

**Request**
```json
{
  "rows": [1, 3, 4, 5, 6, 7, 8, 9]
}
```

### GET /classrooms/{classroom_id}/teachers/export

講師CSVエクスポート

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| scope | string | 'all': 全件, 'filtered': 現在のフィルター条件に合致するもの |
| subject_id | string | 指導可能科目でフィルター（scope=filteredの場合） |
| grade | string | 指導可能学年でフィルター（scope=filteredの場合） |
| gender | string | 性別でフィルター（scope=filteredの場合） |
| status | string | ステータスでフィルター（scope=filteredの場合） |

**Response 200** (text/csv)
```csv
講師ID,氏名,性別,指導可能科目,指導可能学年,最小コマ,最大コマ,最大連続コマ,大学ランク,中受経験,高受経験,ステータス
T001,佐藤一郎,男,"中受算数,中受理科","小4,小5,小6",3,6,2,A,true,false,active
T002,田中花子,女,"中学英語,高校12英語","中1,中2,中3,高1,高2",4,8,3,B,false,true,active
```

**Response Headers**
```
Content-Disposition: attachment; filename="teachers_20250401.csv"
Content-Type: text/csv; charset=utf-8
```

---

## 7. 生徒 API

### GET /classrooms/{classroom_id}/students

生徒一覧取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| grade | string | 学年でフィルター |
| subject_id | string | 受講科目でフィルター |
| aspiration_level | string | 志望レベルでフィルター |
| purpose | string | 通塾目的でフィルター |
| status | string | ステータスでフィルター |
| search | string | 氏名で検索 |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "display_id": "S001",
      "version": {
        "id": "uuid",
        "version_number": 2,
        "name": "田中太郎",
        "grade": "elementary_5",
        "subjects": [
          { "id": "uuid", "name": "中受算数", "slots_per_week": 2 },
          { "id": "uuid", "name": "中受国語", "slots_per_week": 1 }
        ],
        "total_slots_per_week": 3,
        "max_consecutive_slots": 2,
        "preferred_teacher": { "id": "uuid", "name": "佐藤一郎" },
        "preferred_teacher_gender": "none",
        "aspiration_level": "A",
        "purpose": "junior_high_exam",
        "status": "enrolled"
      }
    }
  ],
  "pagination": { ... }
}
```

### GET /classrooms/{classroom_id}/students/{id}

生徒詳細取得

### POST /classrooms/{classroom_id}/students

生徒新規登録

**Request**
```json
{
  "name": "山田花子",
  "grade": "elementary_4",
  "subjects": [
    { "subject_id": "uuid", "slots_per_week": 2 },
    { "subject_id": "uuid", "slots_per_week": 1 }
  ],
  "max_consecutive_slots": 2,
  "preferred_teacher_id": null,
  "preferred_teacher_gender": "female",
  "aspiration_level": "B",
  "purpose": "junior_high_exam"
}
```

### PUT /classrooms/{classroom_id}/students/{id}

生徒情報更新（新バージョン作成）

### DELETE /classrooms/{classroom_id}/students/{id}

生徒削除（論理削除）

### POST /classrooms/{classroom_id}/students/import

生徒CSVインポート

**制限**: 最大30件/回

### POST /classrooms/{classroom_id}/students/import/confirm

CSVインポート確定

### GET /classrooms/{classroom_id}/students/export

生徒CSVエクスポート

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| scope | string | 'all': 全件, 'filtered': 現在のフィルター条件に合致するもの |
| grade | string | 学年でフィルター（scope=filteredの場合） |
| subject_id | string | 受講科目でフィルター（scope=filteredの場合） |
| aspiration_level | string | 志望レベルでフィルター（scope=filteredの場合） |
| purpose | string | 通塾目的でフィルター（scope=filteredの場合） |
| status | string | ステータスでフィルター（scope=filteredの場合） |

**Response 200** (text/csv)
```csv
生徒ID,氏名,学年,受講科目,科目別コマ数,最大連続コマ,希望講師,NG講師,講師希望性別,志望レベル,通塾目的,ステータス
S001,鈴木健太,小5,"中受算数,中受理科","2,1",2,佐藤一郎,,指定なし,A,中学受験,enrolled
S002,伊藤美咲,中2,"中学英語,公立数学","1,1",2,,,female,B,高校受験,enrolled
```

**Response Headers**
```
Content-Disposition: attachment; filename="students_20250401.csv"
Content-Type: text/csv; charset=utf-8
```

---

## 8. NG関係 API

### GET /classrooms/{classroom_id}/ng-relations

NG関係一覧取得

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "teacher": { "id": "uuid", "display_id": "T001", "name": "佐藤一郎" },
      "student": { "id": "uuid", "display_id": "S005", "name": "田中花子" },
      "created_by": "teacher",
      "reason": "指導方針の相違",
      "created_at": "2025-03-01T10:00:00Z"
    }
  ]
}
```

### POST /classrooms/{classroom_id}/ng-relations

NG関係登録

**Request**
```json
{
  "teacher_id": "uuid",
  "student_id": "uuid",
  "created_by": "teacher",
  "reason": "指導方針の相違"
}
```

### DELETE /classrooms/{classroom_id}/ng-relations/{id}

NG関係削除

---

## 9. 希望データ API

### GET /classrooms/{classroom_id}/terms/{term_id}/preferences

希望データ取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| target_type | string | 'teacher' or 'student' |
| target_id | string | 特定の講師/生徒のみ |

**Response 200**
```json
{
  "data": {
    "target_type": "teacher",
    "targets": [
      {
        "id": "uuid",
        "display_id": "T001",
        "name": "佐藤一郎",
        "preferences": {
          "mon": {
            "1": "available",
            "2": "available",
            "3": "unavailable",
            "4": "unavailable"
          },
          "tue": { ... },
          ...
        },
        "is_manually_edited": false,
        "synced_at": "2025-03-25T10:00:00Z"
      }
    ]
  }
}
```

### PUT /classrooms/{classroom_id}/terms/{term_id}/preferences

希望データ更新

**Request**
```json
{
  "target_type": "teacher",
  "target_id": "uuid",
  "preferences": {
    "mon": {
      "1": "available",
      "2": "unavailable"
    }
  }
}
```

### PUT /classrooms/{classroom_id}/terms/{term_id}/preferences/batch

希望データ一括更新

**Request**
```json
{
  "target_type": "teacher",
  "updates": [
    {
      "target_id": "uuid",
      "preferences": {
        "mon": { "1": "available", "2": "unavailable" },
        "tue": { "1": "available", "2": "available" }
      }
    },
    {
      "target_id": "uuid",
      "preferences": {
        "mon": { "1": "unavailable", "2": "unavailable" }
      }
    }
  ]
}
```

**Response 200**
```json
{
  "data": {
    "updated_count": 2,
    "failed_count": 0,
    "failures": []
  }
}
```

### POST /classrooms/{classroom_id}/terms/{term_id}/preferences/sync

Google Form同期

**Response 200**
```json
{
  "data": {
    "synced_count": 15,
    "skipped_count": 2,
    "skipped_targets": [
      { "id": "uuid", "name": "佐藤一郎", "reason": "手動編集済み" }
    ],
    "synced_at": "2025-03-25T15:00:00Z"
  }
}
```

### GET /classrooms/{classroom_id}/terms/{term_id}/preferences/missing

未回答者一覧取得

**Response 200**
```json
{
  "data": {
    "teachers": [
      { "id": "uuid", "display_id": "T008", "name": "高橋三郎" }
    ],
    "students": [
      { "id": "uuid", "display_id": "S012", "name": "山本四郎" }
    ]
  }
}
```

---

## 10. ターム API

### GET /classrooms/{classroom_id}/terms

ターム一覧取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| status | string | ステータスでフィルター |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "2025年4月期",
      "start_date": "2025-04-01",
      "end_date": "2025-04-30",
      "status": "draft",
      "latest_schedule": {
        "id": "uuid",
        "version": 2,
        "status": "draft",
        "fulfillment_rate": 87.5
      }
    }
  ]
}
```

### GET /classrooms/{classroom_id}/terms/{id}

ターム詳細取得

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "name": "2025年4月期",
    "start_date": "2025-04-01",
    "end_date": "2025-04-30",
    "status": "draft",
    "schedules": [
      {
        "id": "uuid",
        "version": 2,
        "status": "draft",
        "fulfillment_rate": 87.5,
        "created_at": "2025-03-20T10:00:00Z"
      },
      {
        "id": "uuid",
        "version": 1,
        "status": "archived",
        "fulfillment_rate": 82.3,
        "created_at": "2025-03-15T10:00:00Z"
      }
    ],
    "constraints_count": 12
  }
}
```

### POST /classrooms/{classroom_id}/terms

ターム新規作成

**Request**
```json
{
  "name": "2025年5月期",
  "start_date": "2025-05-01",
  "end_date": "2025-05-31"
}
```

### PUT /classrooms/{classroom_id}/terms/{id}

ターム更新

### DELETE /classrooms/{classroom_id}/terms/{id}

ターム削除

### POST /classrooms/{classroom_id}/terms/{id}/duplicate

ターム複製

**Request**
```json
{
  "name": "2025年5月期",
  "start_date": "2025-05-01",
  "end_date": "2025-05-31",
  "copy_constraints": true
}
```

---

## 11. 制約条件 API

### GET /constraint-types

制約種別マスタ一覧取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| kind | string | 種別でフィルター（'hard', 'soft'） |
| category | string | カテゴリでフィルター（'teacher', 'student', 'matching', 'time'） |

**Response 200**
```json
{
  "data": {
    "hard_constraints": [
      {
        "id": "uuid",
        "code": "H001",
        "kind": "hard",
        "category": "matching",
        "name": "科目適合",
        "description": "講師の指導可能科目に、生徒の受講科目が含まれていること"
      },
      {
        "id": "uuid",
        "code": "H002",
        "kind": "hard",
        "category": "matching",
        "name": "学年適合",
        "description": "講師の指導可能学年に、生徒の学年が含まれていること"
      },
      {
        "id": "uuid",
        "code": "H003",
        "kind": "hard",
        "category": "teacher",
        "name": "講師出勤可能時間",
        "description": "講師は出勤可能な時間帯（シフト希望で○）にのみ配置"
      },
      {
        "id": "uuid",
        "code": "H004",
        "kind": "hard",
        "category": "student",
        "name": "生徒通塾可能時間",
        "description": "生徒は通塾可能な時間帯（受講希望で○または△）にのみ配置"
      },
      {
        "id": "uuid",
        "code": "H005",
        "kind": "hard",
        "category": "matching",
        "name": "NG組み合わせ禁止",
        "description": "講師-生徒のNG組み合わせは配置禁止"
      }
    ],
    "soft_constraints": [
      {
        "id": "uuid",
        "code": "C001",
        "kind": "soft",
        "category": "teacher",
        "name": "科目限定",
        "description": "講師の担当科目を限定",
        "parameters_schema": {
          "type": "object",
          "properties": {
            "teacher_id": { "type": "string", "format": "uuid" },
            "subject_ids": { "type": "array", "items": { "type": "string" } }
          },
          "required": ["teacher_id", "subject_ids"]
        },
        "example": "佐藤先生は中受算数と中受理科のみ担当"
      },
      {
        "id": "uuid",
        "code": "C010",
        "kind": "soft",
        "category": "student",
        "name": "講師希望",
        "description": "特定講師を希望",
        "parameters_schema": {
          "type": "object",
          "properties": {
            "student_id": { "type": "string", "format": "uuid" },
            "teacher_id": { "type": "string", "format": "uuid" }
          },
          "required": ["student_id", "teacher_id"]
        },
        "example": "山田くんは佐藤先生を希望"
      }
    ]
  }
}
```

### GET /classrooms/{classroom_id}/terms/{term_id}/constraints

制約条件一覧取得

**Response 200**
```json
{
  "data": {
    "hard_constraints": [
      {
        "code": "H001",
        "name": "科目適合",
        "description": "講師の指導可能科目に、生徒の受講科目が含まれていること",
        "is_always_active": true
      },
      {
        "code": "H002",
        "name": "学年適合",
        "description": "講師の指導可能学年に、生徒の学年が含まれていること",
        "is_always_active": true
      },
      {
        "code": "H003",
        "name": "講師出勤可能時間",
        "description": "講師は出勤可能な時間帯（シフト希望で○）にのみ配置",
        "is_always_active": true
      },
      {
        "code": "H004",
        "name": "生徒通塾可能時間",
        "description": "生徒は通塾可能な時間帯（受講希望で○または△）にのみ配置",
        "is_always_active": true
      },
      {
        "code": "H005",
        "name": "NG組み合わせ禁止",
        "description": "講師-生徒のNG組み合わせは配置禁止",
        "is_always_active": true
      }
    ],
    "soft_constraints": [
      {
        "id": "uuid",
        "constraint_type": "C001",
        "parameters": {
          "teacher_id": "uuid",
          "subject_ids": ["uuid", "uuid"]
        },
        "source_type": "natural_language",
        "source_text": "佐藤先生は中受算数と中受理科のみ担当",
        "confidence": 0.95,
        "priority": 8,
        "is_active": true
      },
      {
        "id": "uuid",
        "constraint_type": "C010",
        "parameters": {
          "student_id": "uuid",
          "teacher_id": "uuid"
        },
        "source_type": "selection",
        "source_text": null,
        "confidence": null,
        "priority": 5,
        "is_active": true
      }
    ]
  }
}
```

### POST /classrooms/{classroom_id}/terms/{term_id}/constraints

制約条件追加

**Request**
```json
{
  "constraint_type": "C001",
  "parameters": {
    "teacher_id": "uuid",
    "subject_ids": ["uuid", "uuid"]
  },
  "priority": 8
}
```

### POST /classrooms/{classroom_id}/terms/{term_id}/constraints/parse

自然言語から制約条件を解析

**Request**
```json
{
  "text": "佐藤先生は中受算数と中受理科のみ担当してください。田中さんは月曜日NGです。"
}
```

**Response 200**
```json
{
  "data": {
    "parsed_constraints": [
      {
        "constraint_type": "C001",
        "parameters": {
          "teacher_id": "uuid",
          "teacher_name": "佐藤先生",
          "subject_ids": ["uuid", "uuid"],
          "subject_names": ["中受算数", "中受理科"]
        },
        "source_text": "佐藤先生は中受算数と中受理科のみ担当",
        "confidence": 0.95
      },
      {
        "constraint_type": "C004",
        "parameters": {
          "student_id": "uuid",
          "student_name": "田中さん",
          "excluded_days": ["mon"]
        },
        "source_text": "田中さんは月曜日NG",
        "confidence": 0.88
      }
    ]
  }
}
```

### PUT /classrooms/{classroom_id}/terms/{term_id}/constraints/{id}

制約条件更新

### DELETE /classrooms/{classroom_id}/terms/{term_id}/constraints/{id}

制約条件削除

---

## 12. 時間割生成 API

### GET /algorithms

アルゴリズム一覧取得

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "code": "ALG001",
      "name": "遺伝的アルゴリズム (GA)",
      "applicable_cases": "中〜大規模、柔軟な制約",
      "characteristics": "大域的探索、多様な解"
    },
    {
      "id": "uuid",
      "code": "ALG002",
      "name": "制約充足ソルバー (CSP)",
      "applicable_cases": "ハード制約が多い",
      "characteristics": "制約の完全充足を保証"
    }
  ]
}
```

### POST /classrooms/{classroom_id}/terms/{term_id}/schedules/recommend-algorithm

アルゴリズム推奨取得

問題規模・制約密度・時間予算・品質要求に基づき最適なアルゴリズムを推奨

**Request**
```json
{
  "time_budget_seconds": 300,
  "quality_target": 90
}
```

**Response 200**
```json
{
  "data": {
    "recommended_algorithm": {
      "code": "ALG001",
      "name": "遺伝的アルゴリズム (GA)",
      "confidence": 0.85
    },
    "analysis": {
      "problem_scale": "medium",
      "teacher_count": 15,
      "student_count": 45,
      "constraint_count": 12,
      "constraint_density": "low"
    },
    "alternatives": [
      {
        "code": "ALG006",
        "name": "ハイブリッド",
        "reason": "制約が複雑な場合に有効"
      },
      {
        "code": "ALG005",
        "name": "貪欲法+局所探索",
        "reason": "時間制約が厳しい場合に有効"
      }
    ]
  }
}
```

### POST /classrooms/{classroom_id}/terms/{term_id}/schedules/generate

時間割生成開始

**Request**
```json
{
  "time_budget_seconds": 300,
  "quality_target": 90,
  "algorithm_preference": null
}
```

**Response 202** (Accepted)
```json
{
  "data": {
    "job_id": "uuid",
    "status": "started",
    "estimated_completion": "2025-03-25T10:05:00Z"
  }
}
```

### GET /classrooms/{classroom_id}/terms/{term_id}/schedules/generate/{job_id}

生成進捗取得

**Response 200**
```json
{
  "data": {
    "job_id": "uuid",
    "status": "running",
    "progress": {
      "phase": "optimization",
      "algorithm": "GA",
      "generation": 150,
      "total_generations": 500,
      "current_fulfillment_rate": 85.2,
      "constraint_violations": 3
    },
    "agent_log": [
      {
        "timestamp": "2025-03-25T10:01:00Z",
        "action": "analyze_problem",
        "result": "問題規模: 中（講師15名、生徒45名）"
      },
      {
        "timestamp": "2025-03-25T10:01:30Z",
        "action": "select_algorithm",
        "result": "GA（遺伝的アルゴリズム）を選択"
      }
    ]
  }
}
```

### POST /classrooms/{classroom_id}/terms/{term_id}/schedules/generate/{job_id}/pause

生成一時停止

### POST /classrooms/{classroom_id}/terms/{term_id}/schedules/generate/{job_id}/resume

生成再開

### POST /classrooms/{classroom_id}/terms/{term_id}/schedules/generate/{job_id}/cancel

生成キャンセル

---

## 13. 時間割 API

### GET /classrooms/{classroom_id}/terms/{term_id}/schedules

時間割一覧取得

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "version": 2,
      "status": "draft",
      "parent_version_id": "uuid",
      "fulfillment_rate": 87.5,
      "algorithm_used": "GA",
      "created_by": { "id": "uuid", "name": "山田太郎" },
      "created_at": "2025-03-20T10:00:00Z",
      "confirmed_at": null
    }
  ]
}
```

### GET /classrooms/{classroom_id}/terms/{term_id}/schedules/{id}

時間割詳細取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| view | string | 'calendar', 'teacher', 'student' |
| target_id | string | 講師/生徒ID（view=teacher/studentの場合） |

**Response 200** (view=calendar)
```json
{
  "data": {
    "id": "uuid",
    "version": 2,
    "status": "draft",
    "fulfillment_rate": 87.5,
    "slots": {
      "mon": {
        "1": [
          {
            "id": "uuid",
            "teacher": { "id": "uuid", "name": "佐藤一郎" },
            "slot_type": "one_to_two",
            "students": [
              { "id": "uuid", "name": "田中太郎", "subject": "中受算数" },
              { "id": "uuid", "name": "山田花子", "subject": "中受算数" }
            ]
          },
          {
            "id": "uuid",
            "teacher": { "id": "uuid", "name": "鈴木次郎" },
            "slot_type": "one_to_one",
            "students": [
              { "id": "uuid", "name": "高橋三郎", "subject": "中学英語" }
            ]
          }
        ],
        "2": [ ... ]
      },
      "tue": { ... }
    },
    "statistics": {
      "total_slots": 120,
      "one_to_two_slots": 100,
      "one_to_one_slots": 20,
      "fulfillment_rate": 87.5,
      "constraint_violations": 2
    },
    "violations": [
      {
        "constraint_id": "uuid",
        "constraint_type": "C003",
        "description": "佐藤先生が4コマ連続になっています",
        "severity": "warning"
      }
    ]
  }
}
```

### PUT /classrooms/{classroom_id}/terms/{term_id}/schedules/{id}/slots/{slot_id}

コマ移動・編集

**Request**
```json
{
  "day_of_week": "tue",
  "slot_number": 2,
  "teacher_id": "uuid"
}
```

**Response 200**
```json
{
  "data": {
    "slot": { ... },
    "validation": {
      "is_valid": true,
      "warnings": [
        "移動により充足率が87.5%から86.2%に低下します"
      ]
    }
  }
}
```

### POST /classrooms/{classroom_id}/terms/{term_id}/schedules/{id}/confirm

時間割確定

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "version": 2,
    "status": "confirmed",
    "confirmed_at": "2025-03-25T15:00:00Z",
    "confirmed_by": { "id": "uuid", "name": "山田太郎" }
  }
}
```

### POST /classrooms/{classroom_id}/terms/{term_id}/schedules/{id}/derive

確定済み時間割から派生

**Response 201**
```json
{
  "data": {
    "id": "new-uuid",
    "version": 3,
    "status": "draft",
    "parent_version_id": "uuid"
  }
}
```

### GET /classrooms/{classroom_id}/terms/{term_id}/schedules/{id}/export/pdf

PDF出力

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| type | string | 'all', 'teacher', 'student' |
| target_id | string | 講師/生徒ID |

**Response 200** (application/pdf)

---

## 14. AIエージェント対話 API

### POST /classrooms/{classroom_id}/terms/{term_id}/schedules/{id}/chat

AIエージェントとの対話

**Request**
```json
{
  "message": "月曜3限の佐藤先生のコマを火曜に移動できる？"
}
```

**Response 200**
```json
{
  "data": {
    "response": "火曜1限と2限が空いています。1限は生徒Aも空いています（推奨）。どちらに移動しますか？",
    "suggestions": [
      {
        "action": "move_slot",
        "parameters": {
          "slot_id": "uuid",
          "target_day": "tue",
          "target_slot": 1
        },
        "label": "火曜1限に移動（推奨）",
        "impact": {
          "fulfillment_rate_change": 0.7,
          "new_violations": 0
        }
      },
      {
        "action": "move_slot",
        "parameters": {
          "slot_id": "uuid",
          "target_day": "tue",
          "target_slot": 2
        },
        "label": "火曜2限に移動",
        "impact": {
          "fulfillment_rate_change": -0.3,
          "new_violations": 1
        }
      }
    ],
    "thinking_process": [
      "月曜3限の佐藤先生のコマを特定",
      "火曜の空きスロットを検索",
      "生徒の希望データを確認",
      "制約違反をチェック"
    ]
  }
}
```

### POST /classrooms/{classroom_id}/terms/{term_id}/schedules/{id}/chat/execute

提案を実行

**Request**
```json
{
  "action": "move_slot",
  "parameters": {
    "slot_id": "uuid",
    "target_day": "tue",
    "target_slot": 1
  }
}
```

**Response 200**
```json
{
  "data": {
    "success": true,
    "message": "移動しました。充足率: 87.5% → 88.2%",
    "updated_slot": { ... },
    "statistics": {
      "fulfillment_rate": 88.2,
      "constraint_violations": 1
    }
  }
}
```

---

## 15. 振替 API

### GET /classrooms/{classroom_id}/absences

欠席・振替一覧取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| status | string | ステータスでフィルター |
| term_id | string | タームでフィルター |
| absent_type | string | 'teacher' or 'student' |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "schedule_slot": {
        "id": "uuid",
        "day_of_week": "mon",
        "slot_number": 2,
        "teacher": { "id": "uuid", "name": "佐藤一郎" },
        "students": [
          { "id": "uuid", "name": "田中太郎", "subject": "中受算数" }
        ]
      },
      "absent_type": "student",
      "absent_target": { "id": "uuid", "name": "田中太郎" },
      "reason": "体調不良",
      "status": "pending",
      "reschedule": null,
      "created_at": "2025-03-25T10:00:00Z"
    }
  ]
}
```

### POST /classrooms/{classroom_id}/absences

欠席登録

**Request**
```json
{
  "schedule_slot_id": "uuid",
  "absent_type": "student",
  "absent_id": "uuid",
  "reason": "体調不良",
  "needs_reschedule": true
}
```

**Response 201**
```json
{
  "data": {
    "id": "uuid",
    "status": "pending",
    "candidates": [
      {
        "slot": {
          "day_of_week": "wed",
          "slot_number": 2,
          "date": "2025-03-27"
        },
        "type": "same_teacher",
        "teacher": { "id": "uuid", "name": "佐藤一郎" },
        "priority_score": 95,
        "reasons": ["元講師が担当可能", "生徒の希望時間帯", "日程が近い"]
      },
      {
        "slot": {
          "day_of_week": "thu",
          "slot_number": 1,
          "date": "2025-03-28"
        },
        "type": "substitute",
        "teacher": { "id": "uuid", "name": "鈴木次郎" },
        "priority_score": 72,
        "reasons": ["生徒の希望時間帯", "同一科目指導可能"]
      }
    ]
  }
}
```

### POST /classrooms/{classroom_id}/absences/{id}/reschedule

振替確定

**Request**
```json
{
  "day_of_week": "wed",
  "slot_number": 2,
  "teacher_id": "uuid",
  "reschedule_type": "same_teacher"
}
```

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "status": "rescheduled",
    "reschedule": {
      "id": "uuid",
      "new_slot": {
        "day_of_week": "wed",
        "slot_number": 2,
        "teacher": { "id": "uuid", "name": "佐藤一郎" }
      },
      "confirmed_at": "2025-03-25T11:00:00Z"
    }
  }
}
```

### DELETE /classrooms/{classroom_id}/absences/{id}

欠席登録取消

---

## 16. ダッシュボード API

### GET /classrooms/{classroom_id}/dashboard

教室長ダッシュボード取得

**Response 200**
```json
{
  "data": {
    "fulfillment_summary": {
      "current_rate": 87.5,
      "target_rate": 90.0,
      "trend": "up",
      "change_from_last_term": 2.3
    },
    "heatmap": {
      "mon": {
        "1": { "supply": 6, "demand": 5, "status": "sufficient" },
        "2": { "supply": 5, "demand": 6, "status": "shortage" }
      },
      ...
    },
    "subject_coverage": [
      { "subject": "中受算数", "coverage_rate": 120, "status": "sufficient" },
      { "subject": "中学英語", "coverage_rate": 85, "status": "warning" }
    ],
    "supply_demand": {
      "total_supply": 150,
      "total_demand": 142,
      "balance": 8
    },
    "alerts": [
      {
        "type": "low_coverage",
        "message": "中学英語のカバー率が85%です",
        "severity": "warning",
        "action": { "label": "講師追加を検討", "link": "/teachers" }
      },
      {
        "type": "missing_preferences",
        "message": "3名の講師が希望データ未提出です",
        "severity": "info",
        "action": { "label": "確認する", "link": "/preferences/missing" }
      }
    ],
    "current_term": {
      "id": "uuid",
      "name": "2025年4月期",
      "status": "draft",
      "days_until_start": 7
    }
  }
}
```

### GET /areas/{area_id}/dashboard

エリアマネジャーダッシュボード取得

**Response 200**
```json
{
  "data": {
    "area": {
      "id": "uuid",
      "name": "東京エリア"
    },
    "classrooms": [
      {
        "id": "uuid",
        "name": "渋谷教室",
        "fulfillment_rate": 92.5,
        "status": "healthy",
        "change_from_last_term": 3.2,
        "alerts_count": 0
      },
      {
        "id": "uuid",
        "name": "新宿教室",
        "fulfillment_rate": 78.3,
        "status": "warning",
        "change_from_last_term": -5.1,
        "alerts_count": 3
      }
    ],
    "summary": {
      "total_classrooms": 5,
      "healthy_count": 3,
      "warning_count": 1,
      "critical_count": 1,
      "average_fulfillment_rate": 85.2
    }
  }
}
```

---

## 17. ユーザー管理 API（管理者用）

### GET /admin/users

ユーザー一覧取得

### GET /admin/users/{id}

ユーザー詳細取得

### POST /admin/users

ユーザー新規作成

**Request**
```json
{
  "name": "新規ユーザー",
  "email": "new@example.com",
  "role": "classroom_manager",
  "classroom_id": "uuid"
}
```

### PUT /admin/users/{id}

ユーザー更新

### DELETE /admin/users/{id}

ユーザー削除

### POST /admin/users/{id}/reset-password

パスワードリセット（管理者実行）

### GET /admin/audit-logs

監査ログ一覧取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| user_id | string | ユーザーIDでフィルター |
| action | string | 操作種別でフィルター |
| target_type | string | 対象タイプでフィルター |
| from | string | 開始日時（ISO 8601） |
| to | string | 終了日時（ISO 8601） |
| page | number | ページ番号 |
| per_page | number | 1ページあたり件数 |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "user": { "id": "uuid", "name": "山田太郎" },
      "action": "update",
      "target_type": "teacher",
      "target_id": "uuid",
      "details": {
        "before": { "max_slots_per_week": 8 },
        "after": { "max_slots_per_week": 10 }
      },
      "ip_address": "192.168.1.1",
      "created_at": "2025-03-25T10:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

### GET /admin/audit-logs/{id}

監査ログ詳細取得

---

## 18. 通知 API

### GET /notifications

通知一覧取得（ログインユーザーの通知）

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| is_read | boolean | 既読フラグでフィルター |
| severity | string | 重要度でフィルター |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "type": "low_coverage",
      "title": "カバー率低下",
      "message": "中学英語のカバー率が85%です",
      "severity": "warning",
      "action_link": "/classrooms/uuid/teachers",
      "is_read": false,
      "created_at": "2025-03-25T10:00:00Z"
    }
  ],
  "unread_count": 3
}
```

### PUT /notifications/{id}/read

通知を既読にする

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "is_read": true,
    "read_at": "2025-03-25T10:30:00Z"
  }
}
```

### PUT /notifications/read-all

全通知を既読にする

**Response 200**
```json
{
  "data": {
    "updated_count": 5
  }
}
```

---

## 19. Google Form連携 API

### GET /classrooms/{classroom_id}/google-connections

連携設定一覧取得

### POST /classrooms/{classroom_id}/google-connections

連携設定作成

**Request**
```json
{
  "data_type": "teacher_shift",
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/xxx",
  "sheet_name": "シフト希望"
}
```

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "data_type": "teacher_shift",
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/xxx",
    "sheet_name": "シフト希望",
    "detected_columns": [
      { "index": 0, "header": "講師名", "suggested_mapping": "teacher_name" },
      { "index": 1, "header": "月曜1限", "suggested_mapping": "preference_mon_1" }
    ],
    "column_mapping": null,
    "sync_status": "pending_setup"
  }
}
```

### PUT /classrooms/{classroom_id}/google-connections/{id}/mapping

カラムマッピング設定

**Request**
```json
{
  "column_mapping": {
    "teacher_name": 0,
    "preference_mon_1": 1,
    "preference_mon_2": 2,
    ...
  }
}
```

### POST /classrooms/{classroom_id}/google-connections/{id}/test

接続テスト

### DELETE /classrooms/{classroom_id}/google-connections/{id}

連携設定削除

---

## 20. 科目マスタ API

### GET /subjects

科目一覧取得

**Query Parameters**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| category | string | カテゴリでフィルター |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "中受算数",
      "code": "MATH_JR_EXAM",
      "category": "elementary",
      "display_order": 3
    }
  ]
}
```

---

## 21. WebSocket API

### 接続

```
wss://api.example.com/v1/ws?token={jwt_token}
```

### イベント

#### 時間割生成進捗

```json
{
  "type": "schedule_generation_progress",
  "data": {
    "job_id": "uuid",
    "progress": 45,
    "phase": "optimization",
    "current_fulfillment_rate": 82.5
  }
}
```

#### 通知

```json
{
  "type": "notification",
  "data": {
    "id": "uuid",
    "title": "希望データ同期完了",
    "message": "15件のデータを同期しました",
    "severity": "info",
    "action": { "label": "確認", "link": "/preferences" }
  }
}
```

---

## 22. エラーコード一覧

| コード | HTTPステータス | 説明 |
|-------|--------------|------|
| INVALID_CREDENTIALS | 401 | 認証情報が無効 |
| TOKEN_EXPIRED | 401 | トークン期限切れ |
| FORBIDDEN | 403 | 権限不足 |
| NOT_FOUND | 404 | リソースが見つからない |
| VALIDATION_ERROR | 400 | バリデーションエラー |
| DUPLICATE_ENTRY | 409 | 重複エントリ |
| SCHEDULE_LOCKED | 422 | 確定済み時間割は編集不可 |
| CONSTRAINT_VIOLATION | 422 | 制約違反 |
| GENERATION_IN_PROGRESS | 409 | 生成処理中 |
| SYNC_ERROR | 422 | 同期エラー |
| INTERNAL_ERROR | 500 | サーバー内部エラー |
