"""
timeline_export.py
Run: python timeline_export.py
"""

import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

DB_PATH = "incidents/shieldeye.db"

def export_timeline(output_path="incidents/anomaly_timeline.html"):
    os.makedirs("incidents", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, suspicion_score, zone, behavior_tags, is_false_alarm "
        "FROM incidents ORDER BY timestamp"
    ).fetchall()
    conn.close()

    if not rows:
        print("No incidents to plot.")
        return

    times  = [r[0] for r in rows]
    scores = [r[1] for r in rows]
    clrs   = ["#27ae60" if r[4] else "#e94560" for r in rows]

    matplotlib.rcParams.update({
        'figure.facecolor': '#0d1121',
        'axes.facecolor':   '#0d1121',
        'axes.edgecolor':   '#1e2d4a',
        'axes.labelcolor':  '#8896b0',
        'xtick.color':      '#4a5568',
        'ytick.color':      '#4a5568',
        'text.color':       '#c9d1e0',
        'grid.color':       '#1e2d4a',
    })

    fig, ax = plt.subplots(figsize=(14, 5), facecolor='#0d1121')
    ax.scatter(range(len(scores)), scores, c=clrs, s=80, zorder=3)
    ax.plot(range(len(scores)), scores,
            color="#00d4ff", alpha=0.5, linewidth=1.5)
    ax.axhline(0.55, ls='--', color='#e94560', alpha=0.7,
               label='Alert Threshold (0.55)')

    ax.set_xticks(range(len(times)))
    ax.set_xticklabels([t[11:19] for t in times],
                       rotation=45, ha='right', fontsize=7)
    ax.set_ylabel("Suspicion Score")
    ax.set_title("AegisAI -- Anomaly Score Timeline",
                 fontsize=13, fontweight='bold', color='#c9d1e0')
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)

    red_patch   = mpatches.Patch(color='#e94560', label='Confirmed Incident')
    green_patch = mpatches.Patch(color='#27ae60', label='False Alarm')
    ax.legend(handles=[red_patch, green_patch],
              facecolor='#0d1121', edgecolor='#1e2d4a', labelcolor='#c9d1e0')

    plt.tight_layout()
    img_path = output_path.replace('.html', '.png')
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Timeline image saved: {img_path}")

    # HTML -- ASCII only, no emoji
    html = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        "  <meta charset='utf-8'>\n"
        "  <title>AegisAI Anomaly Timeline</title>\n"
        "  <style>\n"
        "    body { font-family: Arial; background: #0a0e1a; color: #c9d1e0; padding: 20px; }\n"
        "    table { width: 100%; border-collapse: collapse; }\n"
        "    th { background: #0d1121; padding: 8px; color: #8896b0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #1e2d4a; }\n"
        "    td { padding: 6px; border-bottom: 1px solid #141928; font-size: 0.85rem; }\n"
        "    .real { color: #e94560; font-weight: 600; }\n"
        "    .fa   { color: #27ae60; }\n"
        "    h1 { color: #00d4ff; letter-spacing: 2px; }\n"
        "    h2 { color: #8896b0; font-size: 1rem; letter-spacing: 1px; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <h1>AEGIS AI -- ANOMALY REPORT</h1>\n"
        f"  <img src='{os.path.basename(img_path)}' style='width:100%;max-width:900px'>\n"
        "  <h2>INCIDENT LOG</h2>\n"
        "  <table>\n"
        "    <tr><th>#</th><th>TIME</th><th>SCORE</th><th>ZONE</th><th>BEHAVIOUR</th><th>STATUS</th></tr>\n"
    )

    for i, r in enumerate(rows, 1):
        cls  = "fa" if r[4] else "real"
        stat = "False Alarm" if r[4] else "INCIDENT"
        tags = (r[3] or "").encode('ascii', 'ignore').decode('ascii')
        html += (
            f"    <tr>"
            f"<td>{i}</td>"
            f"<td>{r[0]}</td>"
            f"<td class='{cls}'>{r[1]:.0%}</td>"
            f"<td>{r[2]}</td>"
            f"<td>{tags}</td>"
            f"<td class='{cls}'>{stat}</td>"
            f"</tr>\n"
        )

    html += "  </table>\n</body>\n</html>"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML timeline saved: {output_path}")


if __name__ == "__main__":
    export_timeline()