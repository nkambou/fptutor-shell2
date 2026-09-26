"""Reproduce the Python map-family session from supplied PyTutor modules."""
import json
import os
import sys

BASE = os.path.dirname(__file__)
PYTUTOR = os.path.join(BASE, "pytutor")
sys.path.insert(0, PYTUTOR)
os.environ["LANGUE_TUTEUR"] = "langue_python"
import noyau as K

with open(os.path.join(PYTUTOR, "referentiel.json"), encoding="utf-8") as f:
    ref = json.load(f)

cid = "transformation"
family = K.concept(ref, cid)[0]["famille"]
learner = K.nouvel_apprenant("trace", "reproduction")
sources = {
    "doubler": "def doubler(xs):\n    return [2 * x for x in xs]\n",
    "majuscules": "def majuscules(xs):\n    if not xs: return []\n    return [xs[0].upper()] + majuscules(xs[1:])\n",
    "initiales": "def initiales(xs):\n    if not xs: return []\n    return [xs[0][0]] + initiales(xs[1:])\n",
    "carres": "def carres(xs):\n    if not xs: return []\n    return [xs[0] * xs[0]] + carres(xs[1:])\n",
    "notes": "def notes(xs):\n    if not xs: return []\n    return [xs[0][1]] + notes(xs[1:])\n",
}

print("minimum:", ref["reglages"]["instances_min"])
for activity in K.ACTIVITES[family]:
    name, _, _, _, tests = activity
    if name not in sources:
        continue
    source = sources[name]
    verdict = K.evaluer(source, tests)
    admission = K.admettre(name, source, family, verdict)
    if not verdict["reussite"]:
        raise RuntimeError((name, verdict))
    if admission["admis"]:
        learner["corpus"].setdefault(cid, []).append({"nom": name, "code": source, "canon": admission["canon"]})
    else:
        learner["ecartes"].setdefault(cid, []).append((name, admission["motif"], source))
    corpus = learner["corpus"].get(cid, [])
    count = K.etat_alignement([(x["nom"], x["code"]) for x in corpus])[0] if len(corpus) >= 2 else None
    first = K.decider(ref, learner, cid)
    repeated = K.decider(ref, learner, cid)
    assert first == repeated, (name, first, repeated)
    print(f"{name}: tests=ok, admission={'yes' if admission['admis'] else 'no'}, "
          f"corpus={len(corpus)}/3, points={count}, decision={first[0]}, reason={first[1]}")
assert first[0] == "remontee", first
print("workshop corpus:", ", ".join(x["nom"] for x in corpus))
print("set aside:", ", ".join(x[0] for x in learner["ecartes"].get(cid, [])))
