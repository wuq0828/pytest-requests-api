# pytest_requests_api

基于 `Python + pytest + requests` 的接口自动化测试框架 MVP。

## 目录说明

- `config/`：环境与全局配置
- `utils/`：配置读取、请求封装、断言、日志
- `data/`：测试数据（YAML）
- `testcases/`：测试用例
- `reports/allure-results/`：Allure 原始结果
- `logs/`：日志输出目录

## 首次使用

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

生成 Allure 可视化报告（本机需安装 allure 命令行）：

```bash
allure serve reports/allure-results
```

## 环境切换

默认环境在 `config/config.yaml` 的 `env` 字段中。

也可以通过环境变量覆盖：

```bash
TEST_ENV=prod pytest
```

## 新增接口用例（4 步）

1. 在 `data/*.yaml` 中新增接口测试数据：
   - `method`
   - `path`
   - `expected_code`
   - 其他请求参数（如 `params`、`json`、`headers`）
2. 在 `testcases/` 新增或扩展测试函数。
3. 使用 `client.send(method, path, **kwargs)` 发起请求。
4. 使用统一断言函数（如 `assert_status_code`）补充断言。

## 示例

当前示例用例：
- 数据文件：`data/user_api.yaml`
- 测试用例：`testcases/test_user_api.py`

## 已落地能力（本次新增）

- 鉴权自动注入：支持 `API_TOKEN` 环境变量优先，其次读取 `config/config.yaml` 中 `auth.token`
- 登录自动获取并缓存 token：可开启 `auth.login.enabled`，首次请求前自动登录并缓存 token 供后续复用
- 参数化执行：示例用例已使用 `pytest.mark.parametrize`，测试数据位于 `data/user_api.yaml`
- 请求失败重试：可在 `config/config.yaml` 的 `retry` 节点配置重试次数、回退时间与状态码
- 请求/响应日志脱敏：可在 `config/config.yaml` 的 `log_mask_fields` 配置敏感字段
- 失败自动附加响应体到 Allure：用例失败时会自动附加最后一次接口响应内容与元信息

## 相关配置示例

```yaml
auth:
  token: ""
  token_type: Bearer
  header_name: Authorization
  login:
    enabled: false
    method: POST
    path: /login
    request_json: {}
    token_field: token

retry:
  total: 2
  backoff_factor: 0.3
  status_forcelist: [429, 500, 502, 503, 504]

log_mask_fields:
  - token
  - authorization
  - password
```

开启自动登录后，`token_field` 支持点路径，例如 `data.access_token`。

## 后续建议

- 接入 CI（Jenkins/GitHub Actions）
