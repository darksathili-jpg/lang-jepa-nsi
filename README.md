# LANG-JEPA NSI — V0.1

Prototype pédagogique local pour Première et Terminale NSI.

## Démarrage Windows
```powershell
.\scripts\dev.ps1
```
Ouvrir http://127.0.0.1:8765. Tests : `.\scripts\check.ps1`.

Cette V0.1 est une interface statique hors ligne : **aucun modèle LANG-JEPA n'est encore connecté**. L'exécution Python élève n'est pas disponible.

## Règles de production
- Dépôt unique, branche `main`, pas de branches temporaires.
- Tests ciblés avant commit, recette complète aux jalons.
- Poids et jeux de données exclus du dépôt.
- Ne jamais présenter une réponse simulée comme issue de LANG-JEPA.
- Ne jamais exécuter le code élève dans le processus serveur.

Amont scientifique : https://github.com/jerber/lang-jepa — l'inférence requiert un checkpoint d'encodeur ; décodeur facultatif. Audit de licence, checkpoints et CPU à réaliser.
