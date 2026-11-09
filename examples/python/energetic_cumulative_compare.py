import os

from absl import flags
from ortools.sat.python import cp_model


print("TT_MODES =", os.environ.get("TT_MODES"))
flags.FLAGS(["energetic_cumulative_compare.py"])

HORIZON = 143   # sum of the longest mode of each task
# Resources 1-2 are renewable (rtype 1) -> add_cumulative.
# Resources 3-5 are non-renewable (rtype 2) -> sum over tasks of demand <= cap.
CAPACITIES = [18, 13, 39, 41, 73]
RENEWABLE = [True, True, False, False, False]

TASKS_MODES = [
    # task 1
    [(7, [0, 5, 0, 9, 9]), (8, [6, 0, 8, 0, 0]), (9, [3, 0, 7, 0, 8])],
    # task 2  (dup dur)
    [(4, [0, 6, 3, 2, 0]), (8, [4, 0, 0, 2, 0]), (8, [4, 0, 0, 0, 7])],
    # task 3
    [(1, [10, 0, 0, 7, 9]), (2, [5, 0, 0, 5, 0]), (9, [0, 3, 4, 3, 0])],
    # task 4
    [(4, [0, 6, 0, 0, 6]), (7, [0, 4, 0, 3, 0]), (10, [6, 0, 0, 0, 5])],
    # task 5  (dup dur)
    [(5, [0, 6, 3, 0, 4]), (5, [4, 0, 0, 0, 6]), (6, [2, 0, 0, 0, 2])],
    # task 6
    [(2, [9, 0, 0, 0, 6]), (3, [0, 10, 0, 0, 2]), (10, [0, 8, 0, 6, 0])],
    # task 7
    [(2, [10, 0, 0, 0, 9]), (6, [0, 7, 0, 7, 8]), (7, [0, 1, 8, 0, 6])],
    # task 8  (dup dur)
    [(4, [8, 0, 0, 6, 0]), (4, [0, 1, 7, 0, 4]), (10, [8, 0, 0, 0, 4])],
    # task 9  (dup dur)
    [(6, [6, 0, 0, 3, 0]), (10, [0, 9, 0, 0, 6]), (10, [4, 0, 9, 0, 0])],
    # task 10
    [(5, [0, 7, 0, 7, 10]), (6, [0, 7, 7, 7, 0]), (10, [0, 6, 6, 0, 0])],
    # task 11
    [(1, [1, 0, 0, 0, 7]), (7, [0, 2, 7, 0, 6]), (9, [0, 2, 6, 2, 5])],
    # task 12
    [(5, [0, 8, 5, 0, 10]), (8, [0, 5, 0, 2, 7]), (10, [8, 0, 0, 1, 6])],
    # task 13
    [(3, [9, 0, 0, 0, 7]), (5, [8, 0, 0, 5, 7]), (8, [6, 0, 0, 3, 6])],
    # task 14
    [(1, [0, 9, 0, 9, 7]), (3, [6, 0, 3, 4, 0]), (10, [0, 6, 2, 0, 0])],
    # task 15
    [(1, [7, 0, 0, 5, 8]), (6, [7, 0, 0, 4, 8]), (8, [0, 9, 0, 0, 4])],
    # task 16
    [(4, [6, 0, 9, 0, 0]), (7, [0, 5, 6, 6, 6]), (9, [0, 1, 5, 0, 0])],
]

TASK_WINDOWS = [
    (0, HORIZON - min(d for d, _ in m), min(d for d, _ in m), HORIZON)
    for m in TASKS_MODES
]

# 0-based (task i ends before task j starts), converted from succ
PRECEDENCES = [
    (0, 3), (0, 8), (0, 12),
    (1, 3), (1, 8), (1, 13),
    (2, 3), (2, 4),
    (3, 10),
    (4, 5), (4, 6), (4, 10),
    (5, 13), (5, 15),
    (6, 7), (6, 9), (6, 13),
    (7, 8), (7, 11),
    (8, 14), (8, 15),
    (9, 11), (9, 12),
    (10, 11),
    (11, 14),
    (12, 14), (12, 15),
]


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
            groups = {}
            for m, (d, _) in enumerate(modes):
                model.add(duration == d).only_enforce_if(literals[m])
                groups.setdefault(d, []).append(literals[m])
            for d, grp in groups.items():
                # fires only when every mode with this duration is false
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
    solver.parameters.cp_model_presolve = True
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