"""FastAPI OpenAPI スキーマをエクスポート"""
import json
import argparse
import sys
from pathlib import Path

# backend ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


def main():
    parser = argparse.ArgumentParser(description="Export OpenAPI schema")
    parser.add_argument(
        "-o", "--output",
        default="openapi.json",
        help="Output file path (default: openapi.json)"
    )
    args = parser.parse_args()

    openapi_schema = app.openapi()

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI schema exported to: {args.output}")


if __name__ == "__main__":
    main()
