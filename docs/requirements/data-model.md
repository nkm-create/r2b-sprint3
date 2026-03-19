# データモデル設計書

## 1. 概要

本ドキュメントは、学習塾時間割最適化システムのデータモデルを定義する。

### 1.1 設計方針

- **バージョン管理**: 講師・生徒・時間割は履歴管理を行い、過去データとの整合性を維持
- **論理削除**: 削除は`deleted_at`フラグで管理し、物理削除は行わない
- **正規化**: 基本的に第3正規形を維持。パフォーマンス上必要な場合のみ非正規化
- **命名規則**: スネークケース、テーブル名は複数形

---

## 2. ER図

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              システム管理領域                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐     ┌──────────────┐     ┌──────────┐                        │
│  │  users   │────<│ user_roles   │>────│  roles   │                        │
│  └──────────┘     └──────────────┘     └──────────┘                        │
│       │                                                                     │
│       │ belongs_to                                                          │
│       ▼                                                                     │
│  ┌────────────┐     ┌──────────┐                                           │
│  │ classrooms │────<│  areas   │                                           │
│  └────────────┘     └──────────┘                                           │
│       │                                                                     │
└───────┼─────────────────────────────────────────────────────────────────────┘
        │
        │ has_many
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              教室設定領域                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────┐     ┌──────────────┐                                │
│  │ classroom_settings│     │  time_slots  │                                │
│  └───────────────────┘     └──────────────┘                                │
│                                   │                                         │
│                                   │ referenced_by                           │
│                                   ▼                                         │
│                            ┌─────────────────┐                             │
│                            │ shift_preferences│                             │
│                            └─────────────────┘                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              マスタ領域（バージョン管理）                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐     ┌───────────────────┐     ┌───────────────────┐          │
│  │ teachers │────<│ teacher_versions  │────<│ teacher_subjects  │          │
│  └──────────┘     └───────────────────┘     └───────────────────┘          │
│                           │                         │                       │
│                           │                         ▼                       │
│                           │                   ┌──────────┐                 │
│                           │                   │ subjects │                 │
│                           │                   └──────────┘                 │
│                           │                         ▲                       │
│                           │                         │                       │
│  ┌──────────┐     ┌───────────────────┐     ┌───────────────────┐          │
│  │ students │────<│ student_versions  │────<│ student_subjects  │          │
│  └──────────┘     └───────────────────┘     └───────────────────┘          │
│                                                                             │
│                   ┌───────────────────┐                                    │
│                   │   ng_relations    │                                    │
│                   └───────────────────┘                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              時間割領域                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐     ┌──────────────┐     ┌────────────────┐                  │
│  │  terms   │────<│  schedules   │────<│ schedule_slots │                  │
│  └──────────┘     └──────────────┘     └────────────────┘                  │
│       │                  │                     │                            │
│       │                  │                     │ references                 │
│       │                  │                     ▼                            │
│       │                  │              ┌─────────────────┐                │
│       │                  └─────────────>│ master_snapshots│                │
│       │                                 └─────────────────┘                │
│       │                                                                     │
│       │           ┌──────────────┐                                         │
│       └──────────>│ constraints  │                                         │
│                   └──────────────┘                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              振替領域                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐     ┌──────────────┐                                         │
│  │ absences │────<│ reschedules  │                                         │
│  └──────────┘     └──────────────┘                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. テーブル定義

### 3.1 ユーザー管理

#### users

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| name | VARCHAR(50) | NO | 氏名 |
| email | VARCHAR(255) | NO | メールアドレス（ユニーク） |
| password_hash | VARCHAR(255) | NO | パスワードハッシュ |
| status | ENUM | NO | 'active', 'inactive', 'locked' |
| failed_login_count | INT | NO | ログイン失敗回数（デフォルト: 0） |
| last_login_at | TIMESTAMP | YES | 最終ログイン日時 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |
| deleted_at | TIMESTAMP | YES | 削除日時（論理削除） |

#### roles

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| name | VARCHAR(50) | NO | 役割名（'classroom_manager', 'area_manager', 'system_admin'） |
| description | VARCHAR(200) | YES | 説明 |

#### user_roles

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| user_id | UUID | NO | FK: users.id |
| role_id | UUID | NO | FK: roles.id |
| classroom_id | UUID | YES | FK: classrooms.id（教室長の場合） |
| area_id | UUID | YES | FK: areas.id（エリアマネジャーの場合） |

#### refresh_tokens

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| user_id | UUID | NO | FK: users.id |
| token_hash | VARCHAR(255) | NO | トークンのハッシュ値 |
| expires_at | TIMESTAMP | NO | 有効期限 |
| revoked_at | TIMESTAMP | YES | 無効化日時 |
| user_agent | VARCHAR(500) | YES | ユーザーエージェント |
| ip_address | VARCHAR(45) | YES | IPアドレス |
| created_at | TIMESTAMP | NO | 作成日時 |

---

### 3.2 教室管理

#### areas

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| name | VARCHAR(100) | NO | エリア名 |
| code | VARCHAR(20) | NO | エリアコード（ユニーク） |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

#### classrooms

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| area_id | UUID | NO | FK: areas.id |
| name | VARCHAR(100) | NO | 教室名 |
| code | VARCHAR(20) | NO | 教室コード（ユニーク） |
| address | VARCHAR(200) | YES | 住所 |
| phone | VARCHAR(20) | YES | 電話番号 |
| status | ENUM | NO | 'active', 'closed' |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |
| deleted_at | TIMESTAMP | YES | 削除日時 |

#### classroom_settings

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| classroom_id | UUID | NO | FK: classrooms.id |
| operating_days | JSONB | NO | 営業曜日（例: ["mon","tue","wed","thu","fri","sat"]） |
| capacity | INT | NO | ブース数（同時実施可能コマ数） |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

#### time_slots

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| classroom_id | UUID | NO | FK: classrooms.id |
| day_type | ENUM | NO | 'weekday', 'saturday' |
| slot_number | INT | NO | 限の番号（0〜4） |
| start_time | TIME | NO | 開始時刻 |
| end_time | TIME | NO | 終了時刻 |
| is_active | BOOLEAN | NO | 有効フラグ |

---

### 3.3 科目マスタ

#### subjects

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| name | VARCHAR(50) | NO | 科目名 |
| category | ENUM | NO | 'elementary', 'junior_high', 'high_school' |
| code | VARCHAR(20) | NO | 科目コード（ユニーク） |
| display_order | INT | NO | 表示順 |
| is_active | BOOLEAN | NO | 有効フラグ |

**デフォルト科目データ**:
- 小学生: 小学英語, 公立算数, 中受算数, 小学国語, 小論, 公立理科, 中受理科, 公立社会, 中受社会
- 中学生: 中学英語, 公立数学, 私立数学, 中学国語, 中学理科, 中学社会
- 高校生: 高校12英語, 高3英語, 高校国語, 数1A, 数ⅡB, 数Ⅲ, 生物, 化学, 物理, 世界史, 日本史, 地理

---

### 3.4 講師管理（バージョン管理対応）

#### teachers

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー（講師の不変ID） |
| classroom_id | UUID | NO | FK: classrooms.id |
| display_id | VARCHAR(20) | NO | 表示用ID（例: T001） |
| created_at | TIMESTAMP | NO | 作成日時 |
| deleted_at | TIMESTAMP | YES | 削除日時 |

#### teacher_versions

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| teacher_id | UUID | NO | FK: teachers.id |
| version_number | INT | NO | バージョン番号 |
| is_current | BOOLEAN | NO | 現在有効なバージョンか |
| valid_from | TIMESTAMP | NO | 有効開始日時 |
| valid_to | TIMESTAMP | YES | 有効終了日時 |
| change_reason | VARCHAR(200) | YES | 変更理由 |
| name | VARCHAR(50) | NO | 氏名 |
| gender | ENUM | NO | 'male', 'female' |
| min_slots_per_week | INT | NO | 最小コマ/週 |
| max_slots_per_week | INT | NO | 最大コマ/週 |
| max_consecutive_slots | INT | NO | 最大連続コマ |
| university_rank | ENUM | YES | 'A', 'B', 'C' |
| has_junior_high_exam_exp | BOOLEAN | NO | 中学受験経験 |
| has_high_school_exam_exp | BOOLEAN | NO | 高校受験経験 |
| status | ENUM | NO | 'active', 'inactive' |
| created_at | TIMESTAMP | NO | 作成日時 |

#### teacher_subjects

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| teacher_version_id | UUID | NO | FK: teacher_versions.id |
| subject_id | UUID | NO | FK: subjects.id |

#### teacher_grades

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| teacher_version_id | UUID | NO | FK: teacher_versions.id |
| grade | ENUM | NO | 'elementary_1'〜'high_school_3' |

---

### 3.5 生徒管理（バージョン管理対応）

#### students

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー（生徒の不変ID） |
| classroom_id | UUID | NO | FK: classrooms.id |
| display_id | VARCHAR(20) | NO | 表示用ID（例: S001） |
| created_at | TIMESTAMP | NO | 作成日時 |
| deleted_at | TIMESTAMP | YES | 削除日時 |

#### student_versions

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| student_id | UUID | NO | FK: students.id |
| version_number | INT | NO | バージョン番号 |
| is_current | BOOLEAN | NO | 現在有効なバージョンか |
| valid_from | TIMESTAMP | NO | 有効開始日時 |
| valid_to | TIMESTAMP | YES | 有効終了日時 |
| change_reason | VARCHAR(200) | YES | 変更理由 |
| name | VARCHAR(50) | NO | 氏名 |
| grade | ENUM | NO | 'elementary_1'〜'high_school_3' |
| max_consecutive_slots | INT | NO | 最大連続コマ |
| preferred_teacher_id | UUID | YES | FK: teachers.id（希望講師） |
| preferred_teacher_gender | ENUM | YES | 'male', 'female', 'none' |
| aspiration_level | ENUM | YES | 'A', 'B', 'C' |
| purpose | ENUM | YES | 'high_school_exam', 'junior_high_exam', 'internal_promotion', 'supplementary', 'other' |
| status | ENUM | NO | 'enrolled', 'suspended', 'withdrawn' |
| created_at | TIMESTAMP | NO | 作成日時 |

#### student_subjects

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| student_version_id | UUID | NO | FK: student_versions.id |
| subject_id | UUID | NO | FK: subjects.id |
| slots_per_week | INT | NO | 週あたりコマ数 |

---

### 3.6 NG関係

#### ng_relations

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| teacher_id | UUID | NO | FK: teachers.id |
| student_id | UUID | NO | FK: students.id |
| created_by | ENUM | NO | 'teacher', 'student'（どちら側から設定されたか） |
| reason | VARCHAR(200) | YES | 理由 |
| created_at | TIMESTAMP | NO | 作成日時 |

**制約**: (teacher_id, student_id) でユニーク

---

### 3.7 希望データ

#### shift_preferences

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| classroom_id | UUID | NO | FK: classrooms.id |
| term_id | UUID | NO | FK: terms.id |
| target_type | ENUM | NO | 'teacher', 'student' |
| target_id | UUID | NO | 対象者ID（teacher_id or student_id） |
| day_of_week | ENUM | NO | 'mon'〜'sat' |
| slot_number | INT | NO | 限の番号 |
| preference | ENUM | NO | 'available', 'unavailable', 'preferred' |
| is_manually_edited | BOOLEAN | NO | 手動編集フラグ |
| source | ENUM | NO | 'google_form', 'manual' |
| synced_at | TIMESTAMP | YES | Google Form同期日時 |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

---

### 3.8 ターム・時間割

#### terms

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| classroom_id | UUID | NO | FK: classrooms.id |
| name | VARCHAR(100) | NO | ターム名（例: 2025年4月期） |
| start_date | DATE | NO | 開始日 |
| end_date | DATE | NO | 終了日 |
| status | ENUM | NO | 'draft', 'confirmed', 'archived' |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |
| deleted_at | TIMESTAMP | YES | 削除日時 |

#### constraints

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| term_id | UUID | NO | FK: terms.id |
| constraint_type | VARCHAR(20) | NO | 制約ID（例: C001） |
| parameters | JSONB | NO | 制約パラメータ |
| source_text | TEXT | YES | 元の自然言語テキスト |
| confidence | DECIMAL(3,2) | YES | 解析信頼度（0.00〜1.00） |
| priority | INT | NO | 優先度（1〜10） |
| is_active | BOOLEAN | NO | 有効フラグ |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

#### schedules

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| term_id | UUID | NO | FK: terms.id |
| version | INT | NO | バージョン番号 |
| status | ENUM | NO | 'draft', 'confirmed', 'archived' |
| parent_version_id | UUID | YES | FK: schedules.id（派生元） |
| fulfillment_rate | DECIMAL(5,2) | YES | 1対2充足率 |
| algorithm_used | VARCHAR(20) | YES | 使用アルゴリズム（ALG001等） |
| generation_config | JSONB | YES | 生成時の設定 |
| agent_log | JSONB | YES | AIエージェントのログ |
| created_by | UUID | NO | FK: users.id |
| confirmed_at | TIMESTAMP | YES | 確定日時 |
| confirmed_by | UUID | YES | FK: users.id |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

#### master_snapshots

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| schedule_id | UUID | NO | FK: schedules.id |
| snapshot_type | ENUM | NO | 'teacher', 'student' |
| data | JSONB | NO | スナップショットデータ |
| created_at | TIMESTAMP | NO | 作成日時 |

#### schedule_slots

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| schedule_id | UUID | NO | FK: schedules.id |
| day_of_week | ENUM | NO | 'mon'〜'sat' |
| slot_number | INT | NO | 限の番号 |
| teacher_id | UUID | NO | FK: teachers.id |
| teacher_version_id | UUID | NO | FK: teacher_versions.id |
| slot_type | ENUM | NO | 'one_to_one', 'one_to_two' |
| status | ENUM | NO | 'scheduled', 'absent', 'rescheduled' |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

#### schedule_slot_students

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| schedule_slot_id | UUID | NO | FK: schedule_slots.id |
| student_id | UUID | NO | FK: students.id |
| student_version_id | UUID | NO | FK: student_versions.id |
| subject_id | UUID | NO | FK: subjects.id |
| position | INT | NO | 席番号（1 or 2） |

---

### 3.9 振替管理

#### absences

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| schedule_slot_id | UUID | NO | FK: schedule_slots.id |
| absent_type | ENUM | NO | 'teacher', 'student' |
| absent_id | UUID | NO | 対象者ID |
| reason | VARCHAR(200) | YES | 欠席理由 |
| needs_reschedule | BOOLEAN | NO | 振替希望有無 |
| status | ENUM | NO | 'pending', 'rescheduled', 'cancelled' |
| created_by | UUID | NO | FK: users.id |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

#### reschedules

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| absence_id | UUID | NO | FK: absences.id |
| new_schedule_slot_id | UUID | NO | FK: schedule_slots.id |
| reschedule_type | ENUM | NO | 'same_teacher', 'substitute' |
| confirmed_at | TIMESTAMP | YES | 確定日時 |
| confirmed_by | UUID | YES | FK: users.id |
| created_at | TIMESTAMP | NO | 作成日時 |

---

### 3.10 Google Form連携

#### google_form_connections

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| classroom_id | UUID | NO | FK: classrooms.id |
| data_type | ENUM | NO | 'teacher_shift', 'student_preference' |
| spreadsheet_url | VARCHAR(500) | NO | スプレッドシートURL |
| sheet_name | VARCHAR(100) | NO | シート名 |
| column_mapping | JSONB | NO | カラムマッピング |
| last_synced_at | TIMESTAMP | YES | 最終同期日時 |
| sync_status | ENUM | NO | 'active', 'error', 'disconnected' |
| created_at | TIMESTAMP | NO | 作成日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

---

### 3.11 監査・通知

#### audit_logs

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| user_id | UUID | YES | FK: users.id（システム操作の場合はNULL） |
| action | VARCHAR(50) | NO | 操作種別（'login', 'create', 'update', 'delete', 'export'等） |
| target_type | VARCHAR(50) | NO | 対象タイプ（'teacher', 'student', 'schedule'等） |
| target_id | UUID | YES | 対象ID |
| details | JSONB | YES | 操作詳細（変更前後の値等） |
| ip_address | VARCHAR(45) | YES | IPアドレス |
| user_agent | VARCHAR(500) | YES | ユーザーエージェント |
| created_at | TIMESTAMP | NO | 作成日時 |

**備考**: 書き込み専用。削除・更新は不可。90日経過後にアーカイブ、1年後に削除。

#### notifications

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| user_id | UUID | NO | FK: users.id |
| type | VARCHAR(50) | NO | 通知種別（'low_coverage', 'missing_preferences', 'term_deadline'等） |
| title | VARCHAR(100) | NO | 通知タイトル |
| message | TEXT | NO | 通知メッセージ |
| severity | ENUM | NO | 'info', 'warning', 'error' |
| action_link | VARCHAR(500) | YES | アクションリンク |
| is_read | BOOLEAN | NO | 既読フラグ（デフォルト: false） |
| related_type | VARCHAR(50) | YES | 関連エンティティタイプ |
| related_id | UUID | YES | 関連エンティティID |
| created_at | TIMESTAMP | NO | 作成日時 |
| read_at | TIMESTAMP | YES | 既読日時 |

---

### 3.12 マスタ（アルゴリズム・制約種別）

#### algorithms

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| code | VARCHAR(20) | NO | アルゴリズムコード（'ALG001'〜'ALG006'）（ユニーク） |
| name | VARCHAR(100) | NO | アルゴリズム名 |
| description | TEXT | YES | 説明 |
| applicable_cases | TEXT | YES | 適用ケース |
| characteristics | TEXT | YES | 特徴 |
| is_active | BOOLEAN | NO | 有効フラグ |
| display_order | INT | NO | 表示順 |

**デフォルトデータ**:
| code | name | 適用ケース |
|------|------|-----------|
| ALG001 | 遺伝的アルゴリズム (GA) | 中〜大規模、柔軟な制約 |
| ALG002 | 制約充足ソルバー (CSP) | ハード制約が多い |
| ALG003 | 整数線形計画法 (ILP) | 小〜中規模 |
| ALG004 | 焼きなまし法 (SA) | 連続的な改善 |
| ALG005 | 貪欲法+局所探索 (Greedy+LS) | 大規模、時間制約が厳しい |
| ALG006 | ハイブリッド (Hybrid) | 複雑な問題 |

#### constraint_types

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| code | VARCHAR(20) | NO | 制約コード（'C001'〜'C032'）（ユニーク） |
| category | ENUM | NO | 'teacher', 'student', 'matching', 'time' |
| name | VARCHAR(100) | NO | 制約名 |
| description | TEXT | YES | 説明 |
| parameters_schema | JSONB | NO | パラメータスキーマ（JSONスキーマ形式） |
| example | TEXT | YES | 使用例 |
| is_active | BOOLEAN | NO | 有効フラグ |
| display_order | INT | NO | 表示順 |

**デフォルトデータ（抜粋）**:
| code | category | name | パラメータ |
|------|----------|------|-----------|
| C001 | teacher | 科目限定 | {講師ID, 科目リスト} |
| C002 | teacher | コマ数固定 | {講師ID, 最小, 最大} |
| C003 | teacher | 連続コマ上限 | {講師ID, 上限} |
| C004 | teacher | 曜日限定 | {講師ID, 曜日リスト} |
| C010 | student | 講師希望 | {生徒ID, 講師ID} |
| C011 | student | 講師NG | {生徒ID, 講師IDリスト} |
| C012 | student | 性別希望 | {生徒ID, 性別} |
| C013 | student | 連続コマ上限 | {生徒ID, 上限} |
| C020 | matching | 志望レベル→大学ランク | {生徒志望レベル, 講師ランクリスト} |
| C021 | matching | 中受経験優先 | {対象科目リスト} |
| C022 | matching | 高受経験優先 | {対象科目リスト} |
| C023 | matching | 同一科目ペアリング | {} |
| C030 | time | 充足率目標 | {目標値} |
| C031 | time | ブースキャパシティ | {上限} |
| C032 | time | 時間帯優先 | {時間帯リスト, 優先度} |

---

### 3.13 インポート履歴

#### import_histories

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| id | UUID | NO | 主キー |
| classroom_id | UUID | NO | FK: classrooms.id |
| import_type | ENUM | NO | 'teacher', 'student' |
| file_name | VARCHAR(255) | NO | ファイル名 |
| total_rows | INT | NO | 総行数 |
| success_count | INT | NO | 成功件数 |
| error_count | INT | NO | エラー件数 |
| error_details | JSONB | YES | エラー詳細 |
| created_by | UUID | NO | FK: users.id |
| created_at | TIMESTAMP | NO | 作成日時 |

---

## 4. インデックス設計

### 4.1 主要インデックス

```sql
-- ユーザー検索
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;

-- 教室検索
CREATE INDEX idx_classrooms_area ON classrooms(area_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_classrooms_code ON classrooms(code) WHERE deleted_at IS NULL;

-- 講師検索（現在バージョン）
CREATE INDEX idx_teacher_versions_current ON teacher_versions(teacher_id)
  WHERE is_current = true;
CREATE INDEX idx_teacher_versions_name ON teacher_versions(name)
  WHERE is_current = true;

-- 生徒検索（現在バージョン）
CREATE INDEX idx_student_versions_current ON student_versions(student_id)
  WHERE is_current = true;
CREATE INDEX idx_student_versions_grade ON student_versions(grade)
  WHERE is_current = true;

-- 時間割検索
CREATE INDEX idx_schedules_term ON schedules(term_id);
CREATE INDEX idx_schedules_status ON schedules(term_id, status);
CREATE INDEX idx_schedule_slots_schedule ON schedule_slots(schedule_id);
CREATE INDEX idx_schedule_slots_teacher ON schedule_slots(teacher_id);

-- 希望データ検索
CREATE INDEX idx_shift_preferences_target ON shift_preferences(target_type, target_id);
CREATE INDEX idx_shift_preferences_term ON shift_preferences(term_id);

-- NG関係
CREATE UNIQUE INDEX idx_ng_relations_pair ON ng_relations(teacher_id, student_id);

-- 監査ログ
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_target ON audit_logs(target_type, target_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- 通知
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created ON notifications(created_at);

-- リフレッシュトークン
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- インポート履歴
CREATE INDEX idx_import_histories_classroom ON import_histories(classroom_id);
CREATE INDEX idx_import_histories_created ON import_histories(created_at);
```

---

## 5. データ整合性制約

### 5.1 外部キー制約

主要な外部キー制約は各テーブル定義に記載。CASCADE DELETE は使用せず、アプリケーション層で整合性を管理。

### 5.2 ビジネスルール制約

```sql
-- 講師: 最小コマ ≤ 最大コマ
ALTER TABLE teacher_versions
ADD CONSTRAINT chk_teacher_slots
CHECK (min_slots_per_week <= max_slots_per_week);

-- 連続コマ上限（1〜4）
ALTER TABLE teacher_versions
ADD CONSTRAINT chk_teacher_consecutive
CHECK (max_consecutive_slots BETWEEN 1 AND 4);

ALTER TABLE student_versions
ADD CONSTRAINT chk_student_consecutive
CHECK (max_consecutive_slots BETWEEN 1 AND 4);

-- 週コマ数（正の整数）
ALTER TABLE student_subjects
ADD CONSTRAINT chk_slots_positive
CHECK (slots_per_week > 0);

-- 充足率（0〜100）
ALTER TABLE schedules
ADD CONSTRAINT chk_fulfillment_rate
CHECK (fulfillment_rate BETWEEN 0 AND 100);
```

### 5.3 学年・科目整合性

アプリケーション層で以下のチェックを実施:

| 学年カテゴリ | 許可される科目カテゴリ |
|------------|---------------------|
| elementary_1〜elementary_6 | elementary |
| junior_high_1〜junior_high_3 | junior_high |
| high_school_1〜high_school_3 | high_school |

---

## 6. バージョン管理の動作

### 6.1 マスタ更新時

```
[講師情報を更新]
    ↓
1. 現在のバージョンをis_current=false, valid_to=nowに更新
    ↓
2. 新バージョンを作成(is_current=true, valid_from=now)
    ↓
3. 関連データ（teacher_subjects, teacher_grades）も新バージョンにコピー
```

### 6.2 時間割確定時

```
[時間割を確定]
    ↓
1. schedule.statusをdraft→confirmedに変更
    ↓
2. master_snapshotsに現在の講師・生徒マスタをJSONで保存
    ↓
3. confirmed_at, confirmed_byを記録
```

### 6.3 確定済み時間割の修正

```
[確定済み時間割を修正したい]
    ↓
1. 既存scheduleをコピーして新version作成
    ↓
2. parent_version_idに元scheduleを設定
    ↓
3. 新scheduleをdraftステータスで作成
    ↓
4. 修正後、再度確定処理
```

---

## 7. 付録: ENUM値一覧

### user_status
- 'active': 有効
- 'inactive': 無効
- 'locked': ロック済み

### role_name
- 'classroom_manager': 教室長
- 'area_manager': エリアマネジャー
- 'system_admin': システム管理者

### classroom_status
- 'active': 運営中
- 'closed': 閉鎖

### gender
- 'male': 男性
- 'female': 女性

### grade
- 'elementary_1'〜'elementary_6': 小1〜小6
- 'junior_high_1'〜'junior_high_3': 中1〜中3
- 'high_school_1'〜'high_school_3': 高1〜高3

### rank
- 'A', 'B', 'C'

### student_status
- 'enrolled': 在籍
- 'suspended': 休会
- 'withdrawn': 退会

### purpose
- 'high_school_exam': 高校受験
- 'junior_high_exam': 中学受験
- 'internal_promotion': 内部進学
- 'supplementary': 補習
- 'other': その他

### preference_value
- 'available': ○（可能）
- 'unavailable': ×（不可）
- 'preferred': △（できれば可）

### term_status
- 'draft': 作成中
- 'confirmed': 確定
- 'archived': アーカイブ

### schedule_status
- 'draft': 作成中
- 'confirmed': 確定
- 'archived': アーカイブ

### slot_type
- 'one_to_one': 1対1
- 'one_to_two': 1対2

### slot_status
- 'scheduled': 予定通り
- 'absent': 欠席
- 'rescheduled': 振替済み

### absence_status
- 'pending': 振替待ち
- 'rescheduled': 振替済み
- 'cancelled': 振替なし

### notification_severity
- 'info': 情報
- 'warning': 警告
- 'error': エラー

### audit_action
- 'login': ログイン
- 'logout': ログアウト
- 'create': 作成
- 'update': 更新
- 'delete': 削除
- 'export': エクスポート
- 'import': インポート
- 'confirm': 確定
- 'generate': 生成

### constraint_category
- 'teacher': 講師制約
- 'student': 生徒制約
- 'matching': マッチング制約
- 'time': 時間制約

### import_type
- 'teacher': 講師
- 'student': 生徒
