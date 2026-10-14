#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CmdHub - 跨设备命令与代码片段协同中转站
(Command & Snippet Dispatch Hub)
Author: Antigravity Pair Programming
"""

import os
import sys
import sqlite3
import socket
from datetime import datetime
from typing import Optional, List

# Ensure safe UTF-8 output on Windows consoles
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
import uvicorn

# -------------------------------------------------------------
# Configuration & Database Setup
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cmdhub.db")

def get_local_ip():
    """Detect LAN IP address to display clickable links."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            slug TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            language TEXT DEFAULT 'bash',
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_pinned INTEGER DEFAULT 0
        )
    """)
    # Seed default projects if none exist
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO projects (slug, name, description) VALUES (?, ?, ?)
        """, [
            ("general", "通用命令库 (General)", "跨设备日常常用命令、自动化脚本与环境配置片段"),
            ("servers", "远程服务器 (Servers)", "Linux / 云服务器部署、系统巡检与运维命令"),
            ("devices", "边缘终端 (Edge Devices)", "嵌入式设备、单板机、路由网关或测试机协同调试")
        ])
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

init_db()

# -------------------------------------------------------------
# FastAPI App Initialization
# -------------------------------------------------------------
app = FastAPI(title="CmdHub - 命令协同中转站", description="跨终端命令与脚本极速中转分发服务")

class SnippetCreate(BaseModel):
    project: str = "general"
    title: str
    content: str
    language: Optional[str] = "bash"
    description: Optional[str] = ""

# -------------------------------------------------------------
# HTML Templates (Embedded Pure CSS / Zero External CDN)
# -------------------------------------------------------------
HTML_BASE_HEAD = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - CmdHub 命令协同中转站</title>
    <style>
        :root {
            --bg-page: #0d1117;
            --bg-card: #161b22;
            --bg-code: #090d13;
            --border: #30363d;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
            --text-bright: #f0f6fc;
            --accent: #238636;
            --accent-hover: #2ea043;
            --primary: #58a6ff;
            --danger: #f85149;
            --tag-bg: #1f2937;
            --tag-text: #79c0ff;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--bg-page);
            color: var(--text-main);
            line-height: 1.5;
            padding: 20px;
        }
        .container {
            max-width: 1080px;
            margin: 0 auto;
        }
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 18px;
            margin-bottom: 24px;
            border-bottom: 1px solid var(--border);
            flex-wrap: wrap;
            gap: 12px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: var(--text-bright);
        }
        .brand-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #1f6feb, #238636);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            color: #fff;
        }
        .brand-text h1 { font-size: 20px; font-weight: 600; color: #fff; }
        .brand-text p { font-size: 12px; color: var(--text-muted); }
        .nav-links {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        .nav-link {
            padding: 6px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 13px;
            background: var(--bg-card);
            color: var(--text-main);
            border: 1px solid var(--border);
            transition: all 0.2s;
        }
        .nav-link:hover, .nav-link.active {
            border-color: var(--primary);
            color: var(--primary);
        }
        .project-tabs {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 12px;
            margin-bottom: 20px;
        }
        .project-tab {
            text-decoration: none;
            background: var(--bg-card);
            color: var(--text-main);
            padding: 8px 16px;
            border-radius: 20px;
            border: 1px solid var(--border);
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
            transition: 0.2s;
        }
        .project-tab:hover {
            border-color: var(--primary);
            color: var(--text-bright);
        }
        .project-tab.active {
            background: #1f6feb;
            border-color: #388bfd;
            color: #ffffff;
            font-weight: 600;
        }
        .tab-badge {
            background: rgba(255,255,255,0.15);
            padding: 2px 7px;
            border-radius: 10px;
            font-size: 11px;
        }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .card-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-bright);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .tag-project {
            background: var(--tag-bg);
            color: var(--tag-text);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-family: monospace;
            border: 1px solid rgba(88,166,255,0.2);
        }
        .time-badge {
            font-size: 12px;
            color: var(--text-muted);
        }
        .code-wrapper {
            position: relative;
            background: var(--bg-code);
            border: 1px solid var(--border);
            border-radius: 6px;
            overflow: hidden;
            margin-top: 10px;
        }
        .code-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: #161b22;
            border-bottom: 1px solid var(--border);
            font-size: 12px;
            color: var(--text-muted);
        }
        .code-actions {
            display: flex;
            gap: 8px;
        }
        .btn {
            background: #21262d;
            color: var(--text-main);
            border: 1px solid var(--border);
            border-radius: 5px;
            padding: 5px 12px;
            font-size: 12px;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.2s;
        }
        .btn:hover {
            background: #30363d;
            border-color: #8b949e;
            color: var(--text-bright);
        }
        .btn-copy {
            background: #238636;
            color: #ffffff;
            border-color: rgba(240,246,252,0.1);
            font-weight: 500;
        }
        .btn-copy:hover {
            background: #2ea043;
        }
        .btn-copy.copied {
            background: #1f6feb !important;
        }
        .btn-danger {
            color: var(--danger);
        }
        .btn-danger:hover {
            background: rgba(248,81,73,0.15);
            border-color: var(--danger);
        }
        pre.code-block {
            padding: 14px;
            overflow-x: auto;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
            font-size: 13.5px;
            color: #e6edf3;
            line-height: 1.45;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .curl-box {
            margin-top: 10px;
            padding: 8px 12px;
            background: rgba(56, 139, 253, 0.1);
            border: 1px dashed rgba(88, 166, 255, 0.4);
            border-radius: 6px;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: #58a6ff;
            gap: 10px;
        }
        .curl-box code {
            font-family: monospace;
            overflow-x: auto;
            white-space: nowrap;
        }
        .form-group {
            margin-bottom: 14px;
        }
        .form-group label {
            display: block;
            margin-bottom: 6px;
            font-size: 13px;
            color: var(--text-bright);
            font-weight: 500;
        }
        .form-control {
            width: 100%;
            padding: 8px 12px;
            background: #0d1117;
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-bright);
            font-size: 14px;
            font-family: inherit;
        }
        .form-control:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(31,111,235,0.3);
        }
        textarea.form-control {
            font-family: monospace;
            min-height: 120px;
            resize: vertical;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        @media (max-width: 600px) {
            .form-row { grid-template-columns: 1fr; }
        }
        .empty-state {
            text-align: center;
            padding: 50px 20px;
            color: var(--text-muted);
        }
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #238636;
            color: #fff;
            padding: 10px 18px;
            border-radius: 6px;
            font-size: 13px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            display: none;
            z-index: 1000;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
<div class="container">
    <header>
        <a href="/" class="brand">
            <div class="brand-icon">&gt;_</div>
            <div class="brand-text">
                <h1>CmdHub 命令协同中转站</h1>
                <p>局域网服务节点: {server_ip} | 随时随地点击查看与一键执行</p>
            </div>
        </a>
        <div class="nav-links">
            <a href="/" class="nav-link {all_active}">全部项目</a>
            <a href="#new-snippet" class="nav-link" style="background:#238636;color:#fff;border-color:#2ea043;">+ 发布命令</a>
        </div>
    </header>
"""

def render_head(title: str, server_ip: str, all_active: str = "") -> str:
    return (HTML_BASE_HEAD
            .replace("{title}", title)
            .replace("{server_ip}", server_ip)
            .replace("{all_active}", all_active))

HTML_BASE_FOOT = """
    <div id="toast" class="toast">已成功复制到剪贴板！</div>
</div>

<script>
function copySnippet(elementId, btn) {
    const text = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(text).then(() => {
        const originalText = btn.innerHTML;
        btn.innerHTML = "已复制 ✓";
        btn.classList.add("copied");
        showToast("已成功复制到剪贴板！");
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.classList.remove("copied");
        }, 2000);
    }).catch(err => {
        alert("复制失败，请手动选择复制: " + err);
    });
}

function copyCurl(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = btn.innerHTML;
        btn.innerHTML = "已复制 ✓";
        showToast("cURL 运行命令已复制！直接在终端粘贴即可");
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);
    });
}

function deleteSnippet(id) {
    if (!confirm("确认删除这条命令记录吗？")) return;
    fetch('/api/snippets/' + id, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'ok') {
                const el = document.getElementById('card-' + id);
                if (el) el.remove();
                showToast("已成功删除！");
            } else {
                alert("删除失败: " + data.message);
            }
        });
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 2500);
}
</script>
</body>
</html>
"""

# -------------------------------------------------------------
# Routes
# -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """List all snippets across all projects or render dashboard."""
    server_ip = get_local_ip()
    port = request.url.port or 8080
    base_url = f"http://{server_ip}:{port}"

    conn = get_db()
    cursor = conn.cursor()

    # Get all projects with count
    cursor.execute("""
        SELECT p.slug, p.name, p.description, COUNT(s.id) as snippet_count
        FROM projects p
        LEFT JOIN snippets s ON p.slug = s.project
        GROUP BY p.slug
        ORDER BY snippet_count DESC
    """)
    projects = cursor.fetchall()

    # Get recent snippets
    cursor.execute("""
        SELECT * FROM snippets ORDER BY id DESC LIMIT 50
    """)
    snippets = cursor.fetchall()
    conn.close()

    # Render Project Tabs
    tabs_html = '<div class="project-tabs">'
    tabs_html += f'<a href="/" class="project-tab active">全部命令 <span class="tab-badge">{len(snippets)}</span></a>'
    for p in projects:
        tabs_html += f'<a href="/p/{p["slug"]}" class="project-tab">#{p["slug"]} <span class="tab-badge">{p["snippet_count"]}</span></a>'
    tabs_html += '</div>'

    # Render Snippets Cards
    cards_html = ""
    if not snippets:
        cards_html = """
        <div class="empty-state">
            <h3>目前还没有记录任何命令</h3>
            <p style="margin-top:8px;">可以通过下方的表单快速提交，或者使用 API 从终端推送！</p>
        </div>
        """
    else:
        for s in snippets:
            s_id = s["id"]
            proj = s["project"]
            title = s["title"]
            content = s["content"]
            created = s["created_at"]
            raw_url = f"{base_url}/raw/{s_id}"
            curl_cmd = f"curl -sSL {raw_url} | bash"

            cards_html += f"""
            <div class="card" id="card-{s_id}">
                <div class="card-header">
                    <div class="card-title">
                        <a href="/p/{proj}" class="tag-project">#{proj}</a>
                        <span>{title}</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span class="time-badge">{created}</span>
                        <button class="btn btn-danger" onclick="deleteSnippet({s_id})">删除</button>
                    </div>
                </div>
                <div class="code-wrapper">
                    <div class="code-toolbar">
                        <span>代码片段 #{s_id} ({s["language"]})</span>
                        <div class="code-actions">
                            <a href="/raw/{s_id}" target="_blank" class="btn">查看 Raw</a>
                            <button class="btn btn-copy" onclick="copySnippet('code-{s_id}', this)">一键复制命令</button>
                        </div>
                    </div>
                    <pre class="code-block" id="code-{s_id}">{content}</pre>
                </div>
                <div class="curl-box">
                    <span>💡 终端免复制直连执行:</span>
                    <code>{curl_cmd}</code>
                    <button class="btn" style="padding:2px 8px;font-size:11px;" onclick="copyCurl('{curl_cmd}', this)">复制 cURL</button>
                </div>
            </div>
            """

    # Form to create snippet
    form_html = f"""
    <div class="card" id="new-snippet" style="border-color:#1f6feb;margin-top:30px;">
        <h3 style="color:#fff;margin-bottom:14px;display:flex;align-items:center;gap:8px;">
            <span>➕ 发布新命令 / 脚本片段</span>
        </h3>
        <form action="/api/snippets/form" method="POST">
            <div class="form-row">
                <div class="form-group">
                    <label>所属项目 (Project Slug):</label>
                    <input type="text" name="project" class="form-control" list="project-list" value="t450s" required placeholder="如: t450s, server, test">
                    <datalist id="project-list">
                        {''.join([f'<option value="{p["slug"]}">{p["name"]}</option>' for p in projects])}
                    </datalist>
                </div>
                <div class="form-group">
                    <label>命令标题 / 说明 (Title):</label>
                    <input type="text" name="title" class="form-control" placeholder="如: T450s 终端联网测试命令" required>
                </div>
            </div>
            <div class="form-group">
                <label>命令内容 / 代码脚本 (Content):</label>
                <textarea name="content" class="form-control" placeholder="在此输入需要分发的一行或多行命令..." required></textarea>
            </div>
            <div style="display:flex;justify-content:flex-end;">
                <button type="submit" class="btn btn-copy" style="padding:8px 20px;font-size:14px;">立即提交并发布</button>
            </div>
        </form>
    </div>
    """

    head = render_head(
        title="全部命令",
        server_ip=server_ip,
        all_active="active"
    )
    return HTMLResponse(head + tabs_html + cards_html + form_html + HTML_BASE_FOOT)

@app.get("/p/{project}", response_class=HTMLResponse)
async def project_page(project: str, request: Request):
    """View snippets specifically for a project."""
    server_ip = get_local_ip()
    port = request.url.port or 8080
    base_url = f"http://{server_ip}:{port}"

    conn = get_db()
    cursor = conn.cursor()

    # Get all projects for tabs
    cursor.execute("""
        SELECT p.slug, p.name, COUNT(s.id) as snippet_count
        FROM projects p
        LEFT JOIN snippets s ON p.slug = s.project
        GROUP BY p.slug
        ORDER BY snippet_count DESC
    """)
    projects = cursor.fetchall()

    # Get snippets for this project
    cursor.execute("""
        SELECT * FROM snippets WHERE project = ? ORDER BY id DESC
    """, (project,))
    snippets = cursor.fetchall()
    conn.close()

    # Render Project Tabs
    tabs_html = '<div class="project-tabs">'
    tabs_html += f'<a href="/" class="project-tab">全部命令</a>'
    for p in projects:
        active = "active" if p["slug"] == project else ""
        tabs_html += f'<a href="/p/{p["slug"]}" class="project-tab {active}">#{p["slug"]} <span class="tab-badge">{p["snippet_count"]}</span></a>'
    tabs_html += '</div>'

    # Project Header Info
    proj_header = f"""
    <div style="margin-bottom: 20px;">
        <h2 style="color:#fff;font-size:22px;display:flex;align-items:center;gap:10px;">
            <span>项目: #{project}</span>
            <span style="font-size:14px;color:var(--text-muted);font-weight:normal;">({len(snippets)} 条命令)</span>
        </h2>
    </div>
    """

    # Render Snippets
    cards_html = ""
    if not snippets:
        cards_html = f"""
        <div class="empty-state">
            <h3>项目 #{project} 目前没有命令</h3>
            <p style="margin-top:8px;">在下方表单提交第一条命令吧！</p>
        </div>
        """
    else:
        for s in snippets:
            s_id = s["id"]
            title = s["title"]
            content = s["content"]
            created = s["created_at"]
            raw_url = f"{base_url}/raw/{s_id}"
            curl_cmd = f"curl -sSL {raw_url} | bash"

            cards_html += f"""
            <div class="card" id="card-{s_id}">
                <div class="card-header">
                    <div class="card-title">
                        <span class="tag-project">#{project}</span>
                        <span>{title}</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span class="time-badge">{created}</span>
                        <button class="btn btn-danger" onclick="deleteSnippet({s_id})">删除</button>
                    </div>
                </div>
                <div class="code-wrapper">
                    <div class="code-toolbar">
                        <span>代码片段 #{s_id} ({s["language"]})</span>
                        <div class="code-actions">
                            <a href="/raw/{s_id}" target="_blank" class="btn">查看 Raw</a>
                            <button class="btn btn-copy" onclick="copySnippet('code-{s_id}', this)">一键复制命令</button>
                        </div>
                    </div>
                    <pre class="code-block" id="code-{s_id}">{content}</pre>
                </div>
                <div class="curl-box">
                    <span>💡 终端免复制直连执行:</span>
                    <code>{curl_cmd}</code>
                    <button class="btn" style="padding:2px 8px;font-size:11px;" onclick="copyCurl('{curl_cmd}', this)">复制 cURL</button>
                </div>
            </div>
            """

    # Form pre-filled with this project
    form_html = f"""
    <div class="card" id="new-snippet" style="border-color:#1f6feb;margin-top:30px;">
        <h3 style="color:#fff;margin-bottom:14px;">➕ 发布命令到 #{project}</h3>
        <form action="/api/snippets/form" method="POST">
            <input type="hidden" name="project" value="{project}">
            <div class="form-group">
                <label>命令标题 / 说明 (Title):</label>
                <input type="text" name="title" class="form-control" placeholder="如: T450s 终端联网测试命令" required>
            </div>
            <div class="form-group">
                <label>命令内容 / 代码脚本 (Content):</label>
                <textarea name="content" class="form-control" placeholder="在此输入需要分发的一行或多行命令..." required></textarea>
            </div>
            <div style="display:flex;justify-content:flex-end;">
                <button type="submit" class="btn btn-copy" style="padding:8px 20px;font-size:14px;">立即提交到 #{project}</button>
            </div>
        </form>
    </div>
    """

    head = render_head(
        title=f"项目 #{project}",
        server_ip=server_ip,
        all_active=""
    )
    return HTMLResponse(head + tabs_html + proj_header + cards_html + form_html + HTML_BASE_FOOT)

# -------------------------------------------------------------
# Raw Plain Text Endpoints (For terminal curl / sh)
# -------------------------------------------------------------

@app.get("/raw/{snippet_id}", response_class=PlainTextResponse)
async def raw_snippet(snippet_id: int):
    """Return raw text for a specific snippet by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM snippets WHERE id = ?", (snippet_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return PlainTextResponse(row["content"], media_type="text/plain; charset=utf-8")

@app.get("/raw/p/{project}/latest", response_class=PlainTextResponse)
async def raw_latest_project_snippet(project: str):
    """Return raw text for the latest snippet of a project."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM snippets WHERE project = ? ORDER BY id DESC LIMIT 1", (project,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"No snippets found in project #{project}")
    return PlainTextResponse(row["content"], media_type="text/plain; charset=utf-8")

# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------

@app.post("/api/snippets")
async def api_create_snippet(snippet: SnippetCreate, request: Request):
    """Submit snippet via JSON API."""
    server_ip = get_local_ip()
    port = request.url.port or 8080
    base_url = f"http://{server_ip}:{port}"

    conn = get_db()
    cursor = conn.cursor()

    # Ensure project exists
    cursor.execute("INSERT OR IGNORE INTO projects (slug, name) VALUES (?, ?)", (snippet.project, snippet.project))

    cursor.execute("""
        INSERT INTO snippets (project, title, content, language, description)
        VALUES (?, ?, ?, ?, ?)
    """, (snippet.project, snippet.title, snippet.content.strip(), snippet.language, snippet.description))
    snippet_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "id": snippet_id,
        "project": snippet.project,
        "title": snippet.title,
        "view_url": f"{base_url}/p/{snippet.project}",
        "raw_url": f"{base_url}/raw/{snippet_id}",
        "curl_exec": f"curl -sSL {base_url}/raw/{snippet_id} | bash"
    }

@app.post("/api/report")
async def api_report(request: Request, project: str = "t450s", title: str = "终端执行日志回传"):
    body = await request.body()
    content = body.decode("utf-8", errors="replace").strip()
    if not content:
        return PlainTextResponse("WARNING: Empty body received\n", status_code=400)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO projects (slug, name) VALUES (?, ?)", (project, project))
    cursor.execute("""
        INSERT INTO snippets (project, title, content, language)
        VALUES (?, ?, ?, ?)
    """, (project, title, content, "log"))
    snippet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return PlainTextResponse(f"OK: Log recorded as #{snippet_id}\n")

@app.post("/api/snippets/form")
async def form_create_snippet(
    project: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    language: str = Form("bash")
):
    """Handle standard HTML form submission and redirect back to project page."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO projects (slug, name) VALUES (?, ?)", (project, project))
    cursor.execute("""
        INSERT INTO snippets (project, title, content, language)
        VALUES (?, ?, ?, ?)
    """, (project, title, content.strip(), language))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/p/{project}", status_code=303)

@app.delete("/api/snippets/{snippet_id}")
async def api_delete_snippet(snippet_id: int):
    """Delete a snippet by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted == 0:
        return {"status": "error", "message": "Snippet not found"}
    return {"status": "ok", "deleted_id": snippet_id}

@app.get("/api/projects")
async def api_get_projects():
    """List all projects."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.slug, p.name, p.description, COUNT(s.id) as snippet_count
        FROM projects p
        LEFT JOIN snippets s ON p.slug = s.project
        GROUP BY p.slug
        ORDER BY snippet_count DESC
    """)
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"projects": projects}

@app.get("/health")
async def health_check():
    return {"status": "ok", "server_time": datetime.now().isoformat(), "host_ip": get_local_ip()}

# -------------------------------------------------------------
# Main Runner
# -------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("CMDHUB_PORT", 8080))
    host = os.environ.get("CMDHUB_HOST", "0.0.0.0")
    print("=" * 60)
    print("CmdHub is starting...")
    print(f"Local URL: http://127.0.0.1:{port}")
    print(f"LAN URL:   http://{get_local_ip()}:{port}")
    print("=" * 60)
    uvicorn.run("app:app", host=host, port=port, reload=False)
