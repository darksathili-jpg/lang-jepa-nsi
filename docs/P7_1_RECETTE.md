# P7.1 · Routage et validations du maximum

**Dépôt** `darksathili-jpg/lang-jepa-nsi`, branche `main`. **Base** `b147994`, paquet 0.7.0. **Build Windows 0.7.1** `c6823395d74538f39bc3389eba9d39682d73d3f9`. [Correctif pédagogique](https://github.com/darksathili-jpg/lang-jepa-nsi/commit/4fa231b725d3a43f64f5c8868b4f59def7f4480f) · [Build final](https://github.com/darksathili-jpg/lang-jepa-nsi/commit/c6823395d74538f39bc3389eba9d39682d73d3f9)

## Cause racine

| Composant | Défaut reproduit | Correction |
| --- | --- | --- |
| `tutor/sessions.py` | L’ouverture du moteur P7 dépendait de l’intention reconnue. Une observation initiale du maximum créait un état historique et les réponses courtes suivantes continuaient dans cet état. | Le serveur choisit la spécification couverte à partir de l’exercice guidé ou de l’énoncé et du niveau. Les trois modes commencent en P7 dès le premier tour pour ces exercices. |
| `pedagogy/progress.py` et `tutor/dialogue.py` | Dans l’ancien maximum, la reconnaissance de `tab[0]` devait être accompagnée d’un marqueur d’action. L’affectation `m=tab[0]` seule ne satisfaisait pas ce deuxième critère. La relance remettait en jeu la stratégie. | L’ancienne chaîne reste disponible pour les comparaisons d’archives. La chaîne normale vérifie maintenant la proposition AST dans la forme du programme et le contrat. |
| `pedagogy/interpretation.py` et `pedagogy/workshop.py` | Le type de réponse était parfois inféré de quelques mots de la question affichée. La question d’exclusion n’était pas une cible à part entière. | L’orchestrateur associe une cible à chaque question admissible et la conserve après la sélection réelle, au tour et à la version de code correspondants. |
| Validation de l’ordre | Le parcours pouvait reconnaître l’ordre des nombres sans expliquer en quoi les tests réels sont écrits dans l’autre sens. | Les relations numériques sont vérifiées pour l’entrée active. L’atelier attribue à l’élève la compréhension de l’ordre, puis explique les tests Python et l’effet du bloc. |

`--parcours-historique` est une option interne de rejeu et `case_based=False` constitue son équivalent dans les tests. Le lancement ordinaire n’utilise aucun des deux. Les sessions vivent en mémoire locale. Une mise à jour démarre une instance identifiée par le nouveau build, sans importer les jetons ou les preuves de l’ancienne version. Dans une même session P7, un changement de structure invalide les essais vérifiés. Les cas précédents et la proposition validée restent identifiables et rattachés à leur version. Les soumissions historiques conservent leurs assertions originales dans le périmètre de compatibilité.

## Dialogue identique avant et après

Le dialogue source est rejoué sans modifier les cinq messages. L’essai `[-4, -2]` sert à illustrer l’observation générale de l’élève. Il est enregistré comme proposition du tuteur. Son champ de résultat déclaré et son champ de résultat exécuté restent vides.

| Tour | Élève | 0.7.0 | 0.7.1 |
| --- | --- | --- | --- |
| 1 | « mon programme renvoie 0 quand la liste passée en paramètre ne contient que des nombres négatifs » | Validation sur l’ancien parcours, puis question sur l’attendu. | P7 reconnaît l’observation générale, annonce un exemple et demande son maximum. |
| 2 | « -2 » | L’ancien parcours mène au traçage. | Le tuteur valide l’attendu du cas actif et pose une question de comparaison. |
| 3 | « a chaque fois 0>-4 et 0>-2 » | L’ordre est admis. La réponse dit qu’aucun entier ne dépasse zéro. | L’ordre est admis. Pour `valeur > m`, les deux tests effectifs sont `-4 > 0` et `-2 > 0`, tous deux faux. Le tuteur explique l’absence d’affectation, puis passe au choix du départ. |
| 4 | « m=tab[0] » | Proposition partielle. Conversation locale demande une nouvelle valeur initiale. En hybride, la question porte sur les résultats à exclure. | Initialisation validée sous la précondition de liste non vide. Le tuteur demande de modifier le programme et de vérifier deux entrées distinctes, puis pose sa question sur les résultats à exclure. |
| 5 | « - inf » | Hors sujet dans les deux profils. En hybride, le tuteur venait pourtant de demander quels résultats exclure. | Moins l’infini est exclu comme résultat final. Une valeur initiale de moins l’infini reste possible quand une entrée entière la remplace. La vérification continue. |

Deux tours supplémentaires appliquent la correction et apportent un essai négatif puis un singleton. Un seul essai, un doublon ou un résultat sur la version d’origine laisse la vérification ouverte. Les essais sont confrontés à une forme reconnue de l’AST. [Avant, Chromium Linux](../p7/preuves-p71/avant-linux.jsonl) · [Après, Chromium Linux](../p7/preuves-p71/apres-linux.jsonl) · [Après, Chromium Windows Server](../p7/preuves-p71/apres-windows.jsonl) · [Messages rejoués](../p7/dialogue_p71.json)

## Contrats et contre-exemples

- Le fragment d’affectation doit cibler l’accumulateur identifié. Un indice doit être valable pour toute liste non vide. Une affectation à `m = 0`, un indice `1` sur un singleton, un autre nom de tableau ou plusieurs affectations ne donnent pas d’acquis. Les formulations équivalentes décrivent le même choix d’initialisation. `ast.parse()` sert à lire les fragments. L’atelier n’exécute pas le code élève.
- Une spécification admettant une liste vide exige une stratégie qui précise ce cas avant d’indexer la liste. Pour le maximum demandé d’une liste non vide d’entiers, une valeur renvoyée de moins l’infini serait incorrecte.
- Une réponse courte dépend de la question réellement affichée. La même chaîne « - inf » peut être une stratégie de départ, une valeur finale exclue ou une réponse erronée à la demande d’un maximum attendu. Sans contexte suffisant, le tuteur demande lequel de ces rôles l’élève vise. Une inégalité contradictoire ou une seule comparaison sur plusieurs entrées laisse le traçage ouvert.
- Les preuves sont établies par les règles. Les deux moteurs ont répondu aux sondes. Sur ces tours, SmolLM3 n’a pas généré la réponse pédagogique. En hybride, JEPA a reclassé la question du troisième tour sous Linux et Windows Server. Les autres relances ont conservé le premier choix de l’orchestrateur. **Bénéfice JEPA non démontré.** [Règles et cas contradictoires](../tests/test_p71.py)

## Recette et livraison

Les 79 tests Python réussissent sous Linux, avec un test spécifique à Linux ignoré sous Windows. Le JavaScript passe le contrôle syntaxique. L’assertion principale échoue dans les trois configurations sur `b147994`. Chromium hors Internet a vérifié les 28 tours courants P7 et P7.1 et l’arrêt sans processus résiduel. Les tests historiques ont été rejoués avec leurs assertions d’origine. Les 14 tours P4, 30 tours P5 et 9 tours P6.2 ont réussi. Le guide historique de cinq étapes a aussi été contrôlé. [Mesures Linux](../p7/preuves-p71/mesures-linux.json) · [P7 courant](../p7/preuves-p71/p7-linux.jsonl) · [P4](../p7/preuves-p71/p4-linux.jsonl) · [P5](../p7/preuves-p71/p5-linux.jsonl) · [P6.2](../p7/preuves-p71/p62-linux.jsonl)

Le test de transparence du guide a d’abord révélé que « répond toujours 0 » n’entrait plus dans le vocabulaire d’observation. La forme verbale et le libellé du suivi ont été conservés. Un contrôle Linux a aussi observé un processus serveur encore en train de sortir après l’annonce d’arrêt. Le lanceur attend maintenant la sortie réelle quand le noyau fournit un descripteur de processus. Windows conserve son attente native. [Premier contrôle Windows](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45166758804)

Le lot indépendant P7 conservé sans modification compte quatre scénarios et douze tours. Conversation locale et hybride obtiennent **11 objectifs sur 12**, **10 intentions sur 12**, **6 essais sur 6**, **2 preuves ciblées sur 3** et **3 dialogues entièrement réussis sur 4**. Le contrôle ne relève aucune validation abusive ciblée, aucune sortie d’exécution inventée et aucune répétition détectée sur ce lot. La question abrégée « Pk sa boucle encore ? » n’est toujours pas comprise comme une explication, et « Je prévois 0 » n’est pas reconnu comme une prévision. La cible de qualification reste hors d’atteinte. [Conversation locale](../p7/preuves-p71/independant-B.json) · [Hybride](../p7/preuves-p71/independant-D.json)

Le ZIP final a été extrait et lancé sous Windows Server x64 avec le Python embarqué. Les deux profils ont passé 14 tours P7 et 14 tours P7.1, avec arrêt sans processus résiduel. Le démarrage a pris 0,453 s et le pic RSS cumulé de Python, du moteur et du navigateur a été de 3,84 Gio sur le runner. La comparaison Windows à 1672 × 941, la géométrie et les transitions du compagnon sont identiques aux mesures P7. Les trois thèmes et sept tailles ont été contrôlés. [Recette Windows](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45167967203) · [Mesures Windows](../p7/preuves-p71/mesures-windows.json) · [Contrôle visuel](../p7/preuves-p71/visuel-windows.json)

Le paquet contient le Python Windows x64 et conserve la procédure d’installation, la vérification des modèles et l’usage hors ligne après préparation. [ZIP corrigé](https://raw.githubusercontent.com/darksathili-jpg/lang-jepa-nsi/main/releases/0.7.1/LANG-JEPA-NSI-0.7.1-Windows-x64.zip) · [SHA-256](../releases/0.7.1/SHA256SUMS.txt) · [Installation](P6_1_INSTALLATION.md) · [Version précédente 0.7.0](https://github.com/darksathili-jpg/lang-jepa-nsi/releases/tag/v0.7.0)

**Validation humaine indépendante non effectuée.** La fiabilité en classe reste à établir. **Recette Windows à effectuer sur le poste cible** Windows 10/11 x64 de 16 Go.
