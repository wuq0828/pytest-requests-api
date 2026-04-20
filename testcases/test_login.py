from pathlib import Path

import pytest
import yaml

from utils.assert_utils import assert_status_code


def load_case_data() -> list[dict]:
    # 从 data 层读取所有 case，供 pytest 参数化执行
    data_path = Path(__file__).resolve().parent.parent / "data" / "login_api.yaml"
    with open(data_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["cases"]


class TestLogin:
    # 你的 case 在这里逐条展开执行，ids 使用 case.name 便于报告定位
    @pytest.mark.parametrize("case", load_case_data(), ids=lambda case: case["name"])
    def test_anonymous_login(self, client, case: dict) -> None:
        # 通用请求参数组装：仅传递当前 case 中配置过的字段
        request_kwargs = {
            key: case[key]
            for key in ("params", "json", "data", "headers")
            if case.get(key) is not None
        }
        resp = client.send(case["method"], case["path"], **request_kwargs)
        # 核心断言：状态码
        assert_status_code(resp, case["expected_code"])

        body = resp.json()
        # 基础结构断言，可按业务继续补充字段断言
        assert isinstance(body, dict), f"响应体不是JSON对象: {body}"
