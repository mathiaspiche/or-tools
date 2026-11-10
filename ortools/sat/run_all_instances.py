"""Run energetic_cumulative_compare.py with TT_MODES=0 and TT_MODES=1 on every
PSPLIB .mm file of a folder, and print/save a comparison table.

For each instance the data block of a COPY of the compare script is rewritten
(your original script is not modified), then the copy is run twice.

Usage (from any folder outside the or-tools repo):
  python run_all_instances.py [--folder DIR] [--script PATH] [--time 60]
                              [--limit N] [--pattern j50*] [--out results.csv]
"""
import argparse
import contextlib
import csv
import io
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from convert_psplib import patch as patch_data
except ImportError:
    from psplib_to_format import patch as patch_data

DEFAULT_FOLDER = r"C:\Users\mathi\or-tools\ortools\sat\instances_mmrcpsp"
DEFAULT_SCRIPT = r"C:\Users\mathi\or-tools\examples\python\energetic_cumulative_compare.py"

FIELDS = ["status", "objective", "branches", "conflicts", "wall_time"]
EXTRA = ["elim"]   # modes eliminated by the sweep (from stderr)


def parse_output(text):
    res = {}
    for f in FIELDS:
        m = re.search(rf"^{f}:\s*(\S+)", text, re.M)
        res[f] = m.group(1) if m else ""
    return res


def count_elim(path):
    """Number of modes eliminated: uses the final summary line if present
    ('modes eliminated=N'), otherwise counts 'elimine' lines. Streams the file."""
    n_lines, summary = 0, None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "elimine" in line:
                n_lines += 1
            elif "modes eliminated=" in line:
                m = re.search(r"modes eliminated=(\d+)", line)
                if m:
                    summary = int(m.group(1))
    return summary if summary is not None else n_lines


def run_once(script, mode, time_limit, workdir):
    env = dict(os.environ, TT_MODES=str(mode))
    errpath = os.path.join(workdir, "stderr.txt")
    try:
        with open(errpath, "w", encoding="utf-8", errors="replace") as ef:
            p = subprocess.run(
                [sys.executable, script], cwd=workdir, env=env,
                stdout=subprocess.PIPE, stderr=ef,
                text=True, errors="replace", timeout=time_limit + 120)
    except subprocess.TimeoutExpired:
        return {f: "" for f in FIELDS} | {"status": "KILLED", "elim": ""}
    out = parse_output(p.stdout)
    out["elim"] = count_elim(errpath)
    if not out["status"]:
        out["status"] = f"ERROR(rc={p.returncode})"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", default=DEFAULT_FOLDER)
    ap.add_argument("--script", default=DEFAULT_SCRIPT)
    ap.add_argument("--time", type=int, default=60, help="solver time limit (s)")
    ap.add_argument("--limit", type=int, default=0, help="only first N instances")
    ap.add_argument("--pattern", default="*.mm")
    ap.add_argument("--out", default="results.csv")
    a = ap.parse_args()

    files = sorted(f for f in os.listdir(a.folder) if fnmatch.fnmatch(f, a.pattern))
    if a.limit:
        files = files[:a.limit]
    if not files:
        sys.exit(f"no file matching {a.pattern} in {a.folder}")

    work = tempfile.mkdtemp(prefix="ttcompare_")
    script = os.path.join(work, "energetic_cumulative_compare.py")
    rows = []
    hdr = f"{'instance':14}{'mode':>5}{'status':>10}{'obj':>8}{'branches':>11}{'conflicts':>11}{'time(s)':>10}{'elim':>8}"
    print(hdr)
    print("-" * len(hdr))
    for f in files:
        shutil.copyfile(a.script, script)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                patch_data(os.path.join(a.folder, f), script)
        except Exception as e:                      # bad instance file
            print(f"{f:14} patch failed: {e}")
            continue
        src = open(script, encoding="utf-8").read()
        if "max_time_in_seconds" not in src:
            src = src.replace(
                "solver.parameters.log_search_progress = True",
                f"solver.parameters.max_time_in_seconds = {a.time}\n"
                "    solver.parameters.log_search_progress = True")
            open(script, "w", encoding="utf-8").write(src)
        results = {}
        for mode in (0, 1):
            r = run_once(script, mode, a.time, work)
            results[mode] = r
            rows.append({"instance": f, "mode": mode, **r})
            t = f"{float(r['wall_time']):.2f}" if r["wall_time"] else ""
            print(f"{f:14}{mode:>5}{r['status']:>10}{r['objective']:>8}"
                  f"{r['branches']:>11}{r['conflicts']:>11}{t:>10}{r['elim']!s:>8}", flush=True)
        r0, r1 = results[0], results[1]
        both_opt = r0["status"] == r1["status"] == "OPTIMAL"
        if both_opt and r0["objective"] != r1["objective"]:
            print(f"{'':14}*** MISMATCH on {f}: {r0['objective']} vs {r1['objective']}"
                  " -> one propagator is unsound ***")
        elif "INFEASIBLE" in (r0["status"], r1["status"]) and r0["status"] != r1["status"]:
            print(f"{'':14}*** MISMATCH on {f}: {r0['status']} vs {r1['status']} ***")

    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["instance", "mode"] + FIELDS + EXTRA)
        w.writeheader()
        w.writerows(rows)
    print(f"\nresults saved to {os.path.abspath(a.out)}")
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()