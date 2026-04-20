from pathlib import Path

import pytest
import yaml

from utils.assert_utils import assert_status_code


def load_case_data() -> list[dict]:
    data_path = Path(__file__).resolve().parent.parent / "data" / "login_api.yaml"
    with open(data_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["cases"]


class TestLogin:
    @pytest.mark.parametrize("case", load_case_data(), ids=lambda case: case["name"])
    def test_anonymous_login(self, client, case: dict) -> None:
        request_kwargs = {
            key: case[key]
            for key in ("params", "json", "data", "headers")
            if case.get(key) is not None
        }
        resp = client.send(case["method"], case["path"], **request_kwargs)
        assert_status_code(resp, case["expected_code"])

        body = resp.json()
        assert isinstance(body, dict), f"响应体不是JSON对象: {body}"
