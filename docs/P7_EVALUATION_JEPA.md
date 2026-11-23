# P7 · Évaluation de JEPA

**Bénéfice JEPA non démontré.** Le profil **Hybride expérimental** garde une sélection explicite. Dans P7, le reclassement est borné aux interventions du maximum et aux formes de départ reconnues. Les autres exercices passent par l’orchestrateur sans JEPA. Les preuves et le niveau d’aide sont établis avant le classement.

Chaque décision P7 journalise dans la trace synthétique la situation encodée, l’identité des poids, les options admissibles, les deux ordres, les scores, l’intervention retenue, le contrôle d’admissibilité et la réponse affichée. En conversation, le panneau enseignant présente les deux ordres lorsqu’ils existent. Une attribution à JEPA exige que son premier choix diffère de celui des règles. [Trace Chromium](../p7/preuves/apres-linux.jsonl) · [Contrats de provenance](P7_CONTRATS_INTERPRETATION.md)

L’ablation fige les situations effectivement encodées et les candidats de D. Elle recalcule le classement sur trois reconstructions vérifiées `fixe-24`, graines 17, 43 et 97, avec quatre conditions. B garde l’ordre des règles. La neutralisation conserve aussi cet ordre. Dans la permutation, une autre situation de la série fournit le signal correspondant à chaque tour, selon une bijection sans point fixe. L’unité d’analyse reste le tour admissible. Les trois graines réutilisent les mêmes entrées et ne triplent pas l’effectif d’exercices.

| Graine | Règles | JEPA | Neutralisé | Mélangé |
| --- | ---: | ---: | ---: | ---: |
| 17 | 0/12 | 7/12 | 0/12 | 8/12 |
| 43 | 0/12 | 7/12 | 0/12 | 6/12 |
| 97 | 0/12 | 6/12 | 0/12 | 7/12 |

Ces fractions mesurent les changements de tête du classement. Les graines produisent des répartitions d’approches différentes. Le mélange déplace lui aussi les questions et la diversité brute. La progression automatisée et les répétitions ne départagent pas B et D sur le banc initial. La pertinence et la diversité utile doivent être jugées à l’aveugle. [Ablations et intervalles](../p7/preuves/jepa.json) · [Trace des classements](../p7/preuves/jepa.jsonl) · [Évaluation P5](P5_EVALUATION_ABC.md)

```bash
python -m p7.jepa_eval --trace RESULTATS/D.jsonl --models RACINE_DES_RECONSTRUCTIONS_FIXE_24 --output ABLATION.jsonl
```
