"""科目マスタ初期データ投入スクリプト"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.database import AsyncSessionLocal
from app.models import Subject, GradeCategory, SubjectCategory


INITIAL_SUBJECTS = [
    # 小学生
    {"subject_id": "ELE_ENG", "subject_name": "小学英語", "grade_category": GradeCategory.ELEMENTARY, "subject_category": SubjectCategory.ENGLISH, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "ELE_MATH_PUB", "subject_name": "公立算数", "grade_category": GradeCategory.ELEMENTARY, "subject_category": SubjectCategory.MATH, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "ELE_MATH_JKN", "subject_name": "中受算数", "grade_category": GradeCategory.ELEMENTARY, "subject_category": SubjectCategory.MATH, "is_jhs_exam_target": True, "is_hs_exam_target": False},
    {"subject_id": "ELE_JPN", "subject_name": "小学国語", "grade_category": GradeCategory.ELEMENTARY, "subject_category": SubjectCategory.JAPANESE, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "ELE_ESSAY", "subject_name": "小論", "grade_category": GradeCategory.ELEMENTARY, "subject_category": SubjectCategory.JAPANESE, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "ELE_SCI_PUB", "subject_name": "公立理科", "grade_category": GradeCategory.ELEMENTARY, "subject_category": SubjectCategory.SCIENCE, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "ELE_SCI_JKN", "subject_name": "中受理科", "grade_category": GradeCategory.ELEMENTARY, "subject_category": SubjectCategory.SCIENCE, "is_jhs_exam_target": True, "is_hs_exam_target": False},
    {"subject_id": "ELE_SOC_PUB", "subject_name": "公立社会", "grade_category": GradeCategory.ELEMENTARY, "subject_category": SubjectCategory.SOCIAL, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "ELE_SOC_JKN", "subject_name": "中受社会", "grade_category": GradeCategory.ELEMENTARY, "subject_category": SubjectCategory.SOCIAL, "is_jhs_exam_target": True, "is_hs_exam_target": False},
    # 中学生
    {"subject_id": "JHS_ENG", "subject_name": "中学英語", "grade_category": GradeCategory.JUNIOR_HIGH, "subject_category": SubjectCategory.ENGLISH, "is_jhs_exam_target": False, "is_hs_exam_target": True},
    {"subject_id": "JHS_MATH_PUB", "subject_name": "公立数学", "grade_category": GradeCategory.JUNIOR_HIGH, "subject_category": SubjectCategory.MATH, "is_jhs_exam_target": False, "is_hs_exam_target": True},
    {"subject_id": "JHS_MATH_PRI", "subject_name": "私立数学", "grade_category": GradeCategory.JUNIOR_HIGH, "subject_category": SubjectCategory.MATH, "is_jhs_exam_target": False, "is_hs_exam_target": True},
    {"subject_id": "JHS_JPN", "subject_name": "中学国語", "grade_category": GradeCategory.JUNIOR_HIGH, "subject_category": SubjectCategory.JAPANESE, "is_jhs_exam_target": False, "is_hs_exam_target": True},
    {"subject_id": "JHS_SCI", "subject_name": "中学理科", "grade_category": GradeCategory.JUNIOR_HIGH, "subject_category": SubjectCategory.SCIENCE, "is_jhs_exam_target": False, "is_hs_exam_target": True},
    {"subject_id": "JHS_SOC", "subject_name": "中学社会", "grade_category": GradeCategory.JUNIOR_HIGH, "subject_category": SubjectCategory.SOCIAL, "is_jhs_exam_target": False, "is_hs_exam_target": True},
    # 高校生
    {"subject_id": "HS_ENG_12", "subject_name": "高校12英語", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.ENGLISH, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_ENG_3", "subject_name": "高3英語", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.ENGLISH, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_JPN", "subject_name": "高校国語", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.JAPANESE, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_MATH_1A", "subject_name": "数1A", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.MATH, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_MATH_2B", "subject_name": "数ⅡB", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.MATH, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_MATH_3", "subject_name": "数Ⅲ", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.MATH, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_BIO", "subject_name": "生物", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.SCIENCE, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_CHEM", "subject_name": "化学", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.SCIENCE, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_PHYS", "subject_name": "物理", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.SCIENCE, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_WHIS", "subject_name": "世界史", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.SOCIAL, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_JHIS", "subject_name": "日本史", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.SOCIAL, "is_jhs_exam_target": False, "is_hs_exam_target": False},
    {"subject_id": "HS_GEO", "subject_name": "地理", "grade_category": GradeCategory.HIGH_SCHOOL, "subject_category": SubjectCategory.SOCIAL, "is_jhs_exam_target": False, "is_hs_exam_target": False},
]


async def seed_subjects():
    """科目マスタを初期データで投入"""
    async with AsyncSessionLocal() as session:
        # 既存データ確認
        result = await session.execute(select(Subject).limit(1))
        if result.scalar_one_or_none():
            print("科目マスタは既に存在します。スキップします。")
            return

        # データ投入
        for subject_data in INITIAL_SUBJECTS:
            subject = Subject(**subject_data)
            session.add(subject)

        await session.commit()
        print(f"{len(INITIAL_SUBJECTS)}件の科目マスタを投入しました。")


if __name__ == "__main__":
    asyncio.run(seed_subjects())
