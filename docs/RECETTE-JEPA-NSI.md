# Recette de la reprise scientifique P3

La mission reprend `main` à `a5bc5fb` avec la base P2 `06a88b2` dans l’historique. Le laboratoire, le lanceur P2 et le mode conversationnel local restent disponibles. Le parcours guidé est devenu le mode par défaut depuis l’atelier. Il fonctionne avec Python 3.12 et le dépôt seul. [Installation](INSTALLATION-P3.md)

| Lot | Livraison | Preuve |
| --- | --- | --- |
| P3.1 | Audit de départ et périmètre CPU | `95ee473`, état Git, 20 tests de départ et vérification du ticket amont. |
| P3.2 | Corpus original synthétique et référentiel | `6085d38`, 16 documents, 48 paires et quatre exercices de Première et Terminale. |
| P3.3 | Entraînement et comparaison de LANG-JEPA | `0f47459`, deux graines, représentations, classements, reconstruction et décodage mesurés. |
| P3.4 | Parcours guidé et provenance des réponses | `7ecb7cd`, règles, constats du parseur, traces distinctes du laboratoire et conservation du mode SmolLM3. |
| P3.5 | Recette finale Q1 à Q4 | Similarité des énoncés, journaux Chromium, captures et nouvelle exécution du pilote. |

## Validation

- **Q1 · 27 tests Python.** Intégrité initiale des ressources P2, classement lexical déterministe, séparation du corpus, validation du catalogue, cas de référence, syntaxe, profondeur d’expression et étiquetage du parcours. Les cas de référence exécutent des fonctions de confiance.
- **Q2 · Service et API locales.** Le navigateur reçoit le catalogue et les indices de la même origine. Les deux entraînements et les chargements P2 ont fonctionné hors réseau. Les recettes du navigateur ont utilisé un espace réseau avec la seule interface de bouclage. Le parcours guidé n’a appelé ni le statut ni l’API du modèle. Le mode conversationnel a gardé les états absent, erreur et prêt, avec quatre tours réels hors réseau. Le pilote a renvoyé un code 130 à l’annulation et n’a pas créé de dossier de résultat incomplet. [Journal du guide](../evaluation/preuves/chromium-guide.txt) · [Journal SmolLM3](../evaluation/preuves/chromium-conversation.txt)
- **Q3 · Maximum et précondition.** Les cinq tours ont demandé un cas de test, orienté vers les entiers négatifs, demandé la trace de `m`, ciblé l’hypothèse d’initialisation puis discuté de `[]`. Les tests vérifient qu’une demande répétée de corrigé ou un commentaire ajouté au code ne déclenchent pas la consolidation. La sélection et l’analyse ont pris de 0,23 à 0,54 ms sur ces cinq tours Linux, hors transport et affichage.
- **Q4 · Chromium.** Navigation, exercice de Terminale sur écran mobile, thèmes clair, sombre et projecteur, absence de débordement horizontal et lecture du résultat scientifique vérifiés par interaction et assertions. Les captures utilisent les données fictives de la recette. [Clair](captures-jepa-nsi/atelier-light.png) · [Sombre](captures-jepa-nsi/atelier-dark.png) · [Projecteur](captures-jepa-nsi/atelier-projector.png) · [Mobile](captures-jepa-nsi/atelier-mobile.png) · [Laboratoire](captures-jepa-nsi/laboratoire-resultats.png)

## Résultat scientifique et limites

Les classes LANG-JEPA du dépôt amont ont réellement entraîné un encodeur, un prédicteur et un décodeur sur CPU. Les graines 17 et 97 donnent respectivement 4 et 2 indices de la bonne famille en tête sur 8 requêtes, contre 4 pour TF-IDF. Les concepts prédits se concentrent et le décodage ne reconstruit pas de phrase intelligible. Le guide utilise les indices rédigés. Le laboratoire montre la sortie brute du pilote et indique sa provenance. [Protocole, mesures CPU et traces](EXPERIENCE-JEPA-NSI.md)

Les droits de redistribution du code amont et des poids privés du pilote restent à clarifier. Le dépôt publie les adaptateurs NSI, le corpus synthétique et les résultats, avec les références et empreintes des ressources locales. Aucun accès à un Windows natif de 16 Go n’a été disponible. Les mesures Linux concernent deux fils CPU et un plafond de 8 Gio. L’échantillon de quatre familles et deux graines ne permet pas de valider l’usage pédagogique général de LANG-JEPA ni l’autonomie en classe. [Audit](AUDIT-JEPA-NSI.md)
