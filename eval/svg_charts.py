"""Minimal SVG chart helpers — no plotting dependency required.

SVG is deliberate rather than a fallback: the output stays crisp at any zoom in
a report or slide deck, and the files are diff-able text in Git.
"""

BLUE = "#2563eb"
GREEN = "#16a34a"
AMBER = "#d97706"
RED = "#dc2626"
GREY = "#6b7280"
LIGHT = "#e5e7eb"
INK = "#1f2937"

FONT = "font-family='-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif'"


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _wrap(width, height, body, title=None):
    head = ""
    if title:
        head = (f"<text x='{width/2}' y='24' text-anchor='middle' {FONT} "
                f"font-size='15' font-weight='600' fill='{INK}'>{_esc(title)}</text>")
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
            f"viewBox='0 0 {width} {height}'>"
            f"<rect width='{width}' height='{height}' fill='white'/>{head}{body}</svg>")


def hbar(title, rows, unit="", width=720, colour=BLUE, note=None):
    """rows: [(label, value, optional_colour), ...] — horizontal bars."""
    top, row_h, gap = 46, 26, 10
    label_w, right_pad = 250, 90
    plot_w = width - label_w - right_pad
    height = top + len(rows) * (row_h + gap) + (34 if note else 14)
    vmax = max([r[1] for r in rows] + [1e-9])

    body = []
    for i, row in enumerate(rows):
        label, value = row[0], row[1]
        col = row[2] if len(row) > 2 else colour
        y = top + i * (row_h + gap)
        w = max(1.0, plot_w * (value / vmax))
        body.append(f"<text x='{label_w - 10}' y='{y + 17}' text-anchor='end' {FONT} "
                    f"font-size='12.5' fill='{INK}'>{_esc(label)}</text>")
        body.append(f"<rect x='{label_w}' y='{y}' width='{plot_w}' height='{row_h}' "
                    f"fill='{LIGHT}' rx='3'/>")
        body.append(f"<rect x='{label_w}' y='{y}' width='{w:.1f}' height='{row_h}' "
                    f"fill='{col}' rx='3'/>")
        body.append(f"<text x='{label_w + plot_w + 8}' y='{y + 17}' {FONT} "
                    f"font-size='12.5' font-weight='600' fill='{INK}'>{value:g}{unit}</text>")
    if note:
        body.append(f"<text x='{label_w}' y='{height - 12}' {FONT} font-size='11' "
                    f"fill='{GREY}'>{_esc(note)}</text>")
    return _wrap(width, height, "".join(body), title)


def stacked(title, segments, width=720, note=None):
    """segments: [(label, value, colour), ...] — one horizontal 100% bar + legend."""
    total = sum(s[1] for s in segments) or 1
    bar_y, bar_h = 52, 40
    x, body = 40, []
    plot_w = width - 80
    for label, value, colour in segments:
        w = plot_w * value / total
        if w > 0:
            body.append(f"<rect x='{x:.1f}' y='{bar_y}' width='{w:.1f}' height='{bar_h}' fill='{colour}'/>")
            if w > 38:
                body.append(f"<text x='{x + w/2:.1f}' y='{bar_y + 25}' text-anchor='middle' "
                            f"{FONT} font-size='12.5' font-weight='600' fill='white'>{value}</text>")
        x += w

    ly, lx = bar_y + bar_h + 26, 40
    for label, value, colour in segments:
        pct = 100 * value / total
        body.append(f"<rect x='{lx}' y='{ly - 9}' width='11' height='11' fill='{colour}' rx='2'/>")
        text = f"{label} — {value} ({pct:.0f}%)"
        body.append(f"<text x='{lx + 17}' y='{ly}' {FONT} font-size='12' fill='{INK}'>{_esc(text)}</text>")
        ly += 20
    height = ly + (24 if note else 8)
    if note:
        body.append(f"<text x='40' y='{height - 10}' {FONT} font-size='11' fill='{GREY}'>{_esc(note)}</text>")
    return _wrap(width, height, "".join(body), title)


def histogram(title, values, bins=10, width=720, height=300, colour=BLUE,
              xlabel="", note=None):
    lo, hi = min(values), max(values)
    if hi == lo:
        hi = lo + 1
    edges = [lo + (hi - lo) * i / bins for i in range(bins + 1)]
    counts = [0] * bins
    for v in values:
        idx = min(bins - 1, int((v - lo) / (hi - lo) * bins))
        counts[idx] += 1
    cmax = max(counts) or 1

    left, right, top, bottom = 52, 20, 46, 52
    plot_w, plot_h = width - left - right, height - top - bottom
    bw = plot_w / bins
    body = [f"<line x1='{left}' y1='{top + plot_h}' x2='{left + plot_w}' y2='{top + plot_h}' "
            f"stroke='{GREY}' stroke-width='1'/>"]
    for i, c in enumerate(counts):
        h = plot_h * c / cmax
        x = left + i * bw
        body.append(f"<rect x='{x + 1:.1f}' y='{top + plot_h - h:.1f}' width='{bw - 2:.1f}' "
                    f"height='{h:.1f}' fill='{colour}' rx='2'/>")
        if c:
            body.append(f"<text x='{x + bw/2:.1f}' y='{top + plot_h - h - 5:.1f}' "
                        f"text-anchor='middle' {FONT} font-size='11' fill='{INK}'>{c}</text>")
    for i in range(bins + 1):
        if i % 2 == 0:
            x = left + i * bw
            body.append(f"<text x='{x:.1f}' y='{top + plot_h + 16}' text-anchor='middle' "
                        f"{FONT} font-size='10.5' fill='{GREY}'>{edges[i]:.1f}</text>")
    if xlabel:
        body.append(f"<text x='{left + plot_w/2}' y='{height - 18}' text-anchor='middle' "
                    f"{FONT} font-size='11.5' fill='{INK}'>{_esc(xlabel)}</text>")
    if note:
        body.append(f"<text x='{left}' y='{height - 4}' {FONT} font-size='10.5' fill='{GREY}'>{_esc(note)}</text>")
    return _wrap(width, height, "".join(body), title)


def strip(title, groups, threshold=None, width=720, height=290,
          xlabel="", note=None):
    """groups: [(label, [values], colour), ...] — 1-D scatter, good for showing
    class separation (e.g. in-scope vs out-of-scope retrieval scores)."""
    allv = [v for _, vals, _ in groups for v in vals]
    lo, hi = min(allv), max(allv)
    pad = (hi - lo) * 0.12 or 0.1
    lo, hi = lo - pad, hi + pad

    left, right, top = 120, 30, 50
    plot_w = width - left - right
    lane_h = 52

    def sx(v):
        return left + plot_w * (v - lo) / (hi - lo)

    body = []
    if threshold is not None:
        tx = sx(threshold)
        body.append(f"<line x1='{tx:.1f}' y1='{top - 6}' x2='{tx:.1f}' "
                    f"y2='{top + len(groups)*lane_h + 4}' stroke='{RED}' "
                    f"stroke-width='1.6' stroke-dasharray='5,4'/>")
        body.append(f"<text x='{tx:.1f}' y='{top - 12}' text-anchor='middle' {FONT} "
                    f"font-size='11' font-weight='600' fill='{RED}'>seuil {threshold}</text>")

    for gi, (label, vals, colour) in enumerate(groups):
        cy = top + gi * lane_h + lane_h / 2
        body.append(f"<text x='{left - 12}' y='{cy + 4}' text-anchor='end' {FONT} "
                    f"font-size='12' fill='{INK}'>{_esc(label)}</text>")
        body.append(f"<line x1='{left}' y1='{cy}' x2='{left + plot_w}' y2='{cy}' "
                    f"stroke='{LIGHT}' stroke-width='1'/>")
        for j, v in enumerate(vals):
            jitter = ((j % 5) - 2) * 3.4
            body.append(f"<circle cx='{sx(v):.1f}' cy='{cy + jitter:.1f}' r='4.5' "
                        f"fill='{colour}' fill-opacity='0.75'/>")

    axis_y = top + len(groups) * lane_h + 16
    body.append(f"<line x1='{left}' y1='{axis_y}' x2='{left + plot_w}' y2='{axis_y}' "
                f"stroke='{GREY}' stroke-width='1'/>")
    for i in range(6):
        v = lo + (hi - lo) * i / 5
        body.append(f"<text x='{sx(v):.1f}' y='{axis_y + 15}' text-anchor='middle' "
                    f"{FONT} font-size='10.5' fill='{GREY}'>{v:.2f}</text>")
    if xlabel:
        body.append(f"<text x='{left + plot_w/2}' y='{axis_y + 34}' text-anchor='middle' "
                    f"{FONT} font-size='11.5' fill='{INK}'>{_esc(xlabel)}</text>")
    if note:
        body.append(f"<text x='{left - 100}' y='{height - 6}' {FONT} font-size='10.5' fill='{GREY}'>{_esc(note)}</text>")
    return _wrap(width, max(height, axis_y + 46), "".join(body), title)


def grouped_bars(title, categories, series, width=720, height=320, unit="",
                 note=None):
    """categories: [str]; series: [(name, [values], colour), ...]"""
    left, right, top, bottom = 52, 24, 52, 66
    plot_w, plot_h = width - left - right, height - top - bottom
    vmax = max(v for _, vals, _ in series for v in vals) or 1
    gw = plot_w / len(categories)
    bw = gw / (len(series) + 0.6)

    body = [f"<line x1='{left}' y1='{top + plot_h}' x2='{left + plot_w}' "
            f"y2='{top + plot_h}' stroke='{GREY}' stroke-width='1'/>"]
    for ci, cat in enumerate(categories):
        for si, (name, vals, colour) in enumerate(series):
            v = vals[ci]
            h = plot_h * v / vmax
            x = left + ci * gw + 0.3 * bw + si * bw
            body.append(f"<rect x='{x:.1f}' y='{top + plot_h - h:.1f}' width='{bw - 3:.1f}' "
                        f"height='{h:.1f}' fill='{colour}' rx='2'/>")
            body.append(f"<text x='{x + (bw-3)/2:.1f}' y='{top + plot_h - h - 5:.1f}' "
                        f"text-anchor='middle' {FONT} font-size='10.5' fill='{INK}'>{v:g}{unit}</text>")
        body.append(f"<text x='{left + ci*gw + gw/2:.1f}' y='{top + plot_h + 17}' "
                    f"text-anchor='middle' {FONT} font-size='12' fill='{INK}'>{_esc(cat)}</text>")

    lx = left
    ly = height - 26
    for name, _, colour in series:
        body.append(f"<rect x='{lx}' y='{ly - 9}' width='11' height='11' fill='{colour}' rx='2'/>")
        body.append(f"<text x='{lx + 16}' y='{ly}' {FONT} font-size='11.5' fill='{INK}'>{_esc(name)}</text>")
        lx += 22 + 7.2 * len(name)
    if note:
        body.append(f"<text x='{left}' y='{height - 6}' {FONT} font-size='10.5' fill='{GREY}'>{_esc(note)}</text>")
    return _wrap(width, height, "".join(body), title)
