import os
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from utils.config_loader import get_base_url, load_config
from utils.logger import get_logger


class RequestClient:
    def __init__(self) -> None:
        config = load_config()
        self.config = config
        self.base_url = get_base_url()
        self.timeout = config.get("timeout", 10)
        self.session = requests.Session()
        self.logger = get_logger("request_client")
        self.cached_token: str | None = None
        self.last_response: requests.Response | None = None
        self._setup_retry()

    def _setup_retry(self) -> None:
        retry_cfg = self.config.get("retry", {})
        retry = Retry(
            total=retry_cfg.get("total", 2),
            backoff_factor=retry_cfg.get("backoff_factor", 0.3),
            status_forcelist=retry_cfg.get("status_forcelist", [429, 500, 502, 503, 504]),
            allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _is_login_path(self, path: str) -> bool:
        auth_cfg = self.config.get("auth", {})
        login_cfg = auth_cfg.get("login", {})
        login_path = login_cfg.get("path")
        if not isinstance(login_path, str) or not login_path:
            return False
        return path.rstrip("/") == login_path.rstrip("/")

    def _build_auth_headers(self, path: str, extra_headers: dict[str, Any] | None) -> dict[str, Any]:
        headers = dict(extra_headers or {})
        if self._is_login_path(path):
            # Avoid recursive auto-login when calling login endpoint itself.
            return headers
        auth_cfg = self.config.get("auth", {})
        token = os.getenv("API_TOKEN") or auth_cfg.get("token") or self._get_cached_token()
        if not token:
            return headers
        header_name = auth_cfg.get("header_name", "Authorization")
        token_type = auth_cfg.get("token_type", "Bearer")
        headers[header_name] = f"{token_type} {token}".strip()
        return headers

    def _extract_token(self, payload: Any, token_field: str) -> str | None:
        if not isinstance(payload, dict):
            return None
        if "." not in token_field:
            value = payload.get(token_field)
            return value if isinstance(value, str) else None
        current: Any = payload
        for part in token_field.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current if isinstance(current, str) else None

    def _get_cached_token(self) -> str | None:
        if self.cached_token:
            return self.cached_token
        auth_cfg = self.config.get("auth", {})
        login_cfg = auth_cfg.get("login", {})
        if not login_cfg.get("enabled", False):
            return None

        method = login_cfg.get("method", "POST")
        path = login_cfg.get("path")
        if not path:
            self.logger.warning("Auth login enabled but no path configured; skip auto login.")
            return None

        login_kwargs: dict[str, Any] = {}
        if login_cfg.get("request_json") is not None:
            login_kwargs["json"] = login_cfg.get("request_json", {})
        if login_cfg.get("request_data"):
            login_kwargs["data"] = login_cfg["request_data"]
        if login_cfg.get("request_params"):
            login_kwargs["params"] = login_cfg["request_params"]
        if login_cfg.get("request_headers"):
            login_kwargs["headers"] = login_cfg["request_headers"]

        login_url = f"{self.base_url}{path}"
        self.logger.info("Auto login for token cache => %s %s", method.upper(), login_url)
        response = self.session.request(
            method=method.upper(),
            url=login_url,
            timeout=self.timeout,
            **login_kwargs,
        )
        response.raise_for_status()

        token_field = login_cfg.get("token_field", "token")
        token = self._extract_token(response.json(), token_field)
        if not token:
            raise ValueError(f"Token field '{token_field}' not found in login response.")
        self.cached_token = token
        self.logger.info("Token cached successfully from login response.")
        return self.cached_token

    def _mask_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._mask_field(k, v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._mask_value(item) for item in value]
        return value

    def _mask_field(self, key: str, value: Any) -> Any:
        mask_fields = [item.lower() for item in self.config.get("log_mask_fields", [])]
        if key.lower() in mask_fields:
            return "***"
        return self._mask_value(value)

    def _log_request(self, method: str, url: str, kwargs: dict[str, Any]) -> None:
        safe_kwargs = self._mask_value(kwargs)
        self.logger.info("Request => %s %s | kwargs=%s", method.upper(), url, safe_kwargs)

    def _log_response(self, response: requests.Response) -> None:
        body = response.text
        if len(body) > 500:
            body = f"{body[:500]}...(truncated)"
        self.logger.info(
            "Response <= %s %s | status=%s | body=%s",
            response.request.method,
            response.url,
            response.status_code,
            body,
        )

    def send(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs["headers"] = self._build_auth_headers(path, kwargs.get("headers"))
        self._log_request(method, url, kwargs)
        response = self.session.request(
            method=method.upper(),
            url=url,
            timeout=self.timeout,
            **kwargs,
        )
        self.last_response = response
        self._log_response(response)
        return response
