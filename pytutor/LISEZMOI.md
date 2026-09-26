# PyTutor — l'instanciation Python du cadre

Même cadre que HaskellTutor, même politique de session, même moteur d'alignement.
Seuls trois fichiers diffèrent : le fournisseur de langage, les ancrages, et le
script de lancement.

## Lancer

    cd pytutor
    ./lancer.sh

    ou, sans le script :
    LANGUE_TUTEUR=langue_python PORT=8081 python3 serveur.py

    apprenant  : http://localhost:8081/
    enseignant : http://localhost:8081/enseignant

Dépendances : Python 3.8 et rien d'autre. Contrairement à HaskellTutor, aucun
compilateur externe n'est nécessaire : les soumissions sont exécutées par
l'interpréteur Python lui-même.

Les deux tuteurs peuvent tourner en même temps sur deux ports différents ; ils ne
partagent ni `etat.json` ni `journal.jsonl`.

## Ce qui change par rapport à HaskellTutor

| Fichier | Rôle | Différence |
| --- | --- | --- |
| `langue_python.py` | fournisseur de langage | **propre à Python** — 270 lignes |
| `activites_python.py` | ancrages avec énoncés et tests | **propre à Python** — 14 activités |
| `lancer.sh` | variable d'environnement | trivial |
| tout le reste | cadre | **identique, octet pour octet** |

`serveur.py`, `noyau.py`, `remontee.py`, `normalisation2.py`, `etudiant.html`,
`enseignant.html`, `referentiel.json`, `releves.py`, `generateur.py`,
`obligations.py` et `ablations.py` sont les fichiers de HaskellTutor sans
modification. Le tuteur change de langage par la variable `LANGUE_TUTEUR`, qui
nomme le module de fournisseur à charger.

## Le fournisseur de langage

Cinq éléments, décrits en tête de `langue_python.py` :

    nom, extension            identification
    commande(chemin)          comment exécuter le module de test
    gabarit_test(code, exprs) comment l'assembler
    analyser(nom, code)       source -> {forme, base, pas} en vocabulaire commun
    categoriser(message)      message d'erreur -> catégorie d'étayage

La normalisation passe par le module `ast` de la bibliothèque standard. Un indice
`[0]` sur le paramètre devient `C1`, une tranche `[1:]` devient `RESTE`, un appel
à la fonction en cours de définition devient `REC`, et les appels de méthode sont
émis en forme préfixe pour que `xs[0].upper()` et `head x` aient la même forme.

Deux normalisations sémantiques : la commutativité, restreinte à `+` et `*`, et la
reconnaissance des trois écritures du test de vacuité — `not xs`, `len(xs) == 0`,
`xs == []`.

## Les formes non comparables

Python offre plusieurs idiomes pour chaque opération sur les listes, et un seul
est comparable au sens du cadre. Le fournisseur les distingue et rend un motif
que le tuteur explique à l'apprenant :

| Écriture | Forme rendue | Ce que le tuteur en fait |
| --- | --- | --- |
| récursion explicite | `constructeurs` | admise au corpus d'alignement |
| compréhension de liste | `comprehension` | réussite comptée à part, forme expliquée |
| boucle `for` ou `while` | `iteratif` | idem |
| appel à une fonction toute faite | `sans-recursion` | idem |

C'est ici que les deux instanciations diffèrent le plus en usage. En Haskell un
apprenant écrit spontanément une récursion et occasionnellement une compréhension ;
en Python les proportions s'inversent. Deux conséquences pratiques :

- **dimensionnez les familles avec un ou deux ancrages de plus** qu'en Haskell,
  puisqu'une partie sera consommée par des soumissions non comparables ;
- **le contrat par défaut devrait probablement être `confronter`** plutôt que
  `expliquer_et_poursuivre`, puisque l'apprenant qui écrit une compréhension
  possède déjà, sous une autre forme, l'abstraction que la descente cherche à
  faire produire.

Le second réglage se fait dans l'onglet Contrats de la console enseignante.

## Vérifier l'installation

    python3 langue_python.py

Aligne trois définitions Python de la famille de transformation et quatre de la
famille du pli, et affiche les points de variation obtenus : un et trois, les
mêmes qu'en Haskell.

    LANGUE_TUTEUR=langue_python python3 -c "import noyau as K; print(K.LANGUE.nom, list(K.ACTIVITES))"

Doit afficher `python` et les trois familles instanciées.

## Les activités

Quatorze ancrages sur trois familles, plus six items de réemploi.

| Famille | Ancrages | Réemplois |
| --- | --- | --- |
| transformation | doubler, majuscules, initiales, carres, notes | negatifs, longueurs |
| sélection | pairs, non_vides, admis, longs | positifs, voyelles |
| pli | somme, produit, longueur, aplatir, concat_mots | maximum_l, tout_vrai |

Pour en ajouter, une seule chose à écrire dans `activites_python.py` : un
identifiant, un énoncé, une signature, une amorce et la liste des tests sous forme
de couples (expression, résultat attendu). Les énoncés évitent tout terme qui
nommerait le schéma visé.

## Les treize autres familles

Comme pour HaskellTutor, les treize familles restantes du référentiel sont
spécifiées mais n'ont pas d'ancrages exécutables. Elles se remplissent de la même
manière, et le contrôle au chargement — `python3 generateur.py` — dira si les
solutions de référence d'une famille s'alignent au compte que le référentiel
annonce.

## Outillage

    python3 obligations.py    induit les ancrages porteurs de chaque famille
    python3 ablations.py      études d'ablation sur le moteur
    python3 releves.py journal.jsonl    relevés de cohorte par chapitre
