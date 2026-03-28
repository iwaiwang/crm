import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("CRM_TEST_BASE_URL", "http://127.0.0.1:5173")
ARTIFACT_DIR = Path(__file__).resolve().parent / "playwright-artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    failed_responses = []
    page_errors = []
    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})

        page.on(
            "response",
            lambda response: failed_responses.append(
                {"url": response.url, "status": response.status}
            )
            if response.status >= 400
            else None,
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )

        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")

        inputs = page.locator("input")
        if inputs.count() < 2:
            raise RuntimeError("登录页输入框不足，无法执行测试")
        inputs.nth(0).fill("admin")
        inputs.nth(1).fill("admin123")
        page.locator("button").first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1200)

        page.goto(f"{BASE_URL}/dashboard", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")

        page.get_by_role("button", name="AI录入合同").click()
        page.get_by_role("heading", name="AI录入合同").wait_for()
        page.get_by_text("SMART INTAKE").wait_for()

        screenshot_path = ARTIFACT_DIR / "ai-contract-import-drawer.png"
        page.screenshot(path=str(screenshot_path), full_page=True)

        result = {
            "ok": True,
            "drawer_opened": True,
            "failed_responses": failed_responses,
            "page_errors": page_errors,
            "console_errors": console_errors,
            "screenshot": str(screenshot_path),
        }
        browser.close()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
