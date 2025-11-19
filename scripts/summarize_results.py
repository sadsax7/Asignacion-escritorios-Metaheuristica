import argparse
import csv
import os
from collections import defaultdict
import statistics


def lex_better(a, b):
    # a, b are (C1, C2, C3)
    if a[0] != b[0]:
        return a[0] > b[0]
    if a[1] != b[1]:
        return a[1] > b[1]
    return a[2] > b[2]

def map_method_label(method: str) -> str:
    """Mapea variantes de nombre de método a 'SA' o 'ILS' cuando corresponde."""
    m = (method or "").lower()
    if m.startswith("ent1"):
        return method
    if "ga" == m:
        return "GA"
    if "ils" in m:
        return "ILS"
    if "sa" in m or "sim" in m or "recoc" in m or "anneal" in m:
        return "SA"
    # mapear etiquetas del experimento: local -> ILS, no_local -> SA
    if m == "local":
        return "ILS"
    if m == "no_local" or m == "no-local":
        return "SA"
    # conservar otros nombres tal cual (por compatibilidad)
    return method


def main():
    parser = argparse.ArgumentParser(description="Summarize experiments.csv")
    parser.add_argument("--in", dest="infile", default="results/experiments.csv")
    parser.add_argument("--out-csv", default="results/summary.csv")
    parser.add_argument("--out-md", default="results/summary.md")
    args = parser.parse_args()

    rows = []
    with open(args.infile, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["C1"] = int(row["C1"]) ; row["C2"] = int(row["C2"]) ; row["C3"] = int(row["C3"])
            row["iters"] = int(row["iters"]) ; row["top_k"] = int(row["top_k"]) ; row["runtime_sec"] = float(row["runtime_sec"])
            # método mapeado a SA/ILS cuando aplique
            row["method_mapped"] = map_method_label(row.get("method", ""))
            rows.append(row)

    by_key = defaultdict(list)  # (instance, method) -> rows
    for row in rows:
        # agrupar por método mapeado (SA / ILS / otros)
        by_key[(row["instance"], row["method_mapped"])].append(row)

    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    # Write CSV summary
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "instance", "method", "runs", "avg_C1", "avg_C2", "avg_C3", "best_C1", "best_C2", "best_C3", "avg_runtime_sec", "best_seed"
        ])
        summaries = {}
        for (inst, method), lst in sorted(by_key.items()):
            n = len(lst)
            avg_c1 = sum(int(r["C1"]) for r in lst) / n
            avg_c2 = sum(int(r["C2"]) for r in lst) / n
            avg_c3 = sum(int(r["C3"]) for r in lst) / n
            avg_rt = sum(float(r["runtime_sec"]) for r in lst) / n
            # elegir mejor por lexicográfico (C1, C2, C3)
            best = max(lst, key=lambda r: (int(r["C1"]), int(r["C2"]), int(r["C3"])))
            w.writerow([
                inst, method, n,
                round(avg_c1, 3), round(avg_c2, 3), round(avg_c3, 3),
                int(best["C1"]), int(best["C2"]), int(best["C3"]), round(avg_rt, 6), best.get("seed", "")
            ])
            summaries[(inst, method)] = {"avg": (avg_c1, avg_c2, avg_c3), "best": (int(best["C1"]), int(best["C2"]), int(best["C3"])), "avg_rt": avg_rt}

    # Write Markdown summary for quick view
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write("**Resumen de Experimentos**\n\n")
        insts = sorted({inst for (inst, _) in summaries.keys()})
        for inst in insts:
            f.write(f"**{inst}**\n")
            methods = sorted([m for (i, m) in summaries.keys() if i == inst])
            best_method = None
            best_avg = None
            for m in methods:
                s = summaries.get((inst, m))
                f.write(f"- {m}: ")
                if s:
                    avg_tuple = tuple(round(x, 3) for x in s['avg'])
                    f.write(f"avg={avg_tuple}, best={s['best']}, avg_time={round(s['avg_rt'],6)}s\n")
                    if best_avg is None or lex_better(s['avg'], best_avg):
                        best_avg = s['avg']
                        best_method = m
                else:
                    f.write("(sin corridas)\n")
            if best_method:
                f.write(f"- Conclusión: promedio lexicográfico favorece {best_method}.\n\n")
            else:
                f.write("- Conclusión: no hay datos.\n\n")
        
    print("Wrote:", args.out_csv)
    print("Wrote:", args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
