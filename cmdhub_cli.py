#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CmdHub CLI Tool - 命令行推送与检索客户端
Usage:
    python cmdhub_cli.py push -p <project> -t <title> -f <script_file>
    python cmdhub_cli.py push -p <project> -t <title> -c "echo Hello"
    python cmdhub_cli.py list -p <project>
    python cmdhub_cli.py cat <snippet_id>
"""

import sys
import argparse
import json
import urllib.request
import urllib.error

DEFAULT_SERVER = "http://127.0.0.1:8080"

def push_snippet(server, project, title, content, language="bash", is_pinned=0):
    url = f"{server.rstrip('/')}/api/snippets"
    payload = json.dumps({
        "project": project,
        "title": title,
        "content": content,
        "language": language,
        "is_pinned": is_pinned
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[SUCCESS] Snippet #{data.get('id')} created in project '{project}'!")
            print(f"Web Link:   {server}/p/{project}")
            print(f"Raw Script: {server}/raw/{data.get('id')}")
            print(f"One-liner:  curl -sSL {server}/raw/{data.get('id')} | bash")
    except Exception as e:
        print(f"[ERROR] Failed to push snippet: {e}", file=sys.stderr)
        sys.exit(1)

def list_snippets(server, project, limit=10):
    url = f"{server.rstrip('/')}/api/snippets?project={project}&limit={limit}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            snippets = data.get("snippets", [])
            print(f"=== Project: {project} ({len(snippets)} snippets) ===")
            for s in snippets:
                pin_mark = "[PIN]" if s.get("is_pinned") else "     "
                print(f"#{s['id']:<4} {pin_mark} {s['title']:<35} ({s.get('created_at', '')})")
    except Exception as e:
        print(f"[ERROR] Failed to list snippets: {e}", file=sys.stderr)
        sys.exit(1)

def cat_snippet(server, snippet_id):
    url = f"{server.rstrip('/')}/raw/{snippet_id}"
    try:
        with urllib.request.urlopen(url) as resp:
            print(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Failed to fetch snippet #{snippet_id}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="CmdHub Client CLI")
    parser.add_argument("--server", "-s", default=DEFAULT_SERVER, help=f"CmdHub server base URL (default: {DEFAULT_SERVER})")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # push command
    p_push = subparsers.add_parser("push", help="Push a new command/script to CmdHub")
    p_push.add_argument("--project", "-p", default="general", help="Project slug")
    p_push.add_argument("--title", "-t", required=True, help="Snippet title")
    p_push.add_argument("--content", "-c", help="Snippet content string")
    p_push.add_argument("--file", "-f", help="Read snippet content from file")
    p_push.add_argument("--lang", "-l", default="bash", help="Snippet language (default: bash)")
    p_push.add_argument("--pin", action="store_true", help="Pin snippet to top")

    # list command
    p_list = subparsers.add_parser("list", help="List snippets in a project")
    p_list.add_argument("--project", "-p", default="general", help="Project slug")
    p_list.add_argument("--limit", "-n", type=int, default=15, help="Number of items to show")

    # cat command
    p_cat = subparsers.add_parser("cat", help="Print raw snippet content")
    p_cat.add_argument("id", type=int, help="Snippet ID")

    args = parser.parse_args()

    if args.command == "push":
        if args.file:
            with open(args.file, "r", encoding="utf-8") as fp:
                content = fp.read()
        elif args.content:
            content = args.content
        else:
            print("[ERROR] Either --content or --file must be specified.", file=sys.stderr)
            sys.exit(1)
        push_snippet(args.server, args.project, args.title, content, args.lang, 1 if args.pin else 0)
    elif args.command == "list":
        list_snippets(args.server, args.project, args.limit)
    elif args.command == "cat":
        cat_snippet(args.server, args.id)

if __name__ == "__main__":
    main()
