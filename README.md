# FPTutor-Shell

FPTutor-Shell is a framework for building tutoring systems that support
bottom-up abstraction in functional programming education. It was extracted
from HaskellTutor and instantiated for Python. This repository accompanies the
article *FPTutor-Shell: Extracting a Language-Independent Pedagogical Framework
from a Functional Programming Tutor* (R. Nkambou and A. Tato).

## Contents

| Path             | Contents                                                                 |
| ---------------- | ------------------------------------------------------------------------ |
| `pytutor/`       | Python provider, activities, session policy, server, and referential     |
| `fptutor-shell/` | Authoring tools: provider template, test bench, and authoring workshop   |
| Repository root  | Haskell normalizer, reference generator, obligation inducer, ablations   |

The system is written in French, and its outputs keep their French labels.
The article gives their English equivalents.

## Reproducing the results

All scripts require a Python 3 interpreter and no external library. Run each
command from the repository root.

| Result in the article                     | Command |
| ----------------------------------------- | ------- |
| Section 5.3, alignments of the Python provider | `cd pytutor && python3 langue_python.py` |
| Sections 5.5 and 5.6, Python session and policy | `python3 trace_pytutor.py` |
| Section 8.1, provider test bench          | `cd fptutor-shell && python3 banc_essai.py --tuteur pytutor --cas cas_exemple.json langue_python` |
| Section 8.2, family validation and Haskell counts | `python3 generateur.py` |
| Sections 8.3 to 8.6, Tables 4 to 7        | `python3 ablations.py` |
| Sections 7.2 and 8.7, Table 3             | `python3 obligations.py` |

## Building a new instantiation

The provider interface (Table 2 of the article) is documented in
`fptutor-shell/gabarit_language.py`, which serves as the starting point for a
new language. The Python provider in `pytutor/langue_python.py` is a complete
example.

## Notes

The interactive tutor, with its learner interface and teacher console, is in the
[haskellTutor](https://github.com/nkambou/haskellTutor) repository; the Python
tutor runs there with `TUTOR_LANGUAGE=language_python python3 serveur.py`.
This repository reproduces the results of the article.

The root referential and the running tutor use the family identifiers `F-map`,
`F-filter` and `F-fold`; `pytutor/referentiel.json` uses the French identifiers
of the version on which the results were produced (`F-transformation`,
`F-selection`, `F-pli`). The fold family declares five anchors, `toutVrai`
among them, in the generator and in the running tutor alike.

## License

MIT. See `LICENSE`.
