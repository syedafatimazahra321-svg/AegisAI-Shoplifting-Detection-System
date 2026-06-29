"""
report_generator.py — Daily PDF report for AegisAI
Matches dashboard logic exactly:
  - confirmed   : suspicion_score >= 0.7 AND is_false_alarm = 0
  - pending     : suspicion_score >= 0.55 AND < 0.7 AND is_false_alarm = 0
  - false alarm : is_false_alarm = 1  OR  score < 0.55
Run: python report_generator.py
"""

import os
import sqlite3
from datetime import datetime, date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)

# ── Paths ─────────────────────────────────────────────────────────────────
_BASE   = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE, "incidents", "shieldeye.db")
OUT     = os.path.join(_BASE, "incidents", "daily_report.pdf")

# ── Brand colors (match dashboard CSS) ────────────────────────────────────
C_DEEP    = colors.HexColor("#060d18")
C_PANEL   = colors.HexColor("#0b1627")
C_CARD    = colors.HexColor("#0f1e33")
C_CYAN    = colors.HexColor("#00d4ff")
C_RED     = colors.HexColor("#ff4d6d")
C_AMBER   = colors.HexColor("#f59e0b")
C_GREEN   = colors.HexColor("#10b981")
C_TEXT    = colors.HexColor("#e2eaf5")
C_MUTED   = colors.HexColor("#9ab4cc")
C_BORDER  = colors.HexColor("#1a3a5c")
C_WHITE   = colors.white
C_ROW_ALT = colors.HexColor("#0d1e32")

# ── Status logic — identical to dashboard ─────────────────────────────────
def get_status(row):
    """row = sqlite3.Row with suspicion_score and is_false_alarm"""
    if row["is_false_alarm"]:
        return "FALSE ALARM"
    score = float(row["suspicion_score"])
    if score >= 0.7:
        return "CONFIRMED"
    if score >= 0.55:
        return "PENDING"
    return "FALSE ALARM"

# ── Paragraph styles ───────────────────────────────────────────────────────
def make_styles():
    s = {}
    s["title"] = ParagraphStyle(
        "Title",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=C_CYAN,
        spaceAfter=2,
        leading=26,
    )
    s["subtitle"] = ParagraphStyle(
        "Subtitle",
        fontName="Helvetica",
        fontSize=10,
        textColor=C_MUTED,
        spaceAfter=0,
    )
    s["section"] = ParagraphStyle(
        "Section",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=C_TEXT,
        spaceBefore=16,
        spaceAfter=8,
    )
    s["body"] = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=9,
        textColor=C_MUTED,
        leading=14,
    )
    s["footer"] = ParagraphStyle(
        "Footer",
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=C_MUTED,
        alignment=1,  # center
    )
    s["cell"] = ParagraphStyle(
        "Cell",
        fontName="Helvetica",
        fontSize=8,
        textColor=C_TEXT,
        leading=10,
    )
    return s

# ── Table border helper ────────────────────────────────────────────────────
def _border(color=C_BORDER, width=0.5):
    return ("GRID", (0, 0), (-1, -1), width, color)

# ── Generate ───────────────────────────────────────────────────────────────
def generate_report():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    conn  = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    today = str(date.today())

    all_rows = conn.execute(
        "SELECT * FROM incidents ORDER BY timestamp"
    ).fetchall()
    today_rows = conn.execute(
        "SELECT * FROM incidents WHERE timestamp LIKE ? ORDER BY timestamp",
        (f"{today}%",)
    ).fetchall()
    conn.close()

    # ── Stats using dashboard logic ────────────────────────────────────────
    def compute_stats(rows):
        total     = len(rows)
        confirmed = sum(1 for r in rows if get_status(r) == "CONFIRMED")
        pending   = sum(1 for r in rows if get_status(r) == "PENDING")
        fa        = sum(1 for r in rows if get_status(r) == "FALSE ALARM")
        fa_rate   = fa / max(total, 1)
        return total, confirmed, pending, fa, fa_rate

    t_total, t_conf, t_pend, t_fa, t_fa_rate = compute_stats(today_rows)
    a_total, a_conf, a_pend, a_fa, a_fa_rate = compute_stats(all_rows)

    # Busiest hour (today)
    hours = {}
    for r in today_rows:
        ts = r["timestamp"] or ""
        if len(ts) >= 13:
            h = int(ts[11:13])
            hours[h] = hours.get(h, 0) + 1
    busiest_hour = max(hours, key=hours.get) if hours else None

    # Camera breakdown (all time)
    cam_counts = {}
    for r in all_rows:
        cam = r["camera_id"] or "Unknown"
        cam_counts[cam] = cam_counts.get(cam, 0) + 1

    # Zone breakdown (all time)
    zone_counts = {}
    for r in all_rows:
        z = r["zone"] or "General Area"
        zone_counts[z] = zone_counts.get(z, 0) + 1

    # ── Document setup ─────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=1.8*cm,
        rightMargin=1.8*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    W = A4[0] - 3.6*cm   # usable page width
    S = make_styles()
    story = []

    # ══════════════════════════════════════════════════════════════════════
    # HEADER BLOCK
    # ══════════════════════════════════════════════════════════════════════
    header_data = [[
        Paragraph("[AEGIS] AegisAI", S["title"]),
        Paragraph(
            f"<b>DAILY SECURITY REPORT</b><br/>"
            f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
            ParagraphStyle("hdr_r", fontName="Helvetica", fontSize=9,
                           textColor=C_MUTED, alignment=2)
        ),
    ]]
    header_tbl = Table(header_data, colWidths=[W*0.55, W*0.45])
    header_tbl.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND",  (0, 0), (-1, -1), C_PANEL),
        ("TOPPADDING",  (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (0, -1), 16),
        ("RIGHTPADDING",(-1, 0), (-1, -1), 16),
        ("LINEBELOW",   (0, 0), (-1, -1), 2, C_CYAN),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 14))

    # ══════════════════════════════════════════════════════════════════════
    # TODAY'S SUMMARY — 4 stat boxes in a row
    # ══════════════════════════════════════════════════════════════════════
    story.append(Paragraph("TODAY'S SUMMARY", S["section"]))

    def stat_cell(value, label, color):
        return [
            Paragraph(f'<font color="#{color[1:]}" size="24"><b>{value}</b></font>', 
                      ParagraphStyle("sv", fontName="Helvetica-Bold", fontSize=24,
                                     textColor=colors.HexColor(color), alignment=1, leading=28)),
            Paragraph(f'<font size="8">{label}</font>',
                      ParagraphStyle("sl", fontName="Helvetica-Bold", fontSize=8,
                                     textColor=C_MUTED, alignment=1, leading=10)),
        ]

    # Pack each stat into a mini 1-col table for the box styling
    def make_stat_box(value, label, hex_color):
        inner = Table(
            [[Paragraph(str(value), ParagraphStyle(
                "SV", fontName="Helvetica-Bold", fontSize=28,
                textColor=colors.HexColor(hex_color), alignment=1, leading=32))],
             [Paragraph(label, ParagraphStyle(
                "SL", fontName="Helvetica-Bold", fontSize=8,
                textColor=C_MUTED, alignment=1, spaceBefore=4))]],
            colWidths=[W/4 - 8],
        )
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), C_CARD),
            ("TOPPADDING",    (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LINEABOVE",     (0, 0), (-1, 0),  3, colors.HexColor(hex_color)),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
        ]))
        return inner

    stat_row = Table(
        [[
            make_stat_box(t_total, "TOTAL DETECTIONS", "#00d4ff"),
            make_stat_box(t_conf,  "VERIFIED CRIMES",  "#ff4d6d"),
            make_stat_box(t_pend,  "PENDING AUDIT",    "#f59e0b"),
            make_stat_box(t_fa,    "FALSE ALARMS",     "#10b981"),
        ]],
        colWidths=[W/4 - 2] * 4,
        hAlign="LEFT",
    )
    stat_row.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    story.append(stat_row)
    story.append(Spacer(1, 14))

    # ══════════════════════════════════════════════════════════════════════
    # METRICS TABLE — side by side: today | all-time
    # ══════════════════════════════════════════════════════════════════════
    story.append(Paragraph("DETAILED METRICS", S["section"]))

    def pct(n, d):
        return f"{n/max(d,1)*100:.0f}%"

    metrics_data = [
        [Paragraph("<b>Metric</b>", ParagraphStyle("mh", fontName="Helvetica-Bold", fontSize=9, textColor=C_WHITE)),
         Paragraph("<b>Today</b>",  ParagraphStyle("mh", fontName="Helvetica-Bold", fontSize=9, textColor=C_CYAN, alignment=1)),
         Paragraph("<b>All Time</b>", ParagraphStyle("mh", fontName="Helvetica-Bold", fontSize=9, textColor=C_CYAN, alignment=1))],
        ["Total Incidents",    str(t_total),          str(a_total)],
        ["Confirmed (≥70%)",   str(t_conf),           str(a_conf)],
        ["Pending (55–69%)",   str(t_pend),           str(a_pend)],
        ["False Alarms",       str(t_fa),             str(a_fa)],
        ["False Alarm Rate",   f"{t_fa_rate:.0%}",    f"{a_fa_rate:.0%}"],
        ["Confirmation Rate",  pct(t_conf, t_total),  pct(a_conf, a_total)],
        ["Busiest Hour (Today)",
         f"{busiest_hour}:00–{busiest_hour}:59" if busiest_hour is not None else "N/A", "—"],
        ["Report Date", today, "—"],
    ]

    col_w = [W*0.5, W*0.25, W*0.25]
    mt = Table(metrics_data, colWidths=col_w)
    mt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  C_PANEL),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  C_WHITE),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 1), (0, -1),  "Helvetica"),
        ("TEXTCOLOR",     (0, 1), (0, -1),  C_MUTED),
        ("TEXTCOLOR",     (1, 1), (-1, -1), C_TEXT),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_CARD, C_ROW_ALT]),
        ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        # Highlight false alarm rate cell if it's high
        ("TEXTCOLOR",     (1, 5), (2, 5),
         C_GREEN if t_fa_rate < 0.2 else C_AMBER if t_fa_rate < 0.5 else C_RED),
        ("FONTNAME",      (1, 5), (2, 5),  "Helvetica-Bold"),
    ]))
    story.append(mt)
    story.append(Spacer(1, 14))

    # ══════════════════════════════════════════════════════════════════════
    # CAMERA + ZONE BREAKDOWN (side by side)
    # ══════════════════════════════════════════════════════════════════════
    if cam_counts or zone_counts:
        story.append(Paragraph("CAMERA & ZONE BREAKDOWN", S["section"]))

        def breakdown_table(data_dict, header, col_w_left, col_w_right, total):
            rows = [[
                Paragraph(f"<b>{header}</b>", ParagraphStyle("bh", fontName="Helvetica-Bold", fontSize=9, textColor=C_WHITE)),
                Paragraph("<b>Count</b>", ParagraphStyle("bh2", fontName="Helvetica-Bold", fontSize=9, textColor=C_CYAN, alignment=1)),
                Paragraph("<b>Share</b>", ParagraphStyle("bh3", fontName="Helvetica-Bold", fontSize=9, textColor=C_CYAN, alignment=1)),
            ]]
            for k, v in sorted(data_dict.items(), key=lambda x: -x[1]):
                rows.append([k, str(v), f"{v/max(total,1)*100:.0f}%"])
            t = Table(rows, colWidths=[col_w_left, col_w_right, col_w_right])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  C_PANEL),
                ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE",      (0, 0), (-1, -1), 9),
                ("TEXTCOLOR",     (0, 1), (0, -1),  C_MUTED),
                ("TEXTCOLOR",     (1, 1), (-1, -1), C_TEXT),
                ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_CARD, C_ROW_ALT]),
                ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
                ("TOPPADDING",    (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ]))
            return t

        half = (W - 12) / 2
        cam_t  = breakdown_table(cam_counts,  "Camera",       half*0.5, half*0.25, a_total)
        zone_t = breakdown_table(zone_counts, "Zone",         half*0.5, half*0.25, a_total)

        side = Table([[cam_t, Spacer(12, 1), zone_t]], colWidths=[half, 12, half])
        side.setStyle(TableStyle([
            ("VALIGN",  (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(side)
        story.append(Spacer(1, 14))

    # ══════════════════════════════════════════════════════════════════════
    # INCIDENT LOG — today's rows
    # ══════════════════════════════════════════════════════════════════════
    story.append(Paragraph(
        f"INCIDENT LOG — {today} ({len(today_rows)} incidents)",
        S["section"]
    ))

    if not today_rows:
        story.append(Paragraph("No incidents recorded today.", S["body"]))
    else:
        log_header = [
            Paragraph("<b>#</b>",        ParagraphStyle("lh", fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE)),
            Paragraph("<b>Time</b>",     ParagraphStyle("lh", fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE)),
            Paragraph("<b>Camera</b>",   ParagraphStyle("lh", fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE)),
            Paragraph("<b>Score</b>",    ParagraphStyle("lh", fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE)),
            Paragraph("<b>Zone</b>",     ParagraphStyle("lh", fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE)),
            Paragraph("<b>Behaviour</b>",ParagraphStyle("lh", fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE)),
            Paragraph("<b>Status</b>",   ParagraphStyle("lh", fontName="Helvetica-Bold", fontSize=8, textColor=C_WHITE)),
        ]
        log_data = [log_header]

        status_colors = {
            "CONFIRMED":   C_RED,
            "PENDING":     C_AMBER,
            "FALSE ALARM": C_GREEN,
        }

        for r in today_rows:
            status = get_status(r)
            sc     = status_colors[status]
            score  = float(r["suspicion_score"])
            tags   = (r["behavior_tags"] or "—")
            short  = tags[:38] + ("..." if len(tags) > 38 else "")
            ts     = (r["timestamp"] or "")
            time_s = ts[11:19] if len(ts) >= 19 else ts

            log_data.append([
                Paragraph(str(r["id"]), ParagraphStyle("lc", fontName="Helvetica", fontSize=8, textColor=C_MUTED)),
                Paragraph(time_s,       ParagraphStyle("lc", fontName="Helvetica", fontSize=8, textColor=C_TEXT)),
                Paragraph(r["camera_id"] or "—", ParagraphStyle("lc", fontName="Helvetica", fontSize=8, textColor=C_CYAN)),
                Paragraph(f"{score:.0%}", ParagraphStyle("lc", fontName="Helvetica-Bold", fontSize=8,
                                                          textColor=C_RED if score >= 0.7 else C_AMBER)),
                Paragraph(r["zone"] or "General Area", ParagraphStyle("lc", fontName="Helvetica", fontSize=8, textColor=C_TEXT)),
                Paragraph(short, ParagraphStyle("lc", fontName="Helvetica", fontSize=7, textColor=C_MUTED, leading=9)),
                Paragraph(f"<b>{status}</b>", ParagraphStyle("lc", fontName="Helvetica-Bold", fontSize=8, textColor=sc)),
            ])

        col_widths = [
            W*0.05,   # #
            W*0.10,   # time
            W*0.09,   # camera
            W*0.08,   # score
            W*0.14,   # zone
            W*0.34,   # behaviour
            W*0.14,   # status
        ]
        lt = Table(log_data, colWidths=col_widths, repeatRows=1)

        # Build per-row status colour commands
        style_cmds = [
            ("BACKGROUND",    (0, 0), (-1, 0),  C_DEEP),
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_CARD, C_ROW_ALT]),
            ("LINEBELOW",     (0, 0), (-1, 0),  1, C_CYAN),
        ]
        lt.setStyle(TableStyle(style_cmds))
        story.append(lt)

    story.append(Spacer(1, 24))

    # ══════════════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════════════
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "AegisAI  |  AI-Powered Retail Security  |  "
        "Behaviour detection, not identity detection  |  "
        f"Report generated {datetime.now().strftime('%d %b %Y %H:%M')}",
        S["footer"]
    ))

    # ── Build ──────────────────────────────────────────────────────────────
    def on_page(canvas, doc):
        """Dark background + page number on every page."""
        canvas.saveState()
        canvas.setFillColor(C_DEEP)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        # Page number
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(C_MUTED)
        canvas.drawRightString(
            A4[0] - 1.8*cm,
            1.2*cm,
            f"Page {doc.page}"
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"[OK] Report saved: {OUT}")
    return OUT


if __name__ == "__main__":
    generate_report()
    print("Done.")