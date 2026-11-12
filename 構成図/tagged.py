"""Render the tagged architecture for browsers and for GitHub's SVG image viewer."""
from collections import defaultdict
from html import escape
from unicodedata import east_asian_width


def all_parts(layout):
    for stage in layout["stages"]:
        for row in stage["rows"]:
            for part in row["parts"]:
                yield stage["tag"], part
    for tag, key in (("対局管理", "management"), ("開発支援", "support")):
        for group in layout[key]:
            for part in group["parts"]:
                yield tag, part


def validate(layout, modules, config):
    scopes = layout["scopes"]
    if scopes != ["統合", "チェス", "囲碁", "将棋"]:
        raise ValueError("タグ付き構成図の対象と列順が不正です")
    ids = set()
    covered = set()
    for stage, part in all_parts(layout):
        key = (part["scope"], stage, part["tag"])
        if key in ids or key[0] not in scopes or any(not text or any(c.isspace() or c == "#" for c in text) for text in key):
            raise ValueError(f"タグの組が重複または不正です: {key}")
        ids.add(key)
        module_id = part.get("module_id")
        related = part.get("related_module_ids", [])
        if module_id:
            covered.add(module_id)
        if not set(related) | ({module_id} if module_id else set()) <= modules.keys():
            raise ValueError(f"タグの構成要素IDが不正です: {key}")
    if not config["labels"].keys() <= covered:
        raise ValueError("既存の構成要素に対応するタグがありません: " + ", ".join(sorted(config["labels"].keys() - covered)))
    for stage in layout["stages"]:
        for row in stage["rows"]:
            counts = [part["scope"] for part in row["parts"] if part["scope"] != "統合"]
            if not row["parts"] or len(counts) != len(set(counts)):
                raise ValueError(f"行の配置が不正です: {stage['tag']} / {row['label']}")


def groups_in_row(row, scopes):
    by_scope = defaultdict(list)
    for part in row["parts"]:
        by_scope[part["scope"]].append(part)
    return by_scope["統合"], [by_scope[scope] for scope in scopes[1:]]


def part_status(part, modules):
    return modules[part["module_id"]]["status"] if "module_id" in part else "review"


def part_tags(stage, part):
    return (part["scope"], stage, part["tag"])


def gate_label(data):
    return "有効" if data["execution_policy"]["live_motor_commands_enabled"] else "停止"


def render_html(data, config, layout, template):
    modules = {module["id"]: module for module in data["modules"]}
    validate(layout, modules, config)

    def card(stage, part, show_part=False):
        scope, stage, tag = part_tags(stage, part)
        ident = escape("part-" + "-".join((scope, stage, tag)))
        tags = escape(f"#{scope} #{stage} #{tag}")
        chip = escape(f"#{scope} #{tag}" if show_part else f"#{scope}")
        title, detail = escape(part["title"]), escape(part["description"])
        status = part_status(part, modules)
        source = f' data-source-module="{escape(part["module_id"])}"' if "module_id" in part else ""
        return (f'<article id="{ident}" class="part {status}" data-scope="{escape(scope)}" '
                f'data-stage="{escape(stage)}" data-part="{escape(tag)}"{source} title="{tags}" '
                f'aria-label="{title} {tags}"><span class="part-tag">{chip}</span>'
                f'<h4>{title}</h4><p>{detail}</p></article>')

    def utility(key, tag, footer=""):
        sections = []
        for group in layout[key]:
            parts = "".join(card(tag, part, True) for part in group["parts"])
            sections.append(f'<section><h3>{escape(group["title"])}</h3>{parts}</section>')
        return (f'<section class="utility {key}" id="{key}"><h2>#{tag}</h2>'
                f'<div class="utility-grid">{"".join(sections)}</div>{footer}</section>')

    styles, legend = [], []
    for status, definition in data["status_definitions"].items():
        style = definition["style"]
        edge = "dashed" if style.get("dash") else "solid"
        styles.append(f'.{status}{{--fill:{style["fill"]};--stroke:{style["stroke"]};--edge:{edge};--weight:{style["stroke_width"]}px}}')
        legend.append(f'<li><i class="{status}"></i>{escape(definition["label"])}</li>')
    legend.append('<li><i class="review"></i>細分案</li>')
    stages = layout["stages"]
    nav = [("management", "対局管理"), *[(stage["id"], stage["tag"]) for stage in stages], ("support", "開発支援")]
    nav_links = "".join(f'<a href="#{escape(ident)}">{escape(label)}</a>' for ident, label in nav)
    title = escape(config["title"])
    body = [f'<header><h1>{title}</h1><p>進捗更新日 {escape(data["updated_on"])}　／　実機送信ゲート {gate_label(data)}</p>'
            f'<ul class="legend" aria-label="進捗の凡例">{"".join(legend)}</ul>'
            f'<nav aria-label="段階へ移動">{nav_links}</nav></header>',
            utility("management", "対局管理"), '<div class="flow">',
            '<div class="column-head"><span>段階・パーツ</span>',
            *[f'<span>#{escape(scope)}</span>' for scope in layout["scopes"][1:]], '</div>']
    for stage in stages:
        tag = stage["tag"]
        body.append(f'<section class="phase" id="{escape(stage["id"])}" aria-label="{escape(tag)}"><h2>#{escape(tag)}</h2>')
        for row in stage["rows"]:
            label = row["label"]
            shared, games = groups_in_row(row, layout["scopes"])
            body.append(f'<div class="substep"><h3>#{escape(label)}</h3><div class="lane">')
            if shared:
                body.extend(['<div class="shared">', *[card(tag, part, part["tag"] != label) for part in shared], '</div>'])
            if any(games):
                body.append('<div class="game-band">')
                for parts in games:
                    body.append('<div class="game-cell">' + "".join(card(tag, part) for part in parts) + '</div>')
                body.append('</div>')
            body.append('</div></div>')
        body.append('</section>')
        if stage["id"] == "engine":
            body.append('<aside class="branch">パス・投了・終局 → <a href="#management">対局管理</a></aside>')
    body.extend(['</div>', utility("support", "開発支援",
        '<ul class="connections"><li>寸法モデル → <a href="#part-統合-動作計画-経路検証">経路検証</a></li>'
        '<li>静止教示 → 連続教示 → 教示経路候補 → <a href="#part-統合-動作計画-経路生成">経路生成</a></li></ul>'),
        '<footer>実線は対局の流れ、破線の矢印は機械モデル・教示の入力です。進捗色は正本JSONに対応し、灰色は独立した進捗記録のない細分案です。</footer>'])
    return template.replace("<!-- TITLE -->", title).replace("<!-- STATUS_STYLES -->", "".join(styles)).replace("<!-- CONTENT -->", "\n".join(body))


def wrap(text, units):
    lines, start, width = [], 0, 0
    for index, character in enumerate(text):
        size = 2 if east_asian_width(character) in "WFA" else 1
        if width + size > units:
            lines.append(text[start:index])
            start, width = index, 0
        width += size
    return lines + [text[start:]]


def render_svg(data, config, layout):
    modules = {module["id"]: module for module in data["modules"]}
    validate(layout, modules, config)
    styles = {status: value["style"] for status, value in data["status_definitions"].items()}
    styles["review"] = {"fill": "#f3f5f7", "stroke": "#c2ccd6", "stroke_width": 1}
    width, left, right, gap = 1440, 206, 1410, 14
    marks, edges = [], []
    by_module = {}

    def label(x, y, value, size=16, weight=400):
        return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}">{escape(value)}</text>'

    def rect(x, y, w, h, style, radius=6):
        dash = f' stroke-dasharray="{style["dash"]}"' if style.get("dash") else ""
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
                f'fill="{style["fill"]}" stroke="{style["stroke"]}" stroke-width="{style["stroke_width"]}"{dash}/>')

    def copy_lines(part, w):
        return wrap(part["description"], int((w - 24) / 8.5))

    def card(stage, part, x, y, w, h):
        tags = " ".join("#" + tag for tag in part_tags(stage, part))
        status = part_status(part, modules)
        marks.append(f'<g data-tags="{escape(tags)}" data-status="{status}"><title>{escape(tags)}</title>')
        marks.append(rect(x, y, w, h, styles[status]))
        marks.append(label(x + 12, y + 19, f'#{part["scope"]} #{part["tag"]}', 13, 600))
        marks.append(label(x + 12, y + 42, part["title"], 19, 600))
        for index, line in enumerate(copy_lines(part, w)):
            marks.append(label(x + 12, y + 63 + 19 * index, line, 16))
        marks.append("</g>")
        box = (x, y, w, h, part["scope"])
        if part.get("module_id"):
            by_module[part["module_id"]] = box
        return box

    def edge(d, arrow=False, dashed=False):
        marker = ' marker-end="url(#arrow)"' if arrow else ""
        dash = ' stroke-dasharray="6 5"' if dashed else ""
        edges.append(f'<path d="{d}"{marker}{dash}/>')

    def connect(starts, ends):
        cy = (max(y + h for _, y, _, h, _ in starts) + min(y for _, y, _, _, _ in ends)) / 2
        if len(starts) == len(ends) and [box[4] for box in starts] == [box[4] for box in ends]:
            for (x, y, w, h, _), (ex, ey, ew, _, _) in zip(starts, ends):
                edge(f"M {x + w / 2} {y + h} V {cy} H {ex + ew / 2} V {ey - 2}", True)
            return
        centers = [x + w / 2 for x, _, w, _, _ in starts + ends]
        edge(f"M {min(centers)} {cy} H {max(centers)}")
        for x, y, w, h, _ in starts:
            edge(f"M {x + w / 2} {y + h} V {cy}")
        for x, y, w, _, _ in ends:
            edge(f"M {x + w / 2} {cy} V {y - 2}", True)

    def utility(key, tag, y):
        marks.append(label(30, y + 21, f"#{tag}", 21, 700))
        y += 35
        groups = layout[key]
        column = (right - 30 - gap * (len(groups) - 1)) / len(groups)
        boxes = []
        for index, group in enumerate(groups):
            x = 30 + index * (column + gap)
            marks.append(label(x, y + 20, group["title"], 17, 650))
            marks_y = y + 29
            for part in group["parts"]:
                height = 72 + 19 * (len(copy_lines(part, column)) - 1)
                card(tag, part, x, marks_y, column, height)
                marks_y += height + 7
            boxes.append((x, y, column, marks_y - y - 7, ""))
        return boxes, max(y + h for _, y, _, h, _ in boxes) + 32

    marks.append(label(30, 37, config["title"], 27, 700))
    marks.append(label(30, 66, f'進捗更新日 {data["updated_on"]} ／ 実機送信ゲート {gate_label(data)}', 16))
    for index, (status, style) in enumerate(styles.items()):
        x = 30 + 175 * index
        marks.append(rect(x, 84, 16, 16, style, 2))
        marks.append(label(x + 23, 98, data["status_definitions"].get(status, {"label": "細分案"})["label"], 14))
    management, y = utility("management", "対局管理", 120)
    edge(f"M {management[0][0] + management[0][2]} {management[0][1] + 13} H {management[1][0] - 2}", True)
    scopes = layout["scopes"]
    column = (right - left - 2 * gap) / 3
    for index, scope in enumerate(scopes[1:]):
        marks.append(label(left + index * (column + gap) + 12, y + 20, f"#{scope}", 19, 700))
    y += 33

    previous = []
    first_box = None
    for stage in layout["stages"]:
        tag = stage["tag"]
        marks.append(rect(30, y, right - 30, 32, {"fill": "#e4eaf0", "stroke": "#e4eaf0", "stroke_width": 1}))
        marks.append(label(42, y + 23, f"#{tag}", 20, 700))
        y += 45
        for row in stage["rows"]:
            marks.append(label(42, y + 22, f'#{row["label"]}', 16, 600))
            shared, games = groups_in_row(row, scopes)
            bands = []
            if shared:
                bands.append(shared)
            if any(games):
                bands.append([parts[0] if parts else None for parts in games])
            for band in bands:
                w = (right - left - gap * (len(band) - 1)) / len(band)
                h = 72 + 19 * (max(len(copy_lines(part, w)) for part in band if part) - 1)
                boxes = [card(tag, part, left + i * (w + gap), y, w, h)
                         for i, part in enumerate(band) if part]
                if previous:
                    connect(previous, boxes)
                else:
                    first_box = boxes[0]
                previous = boxes
                y += h + 23
        if stage["id"] == "engine":
            marks.append(label(42, y - 5, "パス・投了・終局 → 対局管理", 13))
            y += 13
    support, end = utility("support", "開発支援", y + 5)
    for start, target in zip(support[1:], support[2:]):
        edge(f"M {start[0] + start[2]} {start[1] + 13} H {target[0] - 2}", True, True)

    def around(start, target, rail, bridge, dashed=False):
        x, y, w, h, _ = start
        tx, ty, tw, th, _ = target
        entry = tx - 2 if rail < tx else tx + tw + 2
        edge(f"M {x + w / 2} {y + h} V {bridge} H {rail} V {ty + th / 2} H {entry}", True, dashed)

    around(management[1], first_box, 1425, management[1][1] + management[1][3] + 10)
    around(support[0], by_module["simulation"], 14, end - 15, True)
    around(support[3], by_module["motion_integration"], 1425, end - 15, True)
    marks.append(label(30, end + 14, "実線の矢印は対局の流れ、破線の矢印は機械モデル・教示の入力。灰色は独立した進捗記録のない細分案。", 14))
    height = end + 35
    title = escape(config["title"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="diagram-title">'
            f'<title id="diagram-title">{title}</title><rect width="{width}" height="{height}" fill="#f8fafc"/>'
            '<defs><marker id="arrow" viewBox="0 0 8 8" refX="7.5" refY="4" markerWidth="9" markerHeight="9" orient="auto" markerUnits="userSpaceOnUse">'
            '<path d="M 0 0 L 8 4 L 0 8 Z" fill="#526578"/></marker></defs>'
            '<g font-family="sans-serif" fill="#172536">\n' + "\n".join(marks) + '</g>\n'
            '<g fill="none" stroke="#526578" stroke-width="1.7">\n' + "\n".join(edges) + '</g></svg>\n')

