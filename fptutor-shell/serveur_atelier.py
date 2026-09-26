#!/usr/bin/env python3
"""Serveur de l'atelier : interface de creation d'un tuteur.

    python3 serveur_atelier.py            http://localhost:8090
    PORT=8095 python3 serveur_atelier.py

Depuis la racine, le lanceur fait la meme chose :

    python3 fptutor --atelier
    python3 fptutor --atelier 8095

L'atelier sert quatre routes et rien de plus.

    GET  /                    l'interface
    GET  /api/tuteurs         les tuteurs existants et leurs fournisseurs
    POST /api/creer           engendre un repertoire de tuteur
    POST /api/banc            passe un fournisseur au banc d'essai
    POST /api/analyser        rend la forme canonique d'une ecriture

Aucune dependance hors bibliotheque standard.
"""

import http.server, importlib, io, json, os, socketserver, sys, urllib.parse
import contextlib

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
for d in (RACINE, ICI):
    if d not in sys.path:
        sys.path.insert(0, d)

import creer_tuteur, banc_essai

# Les langages fonctionnels courants, avec la commande qui execute un fichier.
# La liste sert a preremplir ; un langage absent s'ajoute en choisissant
# « autre » et en saisissant la commande.
LANGAGES = [
    {"court": "haskell",  "nom": "Haskell",        "interprete": "runghc",       "extension": ".hs"},
    {"court": "ocaml",    "nom": "OCaml",          "interprete": "ocaml",        "extension": ".ml"},
    {"court": "fsharp",   "nom": "F#",             "interprete": "dotnet fsi",   "extension": ".fsx"},
    {"court": "sml",      "nom": "Standard ML",    "interprete": "sml",          "extension": ".sml"},
    {"court": "racket",   "nom": "Racket",         "interprete": "racket",       "extension": ".rkt"},
    {"court": "scheme",   "nom": "Scheme",         "interprete": "guile -s",     "extension": ".scm"},
    {"court": "clojure",  "nom": "Clojure",        "interprete": "clojure -M",   "extension": ".clj"},
    {"court": "elixir",   "nom": "Elixir",         "interprete": "elixir",       "extension": ".exs"},
    {"court": "erlang",   "nom": "Erlang",         "interprete": "escript",      "extension": ".erl"},
    {"court": "elm",      "nom": "Elm",            "interprete": "elm repl",     "extension": ".elm"},
    {"court": "purescript", "nom": "PureScript",   "interprete": "spago script", "extension": ".purs"},
    {"court": "scala",    "nom": "Scala",          "interprete": "scala",        "extension": ".scala"},
    {"court": "python",   "nom": "Python",         "interprete": "python3",      "extension": ".py"},
    {"court": "julia",    "nom": "Julia",          "interprete": "julia",        "extension": ".jl"},
    {"court": "lisp",     "nom": "Common Lisp",    "interprete": "sbcl --script","extension": ".lisp"},
    {"court": "idris",    "nom": "Idris 2",        "interprete": "idris2 --exec main", "extension": ".idr"},
    {"court": "agda",     "nom": "Agda",           "interprete": "agda --compile", "extension": ".agda"},
    {"court": "gleam",    "nom": "Gleam",          "interprete": "gleam run",    "extension": ".gleam"},
]


def modele(tuteur="hstutor"):
    """Les activites du tuteur de reference, pour les instancier ailleurs.

    On rend la structure et non la syntaxe : par famille, les ancrages avec
    leur nom, leur enonce et leurs tests. L'auteur du nouveau tuteur garde
    les enonces et n'a qu'a traduire l'amorce et les expressions de test.
    """
    env = dict(os.environ, TUTOR_DIR=tuteur)
    anciens = dict(os.environ)
    os.environ.update(env)
    try:
        for m in ("noyau", "remontee", "normalisation2"):
            sys.modules.pop(m, None)
        import noyau as K
        fam = {}
        for nom_f, ancrages in sorted(K.ACTIVITES.items()):
            fam[nom_f] = {"instances": [], "reemplois": []}
            for a in ancrages:
                fam[nom_f]["instances"].append(
                    {"nom": a[0], "enonce": a[1], "signature": a[2],
                     "amorce": a[3], "tests": [list(t) for t in a[4]]})
            for a in K.REEMPLOIS.get(nom_f, []):
                fam[nom_f]["reemplois"].append(
                    {"nom": a[0], "enonce": a[1], "signature": a[2],
                     "amorce": a[3], "tests": [list(t) for t in a[4]]})
        return fam
    finally:
        os.environ.clear()
        os.environ.update(anciens)
        for m in ("noyau", "remontee", "normalisation2"):
            sys.modules.pop(m, None)

PORT = int(os.environ.get("PORT", "8090"))


def tuteurs():
    out = []
    for f in sorted(os.listdir(RACINE)):
        d = os.path.join(RACINE, f)
        if not os.path.isdir(d) or f.startswith((".", "_")) or f == "fptutor-shell":
            continue
        fournisseurs = sorted(x[:-3] for x in os.listdir(d)
                              if x.startswith("language_") and x.endswith(".py"))
        if fournisseurs:
            out.append({"repertoire": f, "fournisseurs": fournisseurs,
                        "fichiers": sorted(x for x in os.listdir(d)
                                           if not x.startswith((".", "_"))),
                        "donnees": os.path.exists(os.path.join(d, "etat.json"))})
    return out


def charger(module, tuteur):
    d = os.path.join(RACINE, tuteur)
    if d not in sys.path:
        sys.path.insert(0, d)
    if module in sys.modules:
        del sys.modules[module]
    return importlib.import_module(module)


def api(chemin, corps):
    if chemin == "/api/tuteurs":
        return {"tuteurs": tuteurs(), "racine": RACINE, "langages": LANGAGES}

    if chemin == "/api/modele":
        t = (corps or {}).get("tuteur") or "hstutor"
        try:
            return {"tuteur": t, "familles": modele(t)}
        except Exception as exc:
            return {"refus": "%s : %s" % (type(exc).__name__, exc)}

    if chemin == "/api/creer":
        court = (corps.get("court") or "").strip()
        rep = (corps.get("repertoire") or "").strip() or (court + "tutor")
        if not court.isidentifier():
            return {"refus": "Le nom court doit etre un identifiant : lettres, "
                             "chiffres, tiret bas, sans espace."}
        try:
            cible = creer_tuteur.creer(court, rep,
                                       corps.get("interprete") or "INTERPRETE",
                                       corps.get("extension") or ".EXT",
                                       bool(corps.get("force")))
        except SystemExit as exc:
            return {"refus": str(exc)}
        retenus = corps.get("retenus")
        if retenus:
            try:
                creer_tuteur.ecrire_activites(cible, court, modele(
                    corps.get("modele") or "hstutor"), retenus)
            except Exception as exc:
                return {"refus": "activites : %s : %s" % (type(exc).__name__, exc)}
        return {"repertoire": rep, "chemin": cible,
                "fichiers": sorted(os.listdir(cible)),
                "suite": ["ecrire analyse dans language_%s.py" % court,
                          "passer le banc d'essai",
                          "ecrire les ancrages dans activities_%s.py" % court,
                          "lancer l'inducteur d'obligations",
                          "python3 fptutor %s" % rep]}

    if chemin == "/api/banc":
        module = corps.get("module") or ""
        tuteur = corps.get("tuteur") or ""
        cas = corps.get("cas") or banc_essai.CAS_DEFAUT
        sortie = io.StringIO()
        try:
            with contextlib.redirect_stdout(sortie):
                code = banc_essai.rapport(module, cas, tuteur)
        except SystemExit as exc:
            return {"refus": str(exc)}
        except Exception as exc:
            return {"refus": "%s : %s" % (type(exc).__name__, exc)}
        return {"code": code, "rapport": sortie.getvalue()}

    if chemin == "/api/analyser":
        try:
            f = charger(corps["module"], corps.get("tuteur", ""))
            r = f.analyse(corps.get("fonction", "f"), corps.get("code", ""))
        except Exception as exc:
            return {"refus": "%s : %s" % (type(exc).__name__, exc)}
        return {"forme": r.get("forme", "?"), "base": r.get("base", ""),
                "pas": r.get("pas", "")}

    return {"refus": "route inconnue : %s" % chemin}


class Poste(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _envoyer(self, code, corps, type_mime="application/json"):
        b = corps.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", type_mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/", "/index.html", "/atelier.html"):
            p = os.path.join(ICI, "atelier.html")
            with open(p, encoding="utf-8") as f:
                return self._envoyer(200, f.read(), "text/html")
        if u.path.startswith("/api/"):
            try:
                return self._envoyer(200, json.dumps(
                    api(u.path, dict(urllib.parse.parse_qsl(u.query))),
                    ensure_ascii=False))
            except Exception as exc:
                return self._envoyer(500, json.dumps({"erreur": str(exc)}))
        return self._envoyer(404, "introuvable", "text/plain")

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0"))
        try:
            corps = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            corps = {}
        try:
            return self._envoyer(200, json.dumps(api(u.path, corps),
                                                 ensure_ascii=False))
        except Exception as exc:
            return self._envoyer(500, json.dumps({"erreur": str(exc)}))


class Serveur(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    print("Atelier FPTutor sur http://localhost:%d" % PORT)
    print("  racine du shell : %s" % RACINE)
    print("  tuteurs         : %s" % ", ".join(t["repertoire"] for t in tuteurs()))
    try:
        Serveur(("", PORT), Poste).serve_forever()
    except KeyboardInterrupt:
        print("\narret")


if __name__ == "__main__":
    main()
