# Pilote LANG-JEPA NSI sur CPU

Deux entraînements réels ont utilisé les classes `TextTransformer`, `TextPredictor`, `EMAEncoder`, `ConceptExtractor` et `ConceptDecoder` de la révision amont P2. Le profil démarre sans poids RoBERTa préentraînés. Il emploie le tokenizer RoBERTa d’origine, une couche encodeur de largeur 32, un prédicteur de même largeur et une couche décodeur. Cette petite configuration permet un essai local court. Elle ne mesure pas la configuration amont à 124 M de paramètres. [Audit et droits](AUDIT-JEPA-NSI.md)

## Reproduire

Installer la pile CPU P2 dans un environnement Python 3.12 et préparer les six fichiers de l’archive et du tokenizer selon le verrou P2. Les deux checkpoints ne sont pas nécessaires au départ. Conserver les résultats dans un dossier ignoré par Git. Le répertoire de résultat doit être neuf. La touche Ctrl+C annule le pilote et laisse le résultat partiel hors du chemin de sortie. [Préparation des ressources](INSTALLATION-P2.md) · [Verrou P2](../p2/upstream.json)

```powershell
New-Item -ItemType Directory -Force results | Out-Null
.\.venv\Scripts\python.exe -m evaluation.pilot --assets models/p2 --output results/jepa-17 --seed 17 --threads 2
.\.venv\Scripts\python.exe -m evaluation.pilot --assets models/p2 --output results/jepa-97 --seed 97 --threads 2
.\.venv\Scripts\python.exe scripts/lang_jepa_cpu.py --bundle results/jepa-17 --input p2/probe-en.txt --output results/reconstruction.json --threads 2 --decode
```

Le corpus contient 16 documents synthétiques répartis par document en 8 d’entraînement et 8 de test, soit 24 paires par ensemble. Chaque document comprend un énoncé, une explication de notion, une description d’erreur et un indice ou une question de professeur. Les segments précédents forment un contexte de fenêtre maximale deux. L’encodeur et le prédicteur effectuent 48 mises à jour de la perte Smooth L1 sur des vecteurs normalisés. La cible est une copie à moyenne mobile. Le décodeur effectue séparément 72 mises à jour de l’entropie croisée des tokens de 32 segments d’entraînement. Il reconstruit le texte conditionné sur son concept extrait avec l’encodeur gelé. Aucun de ces objectifs ne récompense directement une bonne réponse à un élève. [Corpus](../evaluation/corpus-nsi.json)

La référence TF-IDF utilise les mots et leurs fréquences dans les seuls segments d’entraînement. La recherche d’indice classe huit indices d’entraînement, avec la famille d’erreur comme vérité de référence. La prédiction classe les huit cibles possibles du même rôle documentaire, avec le segment suivant exact comme vérité de référence. Elle est aussi comparée à la représentation moyenne du contexte par l’encodeur EMA sans utiliser le prédicteur. Les rangs, scores, vecteurs, pertes, textes, paramètres et empreintes sont enregistrés. L’inférence est sans gradient et par lot de 1, sauf pour le contrôle de remplissage. [Graine 17](../evaluation/preuves/seed17.json) · [Graine 97](../evaluation/preuves/seed97.json)

## Représentations

| Mesure hors entraînement | Graine 17 | Graine 97 | Référence |
| --- | ---: | ---: | ---: |
| Écart de cosinus entre énoncés apparentés et d’autres familles | −0,00069 | −0,00045 | +0,08635 en TF-IDF |
| Écart de cosinus entre descriptions d’une même erreur et d’erreurs différentes | −0,00039 | +0,00084 | +0,02972 en TF-IDF |
| Indice de la bonne famille en tête | 4/8 | 2/8 | 4/8 en TF-IDF |
| Rang réciproque moyen des indices | 0,705 | 0,531 | 0,698 en TF-IDF |
| Segment suivant exact en tête | 3/24 | 4/24 | 3/24 en TF-IDF, 4/24 et 5/24 par contexte EMA |
| Rang réciproque moyen du segment suivant | 0,344 | 0,354 | 0,359 en TF-IDF |
| Cosinus avec la vraie cible, avant puis après entraînement | 0,103 → 0,986 | 0,341 → 0,991 | — |
| Cosinus moyen entre prédictions différentes, après entraînement | 0,99865 | 0,99819 | — |

L’écart entre familles change de signe selon la graine et reste faible. Les prédictions deviennent très proches entre elles. Leur écart type moyen par dimension descend de 0,0305 à 0,0062 pour la graine 17 et de 0,0236 à 0,0072 pour la graine 97. Le rang effectif spectral centré reste respectivement de 7,49 et 7,83. Cela indique une contraction marquée, sans démontrer un effondrement total. Le cosinus élevé avec la cible ne suffit donc pas à établir que le prédicteur distingue les prochaines phrases.

À graine fixée, deux inférences identiques donnent les mêmes vecteurs. Le changement de remplissage induit au plus 6 × 10⁻⁸ d’écart absolu. La modification de ponctuation conserve un cosinus moyen supérieur à 0,9998 après entraînement. Cette stabilité locale coexiste avec une faible discrimination. Un second entraînement de la graine 17 a reproduit les courbes, vecteurs, rangs, sorties et empreintes des deux checkpoints sur cet environnement.

## Décodage et usage pédagogique

| Condition | Observation hors entraînement |
| --- | --- |
| Reconstruction d’un énoncé | ` de de.` avec la graine 17, `.` avec la graine 97. |
| Reconstruction d’une explication NSI | Mêmes fragments. Aucune reconstruction exacte. |
| Prédiction du segment suivant | 3/24 et 4/24 en tête parmi huit candidats. |
| Texte produit à partir du concept prédit | Mêmes fragments pour les huit indices testés. Inverser les concepts de conditionnement modifie l’entropie moyenne de moins de 0,001 nat par token. |

Le chargeur P2 a vérifié les empreintes et chargé strictement les poids entraînés du pilote. Une reconstruction et une prédiction avec décodage ont abouti. La sonde NSI P2 longue, de 126 tokens, est correctement refusée avec la limite de 112 du pilote. La sonde française courte passe à 55 tokens. [Reconstruction P2](../evaluation/preuves/p2-reconstruction.json) · [Prédiction P2](../evaluation/preuves/p2-prediction.json)

Pour contribuer au choix des indices, un profil devra distinguer les familles et retrouver des indices au moins aussi bien que la référence lexicale sur les deux graines. Le pilote ne remplit pas ces conditions. Le parcours en service utilise des règles et des indices rédigés. Les sorties JEPA sont consultables au laboratoire avec leur provenance d’expérience. Un corpus plus large, des familles supplémentaires et des formulations réellement indépendantes seront nécessaires avant de généraliser.

## Ressources observées

Sur Linux CPU, deux fils et un espace réseau limité à la boucle locale, la préparation et l’instanciation ont pris 2,86 à 3,39 s. L’encodeur a passé 0,76 à 1,06 s à l’entraînement et le décodeur 3,77 à 3,86 s. Une extraction à chaud a pris 1,33 à 1,49 ms. Le pic résident du processus a atteint environ 521 Mio. Ces mesures concernent uniquement ce profil miniature. Aucune quantification n’a été appliquée. Le poste Windows de 16 Go reste à mesurer.
