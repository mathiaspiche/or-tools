import argparse
import collections
import os
import random
import re
import shutil
import sys


def norm(s):
    return s.replace(" ", "").upper()


def is_multimode(path):
    """Fichier PSPLIB valide avec au moins une tache a plusieurs modes."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()
        n_jobs = None
        start = None
        for i, l in enumerate(lines):
            nl = norm(l.strip())
            if n_jobs is None and nl.startswith("JOBS"):
                n_jobs = int(re.search(r":\s*(\d+)", l).group(1))
            if nl.startswith("PRECEDENCERELATIONS"):
                start = i + 2
                break
        if n_jobs is None or start is None:
            return False
        names = [norm(l.strip()) for l in lines]
        if not any(n.startswith("REQUESTS/DURATIONS") for n in names):
            return False
        if not any(n.startswith("RESOURCEAVAILABILITIES") for n in names):
            return False
        return any(int(lines[start + k].split()[1]) > 1 for k in range(n_jobs))
    except (OSError, ValueError, IndexError, AttributeError):
        return False


def set_name(source, path):
    """Famille d'une instance = 1er dossier sous la source, sans '.mm' (j10.mm -> j10)."""
    rel = os.path.relpath(path, source)
    parts = rel.split(os.sep)
    if len(parts) == 1:
        return "racine"
    name = parts[0]
    return name[:-3] if name.lower().endswith(".mm") else name


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=os.path.join(os.path.expanduser("~"),
                                                     "Downloads", "instances"))
    ap.add_argument("--dest", default=os.path.join(here, "instances_mmrcpsp"))
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--sets", default="j",
                    help='familles : "all", ou prefixes separes par des virgules (defaut "j")')
    ap.add_argument("--clear", action="store_true",
                    help="deplace d'abord les .mm de la destination dans <dest>_sauvegarde")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(args.source):
        sys.exit(f"dossier source introuvable : {args.source}")

    tokens = [t.strip().lower() for t in args.sets.split(",") if t.strip()]
    take_all = "all" in tokens

    candidates = []
    for root, _dirs, files in os.walk(args.source):
        for fn in files:
            low = fn.lower()
            if not low.endswith(".mm") or low.endswith("opt.mm"):
                continue
            path = os.path.join(root, fn)
            fam = set_name(args.source, path)
            if take_all or any(fam.lower().startswith(t) for t in tokens):
                candidates.append((fam, path))
    if not candidates:
        sys.exit(f"aucune instance trouvee dans {args.source} pour --sets {args.sets}")
    candidates.sort()

    rng = random.Random(args.seed)
    rng.shuffle(candidates)
    chosen, rejected = [], 0
    for fam, path in candidates:
        if len(chosen) >= args.n:
            break
        if is_multimode(path):
            chosen.append((fam, path))
        else:
            rejected += 1

    print(f"{len(candidates)} fichiers candidats ; {rejected} ecartes "
          f"(invalides ou a un seul mode) ; {len(chosen)} retenus (demande : {args.n}).")
    if len(chosen) < args.n:
        print(f"ATTENTION : seulement {len(chosen)} instances multi-modes disponibles.")
    count = collections.Counter(fam for fam, _ in chosen)
    print("Repartition par famille : " +
          ", ".join(f"{k}={v}" for k, v in sorted(count.items())))

    if args.dry_run:
        for fam, path in sorted(chosen):
            print("  ", os.path.relpath(path, args.source))
        print("(dry-run : rien n'a ete copie)")
        return

    os.makedirs(args.dest, exist_ok=True)
    if args.clear:
        backup = args.dest.rstrip("\\/") + "_sauvegarde"
        os.makedirs(backup, exist_ok=True)
        moved = 0
        for fn in os.listdir(args.dest):
            if fn.lower().endswith(".mm"):
                target = os.path.join(backup, fn)
                if os.path.exists(target):
                    os.remove(target)
                shutil.move(os.path.join(args.dest, fn), target)
                moved += 1
        print(f"{moved} fichier(s) .mm deplace(s) dans {backup} (rien n'est supprime).")

    lines = []
    for fam, path in sorted(chosen):
        new_name = f"{fam}__{os.path.basename(path)}"
        shutil.copy2(path, os.path.join(args.dest, new_name))
        lines.append(f"{new_name}\t{os.path.relpath(path, args.source)}")
    with open(os.path.join(args.dest, "_selection.txt"), "w", encoding="utf-8") as f:
        f.write(f"graine={args.seed} ; source={args.source}\n")
        f.write("nom copie\tfichier d'origine\n")
        f.write("\n".join(lines) + "\n")
    print(f"{len(chosen)} instances copiees dans {args.dest}")
    print("Liste : " + os.path.join(args.dest, "_selection.txt"))
    print('Lancer le lot :  python ortools\\sat\\run_batch.py --pattern "*.mm"')


if __name__ == "__main__":
    main()