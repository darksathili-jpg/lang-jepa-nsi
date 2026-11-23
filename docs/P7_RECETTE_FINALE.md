# P7 · Recette finale

**B — Tuteur expérimental pédagogiquement prometteur.** La progression est mieux suivie sur les quatre familles étudiées. Le lot de test tenu à part échoue encore à la qualification, et le poste cible et les évaluateurs indépendants manquent.

## Livraison

**Windows 0.7.0**, build `6c6fe3e4190b60113679f0a40c92711c088ce470`, sur `main`, dans la continuité de `5884996`. Extraire le ZIP, préparer les modèles avec `Installer-Modeles.cmd`, puis lancer `Demarrer.cmd`. `Verifier.cmd` fournit le diagnostic et `Arreter.cmd` libère les processus. Les modèles sont préparés séparément à partir des sources verrouillées. [ZIP Windows x64](https://raw.githubusercontent.com/darksathili-jpg/lang-jepa-nsi/main/releases/0.7.0/LANG-JEPA-NSI-0.7.0-Windows-x64.zip) · [SHA-256](../releases/0.7.0/SHA256SUMS.txt) · [Installation](P6_1_INSTALLATION.md) · [Retour à 0.6.2](P7_PERFORMANCES_LOCALES.md)

## Dialogue avant et après

La question « Pourquoi mon programme renvoie 0 quand la liste contient des nombres strictement négatifs ? » déclenchait une évaluation de réponse ambiguë. Puis `maximum([-3, -4, -1])` était écarté, et le tuteur demandait le résultat pour `[-4, -2]`.

P7 reconnaît la demande d’explication et donne une première piste. À la proposition `maximum([-3, -4, -1])`, il répond « Je retiens ton essai [-3, -4, -1]. » La prévision `0` et l’attendu mathématique `-1` restent séparés. « False » valide la comparaison, puis la justification sur l’affectation valide le traçage. Après modification du code, un nouvel essai est vérifié sur cette version. [Avant dans Chromium](../p7/preuves/avant-chromium.jsonl) · [Après sous Linux](../p7/preuves/apres-linux.jsonl)

## Résultats et décision

- SmolLM3 reste suffisant pour les essais bornés dont les preuves sont contrôlables, avec des lacunes sur des formulations libres. Le banc de mise au point donne 32/33 intentions et 12/12 essais. Le lot final donne 10/12 intentions, 6/6 essais et 3/4 dialogues avec tous les objectifs attendus. [Banc NSI](P7_BANC_QUALIFICATION_NSI.md)
- Qwen réduit le pic mémoire du moteur dans le comparatif Linux, avec le même score automatisé. Le banc ne montre aucun gain pédagogique démontré. Une spécialisation n’est pas engagée. [Comparatif](P7_BENCHMARK_LLM.md)
- **Bénéfice JEPA non démontré.** Le reclassement est réel dans son périmètre. Les résultats de progression ne départagent pas B et D, et le mélange change aussi l’ordre. [Ablations](P7_EVALUATION_JEPA.md)
- Les familles évaluées sont le parcours de listes, les boucles non bornées, les dictionnaires et la récursivité. L’atelier reste dépendant de formes statiques prises en charge et de critères de langage bornés. [Contrats](P7_CONTRATS_INTERPRETATION.md)
- **Validation humaine indépendante non effectuée.** Le dossier de lecture, la grille et le générateur à l’aveugle sont fournis. [Protocole](P7_VALIDATION_ENSEIGNANTS.md)

## Contrôles locaux

Les 67 tests et la syntaxe JavaScript sont vérifiés. La recette Linux hors Internet passe 53 tours avec les vrais moteurs et vérifie l’arrêt du lanceur. Le démarrage natif a réussi avec le Python embarqué et un ancien port occupé. La comparaison à 1672 × 941, la géométrie et les transitions du compagnon retrouvent les mesures P6.1 sous Chromium Windows Server. Les preuves distinguent Linux avec réseau externe coupé, Windows Server sous Chromium et le poste physique Windows 10/11 x64 de 16 Go. **Recette Windows à effectuer sur le poste cible.** [Démarrage et captures Windows Server](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45118620932) · [Mesures visuelles](../p7/preuves/visuel-windows.json) · [Performances et sécurité](P7_PERFORMANCES_LOCALES.md)
