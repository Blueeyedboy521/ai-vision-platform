from __future__ import annotations

"""
JSON 工具函数

封装 json 序列化/反序列化，便于后续替换底层实现。
"""

from typing import Any, Optional

import json


def to_json(data: Any, ensure_ascii: bool = False) -> str:
    """
    将 Python 对象序列化为 JSON 字符串。

    Args:
        data: 任意可 JSON 序列化的对象
        ensure_ascii: 是否转义非 ASCII 字符
    """
    return json.dumps(data, ensure_ascii=ensure_ascii)


def from_json(data: Optional[str]) -> Any:
    """
    将 JSON 字符串反序列化为 Python 对象。

    Args:
        data: JSON 字符串，为空或 None 时返回 None
    """
    if not data:
        return None
    return json.loads(data)

