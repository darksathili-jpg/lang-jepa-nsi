# P6.2 · Évaluer la réponse à la question effectivement posée

**Correctif** `8329cd256499cf050c5100c5ed0789ee9d92f394`, sur `main`, à partir de `9adc5a4`. **Version portable 0.6.2**, build `8e64c83a47b4457a88708fe83f724bc0014a81d1`. [Correctif](https://github.com/darksathili-jpg/lang-jepa-nsi/commit/8329cd256499cf050c5100c5ed0789ee9d92f394) · [ZIP Windows](https://raw.githubusercontent.com/darksathili-jpg/lang-jepa-nsi/main/releases/0.6.2/LANG-JEPA-NSI-0.6.2-Windows-x64.zip) · [SHA-256](../releases/0.6.2/SHA256SUMS.txt)

## Dialogue rejoué avec les moteurs locaux

Dans `maximum(tab)`, le programme renvoie `0` pour `[-4, -2]`. L’élève indique que le résultat attendu est `-2`. Dans les deux versions, le tuteur pose ensuite la même question.

> **Tuteur** — Que donne la comparaison avec la valeur de départ quand la boucle rencontre -4 puis -2 ?
>
> **Élève** — toujours False

| Version | Réponse observée |
| --- | --- |
| Avant, Conversation locale | « La réponse ne donne pas d’élément exploitable pour l’objectif en cours. » Indice SmolLM3 « Compare chaque élément avec le maximum actuel et met à jour le maximum si nécessaire. » Question « Peux-tu annoter un tableau avec la condition et les mises à jour à chaque passage ? » |
| Après, les deux profils | « Oui, la condition valeur > m est fausse pour -4 et pour -2. » Puis « Quand la condition est fausse, que se passe-t-il pour l’instruction m = valeur, puis pour m ? » |

Après « La condition est fausse, donc m = valeur ne s’exécute pas et m reste à zéro », le tuteur valide le traçage et demande « Quelle hypothèse sur les éléments rend le zéro de départ inadapté ici ? ». Quand le tuteur demande une valeur de `m`, « toujours False » déclenche une clarification sur le type de la variable et ne valide aucun fait. [Avant dans Chromium](preuves-tour-contextuel/avant-linux.jsonl) · [Après dans Chromium](preuves-tour-contextuel/apres-linux.jsonl)

| Profil | Qui a choisi la comparaison affichée ? | Interprétation de « toujours False » | Fait enregistré et prochaine question | Objectif après l’explication causale |
| --- | --- | --- | --- | --- |
| Conversation locale | Règles pédagogiques sur tout l’échange. | Observation correcte pour les deux comparaisons. Le traçage est partiel. | Comparaison fausse pour `-4` et `-2`. La question des règles porte sur l’affectation et sur `m`. | Identifier l’hypothèse incorrecte, à partir de la question des règles. |
| Hybride expérimental | JEPA a reclassé la question de comparaison. L’orchestrateur l’a validée au même objectif et au même niveau. | Même observation reconnue pour les deux comparaisons. | Comparaison fausse pour `-4` et `-2`. JEPA a conservé le premier choix des règles pour la question sur l’affectation et sur `m`. | Identifier l’hypothèse incorrecte. Le premier choix des règles est resté en tête. |

Le serveur traitait auparavant `trace` comme une seule attente. Il associe maintenant la question effectivement servie à une cible, au tour précédent, à l’entrée et à l’empreinte de la structure Python. Il enregistre les observations partielles séparément du raisonnement complet. Un nouvel énoncé ouvre un nouveau parcours. Une modification de structure invalide la question et les faits partiels associés. Un commentaire conserve le contexte. Les acquis historiques conservent leur preuve. La progression repose sur des critères textuels et statiques pour l’exercice de référence. Les résultats rapportés par l’élève restent des observations déclarées. `[]` reste hors de la précondition de l’exercice.

JEPA peut reclasser les questions admissibles du profil hybride. Un classement qui conserve le premier choix est journalisé sans lui attribuer la question. La mention SmolLM3 indique un indice généré et effectivement affiché. Dans le tour « toujours False » des deux profils, l’indice généré a été écarté et la question des règles est restée visible. **Bénéfice JEPA non démontré.**

## Recette et distribution

- **Tests déterministes.** 61 tests, dont les réponses courtes croisées, la portée ambiguë, les négations, les contradictions, un cas positif, la demande de corrigé, les changements de code et d’énoncé, les réessais et les parcours longs. Le test principal échoue sur `9adc5a4` avec `hors_sujet` à la place de `partielle`.
- **Linux.** Chromium 156 a exécuté les deux profils avec SmolLM3-3B Q4_K_M, llama.cpp b12600 et JEPA P5 `fixe-24` dans un espace réseau limité à la boucle locale. La recette a rejoué 30 tours de régression hybride et 9 tours de dialogue contextuel. Aucun processus n’est resté actif après l’arrêt. Les comparaisons à 1672 × 941 ont retrouvé les mêmes mesures qu’en P6.1. Un deuxième passage navigateur a validé « La condition n’est vraie pour aucune des deux valeurs » dans les deux profils. [Trace longue Linux](preuves-tour-contextuel/hybride-30-linux.jsonl) · [Mesures Linux](preuves-tour-contextuel/mesures-linux.json) · [Trace de la variante](preuves-tour-contextuel/negation-linux.jsonl)
- **Windows Server x64.** Le ZIP construit et extrait démarre avec le Python embarqué. Les 61 tests, la matrice Chromium P6, les 30 tours hybrides et les 9 tours contextuels ont réussi avec les deux moteurs réels. Aucun processus n’est resté actif après l’arrêt. La géométrie et les mesures visuelles sont identiques à celles de P6.1 sous Windows Server. Le premier essai avait révélé une assertion qui attendait encore la version 0.6.1. Le test compare désormais l’affichage à la version verrouillée. [Trace Windows](preuves-tour-contextuel/apres-windows-server.jsonl) · [Trace longue Windows](preuves-tour-contextuel/hybride-30-windows-server.jsonl) · [Mesures Windows](preuves-tour-contextuel/mesures-windows-server.json) · [Recette GitHub Actions](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45081929970)
- **Poste cible.** Recette Windows à effectuer sur Windows 10/11 x64, CPU et 16 Go de RAM. Il reste à vérifier la coupure physique du réseau, la mise à l’échelle du bureau Windows et les performances sur ce matériel.
