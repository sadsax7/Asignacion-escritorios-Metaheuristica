import json
import os
import random
from typing import Dict, List, Tuple

import sys
sys.path.append(os.path.dirname(__file__))
from entrega2_ILS import (
    constructive_assignment,
    score_solution_lex,
    report_assignment,
    export_csv_template,
    validate_assignment,
)


def _copy_assignment(assignment: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {day: seats.copy() for day, seats in assignment.items()}


def _tournament_index(scores: List[Tuple[int, int, int]], rng: random.Random, k: int = 3) -> int:
    best_idx = None
    for _ in range(k):
        idx = rng.randrange(len(scores))
        if best_idx is None or scores[idx] > scores[best_idx]:
            best_idx = idx
    return best_idx if best_idx is not None else 0


def _crossover(parent1: Dict[str, Dict[str, str]],
               parent2: Dict[str, Dict[str, str]],
               rng: random.Random) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
    days = list(parent1.keys())
    if len(days) < 2:
        return _copy_assignment(parent1), _copy_assignment(parent2)
    cut = rng.randint(1, len(days) - 1)
    child1: Dict[str, Dict[str, str]] = {}
    child2: Dict[str, Dict[str, str]] = {}
    for i, day in enumerate(days):
        if i < cut:
            child1[day] = parent1[day].copy()
            child2[day] = parent2[day].copy()
        else:
            child1[day] = parent2[day].copy()
            child2[day] = parent1[day].copy()
    return child1, child2


def _mutate(instance: dict, assignment: Dict[str, Dict[str, str]], rng: random.Random) -> None:
    days = instance.get("Days", [])
    employees = instance.get("Employees", [])
    if not days or len(employees) < 2:
        return
    day = rng.choice(days)
    assigned_today = [e for e in employees if assignment[day].get(e) is not None]
    if len(assigned_today) < 2:
        return
    a, b = rng.sample(assigned_today, 2)
    assignment[day][a], assignment[day][b] = assignment[day][b], assignment[day][a]


def _population_stats(scores: List[Tuple[int, int, int]]) -> Dict[str, Tuple[float, float, float]]:
    n = len(scores)
    if n == 0:
        return {"avg": (0, 0, 0), "max": (0, 0, 0), "min": (0, 0, 0)}
    avg_c1 = sum(s[0] for s in scores) / n
    avg_c2 = sum(s[1] for s in scores) / n
    avg_c3 = sum(s[2] for s in scores) / n
    max_score = max(scores)
    min_score = min(scores)
    return {"avg": (round(avg_c1, 2), round(avg_c2, 2), round(avg_c3, 2)),
            "max": max_score,
            "min": min_score}


def run_ga(instance: dict,
           ngen: int = 30,
           pop_size: int = 20,
           cxpb: float = 0.7,
           mutpb: float = 0.2,
           seed: int = 42,
           top_k_pref: int = 3,
           verbose: bool = False):
    rng = random.Random(seed)
    population = [
        constructive_assignment(instance, seed=rng.randint(0, 10**9), randomize=True, top_k_pref=top_k_pref)
        for _ in range(pop_size)
    ]
    scores = [score_solution_lex(instance, ind) for ind in population]

    best_idx = max(range(len(population)), key=lambda i: scores[i])
    best = _copy_assignment(population[best_idx])
    best_score = scores[best_idx]
    history = []

    for gen in range(ngen):
        new_population: List[Dict[str, Dict[str, str]]] = []
        new_scores: List[Tuple[int, int, int]] = []

        while len(new_population) < pop_size:
            i1 = _tournament_index(scores, rng)
            i2 = _tournament_index(scores, rng)
            parent1 = population[i1]
            parent2 = population[i2]

            child1, child2 = _copy_assignment(parent1), _copy_assignment(parent2)
            if rng.random() < cxpb:
                child1, child2 = _crossover(parent1, parent2, rng)

            if rng.random() < mutpb:
                _mutate(instance, child1, rng)
            if rng.random() < mutpb:
                _mutate(instance, child2, rng)

            score1 = score_solution_lex(instance, child1)
            score2 = score_solution_lex(instance, child2)
            new_population.append(child1)
            new_scores.append(score1)
            if len(new_population) < pop_size:
                new_population.append(child2)
                new_scores.append(score2)

        population = new_population
        scores = new_scores
        gen_best_idx = max(range(len(population)), key=lambda i: scores[i])
        gen_best = population[gen_best_idx]
        gen_best_score = scores[gen_best_idx]
        if gen_best_score > best_score:
            best = _copy_assignment(gen_best)
            best_score = gen_best_score

        stats = _population_stats(scores)
        history.append({"gen": gen + 1, **stats})
        if verbose:
            print(f"Gen {gen+1}: avg={stats['avg']} max={stats['max']} min={stats['min']}")

    return best, history


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Algoritmo Genético para Asignación de Puestos")
    parser.add_argument("--in", dest="infile", default="instance1.json", help="Archivo de instancia")
    parser.add_argument("--ngen", type=int, default=30, help="Número de generaciones")
    parser.add_argument("--pop-size", type=int, default=20, help="Tamaño de la población")
    parser.add_argument("--cxpb", type=float, default=0.7, help="Probabilidad de cruce")
    parser.add_argument("--mutpb", type=float, default=0.2, help="Probabilidad de mutación")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")
    parser.add_argument("--top-k", type=int, default=3, help="Top-k de preferencias para el constructivo")
    parser.add_argument("--validate", action="store_true", help="Valida la solución antes de exportar")
    parser.add_argument("--outdir", default="results_ga", help="Carpeta de salida para resultados y CSVs")
    args = parser.parse_args()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    instance_file = os.path.join(BASE_DIR, args.infile)
    with open(instance_file, "r", encoding="utf-8") as f:
        instance = json.load(f)

    best, history = run_ga(
        instance,
        ngen=args.ngen,
        pop_size=args.pop_size,
        cxpb=args.cxpb,
        mutpb=args.mutpb,
        seed=args.seed,
        top_k_pref=args.top_k,
        verbose=True
    )

    if args.validate:
        ok, errs = validate_assignment(instance, best)
        if ok:
            print("Validación: OK")
        else:
            print("Validación: errores encontrados:")
            for e in errs:
                print(" -", e)
            return

    print("Mejor solución (C1, C2, C3):", score_solution_lex(instance, best))
    report_assignment(instance, best)

    outdir = os.path.join(BASE_DIR, args.outdir)
    os.makedirs(outdir, exist_ok=True)
    out_json = os.path.join(outdir, f"solution_{os.path.splitext(os.path.basename(args.infile))[0]}_ga.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(best, f, ensure_ascii=False, indent=2)
    print(f"Solución guardada en: {out_json}")

    export_csv_template(instance, best, os.path.join(outdir, "csv_export"))
    print(f"CSVs exportados en: {os.path.join(outdir, 'csv_export')}")


if __name__ == "__main__":
    main()
