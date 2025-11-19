# Entrega 3 – Algoritmo Genético para Asignación de Puestos

## 1. Representación de la solución
Cada individuo corresponde a la asignación completa de toda la semana:

- Diccionario `assignment` con llaves = días (`"L"`, `"Ma"`, …).
- Cada día tiene un subdiccionario `empleado → escritorio` (o `None` si teletrabaja).
- Se reutiliza el constructivo de la Entrega 2 para generar individuos factibles y respetar lista de empleados, escritorios y zonas.

```
assignment["L"] = {"E0": "D5", "E1": "D8", ...}
assignment["Ma"] = {...}
...
```

Esta representación coincide con la plantilla oficial y permite aplicar operadores por día.

## 2. Operadores del GA

| Componente | Descripción | Propósito |
|------------|-------------|-----------|
| **Inicialización** | `constructive_assignment` con aleatoriedad controlada por semilla y `top-k`. | Generar individuos factibles y diversos sin violar restricciones. |
| **Selección** | Torneo de tamaño 3 (función `_tournament_index`). | Favorecer soluciones de alta calidad sin perder diversidad. |
| **Crossover** | Corte por día (`_crossover`): se divide la semana en dos segmentos y se intercambian los calendarios completos. | Mantener asignaciones coherentes por día y mezclar bloques de grupos. |
| **Mutación** | Swap dentro de un día (`_mutate`): selecciona dos empleados asignados en el mismo día y permuta sus escritorios. | Explorar el vecindario local manteniendo factibilidad. |
| **Evaluación** | Puntaje lexicográfico `(C1, C2, C3)` reutilizando `score_solution_lex`. | Alinear el GA con los objetivos del curso. |
| **Hall of Fame** | Conserva la mejor solución global para exportarla y reportarla. | Garantiza que la mejor asignación encontrada no se pierda. |

## 3. Pseudocódigo del algoritmo

```
function RUN_GA(instance, ngen, pop_size, cxpb, mutpb, seed):
    rng ← Random(seed)
    population ← [constructive_assignment(instance, rng) for _ in range(pop_size)]
    scores ← [score_solution_lex(instance, ind) for ind in population]
    best ← argmax(population, scores)

    for gen in 1..ngen:
        new_population ← []
        while len(new_population) < pop_size:
            p1 ← torneo(population, scores)
            p2 ← torneo(population, scores)
            child1, child2 ← copiar(p1), copiar(p2)
            if rand() < cxpb:
                child1, child2 ← crossover_por_dias(p1, p2)
            if rand() < mutpb: mutar_swap(child1)
            if rand() < mutpb: mutar_swap(child2)
            new_population += [child1, child2]
        population ← new_population[:pop_size]
        scores ← [score_solution_lex(instance, ind) for ind in population]
        actualizar_mejor(population, scores, best)

    return best
```

## 4. Implementación en código
- Archivo: `instances/entrega3.py`.
- Función reutilizable: `run_ga` (líneas 76–150).
- CLI: `python3 instances/entrega3.py --in instanceX.json --ngen 25 --pop-size 25 --cxpb 0.7 --mutpb 0.2 --validate --report --outdir results_ga`.
- El script valida la solución final, imprime reporte diario y exporta los CSVs para la plantilla (`EmployeeAssignment`, `Groups_Meeting_day`, `Summary`).

## 5. Resultados y análisis
- Las corridas oficiales (3 semillas × 10 instancias) están consolidadas en `results/experiments.csv` y `results/summary.{csv,md}`.
- `results/poster.md` y `results/plots/*.png` contienen las tablas/gráficas listas para el informe. `results/plots_svg/*.svg` ofrece versiones vectoriales.
- El GA logra `C1` comparable a SA/ILS con menor tiempo promedio (≈0.02–0.10 s). SA (con recocido agresivo) domina 9/10 instancias; ILS mantiene buena cohesión C2 con menor tiempo.
- Para cumplir el punto 2 de la rúbrica (pruebas estadísticas), importa `results/experiments.csv` en Python/R/Excel y aplica la prueba elegida (p. ej. Friedman con post-hoc). Documenta en el reporte el método, los valores p y las conclusiones. El repositorio solo incluye el análisis descriptivo.

## 6. Cómo recrear las figuras
1. `python3 scripts/run_experiments.py` (ver parámetros en el README) → actualiza `results/experiments.csv`.
2. `python3 scripts/summarize_results.py` → genera `results/summary.csv` y `results/summary.md`.
3. `python3 scripts/make_poster_assets.py` → produce `results/poster.md` + `results/plots/*.png`.
4. `python3 scripts/make_simple_plots.py` → crea `results/plots_svg/avg_C1.svg`, `avg_C2.svg`, `avg_time.svg`.
5. Inserta las figuras (PNG/SVG) en el reporte o conviértelas a otros formatos según sea necesario.
