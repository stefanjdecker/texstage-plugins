# SPDX-License-Identifier: Apache-2.0
"""Deterministic page geometry and trusted TikZ for checked stable trees."""
from collections import deque

WIDTH = 138.0
GAP = 3.0
HEIGHT = 9.6


def page_width(node):
    # Conservative monospace glyph allowance, including signed four-digit keys.
    keys = " | ".join(map(str, node["keys"])) or "(empty)"
    pointers = " ".join("P" + str(i) for i in node.get("children", []))
    return max(20.0, 5.0 + 1.48 * max(len(keys), len(pointers)))


def geometry(tree):
    nodes = {node["id"]: node for node in tree["nodes"]}
    order, depths = [], {}
    queue = deque([(tree["root"], 0)])
    while queue:
        page, depth = queue.popleft()
        order.append(page)
        depths[page] = depth
        queue.extend((child, depth + 1) for child in nodes[page].get("children", []))
    spans = {}

    def span(page):
        children = nodes[page].get("children", [])
        spans[page] = max(page_width(nodes[page]), sum(span(c) for c in children) + GAP * max(0, len(children) - 1))
        return spans[page]

    width = span(tree["root"])
    positions = {}
    if width <= WIDTH and max(depths.values()) <= 2:
        mode = "tree"

        def place(page, left):
            positions[page] = {"x": left + spans[page] / 2, "y": depths[page] * 16,
                               "width": page_width(nodes[page]), "depth": depths[page]}
            children = nodes[page].get("children", [])
            total = sum(spans[c] for c in children) + GAP * max(0, len(children) - 1)
            child_left = left + (spans[page] - total) / 2
            for child in children:
                place(child, child_left)
                child_left += spans[child] + GAP

        place(tree["root"], (WIDTH - width) / 2)
    else:
        # A breadth-first page map has no crossing long edges or tiny global zoom.
        # Every page retains its depth and exact child / next-leaf pointers.
        mode, x, y = "map", 0.0, 0.0
        for page in order:
            size = page_width(nodes[page])
            if x and x + size > WIDTH:
                x, y = 0.0, y + HEIGHT + 2.0
            positions[page] = {"x": x + size / 2, "y": y, "width": size, "depth": depths[page]}
            x += size + GAP
    return {"mode": mode, "width": WIDTH, "height": max(p["y"] for p in positions.values()) + HEIGHT,
            "order": order, "pages": positions}


def tikz(tree, *, highlighted=(), key=None):
    shape = geometry(tree)
    nodes = {n["id"]: n for n in tree["nodes"]}
    selected = set(highlighted)
    lines = [r"{\centering\resizebox{\linewidth}{!}{%",
             r"\begin{tikzpicture}[x=1mm,y=-1mm,line width=.4pt]",
             rf"\path[use as bounding box] (0,{-HEIGHT / 2:.2f}) rectangle ({WIDTH:.2f},{shape['height'] - HEIGHT / 2:.2f});"]
    if shape["mode"] == "tree":
        for parent in shape["order"]:
            for child in nodes[parent].get("children", []):
                p, c = shape["pages"][parent], shape["pages"][child]
                lines.append(rf"\draw[->,draw=black!55] ({p['x']:.2f},{p['y'] + HEIGHT / 2:.2f}) -- ({c['x']:.2f},{c['y'] - HEIGHT / 2:.2f});")
    for page in shape["order"]:
        node, pos = nodes[page], shape["pages"][page]
        leaf = node["kind"] == "leaf"
        fill = "green!7!white" if leaf else "blue!6!white"
        stroke = "blue!80!black,line width=1pt" if page in selected else "black!65"
        label = f"P{page} " + ("L" if leaf else "I")
        if shape["mode"] == "map":
            label += f" / d{pos['depth']}"
        keys = [r"\textbf{" + str(k) + "}" if k == key else str(k) for k in node["keys"]]
        entries = r"\,|\, ".join(keys) if keys else r"\textnormal{(empty)}"
        if leaf:
            pointers = r"$\rightarrow$ " + (f"P{node['next']}" if node["next"] is not None else r"$\varnothing$")
        else:
            pointers = r"$\downarrow$ " + r"\;".join(f"P{i}" for i in node["children"])
        content = (r"{\fontsize{7}{8}\selectfont\bfseries " + label + r"}\\[-.2ex]" +
                   r"{\fontsize{8}{9}\selectfont\ttfamily " + entries + r"}\\[-.2ex]" +
                   r"{\fontsize{6.8}{7.5}\selectfont " + pointers + "}")
        lines.append(rf"\node[draw={stroke},fill={fill},rounded corners=.6mm,align=center,inner sep=.5mm,"
                     rf"minimum height={HEIGHT:.2f}mm,text width={pos['width'] - 2:.2f}mm] "
                     rf"(p{page}) at ({pos['x']:.2f},{pos['y']:.2f}) {{{content}}};")
    lines += [r"\end{tikzpicture}}\par}"]
    return "\n".join(lines), shape["mode"]
