# P5 · Recette finale

**Prototype hybride fonctionnel — bénéfice JEPA non démontré.**

| État | Résultat |
| --- | --- |
| Réalisé | Corpus synthétique séparé par problème, deux variantes d’apprentissage latent sur trois graines, chargeur vérifié, trois profils de comparaison et deux ablations. |
| Réalisé | Le profil C charge le JEPA fixe-24 et SmolLM3-3B Q4_K_M. Le prédicteur change le choix de questions admissibles sur le maximum. Le serveur conserve les preuves, empêche le retour au traçage après l’explication et attend deux tests déclarés avant consolidation. |
| Partiellement réalisé | Le parcours structuré P5 est évalué en conversation sur le maximum. Les autres exercices gardent leurs profils antérieurs. Le corpus de recherche couvre des notions plus larges que le parcours hybride intégré. |
| Non validé | Le profil C ne dépasse pas B sur la grille du dialogue. Les intervalles obtenus sur les familles inédites ne montrent pas de gain robuste. Le classement C reste expérimental, le parcours stable reste celui du lancement habituel. |
| Bloqué | La recette sur un Windows x64 de 16 Go, les mesures totales en simultané et la procédure de fermeture Windows restent à exécuter sur un poste disponible. |
| Non effectué | Évaluation à l’aveugle par des enseignants indépendants. Une grille et un protocole sont fournis. |

[Architecture](P5_ARCHITECTURE_HYBRIDE.md) · [Audit](P5_AUDIT_INITIAL.md) · [Corpus et provenance](P5_CORPUS_ET_PROVENANCE.md) · [Entraînement](P5_ENTRAINEMENT_JEPA.md) · [Comparaison et grille](P5_EVALUATION_ABC.md) · [Installation Windows](P5_PERFORMANCES_WINDOWS.md)

## Contrôles pédagogiques

Le rejeu historique avec SmolLM3 avant P4 retrouve la même question de trace aux tours 2, 4 et 6. Les profils B et C reconnaissent au quatrième tour l’explication selon laquelle zéro dépasse les deux entiers négatifs. Après une proposition de stratégie, la confirmation de la seconde entrée est nécessaire pour aborder `[]`. Les tests déterministes de 10, 20 et 30 tours conservent les preuves et passent sans question répétée au sens de la distance utilisée. [Rejeu historique](../p5/preuves/rejeu-46da3f3.jsonl) · [Banc automatisé](../p5/compare.py)

La décision est observable dans le dialogue de 10 tours. Au deuxième tour, B demande le suivi des trois valeurs successives de `m`. C choisit de comparer le seuil de départ avec les deux entrées et affiche un indice de SmolLM3 lié à la question. Le changement d’approche est enregistré dans l’état serveur. Le profil reste consultable sans score affiché comme probabilité.

## Recette observée sur Linux

Les **44 tests Python** et la vérification de syntaxe JavaScript réussissent. Les recettes Chromium du laboratoire et du parcours guidé passent sur ordinateur et mobile, avec les deux niveaux NSI. Le profil P4 a également passé son rejeu réel de 14 tours avec SmolLM3 hors réseau. NumPy 2.3.5 a été installé depuis la roue vérifiée sans index. La roue Windows a été préparée et vérifiée séparément. [Rejeu de non-régression P4](../p5/preuves/regression-p4.jsonl)

La recette réelle du profil C avec **Chromium 156, SmolLM3 et JEPA** a parcouru 30 tours sans requête externe. Elle compte 10 questions distinctes, quatre reclassements et quatre indices SmolLM3 affichés. La preuve du tour 4 reste en mémoire au dernier tour. Les tests bloquent les soumissions hors origine et hors limite de taille. Les trois thèmes ont été contrôlés sans débordement horizontal. Le moteur llama.cpp, identifié comme processus fils, a disparu après l’arrêt du serveur. [Trace des 30 tours](../p5/preuves/chromium-30-tours.jsonl) · [Clair](captures-p5/atelier-light.png) · [Sombre](captures-p5/atelier-dark.png) · [Projecteur](captures-p5/atelier-projector.png)

## Reproduire les contrôles

```bash
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
node --check app/tutor.js
python tests/guided_browser.py
python tests/browser_smoke.py
OPENBLAS_NUM_THREADS=1 python tests/hybrid_browser.py \
  --assets models/tutor --weights results/p5/fixe-24-17 \
  --output results/p5-chromium.jsonl --dialogue maximum-30 --captures results/captures-p5
```

Le banc navigateur choisit le Chromium installé en passant `--chromium`, ou le Chromium de Playwright lorsqu’il est préparé. Sous Linux, la recette lance les commandes navigateur dans un espace réseau ne contenant que `lo`. Créer un répertoire de sortie et des noms de traces neufs. [Versions et préparation](P5_PERFORMANCES_WINDOWS.md)

## Suite expérimentale

Enrichir les familles d’exercices et annoter des interventions alternatives avec deux enseignants, puis réserver plusieurs familles inédites au test final. Répéter l’ablation inter-situations et la comparaison C/B avec les paramètres et la grille gelés. Mesurer l’installation, les 30 tours et l’arrêt propre sur un Windows x64 de 16 Go avant de conclure sur le déploiement.
