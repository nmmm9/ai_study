"""HWP 문서 변환 — @ohah/hwpjs CLI."""

import json
import subprocess
from tools.registry import register_tool


@register_tool(
    name="hwp_convert",
    description="HWP(한글) 문서를 텍스트/마크다운/JSON으로 변환합니다. 파일 경로를 입력하세요.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "HWP 파일 경로"},
            "format": {"type": "string", "enum": ["text", "markdown", "json"], "description": "출력 형식", "default": "text"},
        },
        "required": ["file_path"],
    },
)
async def hwp_convert(file_path: str, format: str = "text") -> dict:
    fmt_flag = {"text": "txt", "markdown": "md", "json": "json"}.get(format, "txt")

    try:
        result = subprocess.run(
            f'npx --yes @ohah/hwpjs convert "{file_path}" --format {fmt_flag}',
            capture_output=True, text=True, encoding="utf-8",
            timeout=30, shell=True,
        )
        stdout = result.stdout.strip()
        if stdout:
            if fmt_flag == "json":
                try:
                    return {"file": file_path, "format": format, "data": json.loads(stdout)}
                except json.JSONDecodeError:
                    pass
            return {"file": file_path, "format": format, "content": stdout[:3000]}

        if result.returncode != 0:
            return {"error": f"HWP 변환 실패: {result.stderr[:200]}"}
        return {"error": "변환 결과 없음"}
    except subprocess.TimeoutExpired:
        return {"error": "HWP 변환 타임아웃"}
    except Exception as e:
        return {"error": f"HWP 변환 오류: {str(e)}"}
