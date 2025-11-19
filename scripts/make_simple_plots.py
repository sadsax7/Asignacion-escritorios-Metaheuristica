import csv
import os
from collections import defaultdict


def read_summary(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def aggregate(rows, field):
    acc = defaultdict(list)
    for row in rows:
        try:
            value = float(row[field])
        except ValueError:
            continue
        acc[row["method"]].append(value)
    return {m: (sum(vals) / len(vals) if vals else 0.0) for m, vals in acc.items()}


def svg_bar_chart(data, title, ylabel, out_path, width=800, height=400):
    methods = list(data.keys())
    values = [data[m] for m in methods]
    max_val = max(values) if values else 1.0
    plot_height = height - 120
    plot_width = width - 120
    bar_space = plot_width / max(1, len(methods))
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')
    svg.append(f'<style>.title{{font: bold 18px sans-serif;}} .label{{font: 12px sans-serif;}}</style>')
    svg.append(f'<text class="title" x="{width/2}" y="30" text-anchor="middle">{title}</text>')
    svg.append(f'<text class="label" x="30" y="{height/2}" transform="rotate(-90,30,{height/2})">{ylabel}</text>')
    origin_x, origin_y = 80, height - 60
    svg.append(f'<line x1="{origin_x}" y1="{origin_y}" x2="{origin_x}" y2="{origin_y-plot_height}" stroke="#333" stroke-width="2"/>')
    svg.append(f'<line x1="{origin_x}" y1="{origin_y}" x2="{origin_x+plot_width}" y2="{origin_y}" stroke="#333" stroke-width="2"/>')
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]
    for idx, method in enumerate(methods):
        value = values[idx]
        bar_h = 0 if max_val == 0 else (value / max_val) * plot_height
        x = origin_x + idx * bar_space + bar_space * 0.15
        y = origin_y - bar_h
        w = bar_space * 0.7
        color = colors[idx % len(colors)]
        svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{bar_h:.2f}" fill="{color}"/>')
        svg.append(f'<text class="label" x="{x + w/2:.2f}" y="{origin_y + 20}" text-anchor="middle">{method}</text>')
        svg.append(f'<text class="label" x="{x + w/2:.2f}" y="{y - 5:.2f}" text-anchor="middle">{value:.2f}</text>')
    svg.append("</svg>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print("Escribí", out_path)


def main():
    base = os.path.dirname(os.path.dirname(__file__))
    summary_path = os.path.join(base, "results", "summary.csv")
    if not os.path.exists(summary_path):
        raise SystemExit("No existe results/summary.csv. Ejecuta scripts/summarize_results.py primero.")
    rows = read_summary(summary_path)
    os.makedirs(os.path.join(base, "results", "plots_svg"), exist_ok=True)
    avg_c1 = aggregate(rows, "avg_C1")
    avg_c2 = aggregate(rows, "avg_C2")
    avg_time = aggregate(rows, "avg_runtime_sec")
    svg_bar_chart(avg_c1, "Promedio C1 por método", "C1 promedio", os.path.join(base, "results", "plots_svg", "avg_C1.svg"))
    svg_bar_chart(avg_c2, "Promedio C2 por método", "C2 promedio", os.path.join(base, "results", "plots_svg", "avg_C2.svg"))
    svg_bar_chart(avg_time, "Tiempo promedio por método (s)", "segundos", os.path.join(base, "results", "plots_svg", "avg_time.svg"))


if __name__ == "__main__":
    main()
