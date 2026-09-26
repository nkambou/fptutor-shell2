#!/usr/bin/env python3
"""Engendre le repertoire d'un tuteur pour un nouveau langage fonctionnel.

    python3 creer_tuteur.py ml mltutor
    python3 creer_tuteur.py ml mltutor --interprete "ocaml" --extension .ml

Ce que le generateur ecrit dans le repertoire cible :

    language_<court>.py   le fournisseur, a partir du gabarit, avec les cinq
                          elements et les endroits a ecrire signales
    activities_<court>.py les ancrages et les reemplois, un exemple par famille
    referentiel.json      copie du referentiel commun, a adapter
    LISEZMOI.md           la marche a suivre, dans l'ordre

Le generateur n'ecrit jamais dans un repertoire existant sans le dire, et il
ne touche a rien d'autre : le shell reste partage.

Ce qui reste a faire apres la generation est enonce dans le LISEZMOI produit.
L'essentiel tient en une phrase : ecrire analyse, puis passer le banc d'essai.
"""

import argparse, json, os, shutil, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)


GABARIT_ACTIVITES = '''"""Ancrages et reemplois pour {court}.

ACTIVITES donne, par famille, les exercices servis en phase d'instance.
REEMPLOIS donne ceux servis apres la phase d'abstraction, sur lesquels le
reemploi spontane du schema se mesure.

Un ancrage est un quadruplet :

    (nom, enonce, amorce, [(expression, valeur attendue), ...])

Regle de composition, qui est le point le plus couteux a decouvrir par soi-meme
et que l'inducteur d'obligations verifie : les membres d'une famille doivent
differer autant que possible en surface et pas du tout en structure. Une
famille dont tous les ancrages consomment le premier element ne permettra pas
de decouvrir que l'operation peut l'ignorer.

Lancez l'inducteur des que la famille est ecrite :

    cd .. && python3 obligations.py
'''

GABARIT_ACTIVITES_CORPS = '''
ACTIVITES = {{
    "F-map": [
        ("double", "Des quantites a convertir : multipliez chaque element par deux.",
         "double xs = TODO", [("double [1,2,3]", "[2, 4, 6]")]),
        # au moins trois autres ancrages, de surfaces tres differentes
    ],
    "F-filter": [
        ("pairs", "Des numeros de place : ne gardez que les pairs.",
         "pairs xs = TODO", [("pairs [1,2,3,4]", "[2, 4]")]),
    ],
    "F-fold": [
        ("somme", "Des releves : donnez le total.",
         "somme xs = TODO", [("somme [1,2,3]", "6")]),
        # un ancrage dont l'operation ignore l'element est obligatoire ici :
        # sans lui, l'apprenant conclut que la combinaison consomme la tete
        ("longueur", "Un inventaire dont les elements importent peu : comptez-les.",
         "longueur xs = TODO", [("longueur [7,7,7]", "3")]),
    ],
}}

REEMPLOIS = {{
    "F-map": [
        ("negatif", "Changez le signe de chaque element.",
         "negatif xs = TODO", [("negatif [1,-2]", "[-1, 2]")]),
    ],
    "F-filter": [],
    "F-fold": [],
}}
'''

LISEZMOI = '''# {nom} — tuteur {court}

Engendre par l'atelier FPTutor. Rien du shell n'a ete modifie.

## Dans l'ordre

**1. Ecrire `analyse` dans `language_{court}.py`.** C'est le seul element
substantiel des cinq. Il prend le nom de la fonction et son code, et rend la
forme, le cas de base et le cas recursif en vocabulaire commun.

Ecrivez-le contre trois ou quatre solutions de reference et imprimez les
formes canoniques avant de connecter quoi que ce soit :

    cd ../fptutor-shell && python3 banc_essai.py language_{court}

Le banc rend le nombre de classes d'equivalence. Un fournisseur correct donne
une classe pour des variantes purement syntaxiques et des classes separees
pour des ecritures semantiquement distinctes. Si le compte est faux, la
normalisation n'est pas encore une fonction, et les comptes d'alignement
seraient instables.

**2. Completer `command` et `test_template`.** Deux lignes chacune. La seule
exigence du second est qu'une expression produise exactement une ligne.

**3. Projeter les messages du compilateur dans `categorise`.** Cinq categories
communes, et le cadre ne voit jamais le message.

**4. Ecrire les ancrages dans `activities_{court}.py`,** puis lancer
l'inducteur d'obligations :

    cd .. && TUTOR_DIR={nom} TUTOR_LANGUAGE=language_{court} python3 obligations.py

Il dit, pour chaque famille, quels ancrages sont porteurs. Un ancrage porteur
est le seul de sa famille a exhiber une variation que la famille doit montrer ;
le retirer change le compte de points de variation. C'est le controle qui
remplace des semaines de tatonnement.

**5. Adapter `referentiel.json`.** Concepts, paliers, familles, obligations. Si
votre progression est celle du referentiel commun, vous pouvez supprimer ce
fichier : le noyau prend alors celui de la racine.

**6. Lancer.**

    cd .. && python3 fptutor {nom}

## Verifier avant de servir a des apprenants

    cd .. && TUTOR_DIR={nom} TUTOR_LANGUAGE=language_{court} python3 generateur.py

Le controle aligne les solutions de reference de chaque famille et compare le
resultat a ce que le referentiel annonce. Une famille non conforme n'est pas
servie : elle produirait un plateau, c'est-a-dire une phase d'abstraction
ouverte sur un corpus dont il n'y a rien a extraire.
'''


def ecrire_activites(cible, court, familles, retenus):
    """Ecrit activities_<court>.py en instanciant les activites du modele.

    Les enonces sont conserves : ce sont eux qui portent l'intention
    pedagogique et ils ne dependent pas du langage. L'amorce et les
    expressions de test sont a traduire, et la ligne de reference est laissee
    en commentaire juste au-dessus pour que la traduction soit mecanique.

    retenus est la liste des ancrages a garder, sous la forme
    "famille/instances/nom" ou "famille/reemplois/nom".
    """
    garde = set(retenus or [])

    def bloc(nom_f, groupe):
        lignes = []
        for a in familles.get(nom_f, {}).get(groupe, []):
            cle = "%s/%s/%s" % (nom_f, groupe, a["nom"])
            if garde and cle not in garde:
                continue
            tests = ", ".join('("%s", "%s")' % (t[0].replace('"', '\\"'),
                                                str(t[1]).replace('"', '\\"'))
                              for t in a["tests"])
            lignes.append(
                '        # reference : %s\n'
                '        ("%s", "%s",\n'
                '         "TODO signature",\n'
                '         "TODO amorce",\n'
                '         [%s]),   # TODO adapter les expressions de test\n'
                % (a.get("signature", "").replace("\n", " ; "), a["nom"],
                   a["enonce"].replace('"', '\\"'), tests))
        return "".join(lignes)

    corps = ['"""Ancrages et reemplois pour %s.\n' % court,
             ENTETE_ACTIVITES, '"""\n\n', "ACTIVITES = {\n"]
    for nom_f in sorted(familles):
        b = bloc(nom_f, "instances")
        if b:
            corps.append('    "%s": [\n%s    ],\n' % (nom_f, b))
    corps.append("}\n\nREEMPLOIS = {\n")
    for nom_f in sorted(familles):
        b = bloc(nom_f, "reemplois")
        corps.append('    "%s": [\n%s    ],\n' % (nom_f, b))
    corps.append("}\n")
    chemin = os.path.join(cible, "activities_%s.py" % court)
    open(chemin, "w", encoding="utf-8").write("".join(corps))
    return chemin


ENTETE_ACTIVITES = """
Instancie a partir du tuteur de reference : memes familles, memes ancrages,
memes enonces. Ce qui reste a faire est mecanique et local.

  1. remplacer chaque amorce « nom ... = TODO » par la signature du langage
  2. adapter les expressions de test, la valeur attendue ne changeant pas
  3. ajouter ou retirer des ancrages a volonte

Les enonces sont conserves tels quels : ils portent l'intention pedagogique et
ne dependent pas du langage. La ligne « reference » au-dessus de chaque
ancrage montre l'amorce du tuteur de reference, pour que la traduction soit
immediate.

Regle de composition, que l'inducteur d'obligations verifie : les membres
d'une famille doivent differer autant que possible en surface et pas du tout
en structure. Retirer un ancrage peut supprimer la seule variation que la
famille devait montrer, ce que l'inducteur signale :

    cd .. && TUTOR_DIR=<rep> TUTOR_LANGUAGE=language_<court> python3 obligations.py
"""


def creer(court, nom_rep, interprete, extension, force=False, titre=None):
    cible = os.path.join(RACINE, nom_rep)
    if os.path.isdir(cible) and os.listdir(cible) and not force:
        raise SystemExit(
            "Le repertoire %s existe et n'est pas vide.\n"
            "Choisissez un autre nom, ou ajoutez --force pour ecrire dedans." % cible)
    os.makedirs(cible, exist_ok=True)

    # 1. le fournisseur, a partir du gabarit
    gab = open(os.path.join(ICI, "gabarit_language.py"), encoding="utf-8").read()
    gab = (gab.replace("NOM_LANGAGE", court.capitalize())
              .replace("NOM_COURT", court)
              .replace("TITRE_TUTEUR", titre or (court.capitalize() + "Tutor"))
              .replace("INTERPRETE", interprete)
              .replace(".EXT", extension))
    fournisseur = os.path.join(cible, "language_%s.py" % court)
    open(fournisseur, "w", encoding="utf-8").write(gab)

    # 2. les ancrages
    act = (GABARIT_ACTIVITES.format(court=court) + '"""\n'
           + GABARIT_ACTIVITES_CORPS.format(court=court))
    open(os.path.join(cible, "activities_%s.py" % court), "w",
         encoding="utf-8").write(act)

    # 3. le referentiel, copie pour etre adapte
    ref = os.path.join(RACINE, "referentiel.json")
    if not os.path.exists(ref):
        for d in sorted(os.listdir(RACINE)):
            c = os.path.join(RACINE, d, "referentiel.json")
            if os.path.exists(c):
                ref = c
                break
    if os.path.exists(ref):
        shutil.copy(ref, os.path.join(cible, "referentiel.json"))

    # 4. la marche a suivre
    open(os.path.join(cible, "LISEZMOI.md"), "w", encoding="utf-8").write(
        LISEZMOI.format(nom=nom_rep, court=court))

    return cible


def main():
    a = argparse.ArgumentParser(
        description="Engendre le repertoire d'un tuteur pour un nouveau langage.")
    a.add_argument("court", help="nom court du langage, par exemple ml")
    a.add_argument("repertoire", help="nom du repertoire, par exemple mltutor")
    a.add_argument("--interprete", default="INTERPRETE",
                   help="commande qui execute un fichier, par exemple ocaml")
    a.add_argument("--extension", default=".EXT",
                   help="extension des fichiers source, par exemple .ml")
    a.add_argument("--titre", default=None,
                   help="nom affiche par les interfaces, par exemple OCamlTutor ; "
                        "par defaut le nom court capitalise suivi de Tutor")
    a.add_argument("--force", action="store_true",
                   help="ecrire dans un repertoire non vide")
    o = a.parse_args()
    cible = creer(o.court, o.repertoire, o.interprete, o.extension, o.force,
                  o.titre)
    print("Tuteur engendre dans %s\n" % cible)
    for f in sorted(os.listdir(cible)):
        print("  %s" % f)
    print("\nLa marche a suivre est dans %s/LISEZMOI.md" % o.repertoire)
    print("Etape suivante : ecrire analyse, puis")
    print("  cd fptutor-shell && python3 banc_essai.py language_%s" % o.court)


if __name__ == "__main__":
    main()
