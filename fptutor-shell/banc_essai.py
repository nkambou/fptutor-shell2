#!/usr/bin/env python3
"""Banc d'essai d'un fournisseur de langage.

    python3 banc_essai.py language_python
    python3 banc_essai.py language_ml --tuteur mltutor
    python3 banc_essai.py language_python --cas mes_cas.json

Le banc verifie la seule propriete dont le reste du cadre depend : que la
normalisation soit une fonction. Deux ecritures qui ne different que par la
syntaxe doivent rendre le meme terme, et deux ecritures semantiquement
distinctes doivent rendre des termes distincts.

Il rend le nombre de classes d'equivalence obtenues et le compare a ce que le
jeu de cas annonce. Un ecart signale un defaut du fournisseur, jamais du cadre.

Le jeu de cas par defaut porte sur la somme d'une liste, ecrite de six facons.
Pour un autre langage, fournissez le votre avec --cas, sur le modele de
cas_exemple.json.
"""

import argparse, importlib, json, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
for d in (RACINE, ICI):
    if d not in sys.path:
        sys.path.insert(0, d)

# Un jeu de cas declare deux choses, et le banc verifie les deux separement.
# equivalentes : ces ecritures doivent rendre exactement le meme terme.
# distinctes   : chacune doit rendre un terme different des autres.
CAS_DEFAUT = {
    "fonction": "somme",
    "equivalentes": [
        {"etiquette": "ordre direct",
         "code": "somme [] = 0\nsomme (x:xs) = x + somme xs"},
        {"etiquette": "operandes echanges",
         "code": "somme [] = 0\nsomme (x:xs) = somme xs + x"},
        {"etiquette": "autres noms de variables",
         "code": "somme [] = 0\nsomme (t:r) = t + somme r"},
    ],
    "distinctes": [
        {"etiquette": "sans filtrage par motif",
         "code": "somme l = if null l then 0 else head l + somme (tail l)"},
        {"etiquette": "pli de bibliotheque", "code": "somme xs = foldl (+) 0 xs"},
        {"etiquette": "sans recursion", "code": "somme xs = sum xs"},
    ],
}


def terme(fournisseur, fonction, code):
    r = fournisseur.analyse(fonction, code)
    return (r.get("forme", "?"), r.get("base", ""), r.get("pas", ""))


def classes(fournisseur, cas):
    """Rend la liste des classes, chacune etant (terme, etiquettes)."""
    groupes = {}
    for groupe in ("equivalentes", "distinctes"):
        for e in cas.get(groupe, []):
            cle = terme(fournisseur, cas["fonction"], e["code"])
            groupes.setdefault(cle, []).append(e["etiquette"])
    return sorted(groupes.items(), key=lambda kv: -len(kv[1]))


def rapport(nom_module, cas, tuteur=None):
    if tuteur:
        d = os.path.join(RACINE, tuteur)
        if d not in sys.path:
            sys.path.insert(0, d)
    try:
        f = importlib.import_module(nom_module)
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "\nFournisseur introuvable : %s\n"
            "  cherche dans : %s\n"
            "  ajoutez --tuteur <repertoire> si le fournisseur est dans un tuteur.\n"
            % (exc, ", ".join(sys.path[:3])))

    manquants = [x for x in ("name", "analyse", "categorise", "command", "test_template")
                 if not hasattr(f, x)]
    print("FOURNISSEUR %s" % nom_module)
    print("  langage    : %s" % getattr(f, "name", "?"))
    print("  extension  : %s" % getattr(f, "extension", "?"))
    if manquants:
        print("  INCOMPLET  : il manque %s" % ", ".join(manquants))
        return 1
    print("  cinq elements presents")

    cl = classes(f, cas)
    n = len(cas.get("equivalentes", [])) + len(cas.get("distinctes", []))
    print("\n%d ecritures -> %d terme(s) distinct(s)" % (n, len(cl)))
    print()
    for (forme, base, pas), etiq in cl:
        print("  %-14s base %-8s pas %-26s %s"
              % (forme, base or "-", (pas or "-")[:26], ", ".join(etiq)))

    souci = 0
    print()
    # propriete 1 : les equivalentes coincident
    eq = cas.get("equivalentes", [])
    if eq:
        termes = {terme(f, cas["fonction"], e["code"]) for e in eq}
        if len(termes) == 1:
            print("REUNION  ok : les %d ecritures equivalentes rendent le meme terme." % len(eq))
        else:
            souci = 1
            print("REUNION  ECHEC : %d ecritures equivalentes rendent %d termes."
                  % (len(eq), len(termes)))
            print("         Le tuteur ecarterait des solutions structurellement")
            print("         identiques a d'autres qu'il accepte. Cherchez une")
            print("         normalisation manquante, la commutativite par exemple.")
    # propriete 2 : les distinctes se separent, et de la classe equivalente
    di = cas.get("distinctes", [])
    if di:
        vus = {}
        for e in di:
            vus.setdefault(terme(f, cas["fonction"], e["code"]), []).append(e["etiquette"])
        base = {terme(f, cas["fonction"], e["code"]) for e in eq}
        melanges = [v for k, v in vus.items() if len(v) > 1] + \
                   [v for k, v in vus.items() if k in base]
        if not melanges:
            print("SEPARATION ok : les %d ecritures distinctes rendent des termes distincts."
                  % len(di))
        else:
            souci = 1
            print("SEPARATION ECHEC : ces ecritures coincident alors qu'elles diffferent :")
            for m in melanges:
                print("         %s" % ", ".join(m))
            print("         Le tuteur admettrait au corpus des solutions qui")
            print("         n'exhibent pas ce que la comparaison doit montrer.")

    # les categories d'erreur, verification secondaire
    print("\nCATEGORISATION DES MESSAGES")
    if not cas.get("messages"):
        print("  (messages de Haskell : fournissez \"messages\" dans le jeu de cas)")
    essais = cas.get("messages") or [
        ["non-exhaustive patterns in function f", "missing-base-case"],
        ["Variable not in scope: fo", "unknown-name"],
        ["parse error on input", "syntax"],
        ["", "wrong-result"]]
    for msg, attendu in [tuple(x) for x in essais]:
        obtenu = f.categorise(msg, compile_mais_faux=(msg == ""))
        etat = "ok" if obtenu == attendu else "ATTENDU %s" % attendu
        print("  %-42s -> %-20s %s" % ((msg or "(compile mais faux)")[:42], obtenu, etat))
        if obtenu != attendu:
            souci = 1
    return souci


def main():
    a = argparse.ArgumentParser(description="Valide un fournisseur de langage.")
    a.add_argument("module", help="nom du module, par exemple language_ml")
    a.add_argument("--tuteur", help="repertoire du tuteur qui contient le fournisseur")
    a.add_argument("--cas", help="jeu de cas au format JSON")
    o = a.parse_args()
    cas = CAS_DEFAUT
    if o.cas:
        with open(o.cas, encoding="utf-8") as f:
            cas = json.load(f)
    raise SystemExit(rapport(o.module, cas, o.tuteur))


if __name__ == "__main__":
    main()
