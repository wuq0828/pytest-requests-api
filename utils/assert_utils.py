from typing import Any

import requests


def assert_status_code(resp: requests.Response, expected_code: int) -> None:
    assert resp.status_code == expected_code, (
        f"状态码断言失败，实际: {resp.status_code}，期望: {expected_code}，响应: {resp.text}"
    )


def assert_json_value(resp: requests.Response, key: str, expected: Any) -> None:
    body = resp.json()
    assert key in body, f"响应中不存在字段: {key}，响应: {body}"
    assert body[key] == expected, (
        f"字段断言失败，字段: {key}，实际: {body[key]}，期望: {expected}"
    )
