"""
Minimal, self-contained RCPSP example.

Builds a small RcpspProblem by hand (no external .sm/.mm file needed),
feeds it into solve_rcpsp(), and turns on verbose CP-SAT logging so you
can observe cumulative-constraint-related activity in the solver output.

Usage:
    python rcpsp_example.py

Requires:
    pip install ortools
    A local checkout of the or-tools repo, so solve_rcpsp can be imported
    from examples/python/rcpsp_sat.py. Adjust EXAMPLES_DIR below to point
    at your checkout.
"""

import sys

# --- Point this at your local or-tools checkout's examples/python folder ---
EXAMPLES_DIR = r"C:\Users\mathi\or-tools\examples\python"
sys.path.insert(0, EXAMPLES_DIR)

from ortools.scheduling import rcpsp_pb2
from rcpsp_sat import solve_rcpsp  # noqa: E402 (import after sys.path tweak)
from absl import flags
flags.FLAGS(["rcpsp_example.py"])  # minimal fake argv to trigger flag parsing

def build_toy_problem() -> rcpsp_pb2.RcpspProblem:
    """Builds a tiny multi-mode RCPSP instance by hand.

    Structure:
        source (0) -> task 1 -> task 2 -> sink (3)
                          \\-> task 3 ->/

    Two renewable resources. Task 1 has two modes (fast/expensive vs
    slow/cheap) so you can see mode-selection + decomposed-energy
    machinery engage. Tasks 2 and 3 are single-mode.
    """
    problem = rcpsp_pb2.RcpspProblem()
    problem.name = "toy_multi_mode"
    problem.horizon = 50
    problem.deadline = -1
    problem.is_rcpsp_max = False
    problem.is_resource_investment = False
    problem.is_consumer_producer = False

    # Two renewable resources.
    for cap in (4, 3):
        res = problem.resources.add()
        res.renewable = True
        res.max_capacity = cap

    # --- Task 0: source sentinel ---
    source = problem.tasks.add()
    source.recipes.add().duration = 0
    source.successors.append(1)

    # --- Task 1: multi-mode task ---
    task1 = problem.tasks.add()
    # Mode 0: slower, lighter on resources.
    m0 = task1.recipes.add()
    m0.duration = 6
    m0.demands.append(2)
    m0.resources.append(0)
    # Mode 1: faster, heavier on resources.
    m1 = task1.recipes.add()
    m1.duration = 3
    m1.demands.append(4)
    m1.resources.append(0)
    m1.demands.append(2)
    m1.resources.append(1)
    task1.successors.extend([2, 3])

    # --- Task 2: single-mode ---
    task2 = problem.tasks.add()
    r2 = task2.recipes.add()
    r2.duration = 4
    r2.demands.append(1)
    r2.resources.append(1)
    task2.successors.append(4)

    # --- Task 3: single-mode ---
    task3 = problem.tasks.add()
    r3 = task3.recipes.add()
    r3.duration = 5
    r3.demands.append(3)
    r3.resources.append(0)
    task3.successors.append(4)

    # --- Task 4: sink sentinel ---
    sink = problem.tasks.add()
    sink.recipes.add().duration = 0

    return problem


def main():
    from absl import flags
    flags.FLAGS(["rcpsp_example.py"])

    print("Starting...", flush=True)
    problem = build_toy_problem()
    print(f"Built problem with {len(problem.tasks)} tasks", flush=True)

    last_task = len(problem.tasks) - 1
    active_tasks = set(range(1, last_task))

    params = "log_search_progress:true log_subsolver_statistics:true"

    solve_rcpsp(
        problem=problem,
        proto_file="",
        params=params,
        active_tasks=active_tasks,
        source=0,
        sink=last_task,
    )

if __name__ == "__main__":
    main()