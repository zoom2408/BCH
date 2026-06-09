#!/usr/bin/env python3
"""
Notion → JSON Sync Script
─────────────────────────
Fetches three Notion databases (Tasks, Content, Roadmap) and writes
structured JSON files that index.html can read.

REUSABLE SKILL: notion-property-mapper
  The `map_properties()` function handles all standard Notion property
  types (title, select, multi_select, date, people, rich_text, checkbox,
  number, url, email, phone_number). Extract and reuse for any project.

Usage:
  python scripts/sync_notion.py

Required environment variables (set in GitHub Secrets):
  NOTION_TOKEN       — your Notion integration token (secret_...)
  TASKS_DB_ID        — Notion database ID for Tasks
  CONTENT_DB_ID      — Notion database ID for Content Calendar
  ROADMAP_DB_ID      — Notion database ID for Product Roadmap

Field mapping (edit FIELD_MAP to match your Notion property names):
  Each entry maps a JSON key → your Notion property name
"""

import os
import json
import sys
import datetime
import urllib.request
import urllib.error

# ── Configuration ──────────────────────────────────────────────────────────────

NOTION_VERSION = "2022-06-28"
API_BASE = "https://api.notion.com/v1"

# Map JSON output keys → your actual Notion property names.
# Edit the VALUES (right side) to match your database column names.
FIELD_MAP = {
    "tasks": {
        "title":    "Name",          # Title property
        "status":   "Status",        # Select property
        "priority": "Priority",      # Select property
        "dueDate":  "Due Date",      # Date property
        "assignee": "Assignee",      # People property
        "tags":     "Tags",          # Multi-select property
    },
    "content": {
        "title":       "Name",
        "status":      "Status",
        "priority":    "Priority",
        "publishDate": "Publish Date",
        "assignee":    "Owner",
        "tags":        "Tags",
    },
    "roadmap": {
        "title":      "Name",
        "status":     "Status",
        "priority":   "Priority",
        "targetDate": "Target Date",
        "assignee":   "Owner",
        "tags":       "Tags",
    },
}

# ── Notion API helpers ─────────────────────────────────────────────────────────

def notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

def query_database(token: str, db_id: str) -> list[dict]:
    """Fetch all pages from a Notion database (handles pagination)."""
    url = f"{API_BASE}/databases/{db_id}/query"
    headers = notion_headers(token)
    results = []
    start_cursor = None

    while True:
        body = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor

        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"  ✗ API error {e.code}: {error_body}", file=sys.stderr)
            break

        results.extend(payload.get("results", []))

        if not payload.get("has_more"):
            break
        start_cursor = payload.get("next_cursor")

    return results


# ── Property mapper (REUSABLE SKILL: notion-property-mapper) ──────────────────

def map_properties(page: dict, field_map: dict) -> dict:
    """
    Maps a Notion page's properties to a flat dict using a field_map.

    field_map format: { "json_key": "Notion Property Name", ... }

    Handles all standard Notion property types:
      title, rich_text, select, multi_select, date,
      people, checkbox, number, url, email, phone_number,
      formula, rollup (basic)
    """
    props = page.get("properties", {})
    result = {}

    for json_key, notion_name in field_map.items():
        prop = props.get(notion_name)
        if prop is None:
            result[json_key] = None
            continue
        result[json_key] = extract_property(prop)

    return result


def extract_property(prop: dict):
    """Extract a value from a single Notion property object."""
    ptype = prop.get("type")

    if ptype == "title":
        items = prop.get("title", [])
        return items[0]["plain_text"] if items else None

    elif ptype == "rich_text":
        items = prop.get("rich_text", [])
        return items[0]["plain_text"] if items else None

    elif ptype == "select":
        sel = prop.get("select")
        return sel["name"] if sel else None

    elif ptype == "multi_select":
        return [opt["name"] for opt in prop.get("multi_select", [])]

    elif ptype == "date":
        date_obj = prop.get("date")
        if not date_obj:
            return None
        return date_obj.get("start")  # ISO 8601 string (YYYY-MM-DD or datetime)

    elif ptype == "people":
        people = prop.get("people", [])
        names = []
        for p in people:
            name = p.get("name") or p.get("id", "Unknown")
            names.append(name)
        return ", ".join(names) if names else None

    elif ptype == "checkbox":
        return prop.get("checkbox", False)

    elif ptype == "number":
        return prop.get("number")

    elif ptype == "url":
        return prop.get("url")

    elif ptype == "email":
        return prop.get("email")

    elif ptype == "phone_number":
        return prop.get("phone_number")

    elif ptype == "formula":
        formula = prop.get("formula", {})
        ftype = formula.get("type")
        return formula.get(ftype)

    elif ptype == "rollup":
        rollup = prop.get("rollup", {})
        rtype = rollup.get("type")
        if rtype == "array":
            items = rollup.get("array", [])
            return [extract_property(i) for i in items]
        return rollup.get(rtype)

    elif ptype == "status":
        # Notion's native Status property type
        status = prop.get("status")
        return status["name"] if status else None

    else:
        return None  # unsupported type — extend as needed


# ── Main sync logic ────────────────────────────────────────────────────────────

def sync_database(token: str, db_id: str, db_name: str, field_map: dict) -> dict:
    """Fetch a Notion database and return a structured dict."""
    print(f"  Fetching {db_name} ({db_id[:8]}…)")
    pages = query_database(token, db_id)
    print(f"  Found {len(pages)} items")

    items = []
    for page in pages:
        mapped = map_properties(page, field_map)

        # Inject page ID and URL regardless of field map
        mapped["id"]  = page["id"].replace("-", "")
        mapped["url"] = page.get("url", "")

        # Ensure tags is always a list
        if not isinstance(mapped.get("tags"), list):
            mapped["tags"] = []

        # Ensure title is never None
        if not mapped.get("title"):
            mapped["title"] = "Untitled"

        items.append(mapped)

    return {
        "lastSync": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total":    len(items),
        "items":    items,
    }


def write_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Written to {path}")


def main():
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("ERROR: NOTION_TOKEN environment variable not set.", file=sys.stderr)
        sys.exit(1)

    databases = {
        "tasks":   (os.environ.get("TASKS_DB_ID"),   "Tasks",    FIELD_MAP["tasks"]),
        "content": (os.environ.get("CONTENT_DB_ID"), "Content",  FIELD_MAP["content"]),
        "roadmap": (os.environ.get("ROADMAP_DB_ID"), "Roadmap",  FIELD_MAP["roadmap"]),
    }

    errors = []
    for key, (db_id, label, fmap) in databases.items():
        print(f"\n[{label}]")
        if not db_id:
            print(f"  ⚠ {key.upper()}_DB_ID not set — skipping")
            errors.append(key)
            continue
        try:
            data = sync_database(token, db_id, label, fmap)
            write_json(f"data/{key}.json", data)
        except Exception as e:
            print(f"  ✗ Failed: {e}", file=sys.stderr)
            errors.append(key)

    print("\n" + ("✓ All databases synced." if not errors else f"⚠ Completed with errors: {errors}"))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
