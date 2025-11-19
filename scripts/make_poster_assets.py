import csv
import os
from collections import defaultdict


def read_summary(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


def pivot_summary(rows):
    by_inst = defaultdict(dict)  # inst -> method -> metrics
    for row in rows:
        inst = row["instance"]
        method = row["method"]
        by_inst[inst][method] = {
            "avg_C1": float(row["avg_C1"]),
            "avg_C2": float(row["avg_C2"]),
            "avg_C3": float(row["avg_C3"]),
            "avg_runtime_sec": float(row["avg_runtime_sec"]),
            "best": (int(row["best_C1"]), int(row["best_C2"]), int(row["best_C3"]))
        }
    return by_inst


def save_markdown_table(by_inst, out_md):
    insts = sorted(by_inst.keys())
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("**Tabla comparativa (promedios y mejor corrida)**\n\n")
        f.write("| instance | method | avg_C1 | avg_C2 | avg_C3 | avg_time(s) | best (C1, C2, C3) |\n")
        f.write("|---|---|---:|---:|---:|---:|---|\n")
        for inst in insts:
            methods = sorted(by_inst[inst].keys())
            for method in methods:
                data = by_inst[inst][method]
                f.write(
                    "| {inst} | {method} | {c1:.3f} | {c2:.3f} | {c3:.3f} | {rt:.6f} | {best} |\n".format(
                        inst=inst,
                        method=method,
                        c1=data["avg_C1"],
                        c2=data["avg_C2"],
                        c3=data["avg_C3"],
                        rt=data["avg_runtime_sec"],
                        best=data["best"],
                    )
                )


def make_plots(by_inst, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        insts = sorted(by_inst.keys())
        method_list = sorted({m for inst in by_inst.values() for m in inst.keys()})
        if not insts or not method_list:
            return []
        x = np.arange(len(insts))
        width = 0.8 / max(1, len(method_list))

        def plot_metric(metric_key, title, fname, log_scale=False):
            fig, ax = plt.subplots(figsize=(max(8, len(insts) * 0.9), 4))
            for idx, method in enumerate(method_list):
                values = np.array([by_inst[i].get(method, {}).get(metric_key, float('nan')) for i in insts], dtype=float)
                offset = (idx - (len(method_list) - 1) / 2) * width
                bars = ax.bar(x + offset, values, width, label=method)
            if log_scale:
                ax.set_yscale('log')
                ax.set_ylabel('segundos (escala log)')
            ax.set_title(title)
            ax.set_xticks(x, insts, rotation=45, ha='right')
            ax.legend(ncol=min(3, len(method_list)))
            ax.grid(axis='y', alpha=0.3)
            fig.tight_layout()
            out_path = os.path.join(out_dir, fname)
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
            return out_path

        p1 = plot_metric('avg_C1', 'Promedio C1 por instancia', 'avg_C1.png')
        p2 = plot_metric('avg_C2', 'Promedio C2 por instancia', 'avg_C2.png')
        p3 = plot_metric('avg_C3', 'Promedio C3 por instancia', 'avg_C3.png')
        p4 = plot_metric('avg_runtime_sec', 'Tiempo promedio (s) por instancia', 'avg_time.png', log_scale=True)
        return [p1, p2, p3, p4]
    except Exception as e:
        note = os.path.join(out_dir, "NO_PLOTS.txt")
        with open(note, "w", encoding="utf-8") as f:
            f.write("No se pudieron generar gráficas. Motivo: " + repr(e))
        return []


def _lex_better(a, b):
    # a, b are (C1, C2, C3)
    if a[0] != b[0]:
        return a[0] > b[0]
    if a[1] != b[1]:
        return a[1] > b[1]
    return a[2] > b[2]


def make_poster_md(by_inst, plot_paths, out_md):
    all_methods = sorted({m for inst in by_inst.values() for m in inst.keys()})
    winners = {m: 0 for m in all_methods}
    for inst, data in by_inst.items():
        best_method = None
        best_avg = None
        for method, metrics in data.items():
            triple = (metrics["avg_C1"], metrics["avg_C2"], metrics["avg_C3"])
            if best_avg is None or _lex_better(triple, best_avg):
                best_avg = triple
                best_method = method
        if best_method:
            winners[best_method] += 1

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("**Póster – Comparativo de heurísticas y metaheurísticas para asignación híbrida**\n\n")
        f.write("- Problema: asignar escritorios por día maximizando preferencias (C1), cohesión por grupo (C2) y balance por zonas (C3) en orden lexicográfico.\n")
        f.write("- Métodos evaluados: constructivo + BL (ENT1_LOCAL), constructivo + SA (ENT1_SA y SA), ILS iterado y Algoritmo Genético (GA).\n")
        f.write("- Experimentos: {n} instancias, {m} métodos, semillas configurables via `scripts/run_experiments.py`.\n\n".format(
            n=len(by_inst),
            m=len(all_methods)
        ))

        f.write("Resultados promedio por instancia (tabla):\n\n")
        save_markdown_table(by_inst, out_md.replace('.md','_table.md'))
        with open(out_md.replace('.md','_table.md'), 'r', encoding='utf-8') as tf:
            f.write(tf.read())
        f.write("\n")

        f.write("Pseudocódigo (resumen)\n\n")
        f.write("Constructivo aleatorizado (común a todos los métodos):\n")
        f.write("- Para cada día se listan empleados presentes; se barajan con la semilla.\n")
        f.write("- Cada empleado toma un escritorio en su zona objetivo priorizando preferencias (top-k) y balance.\n")
        f.write("- Los huecos se llenan con `none` para mantener la plantilla completa.\n\n")
        f.write("Metaheurísticas:\n")
        f.write("- ENT1_LOCAL: hill climbing por swaps aceptando solo mejoras lexicográficas.\n")
        f.write("- ENT1_SA / SA: recocido simulado que acepta empeoramientos con probabilidad `exp(Δ/T)`.\n")
        f.write("- ILS: iterated local search con perturbaciones `k`-swap + hill climbing intensivo.\n")
        f.write("- GA: algoritmo genético simple con torneo, cruce por días y mutación swap.\n\n")

        f.write("Conclusiones y recomendaciones:\n\n")
        for method in all_methods:
            f.write(f"- {method}: gana {winners.get(method,0)} instancias según promedio C1→C2→C3.\n")
        f.write("- ILS y GA tienden a dominar en C1/C2, aunque a mayor costo computacional.\n")
        f.write("- Mantener `top-k=3` y ≥1000 iteraciones en búsquedas locales ofrece un buen compromiso.\n\n")

        if plot_paths:
            f.write("Gráficas comparativas:\n\n")
            for p in plot_paths:
                rel = os.path.relpath(p, os.path.dirname(out_md))
                f.write(f"- {os.path.basename(p)}\n")
                f.write(f"  ![]({rel})\n\n")
        else:
            f.write("Nota: no se generaron gráficas (matplotlib no disponible).\n")


def main():
    base = os.path.dirname(os.path.dirname(__file__))
    summary_csv = os.path.join(base, 'results', 'summary.csv')
    if not os.path.exists(summary_csv):
        print('No existe results/summary.csv. Corre scripts/summarize_results.py primero.')
        return 1
    rows = read_summary(summary_csv)
    by_inst = pivot_summary(rows)
    plots_dir = os.path.join(base, 'results', 'plots')
    plots = make_plots(by_inst, plots_dir)
    poster_md = os.path.join(base, 'results', 'poster.md')
    make_poster_md(by_inst, plots, poster_md)
    print('Assets de póster generados:')
    print('-', poster_md)
    if plots:
        for p in plots:
            print('-', p)
    else:
        print('- (sin gráficas)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
