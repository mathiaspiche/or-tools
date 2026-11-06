import os

from absl import flags
from ortools.sat.python import cp_model


print("TT_MODES =", os.environ.get("TT_MODES"))
flags.FLAGS(["energetic_cumulative_compare.py"])

HORIZON = 60
CAPACITIES = [3]
TASKS_MODES = [
    [(12, [1])],                 
    [(1, [1])],                  
    [(1, [1])],                  
    [(1, [1])],                  
    [(1, [3]), (3, [2])],        
]
TASK_WINDOWS = [
    (0, 0, 12, 12),
    (2, 2, 3, 3),
    (5, 5, 6, 6),
    (8, 8, 9, 9),
    (0, 9, 1, 12),
]

PRECEDENCES = []


def build_model():
    model = cp_model.CpModel()
    num_res = len(CAPACITIES)
    starts, ends, intervals = [], [], []
    demands = [[] for _ in range(num_res)]
    mode_lits = {}
    for i, modes in enumerate(TASKS_MODES):
        est, lst, ect, lct = TASK_WINDOWS[i]
        durations = [d for d, _ in modes]
        dmin = min(durations)

        if ect < est + dmin or lst > lct - dmin:
            print(f"  (note: task {i} window is looser than min duration "
                  f"{dmin} allows; CP-SAT will tighten it)")

        start = model.new_int_var(est, lst, f"start_{i}")
        end = model.new_int_var(ect, lct, f"end_{i}")

        if len(modes) > 1:
            literals = [model.new_bool_var(f"t{i}_mode_{m}") for m in range(len(modes))]
            model.add_exactly_one(literals)
            mode_lits[i] = literals

            duration = model.new_int_var_from_domain(
                cp_model.Domain.from_values(durations), f"t{i}_duration")
            # MPS : equivalence mode <=> duree (une seule fois, hors de la boucle des ressources)
            for m, (d, _) in enumerate(modes):
                model.add(duration == d).only_enforce_if(literals[m])
                model.add(duration != d).only_enforce_if(literals[m].negated())

            for k in range(num_res):
                values_k = [req[k] for _, req in modes]
                demand_k = model.new_int_var_from_domain(
                    cp_model.Domain.from_values(values_k), f"t{i}_demand_r{k}")
                for m, (_, req) in enumerate(modes):
                    model.add(demand_k == req[k]).only_enforce_if(literals[m])
                demands[k].append(demand_k)
        else:
            duration = durations[0]
            for k in range(num_res):
                demands[k].append(model.new_constant(modes[0][1][k]))

        intervals.append(model.new_interval_var(start, duration, end, f"t{i}_interval"))
        starts.append(start)
        ends.append(end)

    for a, b in PRECEDENCES:
        model.add(ends[a] <= starts[b])

    for k in range(num_res):
        model.add_cumulative(intervals, demands[k], CAPACITIES[k])

    makespan = model.new_int_var(0, HORIZON, "makespan")
    model.add_max_equality(makespan, ends)
    model.minimize(makespan)
    return model


def solve_and_report(use_overload_checker: bool, log_path: str):
    model = build_model()
    solver = cp_model.CpSolver()

    solver.parameters.num_workers = 1
    solver.parameters.random_seed = 1
    solver.parameters.use_overload_checker_in_cumulative = use_overload_checker

    for flag_name, value in [
        ("use_timetable_edge_finding_in_cumulative", False),
        ("use_conservative_scale_overload_checker", False),
        ("use_disjunctive_constraint_in_cumulative", False),
        ("use_hard_precedences_in_cumulative", False),
    ]:
        if hasattr(solver.parameters, flag_name):
            setattr(solver.parameters, flag_name, value)
        else:
            print(f"  (note: flag '{flag_name}' not found, skipped)")

    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False      # log seulement dans le fichier
    solver.parameters.log_subsolver_statistics = False
    solver.parameters.cp_model_presolve = False
    solver.parameters.cp_model_probing_level = 0
    solver.parameters.linearization_level = 0
    solver.parameters.symmetry_level = 0
    solver.parameters.search_branching = cp_model.FIXED_SEARCH

    log_lines = []
    solver.log_callback = log_lines.append

    status = solver.solve(model)

    log_path = os.path.abspath(log_path)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    label = "Avec energetic overload-checker" if use_overload_checker else "Sans (default)"
    print(f"\n{'=' * 60}\n  {label}\n{'=' * 60}")
    print(f"log : {len(log_lines)} lignes ecrites dans {log_path}")
    print("status:          ", solver.status_name(status))
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("objective:       ", solver.objective_value)
        for i, v in enumerate(model.proto.variables):
            var = model.get_int_var_from_proto_index(i)
            print(f"  x{i} ({v.name or 'constante'}) = {solver.value(var)}")
    print("branches:        ", solver.num_branches)
    print("conflicts:       ", solver.num_conflicts)
    print("propagations:    ", solver.num_integer_propagations)
    print("binary_props:    ", solver.num_binary_propagations)
    print("wall_time:       ", solver.wall_time)


def main():
    solve_and_report(use_overload_checker=False, log_path="run_without.log")


if __name__ == "__main__":
    main()