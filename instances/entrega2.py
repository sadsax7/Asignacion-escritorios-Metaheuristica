# Segunda entrega - Proyecto Heurística - Recocido Simulado
# Autores: [Alejandro Arango, Juan Jose Munoz]
# Universidad EAFIT - 2025

import json
import random
import math
import copy
import os
import csv
import sys
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional

# --- Utilidades y funciones auxiliares (idénticas a entrega1.py) ---
def build_desk_to_zone(desks_z: Dict[str, List[str]]) -> Dict[str, str]:
    d2z = {}
    for z, desks in desks_z.items():
        for d in desks:
            d2z[d] = z
    return d2z

def employee_group(emp: str, employees_g: Dict[str, List[str]]) -> Optional[str]:
    for g, members in employees_g.items():
        if emp in members:
            return g
    return None

def employees_present_today(day: str, days_e: Dict[str, List[str]], employees: List[str]) -> List[str]:
    if not days_e:
        return employees[:]
    return [e for e in employees if day in days_e.get(e, [])]

def constructive_assignment(instance: dict, seed: int = 42, randomize: bool = True, top_k_pref: int = 3) -> Dict[str, Dict[str, Optional[str]]]:
    rng = random.Random(seed)
    employees = instance["Employees"]
    desks = instance["Desks"]
    days = instance.get("Days", [])
    desks_e = instance.get("Desks_E", {})
    employees_g = instance.get("Employees_G", {})
    days_e = instance.get("Days_E", {})
    desks_z = instance.get("Desks_Z", {})
    d2z = build_desk_to_zone(desks_z)

    assignment: Dict[str, Dict[str, Optional[str]]] = {day: {} for day in days}

    for day in days:
        present = employees_present_today(day, days_e, employees)
        if randomize:
            rng.shuffle(present)
        used_desks = set()
        group_zone_count = defaultdict(Counter)

        for e in present:
            g = employee_group(e, employees_g)
            target_zone = group_zone_count[g].most_common(1)[0][0] if (g and group_zone_count[g]) else None

            pref_list = desks_e.get(e, [])
            pref_avail = [d for d in pref_list if d not in used_desks]
            pref_avail_target = [d for d in pref_avail if d2z.get(d) == target_zone] if target_zone else pref_avail[:]

            chosen = None
            if pref_avail_target:
                chosen = rng.choice(pref_avail_target[:min(top_k_pref, len(pref_avail_target))]) if randomize else pref_avail_target[0]
            elif pref_avail:
                chosen = rng.choice(pref_avail[:min(top_k_pref, len(pref_avail))]) if randomize else pref_avail[0]
            else:
                free_desks = [d for d in desks if d not in used_desks]
                free_target = [d for d in free_desks if d2z.get(d) == target_zone] if target_zone else free_desks[:]
                pool = free_target if free_target else free_desks
                chosen = rng.choice(pool) if (randomize and pool) else (pool[0] if pool else None)

            assignment[day][e] = chosen
            if chosen:
                used_desks.add(chosen)
                if g:
                    z = d2z.get(chosen)
                    if z:
                        group_zone_count[g][z] += 1

        for e in employees:
            assignment[day].setdefault(e, None)

    return assignment

def score_solution_lex(instance: dict, assignment: Dict[str, Dict[str, Optional[str]]]) -> Tuple[int, int, int]:
    desks_e = instance.get("Desks_E", {})
    employees_g = instance.get("Employees_G", {})
    desks_z = instance.get("Desks_Z", {})
    d2z = build_desk_to_zone(desks_z)
    days = instance.get("Days", [])
    employees = instance.get("Employees", [])

    c1_pref_hits, c2_group_cohesion, c3_balance = 0, 0, 0

    for day in days:
        for e in employees:
            d = assignment[day].get(e)
            if d and d in desks_e.get(e, []):
                c1_pref_hits += 1
        for g, members in employees_g.items():
            z_count = Counter()
            for e in members:
                d = assignment[day].get(e)
                if d:
                    z = d2z.get(d)
                    if z:
                        z_count[z] += 1
            if z_count:
                c2_group_cohesion += z_count.most_common(1)[0][1]
        z_occ = Counter()
        for e in employees:
            d = assignment[day].get(e)
            if d:
                z = d2z.get(d)
                if z:
                    z_occ[z] += 1
        if z_occ:
            mx, mn = max(z_occ.values()), min(z_occ.values())
            c3_balance += -(mx - mn)
    return (c1_pref_hits, c2_group_cohesion, c3_balance)


# ---------- Validación, reporte y exportación ----------
def _day_order(instance: dict) -> List[str]:
    return list(instance.get("Days", []))


def _groups_meeting_day(instance: dict, assignment: Dict[str, Dict[str, Optional[str]]]) -> Dict[str, str]:
    days = _day_order(instance)
    employees_g = instance.get("Employees_G", {})
    result: Dict[str, str] = {}
    for g, members in employees_g.items():
        best_day, best_count = None, -1
        for day in days:
            cnt = sum(1 for e in members if assignment.get(day, {}).get(e) is not None)
            if cnt > best_count:
                best_count = cnt
                best_day = day
        result[g] = best_day if best_day is not None else (days[0] if days else "")
    return result


def _isolated_employees(instance: dict, assignment: Dict[str, Dict[str, Optional[str]]]) -> Tuple[int, Dict[str, int]]:
    employees_g = instance.get("Employees_G", {})
    desks_z = instance.get("Desks_Z", {})
    d2z = build_desk_to_zone(desks_z)
    days = _day_order(instance)
    total = 0
    per_day: Dict[str, int] = {}
    emp2g: Dict[str, Optional[str]] = {}
    for g, members in employees_g.items():
        for e in members:
            emp2g[e] = g
    for day in days:
        m = assignment.get(day, {})
        group_zone = defaultdict(Counter)
        for e, d in m.items():
            if d is None:
                continue
            g = emp2g.get(e)
            if not g:
                continue
            z = d2z.get(d)
            if z:
                group_zone[g][z] += 1
        isolated = 0
        for e, d in m.items():
            if d is None:
                continue
            g = emp2g.get(e)
            if not g:
                continue
            z = d2z.get(d)
            if not z:
                continue
            if group_zone[g][z] <= 1:
                isolated += 1
        per_day[day] = isolated
        total += isolated
    return total, per_day


def validate_assignment(instance: dict, assignment: Dict[str, Dict[str, Optional[str]]]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    days = instance.get("Days", [])
    employees = set(instance.get("Employees", []))
    desks = set(instance.get("Desks", []))

    for day in days:
        if day not in assignment:
            errors.append(f"Falta el día en la solución: {day}")
            continue

        mapping = assignment[day]
        missing = [e for e in employees if e not in mapping]
        if missing:
            errors.append(f"Día {day}: faltan empleados {missing}")

        used = [d for d in mapping.values() if d is not None]
        bad = [d for d in used if d not in desks]
        if bad:
            errors.append(f"Día {day}: escritorios inexistentes {sorted(set(bad))}")
        seen, dup = set(), set()
        for d in used:
            if d in seen:
                dup.add(d)
            else:
                seen.add(d)
        if dup:
            errors.append(f"Día {day}: escritorios duplicados {sorted(dup)}")

    return (len(errors) == 0, errors)


def report_assignment(instance: dict, assignment: Dict[str, Dict[str, Optional[str]]]) -> None:
    desks_e = instance.get("Desks_E", {})
    employees_g = instance.get("Employees_G", {})
    desks_z = instance.get("Desks_Z", {})
    d2z = build_desk_to_zone(desks_z)
    days = instance.get("Days", [])
    employees = instance.get("Employees", [])

    total_c1 = total_c2 = total_c3 = 0
    print("Reporte por día:")
    for day in days:
        c1 = 0
        for e in employees:
            d = assignment[day].get(e)
            if d and d in desks_e.get(e, []):
                c1 += 1
        c2 = 0
        for g, members in employees_g.items():
            z_count = Counter()
            for e in members:
                d = assignment[day].get(e)
                if d:
                    z = d2z.get(d)
                    if z:
                        z_count[z] += 1
            if z_count:
                c2 += z_count.most_common(1)[0][1]
        z_occ = Counter()
        for e in employees:
            d = assignment[day].get(e)
            if d:
                z = d2z.get(d)
                if z:
                    z_occ[z] += 1
        c3 = 0
        if z_occ:
            mx, mn = max(z_occ.values()), min(z_occ.values())
            c3 = -(mx - mn)
        assigned = sum(1 for e in employees if assignment[day].get(e) is not None)
        print(f"- {day}: asignados={assigned} | C1={c1} C2={c2} C3={c3}")
        total_c1 += c1
        total_c2 += c2
        total_c3 += c3
    print(f"Totales: C1={total_c1} C2={total_c2} C3={total_c3}")


def export_csv_template(instance: dict, assignment: Dict[str, Dict[str, Optional[str]]], export_dir: str) -> None:
    os.makedirs(export_dir, exist_ok=True)
    days = _day_order(instance)
    employees = instance.get("Employees", [])

    emp_file = os.path.join(export_dir, "EmployeeAssignment.csv")
    with open(emp_file, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Employee"] + days)
        for e in employees:
            row = [e]
            for day in days:
                val = assignment.get(day, {}).get(e)
                row.append(val if val is not None else "none")
            w.writerow(row)

    gmd = _groups_meeting_day(instance, assignment)
    gmd_file = os.path.join(export_dir, "Groups_Meeting_day.csv")
    with open(gmd_file, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Group", "MeetingDay"])
        for g in instance.get("Employees_G", {}).keys():
            w.writerow([g, gmd.get(g, "")])

    valid = 0
    for day in days:
        valid += sum(1 for e in employees if assignment.get(day, {}).get(e) is not None)
    c1, c2, c3 = score_solution_lex(instance, assignment)
    iso_total, _ = _isolated_employees(instance, assignment)
    sum_file = os.path.join(export_dir, "Summary.csv")
    with open(sum_file, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Valid_assignments", "Employee_preferences", "Isolated_employees", "C2", "C3"])
        w.writerow([valid, c1, iso_total, c2, c3])

# --- Recocido Simulado ---
def generar_vecino_swap(assignment, instance):
    days = instance.get("Days", [])
    employees = instance.get("Employees", [])
    # Usar random global, no crear nueva instancia cada vez
    new = {d: m.copy() for d, m in assignment.items()}
    if not days:
        return new
    day = random.choice(days)
    assigned_today = [e for e in employees if new[day].get(e) is not None]
    if len(assigned_today) < 2:
        return new
    a, b = random.sample(assigned_today, 2)
    new[day][a], new[day][b] = new[day][b], new[day][a]
    return new

def generar_vecino_swap_simple(assignment):
    """Versión compatible con run_experiments.py"""
    days = list(assignment.keys())
    if not days:
        return copy.deepcopy(assignment)
    day = random.choice(days)
    employees = list(assignment[day].keys())
    new = {d: m.copy() for d, m in assignment.items()}
    if len(employees) < 2:
        return new
    a, b = random.sample(employees, 2)
    new[day][a], new[day][b] = new[day][b], new[day][a]
    return new


def simulated_annealing(solucion_inicial, evaluar, generar_vecino,
                        T_inicial=200.0, T_final=1.0, alpha=0.95, iter_por_temp=100):
    S = copy.deepcopy(solucion_inicial)
    mejor = copy.deepcopy(S)
    valor_S = evaluar(S)
    valor_mejor = valor_S
    T = T_inicial

    while T > T_final:
        for _ in range(iter_por_temp):
            vecino = generar_vecino(S)
            valor_vecino = evaluar(vecino)
            delta = valor_vecino - valor_S

            if delta > 0 or random.random() < math.exp(delta / T):
                S = copy.deepcopy(vecino)
                valor_S = valor_vecino

                if valor_S > valor_mejor:
                    mejor = copy.deepcopy(S)
                    valor_mejor = valor_S

        T *= alpha

    return mejor

# --- MAIN ---
if __name__ == "__main__":
    import os, argparse, sys

    parser = argparse.ArgumentParser(description="Entrega 2 - Constructivo + Recocido Simulado")
    parser.add_argument("--in", dest="infile", default="instance1.json",
                        help="Archivo de instancia (ej: instance1.json)")
    parser.add_argument("--outdir", default="solutions",
                        help="Carpeta de salida (se creará si no existe)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para aleatorización")
    parser.add_argument("--top-k", type=int, default=3, help="Top-k preferencias a muestrear")
    parser.add_argument("--iters", type=int, default=1000, help="Iteraciones por temperatura")
    parser.add_argument("--tinit", type=float, default=200.0, help="Temperatura inicial")
    parser.add_argument("--tfinal", type=float, default=1.0, help="Temperatura final")
    parser.add_argument("--alpha", type=float, default=0.95, help="Factor de enfriamiento")
    parser.add_argument("--stdout", action="store_true",
                        help="Imprime la solución por stdout en lugar de escribir archivo")
    parser.add_argument("--report", action="store_true", help="Imprime un reporte por día y totales")
    parser.add_argument("--validate", action="store_true", help="Valida la solución antes de guardar")
    parser.add_argument("--export-csv", action="store_true",
                        help="Exporta CSVs (EmployeeAssignment, Groups_Meeting_day, Summary)")
    parser.add_argument("--export-dir", default=None,
                        help="Carpeta para exportación CSV (por defecto usa --outdir/csv_export)")
    args = parser.parse_args()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    instance_file = os.path.join(BASE_DIR, args.infile)
    _out_raw = os.path.expanduser(os.path.expandvars(args.outdir))
    out_dir = _out_raw if os.path.isabs(_out_raw) else os.path.join(BASE_DIR, _out_raw)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"solution_{os.path.splitext(os.path.basename(args.infile))[0]}_annealing.json")

    print("--Script: ", __file__,"--")
    print("--BASE_DIR:", BASE_DIR,"--")
    print("--CWD:", os.getcwd(),"--")
    print("--Leyendo:", instance_file,"--")
    print("--Salida en:", out_file,"--")

    if not os.path.isfile(instance_file):
        print("ERROR: no encuentro la instancia:", instance_file)
        print("Archivos en la carpeta:", os.listdir(BASE_DIR))
        sys.exit(1)

    with open(instance_file, "r", encoding="utf-8") as f:
        instance = json.load(f)

    # Construcción inicial
    assignment = constructive_assignment(
        instance, seed=args.seed, randomize=True, top_k_pref=args.top_k
    )

    # Mejora con recocido simulado
    # Cambia la función de evaluación para priorizar C1, luego C2, luego C3
    def _score(s):
        c1, c2, c3 = score_solution_lex(instance, s)
        return c1 * 10000 + c2 * 100 + c3

    before = score_solution_lex(instance, assignment)
    assignment = simulated_annealing(
        assignment,
        evaluar=_score,
        generar_vecino=lambda s: generar_vecino_swap(s, instance),
        T_inicial=args.tinit, T_final=args.tfinal, alpha=args.alpha, iter_por_temp=args.iters
    )
    after = score_solution_lex(instance, assignment)
    print("Puntaje antes (C1, C2, C3):", before)
    print("Puntaje después (C1, C2, C3):", after)

    if args.validate:
        ok, errs = validate_assignment(instance, assignment)
        if ok:
            print("Validación: OK")
        else:
            print("Validación: errores encontrados:")
            for e in errs:
                print(" -", e)
            sys.exit(2)

    if args.report:
        report_assignment(instance, assignment)

    # Escritura
    if args.stdout:
        print(json.dumps(assignment, ensure_ascii=False, indent=2))
    else:
        try:
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(assignment, f, ensure_ascii=False, indent=2)
            print("-Solución guardada en:", out_file)
        except Exception as e:
            print("No pude escribir el archivo de salida:", e)
            print("Directorio existe?", os.path.isdir(os.path.dirname(out_file)), "->", os.path.dirname(out_file))
            raise

    if args.export_csv:
        export_dir = args.export_dir if args.export_dir else os.path.join(out_dir, "csv_export")
        export_dir = os.path.expanduser(os.path.expandvars(export_dir))
        if not os.path.isabs(export_dir):
            export_dir = os.path.join(BASE_DIR, export_dir)
        export_csv_template(instance, assignment, export_dir)
        print("-CSVs exportados en:", export_dir)

    print("Fin.")
