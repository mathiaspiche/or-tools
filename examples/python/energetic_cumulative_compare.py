import os

from absl import flags
from ortools.sat.python import cp_model


print("TT_MODES =", os.environ.get("TT_MODES"))
flags.FLAGS(["energetic_cumulative_compare.py"])

HORIZON = 402   # sum of the longest mode of each task
CAPACITIES = [29, 28, 124, 160]
RENEWABLE = [True, True, False, False]

TASKS_MODES = [
    # task 1  (dummy)
    [(0, [0, 0, 0, 0])],
    # task 2
    [(6, [4, 9, 0, 3]), (9, [2, 8, 1, 0]), (10, [1, 8, 1, 0])],
    # task 3
    [(3, [4, 4, 0, 9]), (5, [4, 4, 0, 8]), (8, [2, 4, 0, 9])],
    # task 4
    [(6, [3, 6, 6, 0]), (7, [3, 5, 0, 9]), (9, [2, 1, 0, 9])],
    # task 5
    [(1, [9, 8, 0, 9]), (5, [8, 6, 4, 0]), (6, [8, 3, 0, 7])],
    # task 6
    [(6, [5, 9, 0, 7]), (7, [4, 5, 0, 7]), (9, [4, 2, 0, 5])],
    # task 7
    [(2, [5, 6, 8, 0]), (7, [5, 5, 0, 5]), (10, [3, 3, 5, 0])],
    # task 8
    [(1, [6, 8, 0, 8]), (3, [6, 6, 5, 0]), (9, [6, 6, 0, 8])],
    # task 9
    [(2, [6, 2, 0, 6]), (8, [6, 2, 0, 5]), (10, [6, 2, 0, 4])],
    # task 10
    [(2, [5, 9, 4, 0]), (5, [4, 7, 3, 0]), (6, [3, 7, 0, 8])],
    # task 11
    [(4, [2, 6, 0, 8]), (6, [1, 5, 4, 0]), (9, [1, 4, 0, 5])],
    # task 12
    [(5, [4, 8, 1, 0]), (7, [3, 7, 1, 0]), (9, [2, 6, 0, 4])],
    # task 13
    [(1, [8, 4, 0, 8]), (8, [6, 3, 0, 8]), (10, [6, 2, 5, 0])],
    # task 14
    [(3, [5, 3, 0, 6]), (4, [3, 2, 0, 5]), (5, [3, 1, 7, 0])],
    # task 15
    [(3, [10, 8, 0, 5]), (6, [4, 6, 0, 4]), (9, [3, 6, 3, 0])],
    # task 16
    [(1, [6, 7, 1, 0]), (2, [5, 6, 0, 6]), (10, [5, 3, 1, 0])],
    # task 17
    [(3, [7, 7, 0, 8]), (4, [4, 4, 0, 6]), (7, [2, 2, 5, 0])],
    # task 18
    [(4, [10, 5, 8, 0]), (5, [10, 4, 5, 0]), (8, [10, 4, 4, 0])],
    # task 19
    [(2, [5, 4, 0, 7]), (6, [3, 4, 0, 7]), (9, [3, 4, 3, 0])],
    # task 20
    [(3, [8, 10, 8, 0]), (9, [5, 5, 0, 7]), (10, [3, 1, 0, 4])],
    # task 21
    [(3, [8, 6, 0, 8]), (4, [8, 5, 5, 0]), (5, [8, 5, 0, 4])],
    # task 22
    [(2, [7, 9, 0, 8]), (6, [7, 5, 0, 7]), (7, [5, 4, 0, 7])],
    # task 23
    [(1, [8, 7, 4, 0]), (6, [8, 7, 3, 0]), (10, [7, 7, 0, 6])],
    # task 24
    [(5, [7, 10, 0, 8]), (6, [4, 5, 7, 0]), (7, [2, 4, 7, 0])],
    # task 25
    [(4, [9, 8, 0, 9]), (5, [6, 7, 0, 9]), (8, [4, 7, 7, 0])],
    # task 26
    [(3, [9, 9, 5, 0]), (7, [6, 8, 3, 0]), (8, [3, 7, 3, 0])],
    # task 27
    [(4, [10, 8, 8, 0]), (6, [10, 5, 4, 0]), (10, [10, 1, 0, 4])],
    # task 28
    [(3, [6, 5, 0, 7]), (4, [6, 3, 0, 6]), (8, [6, 1, 0, 6])],
    # task 29
    [(2, [10, 6, 10, 0]), (5, [8, 5, 5, 0]), (8, [8, 5, 0, 8])],
    # task 30
    [(2, [10, 2, 9, 0]), (7, [9, 1, 6, 0]), (8, [7, 1, 4, 0])],
    # task 31
    [(2, [2, 3, 9, 0]), (4, [1, 3, 0, 6]), (7, [1, 3, 5, 0])],
    # task 32
    [(7, [4, 5, 0, 3]), (9, [4, 4, 5, 0]), (10, [4, 4, 0, 2])],
    # task 33
    [(4, [2, 9, 7, 0]), (5, [1, 9, 4, 0]), (9, [1, 9, 3, 0])],
    # task 34  (dup dur)
    [(4, [6, 4, 4, 0]), (4, [5, 3, 0, 8]), (6, [5, 3, 2, 0])],
    # task 35
    [(2, [8, 10, 9, 0]), (6, [8, 8, 0, 6]), (7, [6, 8, 0, 6])],
    # task 36
    [(1, [10, 2, 0, 4]), (4, [4, 2, 2, 0]), (6, [2, 2, 0, 2])],
    # task 37
    [(4, [4, 5, 4, 0]), (5, [3, 4, 4, 0]), (7, [1, 1, 0, 2])],
    # task 38
    [(2, [6, 7, 0, 9]), (4, [5, 4, 0, 8]), (10, [4, 1, 0, 7])],
    # task 39  (dup dur)
    [(2, [5, 7, 5, 0]), (3, [4, 5, 0, 5]), (3, [4, 4, 1, 0])],
    # task 40  (dup dur)
    [(2, [8, 4, 0, 3]), (8, [6, 4, 0, 2]), (8, [2, 4, 5, 0])],
    # task 41
    [(1, [7, 8, 0, 2]), (5, [6, 7, 4, 0]), (9, [4, 6, 3, 0])],
    # task 42
    [(5, [4, 5, 5, 0]), (6, [3, 5, 0, 6]), (7, [2, 4, 2, 0])],
    # task 43
    [(3, [4, 7, 9, 0]), (4, [4, 5, 0, 5]), (8, [3, 3, 8, 0])],
    # task 44
    [(6, [3, 10, 0, 8]), (7, [1, 7, 8, 0]), (10, [1, 6, 0, 4])],
    # task 45  (dup dur)
    [(3, [7, 8, 4, 0]), (5, [4, 5, 3, 0]), (5, [4, 2, 0, 3])],
    # task 46
    [(1, [10, 9, 0, 2]), (6, [8, 8, 0, 2]), (7, [5, 8, 5, 0])],
    # task 47
    [(5, [8, 9, 5, 0]), (6, [5, 7, 0, 3]), (9, [2, 5, 3, 0])],
    # task 48
    [(3, [9, 7, 0, 6]), (4, [7, 4, 0, 5]), (9, [5, 4, 0, 5])],
    # task 49
    [(3, [6, 8, 0, 6]), (4, [5, 7, 0, 6]), (7, [4, 7, 1, 0])],
    # task 50
    [(4, [6, 7, 8, 0]), (6, [4, 6, 8, 0]), (10, [4, 5, 0, 3])],
    # task 51  (dup dur)
    [(2, [7, 7, 7, 0]), (6, [5, 6, 6, 0]), (6, [3, 6, 0, 4])],
    # task 52  (dummy)
    [(0, [0, 0, 0, 0])],
]

TASK_WINDOWS = [
    (0, HORIZON - min(d for d, _ in m), min(d for d, _ in m), HORIZON)
    for m in TASKS_MODES
]

# 0-based (task i ends before task j starts)
PRECEDENCES = [
    (0, 1), (0, 2), (0, 3), (0, 12),
    (1, 14), (1, 5), (1, 4),
    (2, 14), (2, 10), (2, 9), (2, 5),
    (3, 14), (3, 10), (3, 9), (3, 7),
    (4, 9), (4, 8), (4, 6),
    (5, 21), (5, 17), (5, 16), (5, 15), (5, 13),
    (6, 21), (6, 17), (6, 16), (6, 15), (6, 13),
    (7, 21), (7, 17), (7, 13), (7, 11),
    (8, 24), (8, 21), (8, 17), (8, 15), (8, 13),
    (9, 21), (9, 17), (9, 11),
    (10, 24), (10, 21), (10, 17), (10, 13),
    (11, 24), (11, 19), (11, 15),
    (12, 21), (12, 19), (12, 15),
    (13, 27), (13, 25), (13, 20), (13, 19), (13, 18),
    (14, 15),
    (15, 27), (15, 25), (15, 20), (15, 18),
    (16, 27), (16, 24), (16, 20), (16, 18),
    (17, 28), (17, 27), (17, 20), (17, 19),
    (18, 34), (18, 31), (18, 22),
    (19, 31), (19, 30), (19, 23),
    (20, 30), (20, 23),
    (21, 37), (21, 36), (21, 35), (21, 34), (21, 33), (21, 30), (21, 29), (21, 28),
    (22, 37), (22, 36), (22, 35), (22, 33), (22, 30), (22, 29), (22, 28),
    (23, 36), (23, 35), (23, 26),
    (24, 37), (24, 36), (24, 34), (24, 33), (24, 30), (24, 29),
    (25, 37), (25, 36), (25, 35), (25, 30), (25, 29),
    (26, 38), (26, 37), (26, 34), (26, 33), (26, 29),
    (27, 40), (27, 35), (27, 33), (27, 32),
    (28, 41), (28, 40), (28, 32),
    (29, 40), (29, 32),
    (30, 49), (30, 47), (30, 41), (30, 39), (30, 38),
    (31, 50), (31, 46), (31, 42), (31, 40), (31, 37),
    (32, 50), (32, 49), (32, 47), (32, 45), (32, 42), (32, 39),
    (33, 50), (33, 49), (33, 47), (33, 46), (33, 45), (33, 42), (33, 41),
    (34, 48), (34, 46), (34, 42), (34, 41), (34, 40),
    (35, 49), (35, 48), (35, 47), (35, 46), (35, 45), (35, 44), (35, 42),
    (36, 50), (36, 47), (36, 46), (36, 45), (36, 44), (36, 42),
    (37, 49), (37, 48), (37, 45), (37, 44), (37, 43),
    (38, 46), (38, 45), (38, 44), (38, 42),
    (39, 48), (39, 46), (39, 44), (39, 43),
    (40, 47), (40, 45),
    (41, 44), (41, 43),
    (42, 43),
    (43, 51),
    (44, 51),
    (45, 51),
    (46, 51),
    (47, 51),
    (48, 51),
    (49, 51),
    (50, 51),
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