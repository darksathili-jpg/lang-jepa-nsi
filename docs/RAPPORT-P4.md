# P4 · Progression du dialogue socratique

## Défaut reproduit

Le dialogue de référence a été rejoué sur `46da3f3` avec SmolLM3-3B Q4_K_M, révision `4965cb60`, llama.cpp b12600, deux fils CPU et accès Internet coupé. Au quatrième tour, après « Car 0 est supérieur à -4 et à -2. », la génération est restée au niveau 2 et a répété exactement la question du deuxième tour « Quelle est la valeur de `m` après l’itération avec `-4` ? ». Le cinquième tour a, en plus, produit une réponse refusée pour le format. [Entrées](../p4/reference.json) · [Trace brute avant correction](../p4/preuves/avant.jsonl)

Le modèle recevait les trois derniers échanges. L’étape évoluait selon des indices superficiels dans le texte et selon la présence d’un changement de code. L’orchestrateur ne détenait ni preuve d’acquisition ni liste des questions déjà posées.

## Correction

| Élément | Comportement |
| --- | --- |
| État du maximum | Notion, objectif en cours, objectif suivant, acquis et erreurs avec tour, extrait et critère, questions et stratégies déjà employées. |
| Validation | Regroupe la valeur et son rôle dans le test, la relation d’ordre ou la déclaration d’un résultat sur la version corrigée. Les cinq catégories restent des jugements heuristiques propres au cas de référence. |
| Répétitions | Comparaison déterministe des termes normalisés, avec quelques synonymes et un seuil de Jaccard de 0,63. L’orchestrateur alterne les approches et conserve les questions lors d’un changement de code. Une fois les questions utiles épuisées, il propose une action au lieu de rouvrir un objectif validé. |
| Vérification | Une modification de code seule laisse l’objectif de vérification ouvert. La consolidation exige une forme d’accumulation reconnue statiquement et le résultat −2 déclaré pour le test `[-4, -2]`. L’atelier n’exécute jamais la saisie de l’élève. |
| SmolLM3 | Produit un indice bref dans un format dédié. Les règles choisissent la question. L’atelier indique la source et écarte les formulations répétitives, les affirmations, les résultats et les suggestions directes de code. |
| Changement de notion | La demande explicite est reconnue et l’atelier propose de sélectionner un autre exercice ou de remplacer l’énoncé. Les acquis restent affichables tant que l’élève poursuit le même exercice. |

Le serveur conserve au plus 32 sessions en mémoire. Elles expirent après 45 minutes d’inactivité. Il conserve six échanges récents et jusqu’à 28 questions par état du maximum. Pour ce scénario, SmolLM3 reçoit les intitulés des objectifs acquis, l’objectif en cours, la question du serveur et le dernier message, avec des limites de longueur. Le navigateur transmet le texte, l’identifiant opaque de session et le numéro de tour. Ses déclarations d’historique et de progression ne sont jamais prises comme preuve. Une nouvelle soumission identique rejoue le dernier résultat sans avancer de nouveau. Changer de mode ou de niveau ouvre une nouvelle session. Un changement d’énoncé réinitialise le contexte dans la session.

Ce profil détaillé porte sur le maximum de référence. Le parcours guidé et le mode conversationnel conservent leurs ressources pour les autres exercices, avec l’historique borné du serveur. L’analyse statique du cas de référence reconnaît un sous-ensemble des corrections Python possibles. Une forme différente peut être valide et rester en attente de vérification.

## Recette reproductible

Préparer le moteur et les poids comme indiqué dans le guide d’installation. Pour la recette navigateur uniquement, préparer également Playwright avec `python -m pip install playwright`, puis son Chromium avec `python -m playwright install chromium`. Utiliser `--chromium` avec le chemin de l’exécutable si Chromium est déjà installé. Couper l’accès Internet une fois ces ressources disponibles. [Préparation des poids et du moteur](INSTALLATION-P3.md)

```bash
python -m unittest discover -s tests -v
node --check app/tutor.js
mkdir -p results
python tests/socratic_browser.py --assets models/tutor --output results/p4.jsonl
python tests/guided_browser.py
python tests/browser_smoke.py
python tests/tutor_browser.py --assets models/tutor
```

Sous PowerShell, créer `results` avec `New-Item -ItemType Directory -Force results`. Choisir un nouveau fichier de sortie à chaque nouvelle recette.

La recette réelle utilise les six messages fournis, puis des demandes répétées de corrigé, une proposition de stratégie, un résultat déclaré avant correction, une modification sans résultat, un test avec la version reconnue, le contrat de la liste vide et un changement de notion. Elle vérifie la conservation de la preuve du quatrième tour, l’absence de question répétée, la non-divulgation du programme dans les réponses affichées et la provenance SmolLM3 des indices générés affichés.

## Résultats observés

Le dialogue passe à la stratégie au tour 4, dès que l’élève explique que zéro est supérieur à `-4` et à `-2`. La réponse reconnaît que `m` demeure inchangé et demande quelle propriété devrait avoir la valeur de départ. Les tours 5 et 6 conservent cet acquis. Les 14 tours présentent 11 questions distinctes et passent les contrôles de non-divulgation. Sur les 11 tours qui sollicitent SmolLM3, trois indices générés sont affichés et huit propositions sont écartées. Le temps médian de réponse du serveur pour ces 11 tours est de 9,69 s. [Trace complète après correction](../p4/preuves/apres-chromium.jsonl)

| Tour | Preuve vérifiée dans Chromium |
| --- | --- |
| 1 à 3 | L’élève distingue le résultat observé et le résultat attendu. `m vaut 0` est accepté comme constat et appelle une justification. |
| 4 à 8 | L’explication est reconnue. Le dialogue reste orienté vers la stratégie, y compris après deux demandes de corrigé. |
| 9 à 11 | La stratégie proposée est enregistrée. Un résultat déclaré avec le programme initial et une modification seule laissent la vérification ouverte. |
| 12 et 13 | La forme corrigée reconnue et le résultat −2 déclaré permettent de discuter de `[]`. L’élève précise la précondition de liste non vide. |
| 14 | La demande de passer aux dictionnaires est reconnue. La preuve du tour 4 figure toujours dans l’état serveur. |

La recette a abouti sur Linux x86-64 avec Chromium 156, SmolLM3-3B Q4_K_M, révision `4965cb60`, et llama.cpp b12600 sur deux fils CPU. Seule l’interface de boucle locale était disponible, sans route IPv4. Chromium n’a demandé aucune ressource externe. Les mesures de cette recette caractérisent la machine Linux d’essai. La recette P4 sur Windows natif reste à effectuer.

Les 36 tests Python ont réussi, ainsi que la vérification JavaScript. Les recettes Chromium précédentes ont aussi réussi pour les cinq étapes guidées, les deux niveaux NSI, le laboratoire sur ordinateur et mobile, les états de modèle absent ou corrompu et le dialogue de vérification à quatre tours. La lisibilité et l’absence de débordement horizontal ont été contrôlées dans les trois thèmes. [Clair](captures-p4/atelier-light.png) · [Sombre](captures-p4/atelier-dark.png) · [Projecteur](captures-p4/atelier-projector.png)
