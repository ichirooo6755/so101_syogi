#!/usr/bin/env python3
"""Render the architecture from its JSON progress, using Python's standard library."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from datetime import datetime, timedelta, timezone
from html import escape
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import webbrowser

import tagged

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "構成図/構成図.json"
CONFIG = "構成図/図設定.json"
TAG_LAYOUT = "構成図/タグ付き構成.json"
TAG_TEMPLATE = "構成図/tagged_template.html"
TAG_HTML = "構成図/構成図.html"
TAG_SVG = "構成図/タグ付き構成図.svg"
PLAN = "shogi/docs/shogi-implementation-plan.md"
START = "<!-- generated:architecture-diagram:start -->"
END = "<!-- generated:architecture-diagram:end -->"
ID = re.compile(r"[a-z][a-z0-9_]*\Z")
COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate(data, config):
    if config["source"] != SOURCE:
        raise ValueError("正本JSONの参照先が一致しません")
    modules = data["modules"]
    ids = [module["id"] for module in modules]
    if len(set(ids)) != len(ids) or not all(ID.fullmatch(ident) for ident in ids):
        raise ValueError("構成要素のIDが重複または不正です")
    statuses = data["status_definitions"]
    for name, definition in statuses.items():
        style = definition["style"]
        if (not ID.fullmatch(name)
                or not COLOR.fullmatch(style["fill"])
                or not COLOR.fullmatch(style["stroke"])
                or isinstance(style["stroke_width"], bool)
                or not 0 < style["stroke_width"] <= 10
                or (style.get("dash") is not None
                    and not re.fullmatch(r"\d+(?: \d+)*", style["dash"]))):
            raise ValueError("進捗の色・線の設定が不正です")
    for module in modules:
        if module["status"] not in statuses:
            raise ValueError(f"未知の進捗状態: {module['id']}")
        if not module.get("progress", {}).get("evidence", "").strip():
            raise ValueError(f"進捗の確認根拠がありません: {module['id']}")
    hidden = config["hidden_modules"]
    visible = set(ids) - set(hidden)
    if not set(hidden) <= set(ids) or len(hidden) != len(set(hidden)):
        raise ValueError("非表示の構成要素が不正です")
    if set(config["labels"]) != visible:
        raise ValueError("構成要素と図のラベルが一致しません。図設定.jsonも更新してください")
    if config["direction"] != "TB":
        raise ValueError("図は上から下のTB配置を使います")
    grouped = []
    for group in config["groups"]:
        if not ID.fullmatch(group["id"]):
            raise ValueError("グループIDが不正です")
        grouped.extend(group["modules"])
    if not set(grouped) <= visible or len(grouped) != len(set(grouped)):
        raise ValueError("グループの構成要素が重複または不明です")
    for edge in data["target_architecture"]["edges"]:
        if edge["from"] not in ids or edge["to"] not in ids:
            raise ValueError("接続先の構成要素が存在しません")
        if edge.get("diagram", True) and not {edge["from"], edge["to"]} <= visible:
            raise ValueError("表示する接続が非表示の構成要素を参照しています")
    svg = config["svg"]
    if set(svg["positions"]) != visible:
        raise ValueError("SVG配置と構成要素が一致しません")
    for name in ("width", "node_width", "node_height", "row_gap", "top"):
        value = svg[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError("SVG寸法が不正です")
    for position in svg["positions"].values():
        row = position["row"]
        if (position["column"] not in svg["columns"] or isinstance(row, bool)
                or not isinstance(row, int) or row < 0):
            raise ValueError("SVG配置が不正です")
    for value in svg["columns"].values():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("SVG列の位置が不正です")
    if (svg["row_gap"] < svg["node_height"] + 20
            or min(svg["columns"].values()) < svg["node_width"] / 2 + 20
            or max(svg["columns"].values()) + svg["node_width"] / 2 + 20 > svg["width"]):
        raise ValueError("SVGのノード間隔または余白が不足しています")


def load():
    data, config = read_json(ROOT / SOURCE), read_json(ROOT / CONFIG)
    validate(data, config)
    return data, config


def text_lines(label):
    return re.split(r"<br\s*/?>|\n", label)


def mermaid_label(text):
    return "<br/>".join(escape(line, quote=True) for line in text_lines(text))


def live_note(data):
    return "実機送信ゲート: " + ("有効（記録された検証条件を確認）" if data["execution_policy"]["live_motor_commands_enabled"] else "停止")


def render_mermaid(data, config):
    lines = ["flowchart TB"]
    grouped = {ident for group in config["groups"] for ident in group["modules"]}
    node = lambda ident: f'    {ident}["{mermaid_label(config["labels"][ident])}"]'
    for ident in config["labels"]:
        if ident not in grouped:
            lines.append(node(ident))
    for group in config["groups"]:
        lines.extend([f'    subgraph {group["id"]}["{mermaid_label(group["label"])}"]', "        direction TB"])
        lines.extend("    " + node(ident) for ident in group["modules"])
        lines.append("    end")
    for edge in data["target_architecture"]["edges"]:
        if edge.get("diagram", True):
            lines.append(f'    {edge["from"]} --> {edge["to"]}')
    for name, definition in data["status_definitions"].items():
        style = definition["style"]
        css = f'fill:{style["fill"]},stroke:{style["stroke"]},stroke-width:{style["stroke_width"]}px'
        if style.get("dash"):
            css += f',stroke-dasharray:{style["dash"]}'
        lines.append(f"    classDef {name} {css};")
        members = [module["id"] for module in data["modules"]
                   if module["status"] == name and module["id"] in config["labels"]]
        if members:
            lines.append(f'    class {",".join(members)} {name};')
    return "\n".join(lines)


def render_svg(data, config):
    settings = config["svg"]
    width, box_width, box_height = settings["width"], settings["node_width"], settings["node_height"]
    positions = {ident: (settings["columns"][position["column"]],
                         settings["top"] + position["row"] * settings["row_gap"])
                 for ident, position in settings["positions"].items()}
    height = max(y for _, y in positions.values()) + box_height / 2 + 65
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           f'<title id="title">{escape(config["title"])}</title>',
           '<desc id="desc">JSONの進捗状態から生成。既存実装は実機検証済みを意味しません。</desc>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>',
           f'<rect width="{width}" height="{height}" fill="#f8fafc"/>',
           '<g font-family="sans-serif" fill="#172536">',
           f'<text x="40" y="36" font-size="26" font-weight="bold">{escape(config["title"])}</text>',
           f'<text x="40" y="108" font-size="17">進捗更新日: {escape(data["updated_on"])} ／ {escape(live_note(data))}。線は目標構成の接続関係。</text>']
    for index, definition in enumerate(data["status_definitions"].values()):
        style = definition["style"]
        x = 40 + index * 247
        dash = f' stroke-dasharray="{style["dash"]}"' if style.get("dash") else ""
        out.append(f'<rect x="{x}" y="58" width="22" height="22" fill="{style["fill"]}" stroke="{style["stroke"]}"{dash}/>')
        out.append(f'<text x="{x + 31}" y="75" font-size="17">{escape(definition["label"])}</text>')
    for group in config["groups"]:
        x, y = positions[group["modules"][0]]
        on_left = x < settings["columns"]["main"]
        heading_x = x - box_width / 2 + 10 if on_left else x + box_width / 2 - 10
        anchor = "start" if on_left else "end"
        out.append(f'<text x="{heading_x}" y="{y - box_height / 2 - 15}" text-anchor="{anchor}" font-size="23" font-weight="bold">{escape(group["label"])}</text>')
    for edge in data["target_architecture"]["edges"]:
        if not edge.get("diagram", True):
            continue
        sx, sy = positions[edge["from"]]
        tx, ty = positions[edge["to"]]
        if sy == ty:
            direction = 1 if tx > sx else -1
            path = f'M {sx + direction * box_width / 2} {sy} H {tx - direction * box_width / 2}'
        else:
            start_y, end_y = sy + box_height / 2, ty - box_height / 2
            middle_y = (start_y + end_y) / 2
            path = f'M {sx} {start_y} V {middle_y} H {tx} V {end_y}'
        out.append(f'<path data-from="{edge["from"]}" data-to="{edge["to"]}" d="{path}" fill="none" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>')
    for module in data["modules"]:
        ident = module["id"]
        if ident not in positions:
            continue
        x, y = positions[ident]
        definition = data["status_definitions"][module["status"]]
        style = definition["style"]
        dash = f' stroke-dasharray="{style["dash"]}"' if style.get("dash") else ""
        out.append(f'<g data-module="{ident}" data-status="{module["status"]}">')
        out.append(f'<title>{escape(module["label"])}: {escape(definition["label"])}</title>')
        out.append(f'<rect x="{x - box_width / 2}" y="{y - box_height / 2}" width="{box_width}" height="{box_height}" rx="10" fill="{style["fill"]}" stroke="{style["stroke"]}" stroke-width="{style["stroke_width"]}"{dash}/>')
        labels = text_lines(config["labels"][ident])
        top = y - (len(labels) - 1) * 11 + 6
        for index, label in enumerate(labels):
            out.append(f'<text x="{x}" y="{top + index * 22}" text-anchor="middle" font-size="18">{escape(label)}</text>')
        out.append("</g>")
    out.extend(["</g>", "</svg>"])
    return "\n".join(out) + "\n"


def render_markdown(data, config, mermaid):
    counts = Counter(module["status"] for module in data["modules"])
    lines = [f'# {config["title"]}', "", f'進捗更新日: {data["updated_on"]}。色は[正本JSON](構成図.json)の進捗状態から生成します。',
             "", "[ブラウザ用HTML](構成図.html) · [タグ付きSVG](タグ付き構成図.svg) · [呼び出し方](README.md) · [呼び出しプロンプト](呼び出しプロンプト.md)",
             "", "既存実装は実機での完成を意味しません。" + live_note(data) + "。", "",
             "| 状態 | 件数 |", "| --- | ---: |"]
    for name, definition in data["status_definitions"].items():
        lines.append(f'| {definition["label"]} | {counts[name]} |')
    lines.extend(["", "```mermaid", mermaid, "```", "", "<details>", "<summary>構成要素ごとの進捗と確認根拠</summary>", "",
                  "| ID | 構成要素 | 状態 | 更新日 | 確認根拠 |", "| --- | --- | --- | --- | --- |"])
    cell = lambda value: str(value).replace("|", "&#124;").replace("\n", " ")
    for module in data["modules"]:
        progress = module["progress"]
        values = [module["id"], module["label"], data["status_definitions"][module["status"]]["label"], progress["updated_on"], progress["evidence"]]
        lines.append("| " + " | ".join(map(cell, values)) + " |")
    lines.extend(["", "</details>", ""])
    return "\n".join(lines)


def render_tagged_html(data, config, layout):
    return tagged.render_html(data, config, layout, (ROOT / TAG_TEMPLATE).read_text(encoding="utf-8"))


def build_outputs(data, config):
    validate(data, config)
    data = copy.deepcopy(data)
    mermaid = render_mermaid(data, config)
    data["target_architecture"]["diagram"]["source"] = mermaid
    serialized = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    plan = (ROOT / PLAN).read_text(encoding="utf-8")
    if plan.count(START) != 1 or plan.count(END) != 1 or plan.index(START) >= plan.index(END):
        raise ValueError("計画の構成図生成マーカーが不正です。既存文書を上書きしません")
    begin, finish = plan.index(START), plan.index(END) + len(END)
    section = START + "\n```mermaid\n" + mermaid + "\n```\n" + END
    layout = read_json(ROOT / TAG_LAYOUT)
    return {
        SOURCE: serialized,
        "docs/shogi-go-architecture-plan.json": serialized,
        "構成図/構成図.mmd": mermaid + "\n",
        "構成図/構成図.md": render_markdown(data, config, mermaid),
        "構成図/構成図.svg": render_svg(data, config),
        TAG_HTML: render_tagged_html(data, config, layout),
        TAG_SVG: tagged.render_svg(data, config, layout),
        PLAN: plan[:begin] + section + plan[finish:],
    }


def sync(data, config, check=False):
    outputs = build_outputs(data, config)
    changed = [relative for relative, content in outputs.items()
               if not (ROOT / relative).exists()
               or (ROOT / relative).read_text(encoding="utf-8") != content]
    if check:
        if changed:
            raise ValueError("再生成が必要です: " + ", ".join(changed))
        return changed
    for relative in changed:
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".diagram-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(outputs[relative])
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return changed


def set_status(data, ident, status, evidence):
    if status not in data["status_definitions"]:
        raise ValueError(f"未知の進捗状態: {status}")
    if not evidence.strip():
        raise ValueError("状態更新には確認根拠が必要です")
    module = next((item for item in data["modules"] if item["id"] == ident), None)
    if module is None:
        raise ValueError(f"未知の構成要素: {ident}")
    now = datetime.now(timezone(timedelta(hours=9)))
    progress = module["progress"]
    progress.setdefault("history", []).append({"from": module["status"], "to": status,
                                               "updated_at": now.isoformat(), "evidence": evidence.strip()})
    progress.update(updated_on=now.date().isoformat(), evidence=evidence.strip())
    module["status"] = status
    data["updated_on"] = now.date().isoformat()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    show = commands.add_parser("show", help="最新JSONから図を標準出力へ表示")
    show.add_argument("--format", choices=("markdown", "mermaid", "svg", "html", "tagged-svg"), default="markdown")
    commands.add_parser("open", help="最新のタグ付き構成図を生成してブラウザで開く（通信不要）")
    commands.add_parser("sync", help="JSON・図・計画資料を再生成")
    commands.add_parser("check", help="生成物がJSONと一致するか確認（変更しない）")
    commands.add_parser("list", help="構成要素IDと進捗を一覧表示")
    update = commands.add_parser("set-status", help="確認根拠と進捗を記録し、図の色も更新")
    update.add_argument("module")
    update.add_argument("status")
    update.add_argument("--evidence", required=True)
    args = parser.parse_args(argv)
    try:
        data, config = load()
        command = args.command or "show"
        if command == "show":
            output_format = getattr(args, "format", "markdown")
            if output_format == "svg":
                print(render_svg(data, config), end="")
            elif output_format == "html":
                print(render_tagged_html(data, config, read_json(ROOT / TAG_LAYOUT)), end="")
            elif output_format == "tagged-svg":
                print(tagged.render_svg(data, config, read_json(ROOT / TAG_LAYOUT)), end="")
            else:
                diagram = render_mermaid(data, config)
                print(diagram if output_format == "mermaid" else "```mermaid\n" + diagram + "\n```")
        elif command == "list":
            for module in data["modules"]:
                print(f'{module["id"]}\t{module["status"]}\t{module["label"]}')
        else:
            if command == "set-status":
                set_status(data, args.module, args.status, args.evidence)
            changed = sync(data, config, check=command == "check")
            print("構成図は最新です。" if not changed else "更新: " + ", ".join(changed))
            if command == "open":
                target = (ROOT / TAG_HTML).as_uri()
                if not webbrowser.open(target):
                    print("ブラウザで開いてください: " + target)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("構成図: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
