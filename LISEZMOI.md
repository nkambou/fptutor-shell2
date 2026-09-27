# PyTutor — l'instanciation Python du cadre

Ce dossier contient ce qui est propre à Python dans FPTutor-Shell, le fournisseur
de langage et les ancrages, ainsi que la version du noyau et du serveur sur
laquelle les résultats de l'article ont été produits. Il sert à reproduire ces
résultats ; le tuteur interactif, avec son interface, se lance depuis le dépôt
du cadre.

## Lancer le tuteur interactif

L'interface apprenant et la console enseignante font partie du cadre, dans le
dépôt [haskellTutor](https://github.com/nkambou/haskellTutor). Le même serveur
sert Haskell ou Python selon le fournisseur choisi :

    cd haskellTutor
    TUTOR_LANGUAGE=language_python PORT=8081 python3 serveur.py

    apprenant  : http://localhost:8081/
    enseignant : http://localhost:8081/enseignant

Dépendances : Python 3.8 et rien d'autre. Contrairement au tuteur Haskell, aucun
compilateur externe n'est nécessaire : les soumissions sont exécutées par
l'interpréteur Python lui-même.

Les tuteurs Haskell (`python3 serveur.py`, port 8080) et Python peuvent tourner
en même temps sur deux ports différents. Chacun écrit son état dans `etat.json`
et `journal.jsonl` ; pour les faire tourner côte à côte sans partager ces
fichiers, lancez-les depuis deux copies du dépôt.

## Ce que contient ce dossier

| Fichier | Rôle |
| --- | --- |
| `langue_python.py` | fournisseur de langage Python, propre à Python |
| `activites_python.py` | ancrages avec énoncés et tests, propres à Python |
| `noyau.py`, `serveur.py`, `remontee.py`, `normalisation2.py` | version du cadre utilisée pour les résultats de l'article |
| `referentiel.json` | référentiel des concepts et des familles |
| `lancer.sh` | démarre ce serveur, qui n'expose que l'API (sans interface) |

`trace_pytutor.py`, à la racine du dépôt, utilise ce dossier pour reproduire la
session des sections 5.5 et 5.6 de l'article, et le banc d'essai de
`fptutor-shell/` l'utilise pour la section 8.1.

## Le fournisseur de langage

Cinq éléments, décrits en tête de `langue_python.py`, sous leurs noms français ;
les noms anglais du tableau 2 de l'article (`name`, `command`, `test_template`,
`analyse`, `categorise`) sont définis en fin de fichier :

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
reconnaissance des trois écritures du test de vacuité, `not xs`, `len(xs) == 0`
et `xs == []`. Une sélection s'écrit indifféremment avec deux `return`
successifs, un `if … else` ou une expression conditionnelle ; les trois
donnent la même forme `COND (test) (branche conservée) (branche écartée)`.

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

Depuis ce dossier :

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

Les treize familles restantes du référentiel sont spécifiées mais n'ont pas
d'ancrages exécutables. Elles se remplissent de la même manière, et le contrôle
des familles, `python3 generateur.py` depuis la racine du dépôt, dit si les
solutions de référence d'une famille s'alignent au compte que le référentiel
annonce.

## Outillage

Depuis la racine du dépôt :

    python3 obligations.py    induit les ancrages porteurs de chaque famille
    python3 ablations.py      études d'ablation sur le moteur
    python3 trace_pytutor.py  session Python des sections 5.5 et 5.6
