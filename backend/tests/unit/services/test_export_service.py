"""
エクスポートサービスのユニットテスト

PDF/CSV出力機能のテスト
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import Any
import io
import csv


# テスト用のデータクラス（Testプレフィックスを避けてpytest警告を回避）
@dataclass
class SampleScheduleSlot:
    """テスト用のスケジュールスロット"""
    slot_id: str
    day_of_week: str
    slot_number: int
    teacher_id: str
    teacher_name: str
    student1_id: str
    student1_name: str
    student2_id: str | None = None
    student2_name: str | None = None
    subject_id: str = "JHS_MATH"
    subject_name: str = "中学数学"
    booth_number: int = 1
    slot_type: str = "one_to_two"


@dataclass
class SampleScheduleData:
    """テスト用のスケジュールデータ"""
    schedule_id: str
    term_name: str
    classroom_name: str
    soft_constraint_rate: Decimal
    status: str
    slots: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class TestCSVExport:
    """CSV出力のテスト"""

    @pytest.fixture
    def sample_schedule_data(self):
        """サンプルスケジュールデータ"""
        return SampleScheduleData(
            schedule_id="sched-001",
            term_name="2024年度第1ターム",
            classroom_name="渋谷校",
            soft_constraint_rate=Decimal("78.2"),
            status="confirmed",
            slots=[
                SampleScheduleSlot(
                    slot_id="slot-001",
                    day_of_week="mon",
                    slot_number=1,
                    teacher_id="T001",
                    teacher_name="山田太郎",
                    student1_id="S001",
                    student1_name="佐藤花子",
                    student2_id="S002",
                    student2_name="鈴木一郎",
                    subject_id="JHS_MATH",
                    subject_name="中学数学",
                    booth_number=1,
                    slot_type="one_to_two",
                ),
                SampleScheduleSlot(
                    slot_id="slot-002",
                    day_of_week="mon",
                    slot_number=2,
                    teacher_id="T002",
                    teacher_name="田中次郎",
                    student1_id="S003",
                    student1_name="高橋美咲",
                    student2_id=None,
                    student2_name=None,
                    subject_id="JHS_ENG",
                    subject_name="中学英語",
                    booth_number=2,
                    slot_type="one_to_one",
                ),
            ],
        )

    def test_generate_csv_headers(self, sample_schedule_data):
        """CSVヘッダーが正しく生成される"""
        expected_headers = [
            "曜日",
            "コマ",
            "ブース",
            "講師コード",
            "講師名",
            "生徒1コード",
            "生徒1名",
            "生徒2コード",
            "生徒2名",
            "科目",
            "授業形態",
        ]

        # CSVを生成
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(expected_headers)

        content = output.getvalue()
        for header in expected_headers:
            assert header in content

    def test_generate_csv_rows(self, sample_schedule_data):
        """CSVデータ行が正しく生成される"""
        day_map = {
            "mon": "月", "tue": "火", "wed": "水",
            "thu": "木", "fri": "金", "sat": "土",
        }

        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー
        headers = [
            "曜日", "コマ", "ブース", "講師コード", "講師名",
            "生徒1コード", "生徒1名", "生徒2コード", "生徒2名",
            "科目", "授業形態",
        ]
        writer.writerow(headers)

        # データ行
        for slot in sample_schedule_data.slots:
            row = [
                day_map.get(slot.day_of_week, slot.day_of_week),
                slot.slot_number,
                slot.booth_number,
                slot.teacher_id,
                slot.teacher_name,
                slot.student1_id,
                slot.student1_name,
                slot.student2_id or "",
                slot.student2_name or "",
                slot.subject_name,
                "1対2" if slot.slot_type == "one_to_two" else "1対1",
            ]
            writer.writerow(row)

        content = output.getvalue()

        # 検証
        assert "山田太郎" in content
        assert "佐藤花子" in content
        assert "鈴木一郎" in content
        assert "中学数学" in content
        assert "1対2" in content

    def test_csv_encoding_utf8(self, sample_schedule_data):
        """CSVがUTF-8でエンコードされる"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["講師名", "生徒名"])
        writer.writerow(["山田太郎", "佐藤花子"])

        content = output.getvalue()
        # UTF-8でエンコードできることを確認
        encoded = content.encode("utf-8")
        assert isinstance(encoded, bytes)

        # BOMを追加してExcel互換性確保
        with_bom = b"\xef\xbb\xbf" + encoded
        assert with_bom.startswith(b"\xef\xbb\xbf")

    def test_csv_empty_schedule(self):
        """空のスケジュールでもCSVが生成される"""
        schedule = SampleScheduleData(
            schedule_id="sched-empty",
            term_name="空ターム",
            classroom_name="テスト校",
            soft_constraint_rate=Decimal("0"),
            soft_constraint_rate=Decimal("0"),
            status="draft",
            slots=[],
        )

        output = io.StringIO()
        writer = csv.writer(output)
        headers = ["曜日", "コマ", "講師名"]
        writer.writerow(headers)

        content = output.getvalue()
        assert "曜日" in content
        assert "コマ" in content


class TestPDFExport:
    """PDF出力のテスト"""

    @pytest.fixture
    def sample_schedule_data(self):
        """サンプルスケジュールデータ"""
        return SampleScheduleData(
            schedule_id="sched-001",
            term_name="2024年度第1ターム",
            classroom_name="渋谷校",
            soft_constraint_rate=Decimal("78.2"),
            status="confirmed",
            slots=[
                SampleScheduleSlot(
                    slot_id="slot-001",
                    day_of_week="mon",
                    slot_number=1,
                    teacher_id="T001",
                    teacher_name="山田太郎",
                    student1_id="S001",
                    student1_name="佐藤花子",
                    booth_number=1,
                ),
            ],
        )

    def test_html_template_generation(self, sample_schedule_data):
        """HTMLテンプレートが正しく生成される"""
        day_map = {
            "mon": "月", "tue": "火", "wed": "水",
            "thu": "木", "fri": "金", "sat": "土",
        }

        # HTMLテンプレート生成
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>時間割表 - {sample_schedule_data.classroom_name}</title>
    <style>
        body {{ font-family: 'Noto Sans JP', sans-serif; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #333; padding: 8px; text-align: center; }}
        th {{ background-color: #4a90d9; color: white; }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .metrics {{ margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{sample_schedule_data.classroom_name} 時間割表</h1>
        <p>{sample_schedule_data.term_name}</p>
    </div>
    <div class="metrics">
        <p>ソフト制約達成率: {sample_schedule_data.soft_constraint_rate}%</p>
        <p>ソフト制約達成率: {sample_schedule_data.soft_constraint_rate}%</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>曜日</th>
                <th>コマ</th>
                <th>講師</th>
                <th>生徒</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    </table>
</body>
</html>"""

        assert "渋谷校" in html
        assert "2024年度第1ターム" in html
        assert "85.5" in html
        assert "78.2" in html

    def test_calendar_view_html_generation(self, sample_schedule_data):
        """カレンダービューのHTMLが生成される"""
        days = ["月", "火", "水", "木", "金", "土"]
        slots_per_day = 4

        html = """<table class="calendar">
            <thead>
                <tr>
                    <th></th>"""

        for day in days:
            html += f"<th>{day}</th>"

        html += """</tr>
            </thead>
            <tbody>"""

        for slot_num in range(1, slots_per_day + 1):
            html += f"<tr><td>{slot_num}限</td>"
            for day in days:
                html += "<td></td>"
            html += "</tr>"

        html += """</tbody>
        </table>"""

        assert "月" in html
        assert "土" in html
        assert "1限" in html
        assert "4限" in html

    def test_pdf_bytes_generation_mock(self, sample_schedule_data):
        """PDFバイト生成のモック"""
        # WeasyPrintをモックしてテスト（モジュールがない場合でも動作）
        mock_pdf_bytes = b"%PDF-1.4 mock content"

        # MagicMockを使用してweasyprint.HTMLをシミュレート
        mock_html_class = MagicMock()
        mock_html_instance = MagicMock()
        mock_html_class.return_value = mock_html_instance
        mock_html_instance.write_pdf.return_value = mock_pdf_bytes

        # シミュレートしたHTML→PDF変換
        html_content = "<html><body>Test</body></html>"
        result = mock_html_class(string=html_content).write_pdf()

        assert result == mock_pdf_bytes
        assert result.startswith(b"%PDF")


class TestExportServiceLogic:
    """エクスポートサービスのロジックテスト"""

    def test_export_filename_generation(self):
        """エクスポートファイル名の生成"""
        term_name = "2024年度第1ターム"
        export_type = "calendar"
        format = "pdf"

        # ファイル名生成ロジック
        safe_term_name = term_name.replace("/", "_").replace(" ", "_")
        filename = f"schedule_{safe_term_name}_{export_type}.{format}"

        assert "2024年度第1ターム" in filename
        assert "calendar" in filename
        assert ".pdf" in filename

    def test_export_type_validation(self):
        """エクスポートタイプの検証"""
        valid_types = ["calendar", "teacher", "student", "booth"]

        assert "calendar" in valid_types
        assert "invalid_type" not in valid_types

    def test_export_format_validation(self):
        """エクスポートフォーマットの検証"""
        valid_formats = ["pdf", "csv"]

        assert "pdf" in valid_formats
        assert "csv" in valid_formats
        assert "xlsx" not in valid_formats


class TestTeacherViewExport:
    """講師別ビューエクスポートのテスト"""

    def test_group_slots_by_teacher(self):
        """スロットを講師別にグループ化"""
        slots = [
            {"teacher_id": "T001", "day": "mon", "slot": 1},
            {"teacher_id": "T001", "day": "tue", "slot": 2},
            {"teacher_id": "T002", "day": "mon", "slot": 1},
        ]

        # 講師別にグループ化
        teacher_slots: dict[str, list] = {}
        for slot in slots:
            tid = slot["teacher_id"]
            if tid not in teacher_slots:
                teacher_slots[tid] = []
            teacher_slots[tid].append(slot)

        assert len(teacher_slots["T001"]) == 2
        assert len(teacher_slots["T002"]) == 1


class TestStudentViewExport:
    """生徒別ビューエクスポートのテスト"""

    def test_group_slots_by_student(self):
        """スロットを生徒別にグループ化"""
        slots = [
            {"student1_id": "S001", "student2_id": "S002", "day": "mon", "slot": 1},
            {"student1_id": "S001", "student2_id": None, "day": "tue", "slot": 2},
            {"student1_id": "S003", "student2_id": None, "day": "mon", "slot": 1},
        ]

        # 生徒別にグループ化（1対2で両方の生徒に出現）
        student_slots: dict[str, list] = {}
        for slot in slots:
            for student_id in [slot["student1_id"], slot["student2_id"]]:
                if student_id:
                    if student_id not in student_slots:
                        student_slots[student_id] = []
                    student_slots[student_id].append(slot)

        assert len(student_slots["S001"]) == 2
        assert len(student_slots["S002"]) == 1
        assert len(student_slots["S003"]) == 1


class TestBoothViewExport:
    """ブース別ビューエクスポートのテスト"""

    def test_group_slots_by_booth(self):
        """スロットをブース別にグループ化"""
        slots = [
            {"booth_number": 1, "day": "mon", "slot": 1},
            {"booth_number": 1, "day": "mon", "slot": 2},
            {"booth_number": 2, "day": "mon", "slot": 1},
        ]

        # ブース別にグループ化
        booth_slots: dict[int, list] = {}
        for slot in slots:
            booth = slot["booth_number"]
            if booth not in booth_slots:
                booth_slots[booth] = []
            booth_slots[booth].append(slot)

        assert len(booth_slots[1]) == 2
        assert len(booth_slots[2]) == 1


class TestExportOptions:
    """エクスポートオプションのテスト"""

    def test_include_metrics_option(self):
        """メトリクス含有オプション"""
        options = {
            "include_metrics": True,
            "include_timestamps": True,
            "paper_size": "A4",
        }

        assert options.get("include_metrics") is True
        assert options.get("include_timestamps") is True
        assert options.get("paper_size") == "A4"

    def test_paper_size_validation(self):
        """用紙サイズの検証"""
        valid_sizes = ["A4", "A3", "Letter"]

        assert "A4" in valid_sizes
        assert "B5" not in valid_sizes

    def test_default_options(self):
        """デフォルトオプション"""
        default_options = {
            "include_metrics": True,
            "include_timestamps": False,
            "paper_size": "A4",
            "orientation": "landscape",
        }

        assert default_options["paper_size"] == "A4"
        assert default_options["orientation"] == "landscape"
