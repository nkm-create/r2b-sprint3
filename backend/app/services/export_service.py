"""
エクスポートサービス - PDF/CSV出力

時間割のPDF/CSV出力機能を提供する。
"""
import csv
import io
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

# WeasyPrintはオプショナル（インストールされていない場合はフォールバック）
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# ReportLabはオプショナル
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


@dataclass
class ExportSlot:
    """エクスポート用のスロットデータ"""
    slot_id: str
    day_of_week: str
    slot_number: int
    booth_number: int
    teacher_id: str
    teacher_name: str
    student1_id: str
    student1_name: str
    student2_id: str | None
    student2_name: str | None
    subject_id: str
    subject_name: str
    slot_type: str  # "one_to_one" or "one_to_two"


@dataclass
class ExportData:
    """エクスポート用のデータ"""
    schedule_id: str
    term_name: str
    classroom_name: str
    soft_constraint_rate: Decimal
    status: str
    slots: list[ExportSlot]
    created_at: datetime
    export_type: str  # "calendar", "teacher", "student", "booth"


@dataclass
class ExportResult:
    """エクスポート結果"""
    content: bytes
    filename: str
    content_type: str
    export_id: str


class ExportService:
    """エクスポートサービス"""
    _result_store: dict[str, tuple[ExportResult, datetime]] = {}

    DAY_MAP = {
        "mon": "月", "tue": "火", "wed": "水",
        "thu": "木", "fri": "金", "sat": "土",
    }

    DAYS_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat"]

    def __init__(self, temp_dir: str | None = None):
        """
        初期化

        Args:
            temp_dir: 一時ファイルの保存先ディレクトリ
        """
        self.temp_dir = Path(temp_dir) if temp_dir else Path("/tmp")

    @classmethod
    def store_result(cls, result: ExportResult, expires_at: datetime) -> None:
        """生成済みエクスポート結果を一時保存"""
        cls._result_store[result.export_id] = (result, expires_at)

    @classmethod
    def get_result(cls, export_id: str) -> ExportResult | None:
        """保存済みエクスポート結果を取得"""
        stored = cls._result_store.get(export_id)
        if stored is None:
            return None

        result, expires_at = stored
        if expires_at < datetime.now(timezone.utc):
            cls._result_store.pop(export_id, None)
            return None

        return result

    def generate_csv(
        self,
        data: ExportData,
        options: dict | None = None,
    ) -> ExportResult:
        """
        CSV出力を生成

        Args:
            data: エクスポートデータ
            options: オプション設定

        Returns:
            ExportResult: エクスポート結果
        """
        options = options or {}

        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー行
        if options.get("include_metrics", True):
            writer.writerow(["# 時間割エクスポート"])
            writer.writerow([f"# 教室: {data.classroom_name}"])
            writer.writerow([f"# ターム: {data.term_name}"])
            writer.writerow([f"# ソフト制約達成率: {data.soft_constraint_rate}%"])
            writer.writerow([])

        # データヘッダー
        headers = [
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
        writer.writerow(headers)

        # ソートしてデータ行を出力
        sorted_slots = sorted(
            data.slots,
            key=lambda s: (
                self.DAYS_ORDER.index(s.day_of_week) if s.day_of_week in self.DAYS_ORDER else 99,
                s.slot_number,
                s.booth_number,
            ),
        )

        for slot in sorted_slots:
            row = [
                self.DAY_MAP.get(slot.day_of_week, slot.day_of_week),
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

        # UTF-8 BOM付きでエンコード（Excel互換性）
        content = output.getvalue()
        content_bytes = b"\xef\xbb\xbf" + content.encode("utf-8")

        # ファイル名生成
        safe_term_name = data.term_name.replace("/", "_").replace(" ", "_")
        filename = f"schedule_{safe_term_name}_{data.export_type}.csv"

        return ExportResult(
            content=content_bytes,
            filename=filename,
            content_type="text/csv; charset=utf-8",
            export_id=str(uuid.uuid4()),
        )

    def generate_pdf(
        self,
        data: ExportData,
        options: dict | None = None,
    ) -> ExportResult:
        """
        PDF出力を生成

        Args:
            data: エクスポートデータ
            options: オプション設定

        Returns:
            ExportResult: エクスポート結果
        """
        options = options or {}

        if WEASYPRINT_AVAILABLE:
            return self._generate_pdf_weasyprint(data, options)
        if REPORTLAB_AVAILABLE:
            return self._generate_pdf_reportlab(data, options)
        raise RuntimeError("PDF生成ライブラリが利用できません")

    @staticmethod
    def _resolve_page_layout(options: dict) -> tuple[str, str]:
        paper_size = str(options.get("paper_size", "A4")).upper()
        orientation = str(options.get("orientation", "landscape")).lower()
        if paper_size not in {"A3", "A4"}:
            paper_size = "A4"
        if orientation not in {"landscape", "portrait"}:
            orientation = "landscape"
        return paper_size, orientation

    def _generate_pdf_weasyprint(
        self,
        data: ExportData,
        options: dict,
    ) -> ExportResult:
        """WeasyPrintでPDF生成"""
        html_content = self._build_html_template(data, options)

        paper_size, orientation = self._resolve_page_layout(options)

        css = CSS(string=f"""
            @page {
                size: {paper_size} {orientation};
                margin: 10mm;
            }
            body {
                font-family: 'Noto Sans JP', 'Hiragino Sans', sans-serif;
                font-size: 10pt;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #333;
                padding: 4px 6px;
                text-align: center;
            }
            th {
                background-color: #4a90d9;
                color: white;
                font-weight: bold;
            }
            .header {
                text-align: center;
                margin-bottom: 15px;
            }
            .header h1 {
                margin: 0;
                font-size: 16pt;
            }
            .metrics {
                margin-bottom: 10px;
                font-size: 9pt;
            }
            .one-to-two {
                background-color: #e8f5e9;
            }
            .one-to-one {
                background-color: #fff3e0;
            }
        """)

        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf(stylesheets=[css])

        safe_term_name = data.term_name.replace("/", "_").replace(" ", "_")
        filename = f"schedule_{safe_term_name}_{data.export_type}.pdf"

        return ExportResult(
            content=pdf_bytes,
            filename=filename,
            content_type="application/pdf",
            export_id=str(uuid.uuid4()),
        )

    def _generate_pdf_reportlab(
        self,
        data: ExportData,
        options: dict,
    ) -> ExportResult:
        """ReportLabでPDF生成"""
        paper_size, orientation = self._resolve_page_layout(options)
        page_size = A4 if paper_size == "A4" else (841.89, 1190.55)
        if orientation == "landscape":
            page_size = landscape(page_size)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
        )

        elements = []
        styles = getSampleStyleSheet()

        # タイトル
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=14,
            alignment=1,  # Center
        )
        elements.append(Paragraph(f"{data.classroom_name} 時間割表", title_style))
        elements.append(Paragraph(data.term_name, styles["Normal"]))
        elements.append(Spacer(1, 10 * mm))

        # メトリクス
        if options.get("include_metrics", True):
            metrics_text = f"ソフト制約達成率: {data.soft_constraint_rate}%"
            elements.append(Paragraph(metrics_text, styles["Normal"]))
            elements.append(Spacer(1, 5 * mm))

        # テーブルデータ
        table_data = [
            ["曜日", "コマ", "ブース", "講師", "生徒1", "生徒2", "科目", "形態"]
        ]

        sorted_slots = sorted(
            data.slots,
            key=lambda s: (
                self.DAYS_ORDER.index(s.day_of_week) if s.day_of_week in self.DAYS_ORDER else 99,
                s.slot_number,
                s.booth_number,
            ),
        )

        for slot in sorted_slots:
            row = [
                self.DAY_MAP.get(slot.day_of_week, slot.day_of_week),
                str(slot.slot_number),
                str(slot.booth_number),
                slot.teacher_name,
                slot.student1_name,
                slot.student2_name or "-",
                slot.subject_name,
                "1対2" if slot.slot_type == "one_to_two" else "1対1",
            ]
            table_data.append(row)

        # テーブル作成
        table = Table(table_data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a90d9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)

        doc.build(elements)
        pdf_bytes = buffer.getvalue()

        safe_term_name = data.term_name.replace("/", "_").replace(" ", "_")
        filename = f"schedule_{safe_term_name}_{data.export_type}.pdf"

        return ExportResult(
            content=pdf_bytes,
            filename=filename,
            content_type="application/pdf",
            export_id=str(uuid.uuid4()),
        )

    def _generate_html_fallback(
        self,
        data: ExportData,
        options: dict,
    ) -> ExportResult:
        """PDF生成ライブラリがない場合のHTMLフォールバック"""
        html_content = self._build_html_template(data, options)
        html_bytes = html_content.encode("utf-8")

        safe_term_name = data.term_name.replace("/", "_").replace(" ", "_")
        filename = f"schedule_{safe_term_name}_{data.export_type}.html"

        return ExportResult(
            content=html_bytes,
            filename=filename,
            content_type="text/html; charset=utf-8",
            export_id=str(uuid.uuid4()),
        )

    def _build_html_template(self, data: ExportData, options: dict) -> str:
        """HTMLテンプレートを構築"""
        # テーブル行を構築
        rows_html = ""
        sorted_slots = sorted(
            data.slots,
            key=lambda s: (
                self.DAYS_ORDER.index(s.day_of_week) if s.day_of_week in self.DAYS_ORDER else 99,
                s.slot_number,
                s.booth_number,
            ),
        )

        for slot in sorted_slots:
            row_class = "one-to-two" if slot.slot_type == "one_to_two" else "one-to-one"
            rows_html += f"""
            <tr class="{row_class}">
                <td>{self.DAY_MAP.get(slot.day_of_week, slot.day_of_week)}</td>
                <td>{slot.slot_number}</td>
                <td>{slot.booth_number}</td>
                <td>{slot.teacher_name}</td>
                <td>{slot.student1_name}</td>
                <td>{slot.student2_name or "-"}</td>
                <td>{slot.subject_name}</td>
                <td>{"1対2" if slot.slot_type == "one_to_two" else "1対1"}</td>
            </tr>"""

        # メトリクスセクション
        metrics_html = ""
        if options.get("include_metrics", True):
            metrics_html = f"""
            <div class="metrics">
                <p>ソフト制約達成率: {data.soft_constraint_rate}%</p>
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>時間割表 - {data.classroom_name}</title>
    <style>
        body {{
            font-family: 'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic', sans-serif;
            margin: 20px;
            font-size: 12px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 5px 0;
            font-size: 18px;
        }}
        .header p {{
            margin: 0;
            color: #666;
        }}
        .metrics {{
            text-align: center;
            margin-bottom: 15px;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            border: 1px solid #333;
            padding: 6px 8px;
            text-align: center;
        }}
        th {{
            background-color: #4a90d9;
            color: white;
            font-weight: bold;
        }}
        .one-to-two {{
            background-color: #e8f5e9;
        }}
        .one-to-one {{
            background-color: #fff3e0;
        }}
        @media print {{
            body {{
                margin: 0;
            }}
            @page {{
                size: A4 landscape;
                margin: 10mm;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{data.classroom_name} 時間割表</h1>
        <p>{data.term_name}</p>
    </div>
    {metrics_html}
    <table>
        <thead>
            <tr>
                <th>曜日</th>
                <th>コマ</th>
                <th>ブース</th>
                <th>講師</th>
                <th>生徒1</th>
                <th>生徒2</th>
                <th>科目</th>
                <th>形態</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    <div style="margin-top: 20px; text-align: right; color: #999; font-size: 10px;">
        出力日時: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
    </div>
</body>
</html>"""

        return html

    def generate_teacher_view_csv(
        self,
        data: ExportData,
        options: dict | None = None,
    ) -> ExportResult:
        """講師別ビューのCSVを生成"""
        options = options or {}

        # 講師別にグループ化
        teacher_slots: dict[str, list[ExportSlot]] = {}
        for slot in data.slots:
            if slot.teacher_id not in teacher_slots:
                teacher_slots[slot.teacher_id] = []
            teacher_slots[slot.teacher_id].append(slot)

        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー
        writer.writerow([f"# 講師別時間割 - {data.classroom_name}"])
        writer.writerow([f"# ターム: {data.term_name}"])
        writer.writerow([])

        for teacher_id, slots in sorted(teacher_slots.items()):
            teacher_name = slots[0].teacher_name if slots else teacher_id
            writer.writerow([f"■ {teacher_name} ({teacher_id})"])
            writer.writerow(["曜日", "コマ", "生徒1", "生徒2", "科目"])

            for slot in sorted(slots, key=lambda s: (
                self.DAYS_ORDER.index(s.day_of_week) if s.day_of_week in self.DAYS_ORDER else 99,
                s.slot_number,
            )):
                writer.writerow([
                    self.DAY_MAP.get(slot.day_of_week, slot.day_of_week),
                    slot.slot_number,
                    slot.student1_name,
                    slot.student2_name or "-",
                    slot.subject_name,
                ])

            writer.writerow([])

        content = output.getvalue()
        content_bytes = b"\xef\xbb\xbf" + content.encode("utf-8")

        safe_term_name = data.term_name.replace("/", "_").replace(" ", "_")
        filename = f"schedule_{safe_term_name}_teacher_view.csv"

        return ExportResult(
            content=content_bytes,
            filename=filename,
            content_type="text/csv; charset=utf-8",
            export_id=str(uuid.uuid4()),
        )

    def generate_student_view_csv(
        self,
        data: ExportData,
        options: dict | None = None,
    ) -> ExportResult:
        """生徒別ビューのCSVを生成"""
        options = options or {}

        # 生徒別にグループ化
        student_slots: dict[str, list[ExportSlot]] = {}
        for slot in data.slots:
            # 生徒1
            if slot.student1_id:
                if slot.student1_id not in student_slots:
                    student_slots[slot.student1_id] = []
                student_slots[slot.student1_id].append(slot)
            # 生徒2（1対2の場合）
            if slot.student2_id:
                if slot.student2_id not in student_slots:
                    student_slots[slot.student2_id] = []
                student_slots[slot.student2_id].append(slot)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([f"# 生徒別時間割 - {data.classroom_name}"])
        writer.writerow([f"# ターム: {data.term_name}"])
        writer.writerow([])

        for student_id, slots in sorted(student_slots.items()):
            # 生徒名を取得
            student_name = None
            for slot in slots:
                if slot.student1_id == student_id:
                    student_name = slot.student1_name
                    break
                elif slot.student2_id == student_id:
                    student_name = slot.student2_name
                    break
            student_name = student_name or student_id

            writer.writerow([f"■ {student_name} ({student_id})"])
            writer.writerow(["曜日", "コマ", "講師", "科目", "形態"])

            for slot in sorted(slots, key=lambda s: (
                self.DAYS_ORDER.index(s.day_of_week) if s.day_of_week in self.DAYS_ORDER else 99,
                s.slot_number,
            )):
                writer.writerow([
                    self.DAY_MAP.get(slot.day_of_week, slot.day_of_week),
                    slot.slot_number,
                    slot.teacher_name,
                    slot.subject_name,
                    "1対2" if slot.slot_type == "one_to_two" else "1対1",
                ])

            writer.writerow([])

        content = output.getvalue()
        content_bytes = b"\xef\xbb\xbf" + content.encode("utf-8")

        safe_term_name = data.term_name.replace("/", "_").replace(" ", "_")
        filename = f"schedule_{safe_term_name}_student_view.csv"

        return ExportResult(
            content=content_bytes,
            filename=filename,
            content_type="text/csv; charset=utf-8",
            export_id=str(uuid.uuid4()),
        )
