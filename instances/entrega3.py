import random
import json
import os
from deap import base, creator, tools

# Importa funciones desde entrega2_ILS.py
import sys
sys.path.append(os.path.dirname(__file__))
from entrega2_ILS import (
    constructive_assignment,
    score_solution_lex,
    generar_vecino_swap,
    report_assignment,
    export_csv_template
)

# --------- Configuración del Algoritmo Genético ---------

# 1. Tipo de individuo: un assignment (dict día → empleado → escritorio)
creator.create("FitnessLex", base.Fitness, weights=(1.0, 1.0, 1.0))  # maximizar C1, C2, C3
creator.create("Individual", dict, fitness=creator.FitnessLex)

def init_individual(instance, seed=None):
    return creator.Individual(constructive_assignment(instance, seed=seed or random.randint(0, 999999)))

def eval_assignment(individual, instance):
    return score_solution_lex(instance, individual)

def mutate_assignment(individual, instance):
    mutated = generar_vecino_swap(individual, instance)
    individual.clear()
    individual.update(mutated)
    return (individual,)

def crossover_assignment(ind1, ind2):
    # Mezcla días entre padres
    days = list(ind1.keys())
    cut = random.randint(1, len(days)-1)
    for i, day in enumerate(days):
        if i >= cut:
            ind1[day], ind2[day] = ind2[day], ind1[day]
    return ind1, ind2

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Algoritmo Genético para Asignación de Puestos")
    parser.add_argument("--in", dest="infile", default="instance1.json", help="Archivo de instancia")
    parser.add_argument("--ngen", type=int, default=30, help="Número de generaciones")
    parser.add_argument("--pop-size", type=int, default=20, help="Tamaño de la población")
    parser.add_argument("--cxpb", type=float, default=0.7, help="Probabilidad de cruce")
    parser.add_argument("--mutpb", type=float, default=0.2, help="Probabilidad de mutación")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")
    parser.add_argument("--outdir", default="results_ga", help="Carpeta de salida para resultados y CSVs")
    args = parser.parse_args()

    # Cargar instancia
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    instance_file = os.path.join(BASE_DIR, args.infile)
    with open(instance_file, "r", encoding="utf-8") as f:
        instance = json.load(f)

    random.seed(args.seed)

    # Configuración DEAP
    toolbox = base.Toolbox()
    toolbox.register("individual", init_individual, instance)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", eval_assignment, instance=instance)
    toolbox.register("mate", crossover_assignment)
    toolbox.register("mutate", mutate_assignment, instance=instance)
    toolbox.register("select", tools.selTournament, tournsize=3)

    # Algoritmo principal
    pop = toolbox.population(n=args.pop_size)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", lambda fits: tuple(round(sum(x)/len(x), 2) for x in zip(*fits)))
    stats.register("max", lambda fits: tuple(map(max, zip(*fits))))
    stats.register("min", lambda fits: tuple(map(min, zip(*fits))))

    # Evaluar población inicial
    for ind in pop:
        ind.fitness.values = toolbox.evaluate(ind)

    for gen in range(args.ngen):
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(lambda ind: creator.Individual(ind.copy()), offspring))

        # Cruzamiento
        for i in range(1, len(offspring), 2):
            if random.random() < args.cxpb:
                toolbox.mate(offspring[i-1], offspring[i])
                del offspring[i-1].fitness.values
                del offspring[i].fitness.values

        # Mutación
        for ind in offspring:
            if random.random() < args.mutpb:
                toolbox.mutate(ind)
                del ind.fitness.values

        # Reevaluar
        invalid = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalid:
            ind.fitness.values = toolbox.evaluate(ind)

        pop[:] = offspring
        hof.update(pop)
        record = stats.compile(pop)
        print(f"Gen {gen+1}: avg={record['avg']} max={record['max']} min={record['min']}")

    best = hof[0]
    print("Mejor solución (C1, C2, C3):", score_solution_lex(instance, best))
    report_assignment(instance, best)

    # ----------- GUARDAR RESULTADO Y EXPORTAR CSVs -----------
    outdir = os.path.join(BASE_DIR, args.outdir)
    os.makedirs(outdir, exist_ok=True)
    # Guardar solución JSON
    out_json = os.path.join(outdir, f"solution_{os.path.splitext(os.path.basename(args.infile))[0]}_ga.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(best, f, ensure_ascii=False, indent=2)
    print(f"Solución guardada en: {out_json}")

    # Exportar CSVs usando la función de entrega2_ILS.py
    export_csv_template(instance, best, os.path.join(outdir, "csv_export"))
    print(f"CSVs exportados en: {os.path.join(outdir, 'csv_export')}")

if __name__ == "__main__":
    main()