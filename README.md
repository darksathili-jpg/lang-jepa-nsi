# LANG-JEPA NSI

Laboratoire pédagogique hors ligne pour Première et Terminale NSI. Il comprend une présentation interactive, un quiz et un espace pour saisir un énoncé, du code Python et une question.

## Démarrage Windows

Prérequis du laboratoire : Python 3 et son lanceur Windows `py`. Depuis la racine du dépôt, dans PowerShell :

```powershell
.\scripts\dev.ps1
```

Ouvrir [le laboratoire](http://127.0.0.1:8765). Exécuter `.\scripts\check.ps1` pour les tests. Le serveur écoute uniquement sur l’interface locale. Le formulaire garde la saisie dans l’onglet et traite le code Python comme du texte.

## Mission P2

La révision amont est figée. Le lanceur d’expérimentation CPU fonctionne séparément du laboratoire et exige des poids d’entraînement compatibles. Au 21 novembre 2026, la recherche publique n’a identifié aucun checkpoint d’encodeur ni de décodeur compatible. Le tuteur reste indisponible.

- [Installation, expérimentation et restauration hors ligne](docs/INSTALLATION-P2.md)
- [Audit des checkpoints, estimation CPU et bilan de validation](docs/RAPPORT-P2.md)
- [Architecture et protocole d’évaluation pédagogique](docs/ARCHITECTURE-P2.md)
- [Règles permanentes de développement](AGENTS.md)
