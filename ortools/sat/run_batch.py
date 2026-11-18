import argparse
import csv
import fnmatch
import os
import re
import sys

from ortools.sat.python import cp_model

try:
    import ortools
    ORTOOLS_VERSION = getattr(ortools, "__version__", "?")
except Exception:  
    ORTOOLS_VERSION = "?"

COLUMNS = [
    "label", "instance", "n_jobs", "status", "objective", "best_bound",
    "conflicts", "branches", "integer_propagations", "binary_propagations",
    "wall_time", "time_limit", "ortools_version",
]


def parse(path):
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()

    def norm(s):
        return s.replace(" ", "").upper()

    def find(prefix):
        p = norm(prefix)
        for i, l in enumerate(lines):
            if norm(l.strip()).startswith(p):
                return i
        raise ValueError(f"section '{prefix}' not found")

    def number(prefix):
        return int(re.search(r":\s*(\d+)", lines[find(prefix)]).group(1))

    n_jobs = number("jobs")
    n_ren = number("- renewable")
    n_non = number("- nonrenewable")
    if number("- doubly"):
        raise ValueError("doubly constrained resources are not supported")
    n_res = n_ren + n_non

    i = find("PRECEDENCE RELATIONS") + 2
    n_modes, succ = {}, {}
    for _ in range(n_jobs):
        f = lines[i].split()
        j, nm, ns = int(f[0]), int(f[1]), int(f[2])
        n_modes[j] = nm
        succ[j] = [int(x) for x in f[3:3 + ns]]
        i += 1

    i = find("REQUESTS/DURATIONS") + 3
    modes = {}
    cur = None
    for _ in range(sum(n_modes.values())):
        f = [int(x) for x in lines[i].split()]
        if len(f) == 3 + n_res:         
            cur, f = f[0], f[1:]
        modes.setdefault(cur, []).append((f[1], f[2:2 + n_res]))
        i += 1

    i = find("RESOURCE AVAILABILITIES") + 2
    caps = [int(x) for x in lines[i].split()]

    for j in range(1, n_jobs + 1):
        if len(modes[j]) != n_modes[j]:
            raise ValueError(f"job {j}: mode count mismatch")

    horizon = sum(max(d for d, _ in modes[j]) for j in range(1, n_jobs + 1))
    tasks_modes = [modes[j] for j in range(1, n_jobs + 1)]
    task_windows = [
        (0, horizon - min(d for d, _ in m), min(d for d, _ in m), horizon)
        for m in tasks_modes
    ]
    precedences = [(j - 1, s - 1) for j in range(1, n_jobs + 1) for s in succ[j]]
    renewable = [True] * n_ren + [False] * n_non
    return dict(horizon=horizon, capacities=caps, renewable=renewable,
                tasks_modes=tasks_modes, task_windows=task_windows,
                precedences=precedences, n_jobs=n_jobs)


def build_model(data):
    HORIZON = data["horizon"]
    CAPACITIES = data["capacities"]
    RENEWABLE = data["renewable"]
    TASKS_MODES = data["tasks_modes"]
    TASK_WINDOWS = data["task_windows"]
    PRECEDENCES = data["precedences"]

    model = cp_model.CpModel()
    num_res = len(CAPACITIES)
    starts, ends, intervals = [], [], []
    demands = [[] for _ in range(num_res)]
    mode_lits = {}
    for i, modes in enumerate(TASKS_MODES):
        est, lst, ect, lct = TASK_WINDOWS[i]
        durations = [d for d, _ in modes]

        start = model.new_int_var(est, lst, f"start_{i}")
        end = model.new_int_var(ect, lct, f"end_{i}")

        if len(modes) > 1:
            literals = [model.new_bool_var(f"t{i}_mode_{m}") for m in range(len(modes))]
            model.add_exactly_one(literals)
            mode_lits[i] = literals

            duration = model.new_int_var_from_domain(
                cp_model.Domain.from_values(durations), f"t{i}_duration")
            groups = {}
            for m, (d, _) in enumerate(modes):
                model.add(duration == d).only_enforce_if(literals[m])
                groups.setdefault(d, []).append(literals[m])
            for d, grp in groups.items():
                model.add(duration != d).only_enforce_if([l.negated() for l in grp])

            for k in range(num_res):
                if not RENEWABLE[k]:
                    continue
                values_k = [req[k] for _, req in modes]
                demand_k = model.new_int_var_from_domain(
                    cp_model.Domain.from_values(values_k), f"t{i}_demand_r{k}")
                for m, (_, req) in enumerate(modes):
                    model.add(demand_k == req[k]).only_enforce_if(literals[m])
                demands[k].append(demand_k)
        else:
            literals = None
            duration = durations[0]
            for k in range(num_res):
                if RENEWABLE[k]:
                    demands[k].append(model.new_constant(modes[0][1][k]))

        mode_lits.setdefault(i, literals)
        intervals.append(model.new_interval_var(start, duration, end, f"t{i}_interval"))
        starts.append(start)
        ends.append(end)

    for a, b in PRECEDENCES:
        model.add(ends[a] <= starts[b])

    for k in range(num_res):
        if RENEWABLE[k]:
            model.add_cumulative(intervals, demands[k], CAPACITIES[k])
        else:
            total = 0
            for i, modes in enumerate(TASKS_MODES):
                if mode_lits[i] is None:
                    total += modes[0][1][k]
                else:
                    total += sum(l * req[k] for l, (_, req) in zip(mode_lits[i], modes))
            model.add(total <= CAPACITIES[k])

    makespan = model.new_int_var(0, HORIZON, "makespan")
    model.add_max_equality(makespan, ends)
    model.minimize(makespan)
    return model


def solve(model, args):
    solver = cp_model.CpSolver()
    p = solver.parameters
    p.num_workers = args.workers
    p.random_seed = args.seed
    p.max_time_in_seconds = args.time
    if args.det is not None:
        p.max_deterministic_time = args.det
    p.use_overload_checker_in_cumulative = False
    for flag_name, value in [
        ("use_timetable_edge_finding_in_cumulative", False),
        ("use_conservative_scale_overload_checker", False),
        ("use_disjunctive_constraint_in_cumulative", False),
        ("use_hard_precedences_in_cumulative", False),
    ]:
        if hasattr(p, flag_name):
            setattr(p, flag_name, value)
    p.log_search_progress = False
    p.cp_model_presolve = True
    p.cp_model_probing_level = 0
    p.linearization_level = 0
    p.symmetry_level = 0
    status = solver.solve(model)
    return solver, status


def already_done(csv_path):
    done = set()
    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add((row["label"], row["instance"]))
    return done


def append_row(csv_path, row):
    new_file = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            w.writeheader()
        w.writerow(row)
        f.flush()
        os.fsync(f.fileno())


def _fmt(x, decimals=0):
    """Nombre lisible : 1234567 -> '1 234 567' ; vide si absent."""
    if x in ("", None):
        return "-"
    try:
        v = float(x)
    except ValueError:
        return str(x)
    if decimals == 0 and v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.{decimals}f}".replace(",", " ")


def _md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def write_table(csv_path):
    """Regenere <csv>.md : un tableau par serie, puis une comparaison des series."""
    import statistics
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    labels = []
    for r in rows:
        if r["label"] not in labels:
            labels.append(r["label"])
    by = {lab: {r["instance"]: r for r in rows if r["label"] == lab} for lab in labels}

    md = ["# Resultats CP-SAT sur instances PSPLIB multi-modes", ""]
    for lab in labels:
        rs = list(by[lab].values())
        n_opt = sum(1 for r in rs if r["status"] == "OPTIMAL")
        confl = [float(r["conflicts"]) for r in rs if r["conflicts"] != ""]
        md.append(f"## Serie `{lab}` (OR-Tools {rs[0]['ortools_version']}, "
                  f"limite {rs[0]['time_limit']} s)")
        md.append("")
        md.append(_md_table(
            ["Instance", "Statut", "Objectif", "Conflits", "Branches",
             "Propagations entieres", "Propagations binaires", "Temps (s)"],
            [[r["instance"], r["status"], _fmt(r["objective"]), _fmt(r["conflicts"]),
              _fmt(r["branches"]), _fmt(r["integer_propagations"]),
              _fmt(r["binary_propagations"]), _fmt(r["wall_time"], 3)] for r in rs]))
        md.append("")
        resume = f"{n_opt}/{len(rs)} instances a l'optimum"
        if confl:
            resume += f" ; mediane des conflits : {_fmt(statistics.median(confl))}"
        md.append(f"**Resume** : {resume}.")
        md.append("")

    if len(labels) >= 2:
        ref = "stock" if "stock" in labels else labels[0]
        for lab in labels:
            if lab == ref:
                continue
            common = [i for i in by[ref] if i in by[lab]]
            if not common:
                continue
            table, ratios, n_diff = [], [], 0
            for i in common:
                a, b = by[ref][i], by[lab][i]
                ratio = "-"
                if a["conflicts"] != "" and b["conflicts"] != "" and float(a["conflicts"]) > 0:
                    q = float(b["conflicts"]) / float(a["conflicts"])
                    ratio = f"{q:.2f}"
                    if a["status"] == "OPTIMAL" and b["status"] == "OPTIMAL":
                        ratios.append(q)
                same = "-"
                if a["status"] == "OPTIMAL" and b["status"] == "OPTIMAL":
                    same = "oui" if a["objective"] == b["objective"] else "NON"
                    n_diff += same == "NON"
                table.append([i, _fmt(a["conflicts"]), _fmt(b["conflicts"]), ratio,
                              _fmt(a["objective"]), _fmt(b["objective"]), same])
            md.append(f"## Comparaison `{lab}` contre `{ref}`")
            md.append("")
            md.append(_md_table(
                ["Instance", f"Conflits {ref}", f"Conflits {lab}", "Rapport",
                 f"Objectif {ref}", f"Objectif {lab}", "Objectifs egaux"], table))
            md.append("")
            line = f"{len(common)} instances communes"
            if ratios:
                line += (f" ; mediane du rapport des conflits (instances a l'optimum "
                         f"des deux cotes) : {statistics.median(ratios):.2f}")
            line += f" ; objectifs differents : {n_diff}"
            md.append(f"**Resume** : {line}. (Rapport < 1 : `{lab}` a moins de conflits.)")
            md.append("")

    path = os.path.splitext(csv_path)[0] + ".md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return path


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", default=os.path.join(here, "instances_mmrcpsp"))
    ap.add_argument("--pattern", default="J50*.mm")
    ap.add_argument("--label", default=None)
    ap.add_argument("--time", type=float, default=60.0)
    ap.add_argument("--det", type=float, default=None)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="benchmarks_TT.csv")
    ap.add_argument("--max", type=int, default=None)
    args = ap.parse_args()

    tt = os.environ.get("TT_MODES")
    label = args.label or ("stock" if tt is None else f"tt_modes{tt}")

    if not os.path.isdir(args.folder):
        sys.exit(f"dossier introuvable : {args.folder}")
    files = sorted(f for f in os.listdir(args.folder)
                   if fnmatch.fnmatch(f, args.pattern))
    if not files:
        sys.exit(f"aucun fichier '{args.pattern}' dans {args.folder}")

    print(f"ortools {ORTOOLS_VERSION} | serie '{label}' | {len(files)} instances | "
          f"limite {args.time}s | sortie {os.path.abspath(args.out)}")
    done = already_done(args.out)
    n_new = 0
    for name in files:
        if (label, name) in done:
            continue
        if args.max is not None and n_new >= args.max:
            break
        row = {c: "" for c in COLUMNS}
        row.update(label=label, instance=name, time_limit=args.time,
                   ortools_version=ORTOOLS_VERSION)
        try:
            data = parse(os.path.join(args.folder, name))
            row["n_jobs"] = data["n_jobs"]
            solver, status = solve(build_model(data), args)
            row["status"] = solver.status_name(status)
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                row["objective"] = solver.objective_value
                row["best_bound"] = solver.best_objective_bound
            row["conflicts"] = solver.num_conflicts
            row["branches"] = solver.num_branches
            row["integer_propagations"] = solver.num_integer_propagations
            row["binary_propagations"] = solver.num_binary_propagations
            row["wall_time"] = round(solver.wall_time, 3)
        except Exception as e: 
            row["status"] = f"ERROR: {type(e).__name__}: {e}"[:200]
        append_row(args.out, row)
        write_table(args.out)
        n_new += 1
        print(f"{name:14s} {row['status']:10s} obj={row['objective']!s:7s} "
              f"conflicts={row['conflicts']!s:8s} propag={row['integer_propagations']!s:9s} "
              f"t={row['wall_time']}")
    if os.path.exists(args.out):
        print(f"tableau : {write_table(args.out)}")
    print(f"termine : {n_new} nouvelle(s) instance(s) ecrite(s) dans {args.out}")


if __name__ == "__main__":
    main()