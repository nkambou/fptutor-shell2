# fptutor-shell — atelier de création d'un tuteur

Cet atelier sert à porter FPTutor vers un nouveau langage fonctionnel. Il ne fait pas tourner de tuteur : il en engendre un, puis il valide ce que l'auteur a écrit.

Trois outils, dans l'ordre où on les emploie.

## 1. `creer_tuteur.py` — engendrer le répertoire

    python3 creer_tuteur.py ml mltutor --interprete ocaml --extension .ml

Écrit `../mltutor/` avec quatre fichiers : le fournisseur à partir du gabarit, un squelette d'ancrages, une copie du référentiel à adapter, et un `LISEZMOI.md` qui donne la marche à suivre. Rien du shell n'est modifié, et le générateur refuse d'écrire dans un répertoire non vide sans `--force`.

## 2. `gabarit_language.py` — le modèle du fournisseur

Les cinq éléments de l'interface, avec le vocabulaire commun documenté et les endroits à écrire signalés. Un seul demande un vrai travail, `analyse`, qui prend le code d'une soumission et rend sa forme, son cas de base et son cas récursif en vocabulaire commun. Les quatre autres tiennent en deux lignes chacun.

Le gabarit énonce la propriété dont tout le reste dépend : **la normalisation doit être une fonction**. Deux écritures qui ne diffèrent que par la syntaxe doivent rendre le même terme, sinon les comptes d'alignement deviennent instables et la condition de stabilité perd son sens.

## 3. `banc_essai.py` — valider le fournisseur

    python3 banc_essai.py language_ml --tuteur mltutor
    python3 banc_essai.py language_python --tuteur pytutor --cas cas_exemple.json

Le banc vérifie deux propriétés séparément, ce qui rend le diagnostic utilisable. **Réunion** : les écritures déclarées équivalentes rendent bien le même terme ; un échec signifie que le tuteur écarterait des solutions structurellement identiques à d'autres qu'il accepte. **Séparation** : les écritures déclarées distinctes rendent des termes distincts ; un échec signifie qu'il admettrait au corpus des solutions qui n'exhibent pas ce que la comparaison doit montrer.

Il contrôle aussi la projection des messages du compilateur sur les cinq catégories du cadre.

Un jeu de cas déclare les deux groupes et, si vous le souhaitez, les messages propres à votre compilateur. `cas_exemple.json` en donne un pour Python, à recopier et adapter.

## L'ordre qui fait gagner du temps

Écrivez `analyse` contre trois ou quatre solutions de référence et imprimez les formes canoniques **avant** de connecter quoi que ce soit. Une forme canonique qui paraît fausse à l'œil coûte beaucoup moins cher à diagnostiquer qu'un compte d'alignement erroné deux couches plus haut. C'est la recommandation la plus rentable que l'expérience de la seconde instanciation ait produite.

Puis, une fois les ancrages écrits, lancez l'inducteur d'obligations du shell :

    cd .. && TUTOR_DIR=mltutor TUTOR_LANGUAGE=language_ml python3 obligations.py

Il dit quels ancrages sont porteurs, c'est-à-dire les seuls de leur famille à exhiber une variation que la famille doit montrer. C'est ce contrôle qui remplace des semaines de tâtonnement, et il trouve en quelques secondes des obligations qu'une relecture attentive manque.

## Vérification finale

    cd .. && TUTOR_DIR=mltutor TUTOR_LANGUAGE=language_ml python3 generateur.py

Aligne les solutions de référence de chaque famille et compare le résultat à ce que le référentiel annonce. Une famille non conforme n'est pas servie : elle produirait une phase d'abstraction ouverte sur un corpus dont il n'y a rien à extraire.

## Ce que l'atelier ne fait pas

Il n'écrit pas `analyse` à votre place, et il ne peut pas : c'est là que réside la connaissance du langage. Il ne rédige pas les énoncés d'activité, qui sont l'essentiel de l'effort restant et que le cadre ne réduit pas. Et il ne compose pas les familles, il se borne à dire ce que celles que vous avez composées permettent ou non de découvrir.
