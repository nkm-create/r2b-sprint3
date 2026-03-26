# データ一覧

## 1. 概要

本ドキュメントは、学習塾時間割最適化システムで扱うデータ項目を整理したものである。

### 1.1 参照ドキュメント

| ドキュメント | 内容 |
|------------|------|
| ipo/ipo.md | IPO一覧 |
| requirements-v1/*.md | 各画面の要件定義書 |
| 共通機能.md | 共通機能要件 |

### 1.2 凡例

| 記号 | 意味 |
|------|------|
| PK | 主キー |
| FK | 外部キー |
| UK | ユニークキー |
| NN | NOT NULL |
| ○ | 必須項目 |
| △ | 条件付き必須 |
| - | 任意項目 |

---

## 2. エンティティ一覧

| # | エンティティ名 | 説明 | 対応画面 | バージョン管理 |
|---|--------------|------|---------|--------------|
| 1 | User | システムユーザー | P001, P012 | - |
| 2 | Area | エリア（複数教室のグループ） | P003, P013 | - |
| 3 | Classroom | 教室 | P004, P013 | - |
| 4 | UserClassroom | ユーザー-教室（中間テーブル） | P012, P013 | - |
| 5 | ClassroomSetting | 教室設定（時間枠、営業曜日、キャパシティ） | P004 | - |
| 6 | TimeSlot | 時間枠定義 | P004 | - |
| 7 | GoogleFormConnection | Google Form連携設定 | P004 | - |
| 8 | Teacher | 講師マスタ | P005 | **必須** |
| 9 | TeacherSubject | 講師-指導可能科目（中間テーブル） | P005 | - |
| 10 | TeacherGrade | 講師-指導可能学年（中間テーブル） | P005 | - |
| 11 | Student | 生徒マスタ | P006 | **必須** |
| 12 | StudentSubject | 生徒-科目別コマ数（中間テーブル） | P006 | - |
| 13 | Subject | 科目マスタ（システム固定） | 共通 | - |
| 14 | TeacherShiftPreference | 講師シフト希望 | P007 | 推奨 |
| 15 | StudentPreference | 生徒受講希望 | P007 | 推奨 |
| 16 | NGRelation | NG関係（講師-生徒） | P005, P006 | - |
| 17 | Term | ターム | P008, P011 | - |
| 18 | TermConstraint | ターム固有制約 | P008 | 推奨 |
| 19 | Policy | 全体ポリシー設定 | P008 | 推奨 |
| 20 | PolicyTemplate | ポリシーテンプレート | P008 | - |
| 21 | Schedule | 時間割 | P009 | **必須** |
| 22 | ScheduleSlot | 時間割コマ | P009 | - |
| 23 | Absence | 欠席記録 | P010 | - |
| 24 | Substitution | 振替記録 | P010 | - |
| 25 | Notification | 通知 | P002 | - |
| 26 | PasswordResetToken | パスワードリセットトークン | P001 | - |
| 27 | RefreshToken | リフレッシュトークン | P001 | - |
| 28 | UserArea | ユーザー-エリア（中間テーブル） | P003, P013 | - |
| 29 | AuditLog | 監査ログ | 共通 | - |

### 2.1 バージョン管理方針

| 区分 | 対象エンティティ | 説明 |
|------|-----------------|------|
| **必須** | Teacher, Student, Schedule | マスタ変更履歴の追跡が業務上必須。過去の時間割との関連付けを保証 |
| **推奨** | TeacherShiftPreference, StudentPreference, TermConstraint, Policy | ターム単位で管理されるため実質的にバージョン管理される。別途バージョン属性を追加する場合はterm_id + version_numberで管理可能 |

**備考**: 「推奨」エンティティはターム（term_id）に紐づくため、ターム単位でスナップショットが保持される。必要に応じてversion_number属性を追加して同一ターム内での変更追跡も可能。

---

## 3. エンティティ詳細

### 3.1 User（ユーザー）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| user_id | ユーザーID | UUID | PK | ○ | 自動生成 |
| email | メールアドレス | VARCHAR(255) | UK, NN | ○ | ログインID |
| password_hash | パスワードハッシュ | VARCHAR(255) | NN | ○ | bcrypt (cost=12) |
| name | 氏名 | VARCHAR(50) | NN | ○ | |
| role | 役割 | ENUM | NN | ○ | classroom_manager / area_manager / system_admin |
| status | ステータス | ENUM | NN | ○ | active / inactive |
| login_failed_count | ログイン失敗回数 | INTEGER | | - | デフォルト0 |
| locked_until | ロック解除日時 | TIMESTAMP | | - | 5回失敗で30分ロック |
| force_password_change | 初回パスワード変更要求 | BOOLEAN | | ○ | デフォルトtrue |
| last_login_at | 最終ログイン日時 | TIMESTAMP | | - | ログイン成功時に更新 |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |
| deleted_at | 削除日時 | TIMESTAMP | | - | 論理削除 |

### 3.2 Area（エリア）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| area_id | エリアID | UUID | PK | ○ | 自動生成 |
| area_name | エリア名 | VARCHAR(100) | NN | ○ | |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

### 3.3 Classroom（教室）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| classroom_id | 教室ID | UUID | PK | ○ | 自動生成 |
| area_id | エリアID | UUID | FK | ○ | Area.area_id |
| classroom_code | 教室コード | VARCHAR(20) | UK, NN | ○ | 英数字 |
| classroom_name | 教室名 | VARCHAR(100) | NN | ○ | |
| address | 住所 | VARCHAR(200) | | - | |
| phone_number | 電話番号 | VARCHAR(20) | | - | |
| status | ステータス | ENUM | NN | ○ | operating / closed |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |
| deleted_at | 削除日時 | TIMESTAMP | | - | 論理削除 |

### 3.4 UserClassroom（ユーザー-教室 中間テーブル）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| user_id | ユーザーID | UUID | FK, PK | ○ | User.user_id |
| classroom_id | 教室ID | UUID | FK, PK | ○ | Classroom.classroom_id |

### 3.5 ClassroomSetting（教室設定）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| classroom_id | 教室ID | UUID | FK, PK | ○ | Classroom.classroom_id |
| booth_count | ブース数 | INTEGER | NN | ○ | 同時実施可能コマ数 |
| weekday_slots | 平日時限数 | INTEGER | NN | ○ | デフォルト4 |
| saturday_slots | 土曜時限数 | INTEGER | NN | ○ | デフォルト5 |
| operating_days | 営業曜日 | VARCHAR(20) | NN | ○ | 例: "mon,tue,wed,thu,fri,sat" |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

### 3.6 TimeSlot（時間枠）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| time_slot_id | 時間枠ID | UUID | PK | ○ | 自動生成 |
| classroom_id | 教室ID | UUID | FK | ○ | Classroom.classroom_id |
| day_type | 曜日タイプ | ENUM | NN | ○ | weekday / saturday |
| slot_number | 時限番号 | INTEGER | NN | ○ | 1, 2, 3... |
| start_time | 開始時刻 | TIME | NN | ○ | |
| end_time | 終了時刻 | TIME | NN | ○ | |

### 3.7 GoogleFormConnection（Google Form連携設定）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| connection_id | 連携ID | UUID | PK | ○ | 自動生成 |
| classroom_id | 教室ID | UUID | FK | ○ | Classroom.classroom_id |
| data_type | データ種別 | ENUM | NN | ○ | teacher_shift / student_preference |
| spreadsheet_url | スプレッドシートURL | VARCHAR(500) | NN | ○ | |
| sheet_name | シート名 | VARCHAR(100) | NN | ○ | |
| column_mapping | カラムマッピング | JSONB | NN | ○ | |
| oauth_token_encrypted | OAuthトークン（暗号化） | TEXT | NN | ○ | |
| last_sync_at | 最終同期日時 | TIMESTAMP | | - | |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

### 3.8 Teacher（講師マスタ）

**バージョン管理対象**

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| teacher_version_id | 講師バージョンID | UUID | PK | ○ | 自動生成 |
| teacher_id | 講師ID | VARCHAR(20) | NN | ○ | 不変ID（例: T001）。classroom_id内でユニーク |
| classroom_id | 教室ID | UUID | FK | ○ | Classroom.classroom_id |
| version_number | バージョン番号 | INTEGER | NN | ○ | 1から開始 |
| is_current | 現在バージョン | BOOLEAN | NN | ○ | 最新のみtrue |
| valid_from | 有効開始日時 | TIMESTAMP | NN | ○ | |
| valid_to | 有効終了日時 | TIMESTAMP | | - | 現行はnull |
| change_reason_type | 変更理由種別 | ENUM | NN | ○ | SCHEDULE_CHANGE / SUBJECT_CHANGE / GRADE_CHANGE / NG_CHANGE / STATUS_CHANGE / INITIAL / OTHER |
| change_reason_note | 変更理由補足 | VARCHAR(500) | | △ | OTHERの場合は必須 |
| name | 氏名 | VARCHAR(50) | NN | ○ | |
| gender | 性別 | ENUM | NN | ○ | male / female |
| min_slots_per_week | 最小コマ/週 | INTEGER | NN | ○ | 1以上 |
| max_slots_per_week | 最大コマ/週 | INTEGER | NN | ○ | 最小コマ以上 |
| max_consecutive_slots | 最大連続コマ | INTEGER | NN | ○ | 1〜4 |
| has_jhs_exam_experience | 中学受験経験 | BOOLEAN | | - | デフォルトfalse |
| has_hs_exam_experience | 高校受験経験 | BOOLEAN | | - | デフォルトfalse |
| university_rank | 大学ランク | ENUM | | - | A / B / C / null |
| status | ステータス | ENUM | NN | ○ | active / inactive |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |
| deleted_at | 削除日時 | TIMESTAMP | | - | 論理削除 |

**UK**: (teacher_id, classroom_id) - 教室内で講師IDはユニーク

### 3.9 TeacherSubject（講師-指導可能科目）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| teacher_version_id | 講師バージョンID | UUID | FK, PK | ○ | Teacher.teacher_version_id |
| subject_id | 科目ID | VARCHAR(20) | FK, PK | ○ | Subject.subject_id |

### 3.10 TeacherGrade（講師-指導可能学年）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| teacher_version_id | 講師バージョンID | UUID | FK, PK | ○ | Teacher.teacher_version_id |
| grade | 学年 | ENUM | PK | ○ | ele1〜ele6, jhs1〜jhs3, hs1〜hs3 |

### 3.11 Student（生徒マスタ）

**バージョン管理対象**

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| student_version_id | 生徒バージョンID | UUID | PK | ○ | 自動生成 |
| student_id | 生徒ID | VARCHAR(20) | NN | ○ | 不変ID（例: S001）。classroom_id内でユニーク |
| classroom_id | 教室ID | UUID | FK | ○ | Classroom.classroom_id |
| version_number | バージョン番号 | INTEGER | NN | ○ | 1から開始 |
| is_current | 現在バージョン | BOOLEAN | NN | ○ | 最新のみtrue |
| valid_from | 有効開始日時 | TIMESTAMP | NN | ○ | |
| valid_to | 有効終了日時 | TIMESTAMP | | - | 現行はnull |
| change_reason_type | 変更理由種別 | ENUM | NN | ○ | COURSE_CHANGE / GRADE_UP / PREFERENCE_CHANGE / GOAL_CHANGE / STATUS_CHANGE / INITIAL / OTHER |
| change_reason_note | 変更理由補足 | VARCHAR(500) | | △ | OTHERの場合は必須 |
| name | 氏名 | VARCHAR(50) | NN | ○ | |
| grade | 学年 | ENUM | NN | ○ | ele1〜ele6, jhs1〜jhs3, hs1〜hs3 |
| max_consecutive_slots | 最大連続コマ | INTEGER | NN | ○ | 1〜4 |
| preferred_teacher_id | 希望講師ID | VARCHAR(20) | FK | - | Teacher.teacher_id |
| preferred_teacher_gender | 講師希望性別 | preferred_gender | | - | male / female / any |
| aspiration_level | 志望レベル | ENUM | | - | A / B / C |
| enrollment_purpose | 通塾目的 | ENUM | | - | hs_exam / jhs_exam / internal / remedial / other |
| status | ステータス | ENUM | NN | ○ | active / inactive |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |
| deleted_at | 削除日時 | TIMESTAMP | | - | 論理削除 |

**UK**: (student_id, classroom_id) - 教室内で生徒IDはユニーク

### 3.12 StudentSubject（生徒-科目別コマ数）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| student_version_id | 生徒バージョンID | UUID | FK, PK | ○ | Student.student_version_id |
| subject_id | 科目ID | VARCHAR(20) | FK, PK | ○ | Subject.subject_id |
| slots_per_week | 週あたりコマ数 | INTEGER | NN | ○ | 1以上 |

### 3.13 Subject（科目マスタ）

**システム固定（管理画面からの変更不可）**

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| subject_id | 科目ID | VARCHAR(20) | PK | ○ | 例: ELE_MATH_PUB |
| subject_name | 科目名 | VARCHAR(50) | NN | ○ | 例: 公立算数 |
| grade_category | 対象学年カテゴリ | ENUM | NN | ○ | elementary / junior_high / high_school |
| subject_category | 分類 | ENUM | NN | ○ | english / math / japanese / science / social |
| is_jhs_exam_target | 中受対象 | BOOLEAN | NN | ○ | デフォルトfalse |
| is_hs_exam_target | 高受対象 | BOOLEAN | NN | ○ | デフォルトfalse |

### 3.14 NGRelation（NG関係）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| ng_relation_id | NG関係ID | UUID | PK | ○ | 自動生成 |
| teacher_id | 講師ID | VARCHAR(20) | FK | ○ | Teacher.teacher_id |
| student_id | 生徒ID | VARCHAR(20) | FK | ○ | Student.student_id |
| created_by | 設定元 | ENUM | NN | ○ | teacher / student |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |

**UK**: (teacher_id, student_id)

### 3.15 TeacherShiftPreference（講師シフト希望）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| preference_id | 希望ID | UUID | PK | ○ | 自動生成 |
| teacher_id | 講師ID | VARCHAR(20) | FK | ○ | Teacher.teacher_id |
| classroom_id | 教室ID | UUID | FK | ○ | Classroom.classroom_id |
| term_id | タームID | UUID | FK | ○ | Term.term_id |
| day_of_week | 曜日 | ENUM | NN | ○ | mon / tue / wed / thu / fri / sat |
| slot_number | 時限番号 | INTEGER | NN | ○ | |
| preference_value | 希望値 | ENUM | NN | ○ | available (○) / unavailable (×) |
| is_manually_edited | 手動編集済み | BOOLEAN | NN | ○ | デフォルトfalse |
| synced_at | 同期日時 | TIMESTAMP | | - | Google Form同期時 |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

**UK**: (teacher_id, term_id, day_of_week, slot_number)

### 3.16 StudentPreference（生徒受講希望）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| preference_id | 希望ID | UUID | PK | ○ | 自動生成 |
| student_id | 生徒ID | VARCHAR(20) | FK | ○ | Student.student_id |
| classroom_id | 教室ID | UUID | FK | ○ | Classroom.classroom_id |
| term_id | タームID | UUID | FK | ○ | Term.term_id |
| day_of_week | 曜日 | ENUM | NN | ○ | mon / tue / wed / thu / fri / sat |
| slot_number | 時限番号 | INTEGER | NN | ○ | |
| preference_value | 希望値 | ENUM | NN | ○ | preferred (○) / unavailable (×) / possible (△) |
| is_manually_edited | 手動編集済み | BOOLEAN | NN | ○ | デフォルトfalse |
| synced_at | 同期日時 | TIMESTAMP | | - | Google Form同期時 |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

**UK**: (student_id, term_id, day_of_week, slot_number)

### 3.17 Term（ターム）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| term_id | タームID | UUID | PK | ○ | 自動生成 |
| classroom_id | 教室ID | UUID | FK | ○ | Classroom.classroom_id |
| term_name | ターム名 | VARCHAR(50) | NN | ○ | 例: 2025年4月 |
| start_date | 開始日 | DATE | NN | ○ | |
| end_date | 終了日 | DATE | NN | ○ | |
| status | ステータス | ENUM | NN | ○ | creating / confirmed / archived |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |
| deleted_at | 削除日時 | TIMESTAMP | | - | 論理削除 |

### 3.18 TermConstraint（ターム固有制約）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| constraint_id | 制約ID | UUID | PK | ○ | 自動生成 |
| term_id | タームID | UUID | FK | ○ | Term.term_id |
| target_type | 対象種別 | ENUM | NN | ○ | teacher / student / classroom |
| target_id | 対象ID | VARCHAR(50) | NN | ○ | Teacher.teacher_id / Student.student_id / Classroom.classroom_id |
| constraint_type | 制約種別 | ENUM | NN | ○ | max_slots / min_slots / max_consecutive / subject_limit / day_limit / preferred_teacher / ng_teacher / gender_preference / booth_capacity |
| constraint_value | 制約値 | JSONB | NN | ○ | 制約種別に応じた値 |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

**備考**: target_type=classroom の場合、target_idにはclassroom_id（UUID）を格納。constraint_typeはbooth_capacityのみ有効。

### 3.19 Policy（全体ポリシー設定）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| policy_id | ポリシーID | UUID | PK | ○ | 自動生成 |
| term_id | タームID | UUID | FK | ○ | Term.term_id |
| policy_type | ポリシー種別 | ENUM | NN | ○ | P001〜P006 |
| is_enabled | 有効/無効 | BOOLEAN | NN | ○ | デフォルトtrue |
| parameters | パラメータ | JSONB | NN | ○ | ポリシー種別に応じた設定 |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

### 3.20 PolicyTemplate（ポリシーテンプレート）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| template_id | テンプレートID | UUID | PK | ○ | 自動生成 |
| classroom_id | 教室ID | UUID | FK | ○ | Classroom.classroom_id |
| template_name | テンプレート名 | VARCHAR(100) | NN | ○ | |
| policies | ポリシー設定 | JSONB | NN | ○ | 全ポリシーの設定値 |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

### 3.21 Schedule（時間割）

**バージョン管理対象**

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| schedule_id | 時間割ID | UUID | PK | ○ | 自動生成 |
| term_id | タームID | UUID | FK | ○ | Term.term_id |
| version | バージョン番号 | INTEGER | NN | ○ | 1から開始 |
| status | ステータス | ENUM | NN | ○ | draft / confirmed / archived |
| parent_version_id | 派生元バージョンID | UUID | FK | - | Schedule.schedule_id |
| master_snapshot | マスタスナップショット | JSONB | NN | ○ | 作成時のマスタバージョン参照 |
| generation_config | 生成設定 | JSONB | | - | 再現性のための設定保存 |
| fulfillment_rate | 充足率 | DECIMAL(5,2) | | - | 計算結果をキャッシュ |
| soft_constraint_rate | ソフト制約達成率 | DECIMAL(5,2) | | - | 計算結果をキャッシュ |
| confirmed_at | 確定日時 | TIMESTAMP | | - | 確定時に設定 |
| confirmed_by | 確定者ID | UUID | FK | - | User.user_id |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

### 3.22 ScheduleSlot（時間割コマ）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| slot_id | コマID | UUID | PK | ○ | 自動生成 |
| schedule_id | 時間割ID | UUID | FK | ○ | Schedule.schedule_id |
| day_of_week | 曜日 | ENUM | NN | ○ | mon / tue / wed / thu / fri / sat |
| slot_number | 時限番号 | INTEGER | NN | ○ | |
| booth_number | ブース番号 | INTEGER | NN | ○ | |
| teacher_id | 講師ID | VARCHAR(20) | FK | ○ | Teacher.teacher_id |
| student1_id | 生徒1 ID | VARCHAR(20) | FK | ○ | Student.student_id |
| student2_id | 生徒2 ID | VARCHAR(20) | FK | - | Student.student_id（1対2の場合） |
| subject_id | 科目ID | VARCHAR(20) | FK | ○ | Subject.subject_id |
| slot_type | コマ種別 | ENUM | NN | ○ | one_to_two / one_to_one |
| status | ステータス | ENUM | NN | ○ | scheduled / absent / substituted |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

### 3.23 Absence（欠席記録）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| absence_id | 欠席ID | UUID | PK | ○ | 自動生成 |
| slot_id | コマID | UUID | FK | ○ | ScheduleSlot.slot_id |
| absent_type | 欠席者種別 | ENUM | NN | ○ | teacher / student |
| absent_person_id | 欠席者ID | VARCHAR(20) | NN | ○ | Teacher.teacher_id / Student.student_id |
| absence_reason | 欠席理由 | VARCHAR(200) | | - | |
| needs_substitution | 振替希望有無 | BOOLEAN | NN | ○ | デフォルトtrue |
| substitution_status | 振替ステータス | ENUM | NN | ○ | pending / completed / cancelled |
| registered_by | 登録者ID | UUID | FK | ○ | User.user_id |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |
| updated_at | 更新日時 | TIMESTAMP | NN | ○ | |

### 3.24 Substitution（振替記録）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| substitution_id | 振替ID | UUID | PK | ○ | 自動生成 |
| absence_id | 欠席ID | UUID | FK | ○ | Absence.absence_id |
| original_slot_id | 元コマID | UUID | FK | ○ | ScheduleSlot.slot_id |
| new_slot_id | 振替先コマID | UUID | FK | ○ | ScheduleSlot.slot_id |
| substitution_type | 振替種別 | ENUM | NN | ○ | reschedule / substitute |
| priority_score | 優先度スコア | INTEGER | | - | 候補選択時の計算値 |
| confirmed_by | 確定者ID | UUID | FK | ○ | User.user_id |
| confirmed_at | 確定日時 | TIMESTAMP | NN | ○ | |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |

### 3.25 Notification（通知）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| notification_id | 通知ID | UUID | PK | ○ | 自動生成 |
| user_id | ユーザーID | UUID | FK | ○ | User.user_id |
| classroom_id | 教室ID | UUID | FK | - | Classroom.classroom_id |
| notification_type | 通知種別 | ENUM | NN | ○ | fulfillment_low / unanswered_preference / term_deadline / etc. |
| severity | 重要度 | ENUM | NN | ○ | critical / warning / info |
| title | タイトル | VARCHAR(100) | NN | ○ | |
| message | メッセージ | VARCHAR(500) | NN | ○ | |
| link_url | リンクURL | VARCHAR(500) | | - | |
| is_read | 既読フラグ | BOOLEAN | NN | ○ | デフォルトfalse |
| read_at | 既読日時 | TIMESTAMP | | - | |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |

### 3.26 PasswordResetToken（パスワードリセットトークン）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| token_id | トークンID | UUID | PK | ○ | 自動生成 |
| user_id | ユーザーID | UUID | FK | ○ | User.user_id |
| token_hash | トークンハッシュ | VARCHAR(255) | NN | ○ | |
| expires_at | 有効期限 | TIMESTAMP | NN | ○ | 発行から24時間 |
| used_at | 使用日時 | TIMESTAMP | | - | 使用済みの場合 |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |

### 3.27 RefreshToken（リフレッシュトークン）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| refresh_token_id | リフレッシュトークンID | UUID | PK | ○ | 自動生成 |
| user_id | ユーザーID | UUID | FK | ○ | User.user_id |
| token_hash | トークンハッシュ | VARCHAR(255) | NN | ○ | SHA-256 |
| expires_at | 有効期限 | TIMESTAMP | NN | ○ | 発行から7日間 |
| device_info | デバイス情報 | VARCHAR(500) | | - | User-Agent等 |
| ip_address | IPアドレス | VARCHAR(45) | | - | 発行時のIP |
| is_revoked | 失効フラグ | BOOLEAN | NN | ○ | デフォルトfalse |
| revoked_at | 失効日時 | TIMESTAMP | | - | ログアウト時等 |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |

### 3.28 UserArea（ユーザー-エリア中間テーブル）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| user_id | ユーザーID | UUID | FK, PK | ○ | User.user_id |
| area_id | エリアID | UUID | FK, PK | ○ | Area.area_id |

**備考**: エリアマネジャー（area_manager）がアクセス可能なエリアを管理

### 3.29 AuditLog（監査ログ）

| 属性名 | 日本語名 | データ型 | 制約 | 必須 | 説明 |
|--------|---------|---------|------|------|------|
| log_id | ログID | UUID | PK | ○ | 自動生成 |
| user_id | ユーザーID | UUID | FK | - | User.user_id（システム操作の場合null） |
| action | 操作 | VARCHAR(50) | NN | ○ | CREATE / UPDATE / DELETE / LOGIN / etc. |
| entity_type | エンティティ種別 | VARCHAR(50) | NN | ○ | Teacher / Student / Schedule / etc. |
| entity_id | エンティティID | VARCHAR(50) | | - | |
| old_value | 変更前値 | JSONB | | - | |
| new_value | 変更後値 | JSONB | | - | |
| ip_address | IPアドレス | VARCHAR(45) | | - | |
| user_agent | ユーザーエージェント | VARCHAR(500) | | - | |
| created_at | 作成日時 | TIMESTAMP | NN | ○ | |

---

## 4. ENUM定義

**ENUM値の表記規約**:
- DB格納値は英語小文字（例: `male`, `female`, `active`）
- 日本語表示はアプリケーション層でマッピング（例: `male` → "男", `female` → "女"）
- 学年ENUMは略記形式（例: `ele1` = 小学1年, `jhs1` = 中学1年, `hs1` = 高校1年）

### 4.1 ユーザー関連

| ENUM名 | 値 | 説明 |
|--------|-----|------|
| UserRole | classroom_manager | 教室長 |
| | area_manager | エリアマネジャー |
| | system_admin | システム管理者 |
| UserStatus | active | 有効 |
| | inactive | 無効 |

### 4.2 教室関連

| ENUM名 | 値 | 説明 |
|--------|-----|------|
| ClassroomStatus | operating | 運営中 |
| | closed | 閉鎖 |
| DayType | weekday | 平日 |
| | saturday | 土曜 |
| DayOfWeek | mon, tue, wed, thu, fri, sat | 曜日 |
| GoogleFormDataType | teacher_shift | 講師シフト希望 |
| | student_preference | 生徒受講希望 |

### 4.3 講師・生徒関連

| ENUM名 | 値 | 説明 |
|--------|-----|------|
| Gender | male | 男 |
| | female | 女 |
| PreferredGender | male | 男性講師希望 |
| | female | 女性講師希望 |
| | any | 指定なし |
| Grade | ele1〜ele6 | 小学1年〜6年 |
| | jhs1〜jhs3 | 中学1年〜3年 |
| | hs1〜hs3 | 高校1年〜3年 |
| UniversityRank | A, B, C | 大学ランク |
| AspirationLevel | A, B, C | 志望レベル |
| EnrollmentPurpose | hs_exam | 高校受験 |
| | jhs_exam | 中学受験 |
| | internal | 内部進学 |
| | remedial | 補習 |
| | other | その他 |
| TeacherChangeReason | SCHEDULE_CHANGE, SUBJECT_CHANGE, GRADE_CHANGE, NG_CHANGE, STATUS_CHANGE, INITIAL, OTHER | 講師変更理由 |
| StudentChangeReason | COURSE_CHANGE, GRADE_UP, PREFERENCE_CHANGE, GOAL_CHANGE, STATUS_CHANGE, INITIAL, OTHER | 生徒変更理由 |

### 4.4 希望関連

| ENUM名 | 値 | 説明 |
|--------|-----|------|
| TeacherPreferenceValue | available | ○（勤務可能） |
| | unavailable | ×（勤務不可） |
| StudentPreferenceValue | preferred | ○（受講希望） |
| | unavailable | ×（受講不可） |
| | possible | △（できれば可） |

### 4.5 ターム・時間割関連

| ENUM名 | 値 | 説明 |
|--------|-----|------|
| TermStatus | creating | 作成中 |
| | confirmed | 確定 |
| | archived | アーカイブ |
| ScheduleStatus | draft | 下書き |
| | confirmed | 確定 |
| | archived | アーカイブ |
| SlotType | one_to_two | 1対2 |
| | one_to_one | 1対1 |
| SlotStatus | scheduled | 予定 |
| | absent | 欠席 |
| | substituted | 振替済み |

### 4.6 欠席・振替関連

| ENUM名 | 値 | 説明 |
|--------|-----|------|
| AbsentType | teacher | 講師 |
| | student | 生徒 |
| SubstitutionStatus | pending | 振替待ち |
| | completed | 振替済み |
| | cancelled | キャンセル |
| SubstitutionType | reschedule | 振替（同講師） |
| | substitute | 代講（別講師） |

### 4.7 ポリシー関連

| ENUM名 | 値 | 説明 |
|--------|-----|------|
| PolicyType | P001 | 志望レベル→大学ランクマッピング |
| | P002 | 中受経験優先 |
| | P003 | 高受経験優先 |
| | P004 | 同一科目ペアリング |
| | P005 | 充足率目標 |
| | P006 | 時間帯優先 |

### 4.8 制約関連

| ENUM名 | 値 | 説明 |
|--------|-----|------|
| ConstraintTargetType | teacher | 講師 |
| | student | 生徒 |
| | classroom | 教室 |
| ConstraintType | max_slots | 最大コマ数 |
| | min_slots | 最小コマ数 |
| | max_consecutive | 最大連続コマ |
| | subject_limit | 科目限定 |
| | day_limit | 曜日限定 |
| | preferred_teacher | 講師希望 |
| | ng_teacher | 講師NG |
| | gender_preference | 性別希望 |
| | booth_capacity | ブースキャパシティ |

### 4.9 通知関連

| ENUM名 | 値 | 説明 |
|--------|-----|------|
| NotificationType | fulfillment_low | 充足率低下 |
| | unanswered_preference | 未回答希望データ |
| | term_deadline | ターム確定期限 |
| | schedule_conflict | 時間割競合 |
| Severity | critical | 危険 |
| | warning | 警告 |
| | info | 情報 |

---

## 5. 科目マスタ（システム固定）

| subject_id | subject_name | grade_category | subject_category | is_jhs_exam_target | is_hs_exam_target |
|------------|--------------|----------------|------------------|--------------------|--------------------|
| ELE_ENG | 小学英語 | elementary | english | false | false |
| ELE_MATH_PUB | 公立算数 | elementary | math | false | false |
| ELE_MATH_JKN | 中受算数 | elementary | math | **true** | false |
| ELE_JPN | 小学国語 | elementary | japanese | false | false |
| ELE_ESSAY | 小論 | elementary | japanese | false | false |
| ELE_SCI_PUB | 公立理科 | elementary | science | false | false |
| ELE_SCI_JKN | 中受理科 | elementary | science | **true** | false |
| ELE_SOC_PUB | 公立社会 | elementary | social | false | false |
| ELE_SOC_JKN | 中受社会 | elementary | social | **true** | false |
| JHS_ENG | 中学英語 | junior_high | english | false | **true** |
| JHS_MATH_PUB | 公立数学 | junior_high | math | false | **true** |
| JHS_MATH_PRI | 私立数学 | junior_high | math | false | **true** |
| JHS_JPN | 中学国語 | junior_high | japanese | false | **true** |
| JHS_SCI | 中学理科 | junior_high | science | false | **true** |
| JHS_SOC | 中学社会 | junior_high | social | false | **true** |
| HS_ENG_12 | 高校12英語 | high_school | english | false | false |
| HS_ENG_3 | 高3英語 | high_school | english | false | false |
| HS_JPN | 高校国語 | high_school | japanese | false | false |
| HS_MATH_1A | 数1A | high_school | math | false | false |
| HS_MATH_2B | 数ⅡB | high_school | math | false | false |
| HS_MATH_3 | 数Ⅲ | high_school | math | false | false |
| HS_BIO | 生物 | high_school | science | false | false |
| HS_CHEM | 化学 | high_school | science | false | false |
| HS_PHYS | 物理 | high_school | science | false | false |
| HS_WHIS | 世界史 | high_school | social | false | false |
| HS_JHIS | 日本史 | high_school | social | false | false |
| HS_GEO | 地理 | high_school | social | false | false |

---

## 6. データ関連図

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              エリア・教室                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Area ◄──────┬───────────────── Classroom ──────────► ClassroomSetting     │
│              │                    │                          │              │
│              │                    ├──────────────────────────┼──► TimeSlot │
│              │                    │                          │              │
│              │                    └──► GoogleFormConnection  │              │
└──────────────┼──────────────────────────────────────────────────────────────┘
               │
┌──────────────┼──────────────────────────────────────────────────────────────┐
│              ▼              ユーザー・認証                                   │
│           User ◄────────────────────────────────────────────────────────────┤
│              │                                                              │
│              ├──► UserClassroom ◄── Classroom                              │
│              │                                                              │
│              ├──► UserArea ◄── Area                                         │
│              │                                                              │
│              ├──► PasswordResetToken                                        │
│              │                                                              │
│              └──► RefreshToken                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           講師・生徒マスタ                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Teacher ───┬──► TeacherSubject ◄── Subject ──► StudentSubject ◄── Student │
│  (versioned)│                                                    (versioned)│
│             └──► TeacherGrade                                               │
│                                                                              │
│  Teacher ◄─────────────── NGRelation ─────────────► Student                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              希望データ                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Teacher ──► TeacherShiftPreference ◄── Term ──► StudentPreference ◄── Student │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           ターム・制約・ポリシー                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Classroom ──► Term ──┬──► TermConstraint                                   │
│                       │                                                      │
│                       ├──► Policy                                            │
│                       │                                                      │
│                       └──► Schedule (versioned)                              │
│                                                                              │
│  Classroom ──► PolicyTemplate                                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              時間割・コマ                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Schedule ──► ScheduleSlot ◄─┬── Teacher                                    │
│                              ├── Student (student1)                         │
│                              ├── Student (student2)                         │
│                              └── Subject                                    │
│                                                                              │
│  ScheduleSlot ──► Absence ──► Substitution                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              通知・監査                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  User ──► Notification                                                       │
│                                                                              │
│  User ──► AuditLog                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 更新履歴

| 日付 | 更新内容 |
|------|---------|
| 2026-03-22 | 初版作成（27エンティティ、ENUM定義、科目マスタ、データ関連図） |
| 2026-03-23 | requirements-v1/IPO一覧との整合性検証に基づく修正: RefreshToken/UserAreaエンティティ追加、Teacher/StudentのUK制約明記、GoogleFormDataType ENUM追加 |
| 2026-03-24 | DB設計書との整合性検証に基づく修正: UserClassroomをエンティティ一覧に追加（29件に修正）、ConstraintTargetTypeにclassroom追加、ConstraintTypeにbooth_capacity追加、locked_until/expires_at/preferred_teacher_genderの非機能要件整合 |
