**Proyecto Heurística – Asignación de Puestos en Trabajos Híbridos**

- Autoría del código base: ver `instances/entrega2.py` & `instances/entrega2_ILS.py` (Universidad EAFIT, 2025)
- Este repo contiene un heurístico con construcción aleatorizada, recocido simulado y ILS como metaheuristico de busqueda local

**Contenido**
- ¿Qué resuelve? y formato de instancias
- Puntaje y análisis lexicográfico
- Entregas y métodos implementados
- SA como sustituto (y pseudocódigo)
- ILS como metaheuristico por swaps (y pseudocódigo)
- Validación, reporte y exportación a plantilla (CSV)
- Experimentos y análisis de resultados (scripts incluidos)

**Entregas y Métodos Implementados**
- **Entrega 1 – Constructivo + Búsqueda Local / Recocido Simulado.** `instances/entrega1.py` incluye el constructivo aleatorizado, la búsqueda local pura por swaps (`--method local`) y una metaheurística basada en recocido simulado (`--method sa`). Ambos métodos comparten validación, reportes y exportación de CSVs.
- **Entrega 2 – Recocido Simulado + ILS.** `instances/entrega2.py` ejecuta el recocido clásico y `instances/entrega2_ILS.py` integra ILS con búsqueda local intensiva, validación, reportes y exportación a plantilla.
- **Entrega 3 – Algoritmo Genético.** `instances/entrega3.py` implementa un GA ligero sin dependencias externas (torneo, crossover por días y mutación swap) y permite validar/exportar los resultados. Consulta `docs/entrega3.md` para la descripción completa, representación y pseudocódigo.
- **Scripts de experimentos y gráficas.** `scripts/run_experiments.py`, `scripts/summarize_results.py` y `scripts/make_poster_assets.py` automatizan el banco de pruebas, la generación de resúmenes y el póster (PNG en `results/plots/`). `scripts/make_simple_plots.py` genera gráficas SVG sin dependencias adicionales (`results/plots_svg/`).

**Guía Rápida (WSL/Ubuntu)**
1. Crear entorno virtual (opcional pero recomendado):
   ```
   sudo apt-get install -y python3.12-venv
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Instalar dependencias opcionales:
   ```
   pip install matplotlib
   ```
3. Ejecutar cualquier entrega (ejemplos abajo) o correr el pipeline completo.
4. Regenerar resultados finales:
   ```
   python scripts/run_experiments.py --methods "ent1_local,ent1_sa,sa,ils,ga" --num-seeds 3 --seed-start 1 --top-k 3 --local-iters 600 --ent1-sa-iters 120 --sa-iters 500 --ils-iters 15 --ls-iters 500 --perturb-k 3 --ga-ngen 15 --ga-pop 20 --ga-cxpb 0.7 --ga-mutpb 0.2 --out results/experiments.csv
   python scripts/summarize_results.py --in results/experiments.csv --out-csv results/summary.csv --out-md results/summary.md
   python scripts/make_poster_assets.py
   python scripts/make_simple_plots.py
   ```
5. Al terminar, use `deactivate` para salir del entorno virtual.



**Requisitos**
- Python 3.8 o superior.
- Sin dependencias externas para correr el algoritmo y exportar CSV.
- Para generar gráficas del póster: `matplotlib` (opcional).
  - Windows (PowerShell): `python -m pip install matplotlib`
  - Linux/macOS: `python3 -m pip install matplotlib`

**Qué Resuelve**
- Asigna, para cada día de la semana, a qué escritorio se sienta cada empleado.
- Objetivos (orden lexicográfico):
  - C1 Preferencias: maximizar empleados sentados en uno de sus escritorios preferidos.
  - C2 Cohesión de grupo: para cada grupo, maximizar el tamaño de su mayor agregado por zona.
  - C3 Balance por zonas: minimizar la diferencia de ocupación entre zonas (se suma como `-(max-min)`).

**Formato De Instancias**
- Archivo JSON (ver `instances/instance1.json`):
  - `Employees`: lista de empleados (`"E0"`, `"E1"`, …).
  - `Desks`: lista de escritorios (`"D0"`, `"D1"`, …).
  - `Days`: lista de días (p. ej. `"L"`, `"Ma"`, `"Mi"`, `"J"`, `"V"`).
  - `Groups`: lista de grupos (`"G0"`, …) y `Employees_G`: mapa grupo → empleados.
  - `Zones`: lista de zonas (`"Z0"`, `"Z1"`) y `Desks_Z`: mapa zona → escritorios.
  - `Desks_E`: mapa empleado → lista de escritorios preferidos.
  - `Days_E`: mapa empleado → días en los que asiste (si falta, se asume todos los días).


**Puntaje y Análisis Lexicográfico**
- `score_solution_lex(instance, assignment) -> (C1, C2, C3)`:
  - C1: conteo de asignaciones que respetan preferencias (`Desks_E`).
  - C2: por grupo y día, tamaño del mayor conjunto en una misma zona; se suman por todos los grupos y días.
  - C3: balance por día: `-(max_ocupación_zona - min_ocupación_zona)`.
- Comparación lexicográfica: una solución A es mejor que B si `C1_A > C1_B`, o si empatan en C1 y `C2_A > C2_B`, o si empatan en C1 y C2 y `C3_A > C3_B`.

**Entrega 1 – Constructivo + Búsqueda Local / Recocido Simulado**
`instances/entrega1.py` cubre lo exigido en la primera tarea:

- Método constructivo aleatorizado basado en top-k y zonas objetivo.
- **Búsqueda local pura** (`--method local`): hill climbing por swaps que sólo acepta mejoras lexicográficas.
- **Metaheurística basada en BL** (`--method sa`): recocido simulado con aceptación probabilística de empeoramientos.
- Validación (`--validate`), reporte (`--report`), exportación de plantillas (`--export-csv/--export-dir`) y salida por `stdout`.

Uso típico:
- `python3 instances/entrega1.py --in instance1.json --method local --iters 800 --report --validate --export-csv`
- `python3 instances/entrega1.py --method sa --sa-iters 150 --tinit 200 --tfinal 1 --alpha 0.95`

Metas principales del recocido en esta entrega:

- `generar_vecino_swap`: intercambia dos empleados asignados al mismo día para explorar el vecindario.
- `simulated_annealing_swaps`: controla la temperatura y utiliza la función objetivo lexicográfica `C1→C2→C3` convertida a un escalar.
- Parámetros destacables: `--sa-iters` (iteraciones por temperatura), `--tinit`, `--tfinal` y `--alpha`.

Pseudocódigo resumido:
```
S = solucion_inicial
mejor = S
T = T_inicial
while T > T_final:
    for i in range(iter_por_temp):
        S' = swap_aleatorio(S)
        Δ = evaluar(S') - evaluar(S)
        if Δ > 0 or random() < exp(Δ / T):
            S = S'
            if evaluar(S) > evaluar(mejor):
                mejor = S
    T *= alpha
```

**Entrega 2 – Recocido Simulado e ILS**
- `instances/entrega2.py`: recocido simulado equivalente al de la entrega 1 pero desacoplado, con `--tinit/--tfinal/--alpha`, `--iters` y soporte de `--validate`, `--report`, `--export-csv`.
- `instances/entrega2_ILS.py`: módulo principal que integra el constructivo, SA y el Iterated Local Search con perturbaciones tipo swap, validación y exportación.
- Ejemplos:
  - `python3 instances/entrega2.py --in instance5.json --iters 600 --report --validate --export-csv`
  - `python3 instances/entrega2_ILS.py --in instance5.json --ils --ils-iters 25 --ls-iters 600 --perturb-k 3 --report --validate --export-csv`

Componentes clave del ILS:

- `local_search_swaps_hillclimb`: búsqueda local tipo hill climbing que intercambia dos empleados de un día cuando mejora `(C1,C2,C3)`.
- `perturbation_k_swaps`: aplica `k` swaps aleatorios para diversificar antes de cada nueva búsqueda local.
- `iterated_local_search`: orquesta la intensificación (búsqueda local) y la diversificación (perturbaciones) durante `max_iters` repeticiones.

Pseudocódigo:
```
S = local_search(initial)
best = S
best_val = evaluar(best)
for i in range(max_iters):
    S_p = perturbation(S, k)
    S_p = local_search(S_p)
    val_p = evaluar(S_p)
    if val_p > best_val:
        best = copy(S_p)
        best_val = val_p
        S = S_p
    else:
        S = S_p
return best
```

Este esquema mantiene un balance entre exploración global y explotación local, mejorando cohesión de grupos y balance por zonas con tiempos de cómputo moderados.

**Entrega 3 – Algoritmo Genético**
- `instances/entrega3.py` implementa un GA ligero sin dependencias externas. Cada individuo corresponde a la asignación completa (`día → empleado → escritorio`).
- Operadores: torneo de tamaño 3, cruce por corte de días y mutación por swap. El GA reutiliza el constructivo como generador inicial y la evaluación lexicográfica.
- Parámetros destacados: `--ngen`, `--pop-size`, `--cxpb`, `--mutpb`, `--top-k`, `--seed` y `--validate`. Por defecto se imprime el reporte y se exportan CSVs.
- Ejemplo: `python3 instances/entrega3.py --in instance3.json --ngen 25 --pop-size 25 --validate --outdir results_ga`.
- La función `run_ga` queda disponible para su uso desde `scripts/run_experiments.py`.

**Validación y Reporte**
- `--validate`: verifica por día empleados faltantes, escritorios inexistentes y duplicados; si hay errores, sale con código 2.
- `--report`: imprime, por día y totales, asignados y valores C1/C2/C3 para auditar la solución.

**Exportación A Plantilla (CSV)**
- Para cumplir la entrega tipo plantilla Excel, se generan CSVs equivalentes con `--export-csv`:
  - `EmployeeAssignment.csv`: columnas `[Employee, Day1, Day2, ...]` con `Dk` o `none`.
  - `Groups_Meeting_day.csv`: día de reunión por grupo (día con más miembros del grupo asignados).
  - `Summary.csv`: `Valid_assignments`, `Employee_preferences` (C1), `Isolated_employees`, y también `C2`, `C3`.
- Ubicación por defecto: `instances/solutions/csv_export/` (configurable con `--export-dir`).
- Abra cada CSV en Excel y copie su contenido a las hojas correspondientes de la plantilla oficial.

**Uso del CLI y scripts**
- `instances/entrega1.py`: admite `--method {constructive,local,sa}`, `--iters`, `--sa-iters`, `--tinit`, `--tfinal`, `--alpha`, `--report`, `--validate`, `--export-csv` y `--export-dir`. Ejemplo: `python3 instances/entrega1.py --in instance4.json --method sa --sa-iters 150 --report --validate`.
- `instances/entrega2.py`: recocido simulado con `--tinit/--tfinal/--alpha`, `--iters`, `--report`, `--validate` y `--export-csv`. Ejemplo: `python3 instances/entrega2.py --in instance6.json --iters 500 --report --validate --export-csv`.
- `instances/entrega2_ILS.py`: agrega `--ils`, `--ils-iters`, `--ls-iters`, `--perturb-k` y comparte las banderas de validación/reporte/exportación. Ejemplo: `python3 instances/entrega2_ILS.py --in instance6.json --ils --ils-iters 20 --ls-iters 600 --perturb-k 3 --report --validate`.
- `instances/entrega3.py`: GA con `--ngen`, `--pop-size`, `--cxpb`, `--mutpb`, `--top-k`, `--seed` y `--validate`. Siempre imprime el reporte y exporta CSVs en `--outdir`. Ejemplo: `python3 instances/entrega3.py --in instance8.json --ngen 25 --pop-size 25 --validate --outdir results_ga`.
- `scripts/run_experiments.py`: corre barridos sobre `instances/instance*.json`, soporta métodos `ent1_local, ent1_sa, sa, ils, ga`, controla semillas y parámetros principales y genera `results/experiments.csv`.
- `scripts/summarize_results.py` y `scripts/make_poster_assets.py`: generan `results/summary.csv`, `results/summary.md` y `results/poster.md` (más gráficas si hay `matplotlib`).


**Resultados y análisis – Entrega Final**
- `results/experiments.csv` contiene 10 instancias × 5 métodos × 3 semillas (ENT1_LOCAL, ENT1_SA, SA, ILS, GA). `results/summary.{csv,md}` resume promedios y mejores corridas.
- `results/poster.md` y las imágenes de `results/plots/` reúnen las tablas y gráficas para el reporte; `results/plots_svg/*.svg` son alternativas vectoriales.
- Descriptivo:
  - **Tiempo:** ENT1_LOCAL casi instantáneo; ENT1_SA/SA ≈0.7–3 s; ILS 0.4–2.3 s; GA 0.02–0.1 s.
  - **Calidad:** SA domina en 9/10 instancias; ILS mantiene buenas combinaciones C1/C2; el GA ofrece soluciones competitivas con muy bajo costo.
- **Prueba estadística:** la rúbrica exige incluir un test formal (ANOVA/Friedman/etc.) en el reporte. Los datos necesarios ya están en `results/experiments.csv`; el análisis debe realizarse y documentarse en el informe (actualmente sólo se incluye la comparación descriptiva).

**Guía Paso a Paso**
1. Ejecutar la entrega deseada:
   - Entrega 1 (local/SA): `python3 instances/entrega1.py --method local|sa ...`
   - Entrega 2 (SA): `python3 instances/entrega2.py --iters 500 --report --validate --export-csv`
   - Entrega 2 (ILS): `python3 instances/entrega2_ILS.py --ils --ils-iters 20 --ls-iters 600 --perturb-k 3 --report --validate --export-csv`
   - Entrega 3 (GA): `python3 instances/entrega3.py --ngen 25 --pop-size 25 --validate --outdir results_ga`
2. Pipeline completo:
   ```
   python3 scripts/run_experiments.py ...
   python3 scripts/summarize_results.py ...
   python3 scripts/make_poster_assets.py
   python3 scripts/make_simple_plots.py
   ```
3. Copiar los CSV finales (`instances/solutions`, `instances/results_sa`, `instances/results_ils`, `instances/results_ga/csv_export_instances`) a la plantilla oficial.
