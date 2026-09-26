"""Fournisseur de langage Python pour FPTutor-Shell.

Demonstration de faisabilite : ce module implemente, pour Python, la seule interface
dont le noyau depend, et rend des formes canoniques que l'anti-unificateur de
remontee.py — inchange — sait aligner.

Interface attendue d'un fournisseur de langage
----------------------------------------------
    nom                                 identifiant du langage
    extension                           extension de fichier
    commande(chemin)                    commande d'execution du module de test
    gabarit_test(code, expressions)     source du module de test
    analyser(nom, code) -> dict         {"forme", "base", "pas"} en vocabulaire commun
    categoriser(message) -> str         categorie d'erreur, pour le premier niveau d'aide

Le vocabulaire commun est celui de l'engine : C1..Cn pour les champs du motif,
REC pour l'appel recursif, COND pour une decision, et des applications prefixes
pour tout ce qui n'est pas un operateur infixe.

Pour Python, la normalisation se fait sur l'arbre syntaxique de la bibliotheque
standard, ce qui la rend nettement plus sure que l'analyse textuelle employee pour
Haskell : la variance d'ecriture est absorbee par l'analyseur du langage lui-meme.
"""

import ast, re

nom = "python"
extension = ".py"


def commande(chemin):
    return ["python3", chemin]


GABARIT = """%s

if __name__ == "__main__":
%s
"""


def gabarit_test(code, expressions):
    lignes = "\n".join("    print(%s)" % e for e in expressions)
    return GABARIT % (code.rstrip(), lignes)


# ------------------------------------------------------------ normalisation

INFIXES = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
           ast.Mod: "mod", ast.Pow: "^"}
COMPARES = {ast.Eq: "==", ast.NotEq: "/=", ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">="}


class Normalisateur(ast.NodeVisitor):
    """Traduit une expression Python en terme du vocabulaire commun."""

    def __init__(self, fonction, parametre):
        self.fonction = fonction
        self.parametre = parametre

    def rendre(self, n):
        return self.visit(n)

    # --- feuilles
    def visit_Name(self, n):
        return n.id

    def visit_Constant(self, n):
        if isinstance(n.value, str):
            return '"%s"' % n.value
        if n.value is None:
            return "RIEN"
        if n.value is True:
            return "True"
        if n.value is False:
            return "False"
        return repr(n.value)

    # --- structures
    def visit_List(self, n):
        if not n.elts:
            return "[]"
        return "(LISTE %s)" % " ".join(self.rendre(e) for e in n.elts)

    def visit_BinOp(self, n):
        op = INFIXES.get(type(n.op), "?")
        g, d = self.rendre(n.left), self.rendre(n.right)
        # commutativite limitee a + et * sur les nombres, comme pour le fournisseur
        # Haskell : appliquee a la concatenation elle produirait de fausses egalites
        if op in ("+", "*") and g.strip() == "REC" and d.strip() != "REC":
            g, d = d, g
        return "(%s %s %s)" % (g, op, d)

    def visit_UnaryOp(self, n):
        if isinstance(n.op, ast.Not):
            return "(NON %s)" % self.rendre(n.operand)
        if isinstance(n.op, ast.USub):
            return "(NEG %s)" % self.rendre(n.operand)
        return self.rendre(n.operand)

    def visit_Compare(self, n):
        op = COMPARES.get(type(n.ops[0]), "?")
        return "(%s %s %s)" % (self.rendre(n.left), op, self.rendre(n.comparators[0]))

    def visit_Call(self, n):
        # l'appel recursif devient REC
        if isinstance(n.func, ast.Name) and n.func.id == self.fonction:
            return "REC"
        f = self.rendre(n.func) if not isinstance(n.func, ast.Name) else n.func.id
        args = " ".join(self.rendre(a) for a in n.args)
        return "(%s %s)" % (f, args) if args else f

    def visit_Attribute(self, n):
        # x.upper() devient (upper x) : la meme forme qu'un appel prefixe
        return "(%s %s)" % (n.attr, self.rendre(n.value))

    def visit_Subscript(self, n):
        sur_parametre = isinstance(n.value, ast.Name) and n.value.id == self.parametre
        sl = n.slice
        if sur_parametre and isinstance(sl, ast.Constant) and sl.value == 0:
            return "C1"                      # le premier element de l'entree
        if sur_parametre and isinstance(sl, ast.Slice) and sl.lower is not None:
            if isinstance(sl.lower, ast.Constant) and sl.lower.value == 1:
                return "RESTE"               # le reste de l'entree
        return "(premier %s)" % self.rendre(n.value)

    def visit_IfExp(self, n):
        return "COND (%s) (%s) (%s)" % (self.rendre(n.test), self.rendre(n.body),
                                        self.rendre(n.orelse))

    def generic_visit(self, n):
        return "?"


def _vide(test):
    """Reconnait les tests « l'entree est vide » : not xs, len(xs) == 0, xs == []."""
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return True
    if isinstance(test, ast.Compare):
        d = test.comparators[0]
        if isinstance(d, ast.Constant) and d.value == 0:
            return True
        if isinstance(d, ast.List) and not d.elts:
            return True
    return False


def _serrer(e):
    e = re.sub(r"\s+", " ", e)
    return e.strip()


def analyser(nom_fonction, code):
    """Rend {"forme", "base", "pas"} dans le vocabulaire commun, ou une forme non
    analysable si la definition ne se laisse pas ramener a un cas de base et un cas
    recursif."""
    try:
        arbre = ast.parse(code)
    except SyntaxError:
        return {"forme": "non-analysable", "base": None, "pas": None}
    fn = next((n for n in ast.walk(arbre)
               if isinstance(n, ast.FunctionDef) and n.name == nom_fonction), None)
    if fn is None:
        return {"forme": "non-analysable", "base": None, "pas": None}

    parametre = fn.args.args[0].arg if fn.args.args else "xs"
    N = Normalisateur(nom_fonction, parametre)
    if any(isinstance(n, (ast.ListComp, ast.SetComp, ast.GeneratorExp))
           for n in ast.walk(fn)):
        return {"forme": "comprehension", "base": None, "pas": None,
                "motif": "comprehension : la marche a suivre n'est pas exposee"}
    base, pas = None, None

    corps = fn.body
    # forme reconnue : if <test vide> : return <base>   puis   return <pas>
    for i, stmt in enumerate(corps):
        if isinstance(stmt, ast.If):
            retour = next((s for s in stmt.body if isinstance(s, ast.Return)), None)
            if retour is not None:
                base = _serrer(N.rendre(retour.value))
            suite = stmt.orelse or corps[i + 1:]
            r2 = next((s for s in suite if isinstance(s, ast.Return)), None)
            if r2 is not None:
                pas = _serrer(N.rendre(r2.value))
        elif isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.IfExp):
            t = stmt.value
            base = _serrer(N.rendre(t.body if _vide(t.test) else t.orelse))
            pas = _serrer(N.rendre(t.orelse if _vide(t.test) else t.body))
        elif isinstance(stmt, ast.Return) and pas is None and base is not None:
            pas = _serrer(N.rendre(stmt.value))
        elif isinstance(stmt, ast.For) or isinstance(stmt, ast.While):
            return {"forme": "iteratif", "base": None, "pas": None,
                    "motif": "boucle explicite : pas de cas de base ni de cas recursif"}

    if base is None and pas is None:
        corps_retour = next((x for x in corps if isinstance(x, ast.Return)), None)
        if corps_retour is not None:
            rendu = _serrer(N.rendre(corps_retour.value))
            if "REC" not in rendu:
                return {"forme": "sans-recursion", "base": None, "pas": rendu,
                        "motif": "aucun appel recursif : la solution ne montre pas la marche"}
    if base is None or pas is None:
        return {"forme": "non-analysable", "base": base, "pas": pas}
    if "REC" not in pas:
        return {"forme": "sans-recursion", "base": base, "pas": pas,
                "motif": "aucun appel recursif : la solution ne montre pas la marche"}
    return {"forme": "constructeurs", "base": base, "pas": pas}


# ------------------------------------------------------------ erreurs

FORMES_ALIGNABLES = ("constructeurs",)


def categoriser(message, compile_mais_faux=False):
    if compile_mais_faux:
        return "resultat-faux"
    if "RecursionError" in message:
        return "appel-mauvaise-valeur"
    if "IndexError" in message:
        return "cas-de-base-oublie"
    if "TypeError" in message:
        return "types-incompatibles"
    if "NameError" in message:
        return "nom-inconnu"
    if "SyntaxError" in message or "IndentationError" in message:
        return "syntaxe"
    return "non-classee"


# ------------------------------------------------------------ demonstration

TRANSFORMATION = [
 ("doubler", "def doubler(xs):\n    if not xs:\n        return []\n"
             "    return [2 * xs[0]] + doubler(xs[1:])\n"),
 ("majuscules", "def majuscules(xs):\n    if not xs:\n        return []\n"
                "    return [xs[0].upper()] + majuscules(xs[1:])\n"),
 ("initiales", "def initiales(xs):\n    if not xs:\n        return []\n"
               "    return [xs[0][0]] + initiales(xs[1:])\n"),
]

PLI = [
 ("somme", "def somme(xs):\n    if not xs:\n        return 0\n"
           "    return xs[0] + somme(xs[1:])\n"),
 ("produit", "def produit(xs):\n    if not xs:\n        return 1\n"
             "    return xs[0] * produit(xs[1:])\n"),
 ("longueur", "def longueur(xs):\n    if not xs:\n        return 0\n"
              "    return 1 + longueur(xs[1:])\n"),
 ("aplatir", "def aplatir(xss):\n    if not xss:\n        return []\n"
             "    return xss[0] + aplatir(xss[1:])\n"),
]

HORS_FORME = [
 ("doubler", "def doubler(xs):\n    return [2 * x for x in xs]\n"),
 ("somme", "def somme(xs):\n    total = 0\n    for x in xs:\n        total += x\n"
           "    return total\n"),
]


if __name__ == "__main__":
    import remontee as R

    def aligner(corpus):
        formes, bases = [], []
        for n, c in corpus:
            a = analyser(n, c)
            if a["pas"] is None:
                continue
            formes.append(R.parse(R.tokens(a["pas"])))
            bases.append(a["base"])
        if len(formes) < 2:
            return 0, None
        R.Trou.n = 0
        subst = {}
        g = formes[0]
        for f in formes[1:]:
            g = R.antiunifier(g, f, subst)
        vus = set()
        def compter(x):
            if isinstance(x, R.Trou):
                vus.add(x.i)
            elif isinstance(x, tuple):
                for y in x[1:]:
                    compter(y)
        compter(g)
        return len(vus) + (1 if len(set(bases)) > 1 else 0), R.rendre(g)

    print("FOURNISSEUR PYTHON — normalisation par l'AST, moteur d'alignement inchange")
    print("=" * 78)
    for titre, corpus, attendu in (("famille de transformation", TRANSFORMATION, 1),
                                   ("famille du pli", PLI, 3)):
        print("\n%s" % titre)
        for n, c in corpus:
            a = analyser(n, c)
            print("  %-11s base %-4s pas %s" % (n, a["base"], a["pas"]))
        pts, forme = aligner(corpus)
        print("  -> %d point(s) de variation, attendu %d : %s   forme %s"
              % (pts, attendu, "conforme" if pts == attendu else "NON CONFORME", forme))

    print("\nsoumissions correctes mais non comparables")
    for n, c in HORS_FORME:
        a = analyser(n, c)
        print("  %-11s forme %-16s %s" % (n, a["forme"], a.get("motif", "")))
