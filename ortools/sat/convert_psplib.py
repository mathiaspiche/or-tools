"""Convert a PSPLIB multi-mode RCPSP file (.mm / .sm style, e.g. j50) into the
data block used by energetic_cumulative_compare.py.

Usage:
  python psplib_to_format.py instance.mm > instance_data.py
  python psplib_to_format.py instance.mm --patch path\\to\\energetic_cumulative_compare.py

--patch replaces the data block (from "HORIZON =" up to "def build_model") of
the given script in place and keeps a .bak copy next to it.
"""
import contextlib
import io
import re
import shutil
import sys


def parse(path):
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()

    def find(prefix):
        for i, l in enumerate(lines):
            if l.strip().startswith(prefix):
                return i
        raise ValueError(f"section '{prefix}' not found")

    n_jobs = int(re.search(r":\s*(\d+)", lines[find("jobs")]).group(1))
    n_ren = int(re.search(r":\s*(\d+)", lines[find("- renewable")]).group(1))
    n_non = int(re.search(r":\s*(\d+)", lines[find("- nonrenewable")]).group(1))
    n_dbl = int(re.search(r":\s*(\d+)", lines[find("- doubly")]).group(1))
    if n_dbl:
        raise ValueError("doubly constrained resources are not supported")
    n_res = n_ren + n_non

    # precedence
    i = find("PRECEDENCE RELATIONS") + 2
    n_modes, succ = {}, {}
    for _ in range(n_jobs):
        f = lines[i].split()
        j, nm, ns = int(f[0]), int(f[1]), int(f[2])
        n_modes[j] = nm
        succ[j] = [int(x) for x in f[3:3 + ns]]
        i += 1

    # requests / durations
    i = find("REQUESTS/DURATIONS") + 3
    modes = {}
    cur = None
    for _ in range(sum(n_modes.values())):
        f = [int(x) for x in lines[i].split()]
        if len(f) == 3 + n_res:          # first line of a job: jobnr mode dur r...
            cur, f = f[0], f[1:]
        modes.setdefault(cur, []).append((f[1], f[2:2 + n_res]))
        i += 1

    # capacities
    i = find("RESOURCE AVAILABILITIES") + 2
    caps = [int(x) for x in lines[i].split()]
    return n_jobs, n_ren, n_non, n_modes, succ, modes, caps


def main(path):
    n_jobs, n_ren, n_non, n_modes, succ, modes, caps = parse(path)
    for j in range(1, n_jobs + 1):
        assert len(modes[j]) == n_modes[j], f"job {j}: mode count mismatch"
    horizon = sum(max(d for d, _ in modes[j]) for j in range(1, n_jobs + 1))

    print(f"HORIZON = {horizon}   # sum of the longest mode of each task")
    print(f"CAPACITIES = {caps}")
    print(f"RENEWABLE = {[True] * n_ren + [False] * n_non}")
    print()
    print("TASKS_MODES = [")
    for j in range(1, n_jobs + 1):
        ds = [d for d, _ in modes[j]]
        tag = "  (dup dur)" if len(set(ds)) < len(ds) and len(ds) > 1 else ""
        tag += "  (dummy)" if j in (1, n_jobs) else ""
        print(f"    # task {j}{tag}")
        print("    [" + ", ".join(f"({d}, {r})" for d, r in modes[j]) + "],")
    print("]")
    print()
    print("TASK_WINDOWS = [")
    print("    (0, HORIZON - min(d for d, _ in m), min(d for d, _ in m), HORIZON)")
    print("    for m in TASKS_MODES")
    print("]")
    print()
    print("# 0-based (task i ends before task j starts)")
    print("PRECEDENCES = [")
    for j in range(1, n_jobs + 1):
        if succ[j]:
            print("    " + ", ".join(f"({j - 1}, {s - 1})" for s in succ[j]) + ",")
    print("]")


def patch(instance, target):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main(instance)
    data = buf.getvalue().rstrip() + "\n\n\n"
    src = open(target, encoding="utf-8").read()
    a = src.index("HORIZON =")
    b = src.index("def build_model")
    shutil.copyfile(target, target + ".bak")
    open(target, "w", encoding="utf-8").write(src[:a] + data + src[b:])
    print(f"patched {target} (backup: {target}.bak)")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[2] == "--patch":
        patch(sys.argv[1], sys.argv[3])
    else:
        main(sys.argv[1])