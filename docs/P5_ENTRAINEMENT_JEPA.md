# P5 · Entraînement du JEPA pédagogique

## Méthode

L’encodeur contextuel reçoit un vecteur de 512 cases de hachage signées et normalisées sur mots et bigrammes. Une projection entraînée suivie de `tanh` produit 24 coordonnées. Un prédicteur linéaire de 24 × 24 projette le contexte vers un espace cible. La cible est le texte de la carte d’intervention associé à un critère d’acquisition rédigé. Un encodeur de même forme représente ce texte. L’entrée contextuelle comprend les constats et l’état connus au moment du tour. Les annotations de correction et d’intervention sont employées pour construire la cible.

L’objectif est la moyenne des carrés des écarts latents avec arrêt du gradient côté cible. Deux configurations comparent un encodeur cible fixe à partir d’une projection aléatoire et une cible mise à jour par moyenne mobile de l’encodeur contextuel, coefficient 0,985. Une charnière de variance seuil 0,28 pondérée par 0,8, une pénalité de covariance hors diagonale pondérée par 0,06 et une décroissance des poids limitent la contraction. Adam utilise un pas de 0,006, des lots proches de 15 et 65 époques. L’objectif utilise les paires positives annotées. Les autres cartes sont des distracteurs à l’évaluation et il n’y a pas de terme contrastif sur des paires négatives pendant l’entraînement. Le classement des quatre cartes par cosinus constitue la tête de décision séparée. [Implémentation](../p5/jepa.py)

Les deux variantes ont les mêmes 25 152 coefficients en flottants 32 bits, dont 12 864 mis à jour par l’optimiseur. La variante fixe fournit une cible diversifiée sans coût d’EMA. La variante EMA apprend indirectement la représentation cible, au prix d’un suivi de contraction plus important. Les deux emploient la même dépendance et évitent le chargement d’un encodeur préentraîné. Les poids, la révision du corpus, les paramètres, les pertes, le regroupement par famille et les références sont journalisés. Le chargeur vérifie le manifeste, le SHA-256, les limites de taille, les formes, le type numérique et les valeurs finies. Il désactive les objets Python dans les poids.

Un encodeur multilingue figé comme `paraphrase-multilingual-MiniLM-L12-v2` constituerait une référence suivante. Sa fiche à la révision `e8f8c211` indique Apache-2.0. Ses représentations sont prévues pour le rapprochement de phrases. Leur utilité sur le raisonnement Python, le coût CPU et la mémoire restent à mesurer. L’essai initial privilégie deux variantes de même taille pour isoler l’effet de l’encodeur cible. [Fiche et révision MiniLM](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/tree/e8f8c211226b894fcb81acc59f3b34ba3efd5f42)

## Reproduire

```bash
OPENBLAS_NUM_THREADS=1 python -m p5.train --output results/p5 --seeds 17 43 97 --epochs 65
```

Python 3.12 et NumPy 2.3.5. Pour Windows, exécuter le module avec le Python de l’environnement P5 après préparation des roues. Créer un répertoire de sortie neuf. Le choix de configuration s’effectue par moyenne en validation sur les trois graines. La première graine, 17, alimente la recette conversationnelle indépendamment de ses résultats au test. [Installation hors ligne](P5_PERFORMANCES_WINDOWS.md) · [Rapport machine des essais](../p5/preuves/entrainement.json)

## Résultats observés

| Méthode | Graine | Validation /24 | Test /37 | Encodeur sans prédicteur /37 | Test mélangé /37 |
| --- | ---: | ---: | ---: | ---: | ---: |
| JEPA EMA | 17 | 5 | 15 | 14 | 8 |
| JEPA EMA | 43 | 5 | 14 | 6 | 8 |
| JEPA EMA | 97 | 8 | 15 | 18 | 7 |
| JEPA fixe | 17 | 5 | 16 | 17 | 8 |
| JEPA fixe | 43 | 5 | 14 | 12 | 12 |
| JEPA fixe | 97 | 9 | 15 | 14 | 8 |
| Aléatoire à graine fixée | 292 | — | 13 | — | — |
| Règles | — | — | 12 | — | — |
| Plus proche voisin TF-IDF | — | — | 14 | — | — |
| Classifieur ridge | — | — | 15 | — | — |

La configuration fixe est retenue par la moyenne en validation, 6,33/24 contre 6,00/24. Son meilleur essai de test atteint 16/37. Pour sa graine 17, l’écart à TF-IDF est de +5,4 points et l’intervalle de bootstrap apparié par famille à 95 % couvre environ −8,3 à +21,1 points. Les six intervalles englobent zéro. La tête sans prédicteur dépasse le JEPA pour deux graines. L’écart type moyen des prédictions vaut 0,25–0,29, leur rang effectif 5,2–8,4 sur 24 dimensions et leur cosinus moyen entre situations 0,27–0,37. Aucun effondrement total n’apparaît selon ces indicateurs, avec une dimension effective limitée.

Les performances moyennes en validation de la variante fixe à 5, 10 et 20 familles sont respectivement 25,0 %, 29,2 % et 26,4 %. Ces courbes ne permettent pas de fixer une taille suffisante. Les six entraînements et les courbes ont pris environ 0,9 s au total, avec un pic résident proche de 30 Mio en Linux CPU. Chaque fichier de poids fait environ 99 Kio. Une réinstallation de NumPy 2.3.5 avec la roue Linux verrouillée et sans index a reproduit les six empreintes. Les poids sont générés localement. [Mesures par graine](../p5/preuves/entrainement.json)
