from absl import flags
from ortools.sat.python import cp_model

flags.FLAGS(["energetic_cumulative_compare.py"])

HORIZON = 60
CAPACITY = 8

TASKS_MODES = [
    [(6, 3), (3, 6), (3, 9)],
    [(5, 4), (2, 7), (4, 10)],
    [(4, 5), (2, 8), (1, 10)],
    [(7, 2), (3, 5), (1, 8)],
    [(5, 3), (4, 4), (3, 5)],
    [(6, 4), (3, 7), (2, 10), (1, 13)],
    [(3, 6), (2, 8), (1, 10)],
    [(4, 3), (2, 6), (1, 9)],
]

PRECEDENCES = [(0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7)]


def build_model():
    model = cp_model.CpModel()

    starts, ends, intervals, demands = [], [], [], []

    for i, modes in enumerate(TASKS_MODES):
        start = model.new_int_var(0, HORIZON, f"t{i}_start")
        end = model.new_int_var(0, HORIZON, f"t{i}_end")

        durations = [m[0] for m in modes]
        mode_demands = [m[1] for m in modes]

        if len(modes) > 1:
            literals = [model.new_bool_var(f"t{i}_mode_{r}") for r in range(len(modes))]
            model.add_exactly_one(literals)

            duration = model.new_int_var_from_domain(
                cp_model.Domain.from_values(durations), f"t{i}_duration"
            )
            demand = model.new_int_var_from_domain(
                cp_model.Domain.from_values(mode_demands), f"t{i}_demand"
            )
            for r in range(len(modes)):
                model.add(duration == durations[r]).only_enforce_if(literals[r])
                model.add(demand == mode_demands[r]).only_enforce_if(literals[r])
        else:
            duration = durations[0]
            demand = model.new_constant(mode_demands[0])

        interval = model.new_interval_var(start, duration, end, f"t{i}_interval")

        starts.append(start)
        ends.append(end)
        intervals.append(interval)
        demands.append(demand)

    for a, b in PRECEDENCES:
        model.add(ends[a] <= starts[b])

    model.add_cumulative(intervals, demands, CAPACITY)

    makespan = model.new_int_var(0, HORIZON, "makespan")
    model.add_max_equality(makespan, ends)
    model.minimize(makespan)

    return model


def solve_and_report(use_overload_checker: bool, log_path: str):
    model = build_model()
    solver = cp_model.CpSolver()

    solver.parameters.num_search_workers = 1
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
            print(f"  (note: flag '{flag_name}' not found on this OR-Tools "
                  f"version -- skipped, not pinned)")

    solver.parameters.log_search_progress = False
    solver.parameters.log_subsolver_statistics = False
    status = solver.solve(model)  
    log_lines = []
    solver.log_callback = log_lines.append

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    label = "Avec energetic overload-checker" if use_overload_checker else "Sans (default)"
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print("objective:       ", solver.objective_value)
    print("branches:        ", solver.num_branches)
    print("conflicts:       ", solver.num_conflicts)
    print("propagations:    ", solver.num_integer_propagations)
    print("binary_props:    ", solver.num_binary_propagations)
    print("wall_time:       ", solver.wall_time)
    print(f"full log written to: {log_path}")


def main():
    solve_and_report(use_overload_checker=False, log_path="run_without.log")
    solve_and_report(use_overload_checker=True, log_path="run_with.log")

if __name__ == "__main__":
    main()