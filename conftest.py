import pytest
import allure

from utils.request_client import RequestClient


@pytest.fixture(scope="session")
def client() -> RequestClient:
    return RequestClient()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or report.passed:
        return

    client_obj = item.funcargs.get("client") if hasattr(item, "funcargs") else None
    if not client_obj or not getattr(client_obj, "last_response", None):
        return

    response = client_obj.last_response
    allure.attach(
        body=response.text,
        name="failed_response_body",
        attachment_type=allure.attachment_type.TEXT,
    )
    allure.attach(
        body=f"{response.request.method} {response.url}\nstatus={response.status_code}",
        name="failed_response_meta",
        attachment_type=allure.attachment_type.TEXT,
    )
