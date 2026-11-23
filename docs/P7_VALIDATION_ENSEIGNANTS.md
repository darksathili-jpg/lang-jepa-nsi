# P7 · Validation par des enseignants

**Validation humaine indépendante non effectuée.** Aucun enseignant n’a été recruté ou représenté par un modèle pour cette recette.

Le lot de lecture est formé des six scénarios synthétiques et de leurs sorties `A`, `B`, `C` et `D`. Un coordinateur sépare la clé de correspondance, attribue des identifiants opaques et retire profil, modèle, temps, provenance, scores latents et résultats automatiques avant remise aux évaluateurs. Les textes de l’élève et les interventions réellement affichées doivent être conservés dans l’ordre. Deux enseignants de NSI au moins lisent à l’aveugle, chacun dans un ordre de présentation différent, sans concertation avant le dépôt des grilles.

| Dimension | Critère pour la grille |
| --- | --- |
| Exactitude scientifique | Séparer faits exacts, incertitudes légitimes et erreurs critiques. |
| Prise en compte de l’élève | Le tuteur reprend l’entrée choisie et les éléments déjà établis. |
| Indice et progression | La demande suivante vise une action nouvelle et accessible. |
| Programme officiel | La notion, le vocabulaire et l’exigence correspondent au niveau NSI. |
| Lisibilité | La réponse est compréhensible et exploitable sans assistance. |
| Divulgation | L’indice respecte le degré d’aide et laisse une activité à l’élève. |
| Intérêt en classe | Le dialogue pourrait aider l’élève pendant une séance supervisée. |

Noter chaque ligne de 0 à 2, où 0 signale un problème, 1 une réponse acceptable avec réserve et 2 une réponse satisfaisante. Marquer à part toute erreur critique, fausse preuve, sortie fictive, répétition bloquante ou divulgation. Ajouter un extrait et une justification pour chaque note 0. Relever ensuite l’accord brut par dimension et les désaccords critiques, puis établir un arbitrage documenté et distinguer les notes initiales des notes arbitrées. Dévoiler la clé après ce dépôt. La qualification exige notamment une progression acceptable dans 90 % des dialogues, sur un échantillon de familles étendu. [Scénarios synthétiques](../p7/qualification.json) · [Traces pour préparer la lecture](../p7/preuves/)

```bash
python -m p7.blind --traces p7/preuves --output LECTURE --seed GRAINE_DU_COORDINATEUR
```

Remettre un seul fichier `enseignant-*.json` à chaque évaluateur. Conserver `cle-coordinateur.json` jusqu’à la fin de l’arbitrage.
