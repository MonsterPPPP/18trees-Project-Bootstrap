"""Optional real-browser acceptance: pip install playwright; use local Chromium."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description="离线地图浏览器验收")
    parser.add_argument("html", type=Path)
    parser.add_argument("--browser", required=True, help="本机 Chromium / Chrome / Edge 可执行文件")
    parser.add_argument("--output", type=Path, default=Path("artifacts/browser"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    errors, network, results = [], [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.browser, headless=True)
        context = browser.new_context(offline=True)
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: network.append(request.url) if request.url.startswith(("http:", "https:")) else None)
        for width, height in ((1440, 900), (1600, 1000), (1920, 1080), (2048, 1320)):
            page.set_viewport_size({"width": width, "height": height})
            page.goto(args.html.resolve().as_uri())
            page.frame_locator("#diagram").locator("svg").first.wait_for()
            assert page.locator("h1").inner_text() == "Product / Feature Workflow"
            assert page.locator("nav a").first.get_attribute("href") == "#workflow"
            assert page.locator("section#product").count() == 1
            assert page.locator("section#feature").count() == 1
            assert page.locator("section#capability").count() == 1
            assert page.locator("section#system").count() == 1
            assert page.locator("details[open]").count() == 0
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            frame = page.locator("#diagram").element_handle().content_frame()
            assert frame.evaluate("document.documentElement.scrollWidth <= innerWidth")
            for option in page.locator("#flow option").all():
                page.select_option("#flow", option.get_attribute("value"))
                page.frame_locator("#diagram").locator("svg").first.wait_for()
            page.select_option("#flow", "0")
            page.frame_locator("#diagram").locator("svg").first.wait_for()
            frame = page.locator("#diagram").element_handle().content_frame()
            frame.wait_for_load_state("load")
            frame.wait_for_function("document.querySelectorAll('[data-node-id]').length > 0")
            page.locator("details summary").first.click()
            assert page.locator("details[open]").count() == 1
            page.locator("details summary").first.click()
            for mode in ("light", "dark"):
                page.emulate_media(color_scheme=mode)
                frame.evaluate("mode => document.documentElement.setAttribute('data-theme',mode)", mode)
                page.evaluate("window.scrollTo(0,0)")
                # Wait for theme transitions and the newly navigated iframe to paint.
                page.wait_for_timeout(350)
                page.screenshot(path=str(args.output / f"{width}-{height}-{mode}.png"), full_page=True)
            results.append({"viewport": [width, height], "horizontalOverflow": False, "layers": 4, "metadataCollapsed": True})
        browser.close()
    receipt = {"ok": not errors and not network, "offline": True, "networkRequests": network, "scriptErrors": errors, "viewports": results,
               "visualReview": "pending: inspect screenshots separately"}
    (args.output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    assert not errors, errors
    assert not network, network


if __name__ == "__main__":
    main()
