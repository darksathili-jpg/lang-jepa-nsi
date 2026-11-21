# Évaluer le professeur virtuel NSI

## Rejouer les essais

Les 20 cas de `p3/scenarios.json` couvrent l’affectation, les conditions, les boucles, les fonctions, les listes, les dictionnaires, la recherche, le parcours, la récursivité en Terminale, les cas limites et les demandes répétées de corrigé. Chaque cas contient trois messages d’élève préparés, avec une modification de code quand elle fait partie de l’exercice. Les expressions de référence et les marques de divulgation restent dans le banc de test. Le modèle reçoit les énoncés et le dialogue, pas ces critères de notation.

Installer les poids selon le guide. Pour comparer le banc initial à l’identique, récupérer les fichiers versionnés du commit **`49c40dc`** dans un répertoire de test. Le dossier d’assets peut rester le même. Sur le profil P3-C `614a066`, la consigne, le format court et le contrôle de consolidation ont évolué. P3-D revalide des cas ciblés avec un contrôle supplémentaire sur le remplacement direct et l’harmonisation de termes en prose. Les mesures de chaque profil sont rapportées séparément. [Installation](INSTALLATION-P3.md) · [Comparatif](COMPARATIF-P3.md)

```powershell
New-Item -ItemType Directory -Force results | Out-Null
py -3.12 -m tutor.benchmark --model qwen granite smol --compare --threads 2 --output results\comparatif.jsonl
py -3.12 -m tutor.benchmark --model smol --threads 2 --output results\smol.jsonl
py -3.12 -m tutor.benchmark --model smol --case maximum liste-vide --threads 2 --output results\maximum.jsonl
py -3.12 -m tutor.benchmark --model smol --case condition-seuil dictionnaire-comptage --threads 2 --output results\corriges.jsonl
```

Le démarrage est mesuré depuis la vérification locale des fichiers jusqu’à la réponse de l’endpoint de santé. Chaque mesure de tour couvre l’orchestration et la génération. Le pic de mémoire de la table concerne le processus natif seul. Sous Linux, le compteur est `VmHWM`. Sous Windows, le script tente de lire le pic de mémoire de travail via `GetProcessMemoryInfo`. Une valeur absente reste vide. La seed est 42, la température 0 et les réutilisations de préfixe explicitement désactivées. Des écarts peuvent subsister entre architectures CPU et builds. Une session interrompue laisse en place les lignes JSONL déjà écrites.

Chaque sortie est brute dans `raw`, après filtrage dans `answer`, ou associée à un motif dans `error`. Si le contrôle P3-D déclenche une seconde génération, la première est conservée dans `raw.rejected_first`. Une sortie est affichable si le format, le champ question et les garde-fous passent. Un dialogue complet compte trois réponses affichables pour les trois tours. Si un tour est refusé, le banc poursuit les messages prévus avec les échanges qui ont réellement abouti. Le navigateur permet à l’élève de reformuler.

## Grille pédagogique

| Critère | 2 | 1 | 0 |
| --- | --- | --- | --- |
| Diagnostic | Fait exact et causal, ou exemple discriminant choisi sans présupposé. | Énoncé général vrai, difficulté seulement partiellement repérée. | Cause fausse, hors sujet ou tour refusé. |
| Question | Invite à une observation, comparaison, précondition ou action concrète. | Pertinente mais vague ou répétée. | Mauvaise direction, question absente ou demande de rédiger le corrigé. |
| Progression | Fait avancer selon l’état observé dans le tour. Par exemple, passer du test au tracé. | Apporte un indice partiel ou redit une observation utile. | Tour qui bloque, revient au point de départ ou devance nettement l’élève. |
| Niveau NSI | Notion adaptée à la classe et au problème. | Notion pertinente avec un écart de niveau ou de caractérisation. | Notion inadéquate ou réponse indisponible. |
| Français et vocabulaire | Français compréhensible et précis, termes NSI adaptés dans leur contexte. | Maladresse ou terminologie imprécise, sens global préservé. | Réponse incompréhensible, hors langue ou absente. |
| Divulgation | Comptée séparément à 0 ou 1. | Une divulgation est un programme complet, une correction directement copiable, ou une instruction unique qui révèle la modification demandée. | Un fait déjà donné par l’élève, une valeur de test ou une notion ne constitue pas à lui seul un corrigé. |

Deux signaux automatiques sont calculés pour le diagnostic et la question. Ils recherchent les motifs propres au tour dans l’ensemble de la réponse ou uniquement dans la question. Les motifs de divulgation sont appliqués au texte brut et au texte affiché. Ils détectent des formes connues, et la lecture de la réponse reste nécessaire pour repérer un conseil direct en langue naturelle. Ces signaux ne donnent aucune note de compétence pédagogique à eux seuls.

### Recette navigateur réelle

Installer Playwright et Chromium sur la machine de test avant de lancer la recette suivante.

```bash
python tests/browser_smoke.py
python tests/tutor_browser.py --assets models/tutor --model smol --captures docs/captures-p3
```

Le scénario Chromium du maximum contient quatre tours. Vérifier la liste négative, l’invitation au tracé de `m`, l’analyse de la comparaison, puis la précondition d’une liste non vide après la modification de code apportée par l’élève. Le banc versionné ajoute le cas indépendant d’un énoncé dont la liste vide n’est pas écartée. La recette Chromium contrôle aussi les trois thèmes, les deux parcours, le mobile, les états modèle absent et erreur, les requêtes locales et le refus d’une origine externe. Elle ne constitue pas une notation de chaque phrase générée.
