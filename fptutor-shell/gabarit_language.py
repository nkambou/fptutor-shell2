"""Fournisseur de langage pour NOM_LANGAGE. Gabarit engendre par l'atelier.

Un fournisseur expose cinq elements et rien de plus. Tout le reste du tuteur,
le moteur de reconnaissance, la politique de session, le modele de l'apprenant
et les interfaces, est partage et n'a pas a etre touche.

    name, extension            identification
    command(chemin)            comment executer le module de test
    test_template(code, exprs) comment l'assembler
    analyse(nom, code)          source -> {forme, base, pas} en vocabulaire commun
    categorise(message)        message du compilateur -> categorie d'etayage

Le vocabulaire commun n'appartient a aucun langage :

    C1..Cn   les champs d'un motif           REC    un appel recursif
    COND     une decision                    LIST   une construction de liste
    REST     le reste de la structure        first  le premier element

Le cadre ne regarde jamais a l'interieur de ces termes. Deux ecritures qui
different seulement par la syntaxe doivent rendre le meme terme, sans quoi les
comptes d'alignement deviennent instables : la normalisation doit etre une
fonction.

Ordre de travail recommande. Ecrivez d'abord analyse contre trois ou quatre
solutions de reference et imprimez les formes canoniques obtenues, avant de
connecter quoi que ce soit. Une forme canonique qui parait fausse a l'oeil est
bien moins couteuse a diagnostiquer qu'un compte d'alignement errone deux
couches plus haut. Puis validez sur le banc d'essai :

    python3 banc_essai.py language_NOM_COURT
"""

import re, subprocess, tempfile, os

# ------------------------------------------------------------ identification

name = "NOM_COURT"
extension = ".EXT"

# Nom affiche par les deux interfaces, et langue par defaut du tuteur. Le cadre
# les lit ici : sans eux, les pages afficheraient le nom du premier tuteur ecrit
# et l'anglais.
titre = "TITRE_TUTEUR"
langue_defaut = "fr"


# ------------------------------------------------------------ execution

def command(chemin):
    """Rend la liste d'arguments qui execute le module de test.

    Exemples : ["runghc", "-Wincomplete-patterns", chemin] pour Haskell,
               ["python3", chemin] pour Python.
    """
    return ["INTERPRETE", chemin]


def test_template(code, expressions):
    """Assemble un module qui execute le code et imprime une valeur par ligne.

    Le cadre compare ces lignes aux valeurs attendues, dans l'ordre. La seule
    exigence est que chaque expression produise exactement une ligne.
    """
    lignes = "\n".join("    print(%s)" % e for e in expressions)
    return "%s\n\nif __name__ == '__main__':\n%s\n" % (code, lignes)


# ------------------------------------------------------------ analyse

# Les formes que le cadre sait aligner. Une soumission dont la forme n'y figure
# pas est correcte si les tests passent, mais elle n'entre pas au corpus.
ALIGNABLE_FORMS = ("constructors",)


def analyse(function_name, code):
    """Rend {"forme": ..., "base": ..., "pas": ...} en vocabulaire commun.

    forme vaut l'une des valeurs suivantes :
        constructors   filtrage par motif, cas de base et cas recursif visibles
        no-pattern     correcte, mais sans distinction des cas
        iterative      une boucle
        no-recursion   un appel a une fonction toute faite
        comprehension  une comprehension de liste
        unanalysable   l'analyse n'aboutit pas

    base et pas ne sont renseignes que pour constructors : base est la valeur
    du cas vide, pas est le cas recursif exprime en vocabulaire commun.
    """
    # A ECRIRE. Le squelette ci-dessous n'est qu'un point de depart.
    if "for " in code or "while " in code:
        return {"forme": "iterative", "base": "", "pas": ""}
    if function_name not in code.split("=", 1)[-1]:
        return {"forme": "no-recursion", "base": "", "pas": ""}
    return {"forme": "unanalysable", "base": "", "pas": ""}


# ------------------------------------------------------------ categorisation

# Les categories sont celles du cadre, communes a tous les langages. Un
# fournisseur y projette les messages de son compilateur ; l'echelle d'etayage
# ne voit que la categorie et jamais le message.
CATEGORIES = ("missing-base-case", "incompatible-types", "unknown-name",
              "syntax", "wrong-result", "unclassified")


def categorise(message, compile_mais_faux=False):
    """Projette un message du compilateur sur une categorie du cadre."""
    if compile_mais_faux:
        return "wrong-result"
    m = (message or "").lower()
    # A ECRIRE : les motifs propres au compilateur de NOM_LANGAGE.
    if "non-exhaustive" in m or "incomplete" in m:
        return "missing-base-case"
    if "not in scope" in m or "undefined" in m or "nameerror" in m:
        return "unknown-name"
    if "type" in m:
        return "incompatible-types"
    if "parse" in m or "syntax" in m:
        return "syntax"
    return "unclassified"
