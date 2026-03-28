from pathlib import Path
import json
import os
import sys
from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("CRM_TEST_BASE_URL", "http://127.0.0.1:5173")
TEST_MODE = os.getenv("CRM_TEST_MODE", "open").strip()
OUTPUT_DIR = Path(__file__).resolve().parent / "playwright-artifacts"
OUTPUT_DIR.mkdir(exist_ok=True)


def main():
    console_messages = []
    page_errors = []
    failed_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 960})

        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
        }))
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("response", lambda response: failed_responses.append({
            "url": response.url,
            "status": response.status,
        }) if response.status >= 400 else None)

        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")

        inputs = page.locator("input")
        if inputs.count() >= 2:
            inputs.nth(0).fill("admin")
            inputs.nth(1).fill("admin123")

        page.locator("button").first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)

        current_url = page.url
        if "/login" in current_url:
            page.screenshot(path=str(OUTPUT_DIR / "login-failed.png"), full_page=True)
            browser.close()
            print(json.dumps({
                "ok": False,
                "stage": "login",
                "url": current_url,
                "console": console_messages,
                "page_errors": page_errors,
                "failed_responses": failed_responses,
            }, ensure_ascii=False, indent=2))
            sys.exit(1)

        page.goto(f"{BASE_URL}/settings", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        if TEST_MODE == "cleanup":
            page.locator(".el-tabs__header .el-tabs__item").last.click()
            page.wait_for_timeout(500)
            page.locator("button.el-button--warning").first.click()
            page.wait_for_timeout(500)
            page.locator(".el-dialog__footer button.el-button--danger").last.click()
            page.wait_for_timeout(500)
            page.locator(".el-message-box__btns .el-button--primary").click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1500)

        page.screenshot(path=str(OUTPUT_DIR / "settings-page.png"), full_page=True)

        settings_failures = [
            item for item in failed_responses
            if "/api/settings" in item["url"] or "/api/document/ai-service/status" in item["url"]
        ]
        blocking_console = [
            item for item in console_messages
            if item["type"] in {"error", "warning"}
        ]

        result = {
            "ok": len(settings_failures) == 0 and len(page_errors) == 0,
            "stage": f"settings:{TEST_MODE}",
            "url": page.url,
            "console": console_messages,
            "page_errors": page_errors,
            "failed_responses": failed_responses,
            "settings_failures": settings_failures,
            "settings_title_found": page.locator(".settings-container").count() > 0,
            "screenshot": str(OUTPUT_DIR / "settings-page.png"),
        }

        browser.close()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["ok"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
