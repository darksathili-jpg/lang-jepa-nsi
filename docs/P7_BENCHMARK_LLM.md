# P7 · Comparaison des modèles locaux

Les mêmes 36 tours synthétiques sont rejoués sur quatre configurations. A utilise le parcours Conversation locale de `5884996`, reproduit par l’adaptateur de compatibilité. B utilise SmolLM3 et P7. C conserve P7 avec Qwen. D ajoute JEPA fixe-24 graine 17 à B sur les états du maximum admissibles. Les scénarios sensibles sont exécutés une deuxième fois à graine d’inférence fixe, avec de nouvelles sessions. Les poids, déjà présents localement et vérifiés avant démarrage, sont les mêmes qu’au comparatif P3. [Définition des profils et mesures](../p7/benchmark.py) · [Corpus](../p7/qualification.json)

| Profil | Révision locale | Licence | Quantification | Taille des poids | SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| A, B, D · SmolLM3-3B | `4965cb60b150737b68a0408c36aeefb65078f894` | Apache-2.0 | Q4_K_M | 1 915 305 312 octets | `8334b850b7bd46238c16b0c550df2138f0889bf433809008cc17a8b05761863e` |
| C · Qwen2.5-1.5B-Instruct | `91cad51170dc346986eccefdc2dd33a9da36ead9` | Apache-2.0 | Q4_K_M | 1 117 320 736 octets | `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` |

llama.cpp b12600 CPU, MIT, deux fils. Le pic RSS du modèle est lu sur le processus llama.cpp. Les fenêtres de chargement et la latence sont mesurées localement. Les derniers essais Linux B/C/D ont partagé le quota CPU avec d’autres recettes. Ils permettent d’observer des durées dans ces conditions, avec un signal directionnel recoupé lors d’un premier passage. Le modèle de remplacement n’est pas installé dans le paquet. [Catalogue et empreintes](../p3/models.json) · [Comparaison antérieure incluant Granite](COMPARATIF-P3.md)

| Profil | Intentions exactes | Essais conservés | Objectifs observés | Dialogues complets selon la grille | Médiane des tours sollicitant le LLM |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | instrumentation absente | 0/12 | 5/36 | 0/6 | 13,56 s, 28 tours |
| B | 32/33 | 12/12 | 36/36 | 6/6 | 10,33 s, 3 tours |
| C | 32/33 | 12/12 | 36/36 | 6/6 | 7,37 s, 3 tours |
| D | 32/33 | 12/12 | 36/36 | 6/6 | 12,56 s, 3 tours |

En A, les essais structurés sont absents. La métrique d’objectif compte un échec lorsqu’un état équivalent est absent. Les traces montrent aussi sept répétitions exactes, une validation erronée de `0` après un test positif ignoré, et un tour sans intervention affichable. Ce comparatif évalue en partie la différence de structure entre P6.2 et P7. Il ne remplace pas l’évaluation des réponses à l’aveugle.

| Profil | Chargement du processus | Pic RSS llama.cpp |
| --- | ---: | ---: |
| A | 2,41 s | 3,59 Gio |
| B | 6,12 s | 3,46 Gio |
| C | 2,29 s | 1,85 Gio |
| D | 7,93 s | 3,44 Gio |

B et C ont les mêmes scores automatisés. Qwen a utilisé environ 1,85 Gio de RSS pour le moteur, contre 3,46 Gio pour SmolLM3, et a présenté une latence plus basse sur les trois appels mesurés. Le faible effectif et l’absence de jugement humain empêchent de conclure à un gain pédagogique. Le validateur a rejeté une citation contenant un préambule avant une demande d’explication. Il a aussi écarté les propositions de type « explication » pour deux observations factuelles. Les deux raisonnements ont ensuite progressé grâce aux règles.

La majeure partie de la progression est déterminée par les spécifications et le suivi des cas. SmolLM3 reste le moteur livré. Une spécialisation n’est pas lancée. Avant de l’envisager, il faudrait établir une lacune récurrente sur d’autres familles, obtenir des annotations indépendantes, figer des partitions par famille et mesurer le coût ainsi que la généralisation face au modèle initial.

[Traces A](../p7/preuves/A.jsonl) · [Traces B](../p7/preuves/B.jsonl) · [Traces C](../p7/preuves/C.jsonl) · [Traces D](../p7/preuves/D.jsonl)

```bash
python -m p7.benchmark --profiles ABCD --assets MODELES --weights JEPA_FIXE_24 --output RESULTATS --repetitions 2
python -m p7.benchmark --profiles B --corpus p7/test_final.json --assets MODELES --output TEST_FINAL --repetitions 2
```
