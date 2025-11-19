import argparse
import csv
import glob
import json
import os
import time
from importlib.machinery import SourceFileLoader


def load_module_from(path: str, name: str):
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        base = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(base, path)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return SourceFileLoader(name, path).load_module()


def parse_seeds(seeds_arg: str, num_seeds: int, start: int) -> list[int]:
    if seeds_arg:
        return [int(x) for x in seeds_arg.split(",") if x.strip()]
    return list(range(start, start + num_seeds))


def lex_to_scalar(score):
    c1, c2, c3 = score
    return c1 * 10000 + c2 * 100 + c3


def run_ent1_local(mod, instance, seed, args):
    assignment = mod.constructive_assignment(instance, seed=seed, randomize=True, top_k_pref=args.top_k)
    assignment = mod.local_search_swaps(instance, assignment, iters=args.local_iters, seed=seed)
    return assignment, args.local_iters


def run_ent1_sa(mod, instance, seed, args):
    assignment = mod.constructive_assignment(instance, seed=seed, randomize=True, top_k_pref=args.top_k)
    assignment = mod.simulated_annealing_swaps(
        instance,
        assignment,
        iters_per_temp=args.ent1_sa_iters,
        t_inicial=args.sa_tinit,
        t_final=args.sa_tfinal,
        alpha=args.sa_alpha,
        seed=seed
    )
    return assignment, args.ent1_sa_iters


def run_sa(mod, instance, seed, args):
    assignment = mod.constructive_assignment(instance, seed=seed, randomize=True, top_k_pref=args.top_k)

    def _score(a):
        return lex_to_scalar(mod.score_solution_lex(instance, a))

    assignment = mod.simulated_annealing(
        assignment,
        evaluar=_score,
        generar_vecino=lambda s: mod.generar_vecino_swap(s, instance),
        T_inicial=args.sa_tinit,
        T_final=args.sa_tfinal,
        alpha=args.sa_alpha,
        iter_por_temp=args.sa_iters
    )
    return assignment, args.sa_iters


def run_ils(mod, instance, seed, args):
    assignment = mod.constructive_assignment(instance, seed=seed, randomize=True, top_k_pref=args.top_k)

    def _score(a):
        c1, c2, c3 = mod.score_solution_lex(instance, a)
        return c1 * 10000 + c2 * 100 + c3

    assignment = mod.iterated_local_search(
        instance,
        assignment,
        evaluar=_score,
        local_search_func=mod.local_search_swaps_hillclimb,
        perturb_func=mod.perturbation_k_swaps,
        max_iters=args.ils_iters,
        ls_iters=args.ls_iters,
        perturb_k=args.perturb_k,
        seed=seed
    )
    return assignment, args.ils_iters


def run_ga(mod, instance, seed, args):
    assignment, _history = mod.run_ga(
        instance,
        ngen=args.ga_ngen,
        pop_size=args.ga_pop,
        cxpb=args.ga_cxpb,
        mutpb=args.ga_mutpb,
        seed=seed,
        top_k_pref=args.top_k,
        verbose=False
    )
    return assignment, args.ga_ngen


METHOD_CONFIG = {
    "ent1_local": {"label": "ENT1_LOCAL", "runner": run_ent1_local, "module": "ent1"},
    "ent1_sa": {"label": "ENT1_SA", "runner": run_ent1_sa, "module": "ent1"},
    "sa": {"label": "SA", "runner": run_sa, "module": "sa"},
    "ils": {"label": "ILS", "runner": run_ils, "module": "ils"},
    "ga": {"label": "GA", "runner": run_ga, "module": "ga"},
}

ALIASES = {
    "local": "ils",
    "no_local": "sa",
    "ent1": "ent1_local",
    "ent1_meta": "ent1_sa",
}


def normalize_methods(method_arg: str) -> list[str]:
    if not method_arg:
        return ["sa", "ils"]
    tokens = method_arg.replace(";", ",").split(",")
    result = []
    for tok in tokens:
        key = tok.strip().lower()
        if not key:
            continue
        key = ALIASES.get(key, key)
        if key in METHOD_CONFIG and key not in result:
            result.append(key)
    return result


def main():
    parser = argparse.ArgumentParser(description="Run batch experiments on all heuristics")
    parser.add_argument("--instances-glob", default="instances/instance*.json", help="Glob para instancias")
    parser.add_argument("--methods", default="ent1_local,ent1_sa,sa,ils,ga",
                        help="Lista separada por comas de métodos (ent1_local, ent1_sa, sa, ils, ga)")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--local-iters", type=int, default=1000)
    parser.add_argument("--ent1-sa-iters", type=int, default=200)
    parser.add_argument("--sa-iters", type=int, default=1000)
    parser.add_argument("--sa-tinit", type=float, default=200.0)
    parser.add_argument("--sa-tfinal", type=float, default=1.0)
    parser.add_argument("--sa-alpha", type=float, default=0.95)
    parser.add_argument("--ils-iters", type=int, default=20)
    parser.add_argument("--ls-iters", type=int, default=500)
    parser.add_argument("--perturb-k", type=int, default=3)
    parser.add_argument("--ga-ngen", type=int, default=30)
    parser.add_argument("--ga-pop", type=int, default=20)
    parser.add_argument("--ga-cxpb", type=float, default=0.7)
    parser.add_argument("--ga-mutpb", type=float, default=0.2)
    parser.add_argument("--seeds", default=None, help="Semillas separadas por coma")
    parser.add_argument("--num-seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--out", default="results/experiments.csv", help="CSV de salida")
    parser.add_argument("--algo-ent1", default="instances/entrega1.py", help="Ruta al módulo de Entrega 1")
    parser.add_argument("--algo-sa", default="instances/entrega2.py", help="Ruta al módulo de SA")
    parser.add_argument("--algo-ils", default="instances/entrega2_ILS.py", help="Ruta al módulo de ILS")
    parser.add_argument("--algo-ga", default="instances/entrega3.py", help="Ruta al módulo de GA")
    args = parser.parse_args()

    inst_files = sorted(glob.glob(args.instances_glob))
    if not inst_files:
        print("No instances found for glob:", args.instances_glob)
        return 1

    modules = {}
    for key, path in [("ent1", args.algo_ent1), ("sa", args.algo_sa), ("ils", args.algo_ils), ("ga", args.algo_ga)]:
        try:
            modules[key] = load_module_from(path, f"{key}_mod")
        except Exception as e:
            print(f"Warning: no pude cargar el módulo {key} ({path}): {e}")
            modules[key] = None

    seeds = parse_seeds(args.seeds, args.num_seeds, args.seed_start)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    header = ["instance", "method", "seed", "iters", "top_k", "C1", "C2", "C3", "runtime_sec"]
    methods = normalize_methods(args.methods)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)

        for inst_path in inst_files:
            with open(inst_path, "r", encoding="utf-8") as jf:
                instance = json.load(jf)

            base = os.path.basename(inst_path)
            for method_key in methods:
                config = METHOD_CONFIG[method_key]
                mod = modules.get(config["module"])
                if mod is None:
                    print(f"Skipping {base} {config['label']}: módulo no disponible")
                    continue
                for seed in seeds:
                    t0 = time.perf_counter()
                    try:
                        assignment, iterations = config["runner"](mod, instance, seed, args)
                        c1, c2, c3 = mod.score_solution_lex(instance, assignment)
                    except Exception as e:
                        print(f"Error ejecutando {config['label']} en {base} (seed {seed}): {e}")
                        continue
                    dt = time.perf_counter() - t0
                    w.writerow([base, config["label"], seed, iterations, args.top_k, c1, c2, c3, round(dt, 6)])
                    f.flush()

    print("Wrote:", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
