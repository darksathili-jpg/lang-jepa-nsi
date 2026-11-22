# LANG-JEPA NSI

Atelier local pour travailler le Python en Première et Terminale NSI et laboratoire pour mesurer ce que LANG-JEPA peut apporter au tutorat. Le modèle conversationnel issu de la livraison précédente reste accessible comme mode distinct.

## Parcours guidé hors ligne

Depuis la racine sous Windows avec Python 3.12, exécuter `.\scripts\tutor.ps1` et ouvrir [l’atelier Python](http://127.0.0.1:8765/atelier). Le mode **Parcours guidé** est disponible sans poids de modèle. Il distingue l’analyse statique Python et les indices rédigés. Les exercices couvrent le maximum, le décompte, les dictionnaires et la récursivité.

## Expérimentation LANG-JEPA

Le mandat scientifique reprend les ressources figées en P2. Les expériences mesurent les représentations, la prédiction latente et le décodage séparément. Les deux entraînements courts n’ont pas établi un avantage fiable pour sélectionner les indices. [Audit et critères](docs/AUDIT-JEPA-NSI.md) · [Protocoles et mesures](docs/EXPERIENCE-JEPA-NSI.md) · [Recette finale](docs/RECETTE-JEPA-NSI.md)

## Mode conversationnel · livraison précédente

L’atelier propose des questions et indices progressifs avec un modèle conversationnel qui s’exécute sur le processeur. Le code saisi relève d’une analyse statique locale. Le modèle sélectionné est SmolLM3-3B Q4_K_M. Le profil de déploiement est Windows x64, 16 Go de RAM.

Pour utiliser ce mode, préparer les poids une fois avec `py -3.12 -m tutor.install --model smol`, puis choisir **Conversation locale** dans l’atelier.

- [Installation et fonctionnement hors ligne](docs/INSTALLATION-P3.md)
- [Comparatif des modèles](docs/COMPARATIF-P3.md)
- [Évaluation et résultats P3](docs/RAPPORT-P3.md)
- [Architecture du professeur virtuel](docs/ARCHITECTURE-P3.md)
- [Règles permanentes de développement](AGENTS.md)

## Laboratoire LANG-JEPA · P2

Depuis PowerShell, `.\scripts\dev.ps1 -LaboratoireSeul` sert uniquement le laboratoire sur [127.0.0.1:8765](http://127.0.0.1:8765). Les tests se lancent avec `.\scripts\check.ps1`.

La révision LANG-JEPA d’origine est figée. Le lanceur P2 exige des checkpoints compatibles. Il a été vérifié avec les poids privés produits par le pilote. La recherche P2 n’avait trouvé aucun checkpoint public compatible.

- [Rapport de recherche et compatibilité CPU](docs/RAPPORT-P2.md)
- [Installation et restauration P2](docs/INSTALLATION-P2.md)
- [Architecture du laboratoire P2](docs/ARCHITECTURE-P2.md)
