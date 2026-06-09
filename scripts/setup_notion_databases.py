#!/usr/bin/env python3
"""
Notion Database Setup Script
─────────────────────────────
Automatically creates all 3 databases (Tasks, Content Calendar, Roadmap)
inside a Notion page you specify, with the correct properties pre-configured.

After running this script, it prints the database IDs — paste those into
your GitHub Secrets and you're done.

Usage:
    python scripts/setup_notion_databases.py

You will be prompted for:
  - Your Notion Integration Token
  - The URL (or ID) of the Notion page to create the databases inside

Requirements: Python 3.7+ — no pip installs needed (uses stdlib only)
"""

import json
import os
import sys
import urllib.request
import urllib.error
import re

NOTION_VERSION = "2022-06-28"
API_BASE = "https://api.notion.com/v1"

# ── ANSI colors for nicer terminal output ──────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):  print(f"  {GREEN}✓{RESET} {msg}")
def warn(msg):print(f"  {YELLOW}⚠{RESET} {msg}")
def err(msg): print(f"  {RED}✗{RESET} {msg}")
def head(msg):print(f"\n{BOLD}{msg}{RESET}")


# ── Notion API helpers ─────────────────────────────────────────────────────────

def notion_request(method, path, token, body=None):
    url = f"{API_BASE}/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {body_text}")


def validate_token(token):
    """Check the token works by calling /users/me."""
    try:
        user = notion_request("GET", "users/me", token)
        name = user.get("name") or user.get("bot", {}).get("workspace_name", "Unknown")
        ok(f"Token valid — workspace: {BOLD}{name}{RESET}")
        return True
    except RuntimeError as e:
        err(f"Token validation failed: {e}")
        return False


def extract_page_id(url_or_id):
    """
    Robustly extract a Notion page ID from a URL or raw ID string.

    Handles all known Notion URL formats:
      https://www.notion.so/My-Page-b36f625eaddd1815695b8e3fd8fb9f23
      https://www.notion.so/workspace/My-Page-b36f625eaddd1815695b8e3fd8fb9f23
      https://www.notion.so/b36f625e-addd-1815-695b-8e3fd8fb9f23
      b36f625eaddd1815695b8e3fd8fb9f23            (raw 32-char hex)
      b36f625e-addd-1815-695b-8e3fd8fb9f23        (UUID with dashes)

    Strategy: split by path segments and check each from the END,
    because Notion always puts the page ID at the end of the URL.
    This avoids false matches from hex chars in page names (e.g. "ace", "cafe").
    """
    # Strip query params and fragments first
    raw = url_or_id.strip().split("?")[0].split("#")[0]

    # Split into path segments (handles both / and plain IDs)
    segments = [s for s in raw.replace("\\", "/").split("/") if s]

    # Check each segment from the end — Notion ID is always last
    for segment in reversed(segments):
        # Remove dashes to normalise UUID formats
        clean = segment.replace("-", "").lower()
        # Must be EXACTLY 32 hex chars (full match, not substring)
        if re.fullmatch(r"[0-9a-f]{32}", clean):
            return f"{clean[:8]}-{clean[8:12]}-{clean[12:16]}-{clean[16:20]}-{clean[20:]}"
        # Notion URL slug format: "Page-Title-{32hexchars}" — ID is the last 32 hex chars
        match = re.search(r"([0-9a-f]{32})$", clean)
        if match:
            raw_id = match.group(1)
            return f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"

    return None


def verify_page_access(token, page_id):
    """
    Check that the integration can actually see the page.
    This catches the most common setup mistake: forgetting to add
    the integration via the page's '...' → Connections menu.
    """
    try:
        notion_request("GET", f"pages/{page_id}", token)
        ok("Integration can access the page ✓")
        return True
    except RuntimeError as e:
        error_text = str(e)
        if "404" in error_text or "object_not_found" in error_text:
            err("Page not found — the integration can't see it.")
            print()
            print(f"  {YELLOW}Fix in Notion (takes 10 seconds):{RESET}")
            print(f"  1. Open the page in Notion")
            print(f"  2. Click the  ···  (three dots) menu — top right of the page")
            print(f"  3. Scroll down to  Connections")
            print(f"  4. Find your integration name and click it to connect")
            print(f"  5. Re-run this script")
            print()
            print(f"  {YELLOW}Note: 'Share → Invite' is for people, not integrations.{RESET}")
            print(f"  {YELLOW}Integrations require the Connections menu.{RESET}")
        elif "401" in error_text or "unauthorized" in error_text:
            err("Unauthorised — double-check your NOTION_TOKEN.")
        else:
            err(f"Could not verify page access: {error_text}")
        return False


# ── Database schemas ───────────────────────────────────────────────────────────

def tasks_schema(parent_page_id):
    return {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "✅"},
        "title": [{"type": "text", "text": {"content": "Tasks"}}],
        "properties": {
            "Name": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "To Do",       "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "In Review",   "color": "yellow"},
                        {"name": "Blocked",     "color": "red"},
                        {"name": "Done",        "color": "green"},
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High",   "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low",    "color": "green"},
                    ]
                }
            },
            "Due Date":  {"date": {}},
            "Assignee":  {"people": {}},
            "Tags":      {"multi_select": {
                "options": [
                    {"name": "Dev",     "color": "blue"},
                    {"name": "Design",  "color": "pink"},
                    {"name": "Marketing","color": "orange"},
                    {"name": "Docs",    "color": "gray"},
                    {"name": "Testing", "color": "purple"},
                ]
            }},
            "Notes": {"rich_text": {}},
        },
    }


def content_schema(parent_page_id):
    return {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "📝"},
        "title": [{"type": "text", "text": {"content": "Content Calendar"}}],
        "properties": {
            "Name": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Draft",     "color": "gray"},
                        {"name": "In Progress","color": "blue"},
                        {"name": "In Review", "color": "yellow"},
                        {"name": "Scheduled", "color": "purple"},
                        {"name": "Published", "color": "green"},
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High",   "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low",    "color": "green"},
                    ]
                }
            },
            "Publish Date": {"date": {}},
            "Owner":  {"people": {}},
            "Tags":   {"multi_select": {
                "options": [
                    {"name": "Blog",       "color": "blue"},
                    {"name": "Newsletter", "color": "orange"},
                    {"name": "Social",     "color": "pink"},
                    {"name": "Tutorial",   "color": "purple"},
                    {"name": "Case Study", "color": "brown"},
                    {"name": "Marketing",  "color": "red"},
                ]
            }},
            "Channel": {
                "select": {
                    "options": [
                        {"name": "Blog",      "color": "blue"},
                        {"name": "Email",     "color": "orange"},
                        {"name": "LinkedIn",  "color": "blue"},
                        {"name": "Instagram", "color": "pink"},
                        {"name": "Twitter/X", "color": "gray"},
                    ]
                }
            },
            "Notes": {"rich_text": {}},
        },
    }


def roadmap_schema(parent_page_id):
    return {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "🗺️"},
        "title": [{"type": "text", "text": {"content": "Product Roadmap"}}],
        "properties": {
            "Name": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Planned",     "color": "purple"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "In Review",   "color": "yellow"},
                        {"name": "Blocked",     "color": "red"},
                        {"name": "Done",        "color": "green"},
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High",   "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low",    "color": "green"},
                    ]
                }
            },
            "Target Date": {"date": {}},
            "Owner":  {"people": {}},
            "Tags":   {"multi_select": {
                "options": [
                    {"name": "MVP",          "color": "red"},
                    {"name": "Frontend",     "color": "blue"},
                    {"name": "Backend",      "color": "orange"},
                    {"name": "Integrations", "color": "purple"},
                    {"name": "Infra",        "color": "gray"},
                    {"name": "Design",       "color": "pink"},
                ]
            }},
            "Version": {
                "select": {
                    "options": [
                        {"name": "v1.0", "color": "green"},
                        {"name": "v1.1", "color": "blue"},
                        {"name": "v2.0", "color": "purple"},
                        {"name": "Backlog","color":"gray"},
                    ]
                }
            },
            "Notes": {"rich_text": {}},
        },
    }


# ── Sample rows ────────────────────────────────────────────────────────────────

def add_sample_rows(token, db_id, db_type):
    """Add a few sample rows so the database isn't empty."""
    import datetime
    today = datetime.date.today()

    samples = {
        "tasks": [
            {"Name":"Set up GitHub repo", "Status":"Done",        "Priority":"High",   "Due Date": str(today - datetime.timedelta(days=7))},
            {"Name":"Configure sync script","Status":"In Progress","Priority":"High",   "Due Date": str(today + datetime.timedelta(days=2))},
            {"Name":"Deploy to GitHub Pages","Status":"To Do",     "Priority":"Medium", "Due Date": str(today + datetime.timedelta(days=5))},
        ],
        "content": [
            {"Name":"Launch Announcement", "Status":"Published",   "Priority":"High",   "Publish Date": str(today - datetime.timedelta(days=3))},
            {"Name":"June Newsletter",     "Status":"In Progress", "Priority":"High",   "Publish Date": str(today + datetime.timedelta(days=10))},
            {"Name":"Tutorial: Setup Guide","Status":"Draft",      "Priority":"Medium", "Publish Date": str(today + datetime.timedelta(days=20))},
        ],
        "roadmap": [
            {"Name":"MVP Tracker",         "Status":"Done",        "Priority":"High",   "Target Date": str(today - datetime.timedelta(days=5))},
            {"Name":"Notion Integration",  "Status":"In Progress", "Priority":"High",   "Target Date": str(today + datetime.timedelta(days=4))},
            {"Name":"Mobile Layout",       "Status":"Planned",     "Priority":"Medium", "Target Date": str(today + datetime.timedelta(days=14))},
        ],
    }

    date_field = {"tasks": "Due Date", "content": "Publish Date", "roadmap": "Target Date"}[db_type]

    for row in samples.get(db_type, []):
        props = {
            "Name": {"title": [{"type": "text", "text": {"content": row["Name"]}}]},
            "Status":   {"select": {"name": row["Status"]}},
            "Priority": {"select": {"name": row["Priority"]}},
            date_field: {"date": {"start": row.get(date_field, str(today))}},
        }
        try:
            notion_request("POST", "pages", token, {
                "parent": {"database_id": db_id},
                "properties": props,
            })
        except RuntimeError as e:
            warn(f"  Couldn't add sample row '{row['Name']}': {e}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{BOLD}╔══════════════════════════════════════╗")
    print(f"║  BCH Notion Database Setup Script   ║")
    print(f"╚══════════════════════════════════════╝{RESET}")

    # ── Step 1: Get token ──────────────────────────────────────────────────────
    head("Step 1 — Notion Integration Token")
    print("  Get it from: https://www.notion.so/my-integrations")
    token = input("  Paste your token (secret_...): ").strip()
    if not token.startswith("secret_"):
        warn("Token doesn't start with 'secret_' — double-check you copied the right value.")

    if not validate_token(token):
        print(f"\n{RED}Could not validate token. Exiting.{RESET}")
        sys.exit(1)

    # ── Step 2: Get parent page ────────────────────────────────────────────────
    head("Step 2 — Parent Notion Page")
    print("  Create a blank page in Notion where the 3 databases will live.")
    print("  Then share it with your integration (page '...' → Connections → add integration).")
    print("  Paste the page URL here:")
    raw_input = input("  Page URL or ID: ").strip()
    page_id = extract_page_id(raw_input)
    if not page_id:
        err("Could not extract a page ID from that input. Try pasting the full Notion URL.")
        sys.exit(1)
    ok(f"Parsed page ID: {page_id}")

    # ── Step 2b: Verify the integration can access the page ───────────────────
    print(f"\n  Checking integration has access to the page…")
    if not verify_page_access(token, page_id):
        print(f"\n{RED}Cannot proceed until the integration is connected to the page.{RESET}")
        sys.exit(1)

    # ── Step 3: Create databases ───────────────────────────────────────────────
    head("Step 3 — Creating Databases")
    created = {}

    databases = [
        ("tasks",   "Tasks",            tasks_schema),
        ("content", "Content Calendar", content_schema),
        ("roadmap", "Product Roadmap",  roadmap_schema),
    ]

    for key, label, schema_fn in databases:
        print(f"\n  Creating {label}…")
        try:
            result = notion_request("POST", "databases", token, schema_fn(page_id))
            db_id = result["id"]
            created[key] = db_id
            ok(f"{label} created: {db_id}")
            # Add sample rows
            add_sample_rows(token, db_id, key)
            ok(f"Sample rows added")
        except RuntimeError as e:
            err(f"Failed to create {label}: {e}")
            print(f"\n  {YELLOW}Tip: Make sure you shared the parent page with your integration.{RESET}")

    if not created:
        err("No databases were created. Check that your integration has access to the parent page.")
        sys.exit(1)

    # ── Step 4: Print GitHub Secrets ───────────────────────────────────────────
    head("Step 4 — Add These GitHub Secrets")
    print(f"  Go to: Your GitHub repo → Settings → Secrets and variables → Actions\n")
    print(f"  {BOLD}Secret name          Value{RESET}")
    print(f"  {'─'*60}")
    print(f"  NOTION_TOKEN         {token}")
    for key, db_id in created.items():
        secret_name = f"{key.upper()}_DB_ID"
        print(f"  {secret_name:<20} {db_id}")

    # ── Step 5: Update FIELD_MAP reminder ─────────────────────────────────────
    head("Step 5 — You're Done!")
    print("  The databases were created with property names that exactly match")
    print("  the FIELD_MAP in scripts/sync_notion.py — no edits needed there.")
    print()
    print("  Next steps:")
    print("   1. Add the secrets above to GitHub")
    print("   2. Push tracker/ to your GitHub repo")
    print("   3. Enable GitHub Pages (Settings → Pages → branch: main, folder: /)")
    print("   4. Run the sync manually: Actions → 'Sync Notion → JSON' → Run workflow")
    print("   5. Open your GitHub Pages URL and log in with your passphrase")
    print()
    print(f"  {GREEN}{BOLD}Your passphrase is set in index.html line ~313 (default: bch2024){RESET}")
    print()

    # Save IDs to a local .env file for convenience
    env_path = ".env.notion"
    with open(env_path, "w") as f:
        f.write(f"NOTION_TOKEN={token}\n")
        for key, db_id in created.items():
            f.write(f"{key.upper()}_DB_ID={db_id}\n")
    ok(f"IDs also saved to {env_path} (keep this file private — add to .gitignore)")


if __name__ == "__main__":
    main()
