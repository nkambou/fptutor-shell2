# FPTutor-Shell: available source and reproducible Python session

This repository contains the files currently available for the authoring
workshop, the Python tutor backend, and several analyses. It does not yet
contain the complete Haskell tutor, the learner and teacher HTML pages for
PyTutor, or a versioned archive of all seven studies.

## Reproduce the Python session

Run from the repository root with Python 3:

```sh
python3 trace_pytutor.py
```

The script evaluates five submissions against the tests in
`pytutor/activites_python.py`. `doubler` is a correct list comprehension
and is set aside. `majuscules`, `initiales`, `carres`, and `notes` enter
the alignment corpus. The policy's configured minimum is three admitted
solutions. At three, the count is one and unconfirmed; at four, it remains
one and the workshop opens. The script calls the policy twice at each
stage and fails if an unchanged corpus causes a new decision.

The policy fix in `pytutor/noyau.py` stores the corpus used for the previous
count. Repeated views and revisions at the same corpus size no longer count
as new evidence. `pytutor/serveur.py` reads the updated stability record.

## Contents

| Path | Contents | Current status |
| --- | --- | --- |
| `pytutor/` | Python provider, activities, backend, and its referential | Session trace works; HTML views are not included |
| `fptutor-shell/` | Authoring workshop and provider test bench | Source supplied; its bench expects English provider method names, whereas the supplied Python provider uses French names |
| Repository root | Reference generator, normalizers, obligation inducer, ablations, and research referential | Obligation induction runs; full ablation command needs a matching normalizer version |

The referentials differ: the root uses `F-map`, `F-filter`, and `F-fold`
for the research generator, while `pytutor/referentiel.json` uses
`F-transformation`, `F-selection`, and `F-pli` for the running tutor.
Do not interchange them.

The root generator includes `toutVrai` among five fold reference solutions;
the running tutor's referential declares four fold anchors. Run
`python3 obligations.py` from the repository root to inspect the five
reference solutions.

## Known gaps before a complete artifact release

- Add the learner and teacher HTML files before claiming a working browser UI.
- Add the Haskell provider and its activities before claiming two fully
  reproducible instantiations.
- Reconcile `ablations.py` with `normalisation2.py`: the former calls
  `commuter`, which the supplied normalizer does not define.
- Reconcile the authoring bench's English provider interface with the
  supplied Python provider's French interface before claiming that
  `banc_essai.py` validates this instantiation.
- Replace Figure 5(b) with a capture after the fourth admitted Python
  solution, `notes`.
- Release a versioned archive and record its identifier before claiming
  the complete framework and all seven studies have been deposited.
