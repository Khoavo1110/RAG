---
name: browser-use
description: "Direct browser automation & web research via MCP server browser-use (browser_exec, browser_screenshot) connected to pre-warmed Chrome on port 9222 with Health Guard protection."
version: 2.0.0
author: Antigravity Master Control Hub
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, browser-use, mcp, automation, web-scraping, testing, cdp, chrome]
---

# MCP Browser-Use Standard Operating Procedure

Direct browser automation, scraping, web research, and visual testing using MCP tools:
- `browser_exec(code: string)`: Executes Python in the browser-harness session attached to pre-warmed Google Chrome via Chrome DevTools Protocol (CDP).
- `browser_screenshot(full?: boolean, max_dim?: integer)`: Captures the current active browser page as an image.

---

## 1. PRE-WARMED CHROME & HEALTH GUARD (CRITICAL PREREQUISITE)

User always runs Google Chrome on debugging port 9222:
```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebugProfile"
```

### Mandatory Execution Order:
**BEFORE** calling `browser_exec` or `browser_screenshot`, ALWAYS execute the environment cleanup script in terminal:
```powershell
python C:\Users\vodan\.gemini\config\scripts\browser_health_guard.py
```
**Why:**
- Automatically kills zombie Playwright/daemon processes fighting for port 9222.
- Cleans stale download locks and temporary directories in `$env:TEMP`.
- Guarantees Chrome CDP endpoint `http://127.0.0.1:9222` is alive and responsive.
- Eliminates 30-60 second socket timeouts.

**STRICT RULE:** NEVER call `browser_exec` first and only run `browser_health_guard` after seeing an error. Run health guard FIRST, verify ready, then call `browser_exec`.

---

## 2. BROWSER_EXEC CODING STANDARDS (ZERO-SYNTAX ERROR)

The `browser_exec` tool executes **Python code** in an interactive browser harness session. The namespace persists across calls.

### Pre-Imported Helper Functions (Do NOT re-import):
- `new_tab(url)`: Opens a new tab to `url` and attaches to it. **Always use this for the first navigation.**
- `goto_url(url)`: Navigates the current tab to `url`.
- `page_info()`: Returns a dict with current tab ID, URL, title, and open tab list.
- `click_at_xy(x, y)`: Simulates a mouse click at coordinates (x, y).
- `type_text(text)`: Types text into the focused element.
- `js(code)`: Evaluates JavaScript in the browser context and returns the result.
- `cdp(method, **kwargs)`: Directly invokes Chrome DevTools Protocol methods.
- `wait_for_load()`: Waits for the page load event and network idle.
- `list_tabs()`: Lists all open browser tabs.
- `switch_tab(target)`: Switches harness focus to a specific tab.

---

### Core Coding Rules:

#### Rule 1: No Multi-line JavaScript Strings
**NEVER** write multi-line JS strings containing line breaks `\n` inside `js("""...""")`. This causes `SyntaxError: Invalid or unexpected token` in Python/V8 string evaluation.
```python
# ❌ INCORRECT (SyntaxError):
res = js("""
    const links = document.querySelectorAll('a');
    return Array.from(links).map(a => a.href);
""")

# ✅ CORRECT: Single-line JS or Python processing
html = js("document.body.innerHTML")
# Process and extract links using Python!
```

#### Rule 2: Raw Extraction via 1-Line JS + Local Python Processing
Fetch raw DOM content in one line, then do 100% of the extraction, parsing, regex matching, filtering, and data structuring using local Python:
```python
# Extract text:
text = js("document.body.innerText")

# Extract HTML:
html = js("document.body.innerHTML")

# Parse in Python:
import re
titles = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html)
for t in titles[:10]:
    print("-", t.strip())
```

#### Rule 3: Safe Navigation Latency
After any navigation (`new_tab` or `goto_url`), always call `wait_for_load()` followed by a safety delay to allow dynamic SPA/hydration scripts to finish rendering:
```python
new_tab("https://example.com")
wait_for_load()
import time
time.sleep(1)
print(page_info())
```

#### Rule 4: Visual Evidence via `browser_screenshot`
When visual proof or diagram checking is needed, call the dedicated MCP tool `browser_screenshot`:
```json
{
  "full": false,
  "max_dim": 1440
}
```

---

## 3. COMMON WORKFLOW TEMPLATES

### Template A: Safe Navigation & Page Inspection
```python
new_tab("https://news.ycombinator.com")
wait_for_load()
import time
time.sleep(1)

info = page_info()
print(f"Title: {info.get('title')}")
print(f"URL: {info.get('url')}")

text = js("document.body.innerText")
lines = [line.strip() for line in text.splitlines() if line.strip()]
print("\n--- FIRST 10 LINES ---")
for line in lines[:10]:
    print(line)
```

### Template B: Search & Extract Results
```python
# 1. Navigate to search engine
new_tab("https://duckduckgo.com")
wait_for_load()
import time
time.sleep(1)

# 2. Type query into search box and press enter
js("document.querySelector('input[name=\"q\"]').focus()")
type_text("IUH Software Engineering\n")
wait_for_load()
time.sleep(2)

# 3. Extract results using Python
html = js("document.body.innerHTML")
import re
titles = re.findall(r'<h2[^>]*>(.*?)</h2>', html)
for t in titles[:5]:
    clean = re.sub(r'<[^>]+>', '', t)
    print(f"- {clean.strip()}")
```

### Template C: Form Interaction & Coordinate Clicking
```python
# Find coordinates via DOM bounding box
box = js("document.querySelector('button[type=\"submit\"]').getBoundingClientRect()")
if box:
    x = box['left'] + box['width'] / 2
    y = box['top'] + box['height'] / 2
    click_at_xy(x, y)
    wait_for_load()
    import time
    time.sleep(1)
    print("Clicked button at", x, y)
```

---

## 4. ERROR DIAGNOSIS & SELF-HEALING

| Symptom / Error | Root Cause | Self-Healing Action |
| :--- | :--- | :--- |
| `ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 9222)` | Chrome is not running or CDP port is closed | Run `python C:\Users\vodan\.gemini\config\scripts\browser_health_guard.py` which auto-spawns Chrome with remote debugging. |
| `TimeoutError: Timed out waiting for browser daemon` | Stale locks or zombie processes holding socket | Run `browser_health_guard.py` to kill zombie daemons and purge `$env:TEMP/browser-use-downloads-*`. |
| `SyntaxError: Invalid or unexpected token` | Multi-line string with newlines passed into `js(...)` | Switch to single-line `js("document.body.innerText")` and parse using Python. |
| `NoneType has no attribute ...` or empty text | Page is still dynamically rendering / hydrating | Add `time.sleep(1.5)` after `wait_for_load()` before querying the DOM. |
