# P7 · Banc de qualification NSI

Le banc de comparaison compte six dialogues, 36 tours, 33 annotations d’intention et 12 propositions d’essais à conserver. Le lot tenu à part compte quatre dialogues et 12 tours distincts. Il a été ajouté après le gel du build et ses échecs sont conservés. Les deux lots sont synthétiques et aucune donnée d’élève n’est utilisée. Les dialogues d’un problème restent groupés. Il n’y a pas d’entraînement LLM P7. La séparation s’applique entre les mises au point et le lot final, et les graines JEPA préexistantes sont étudiées séparément. [Banc comparatif](../p7/qualification.json) · [Test final](../p7/test_final.json)

| Famille | Niveau | Validation technique couverte |
| --- | --- | --- |
| Parcours de liste et fonction de maximum | Première | Test libre, prédiction, observation, justification, code modifié, liste vide et entrée positive. |
| Boucle non bornée et valeur renvoyée | Première | Condition initiale vraie ou fausse, variable inchangée, nouveau cas sur le décrément reconnu. |
| Dictionnaires | Première | Première clé absente, liste vide, chaînes de casse différente et incrément reconnu. |
| Récursivité et cas de base | Terminale | Cas présent inaccessible par croissance ou par parité, vérification du cas de base reconnu. |

| Mesure | SmolLM3 P7 B sur le banc comparatif | SmolLM3 P7 B sur le lot final |
| --- | ---: | ---: |
| Ensemble des intentions exact | 32/33, IC 95 % 84,7–99,5 % | 10/12, IC 95 % 55,2–95,3 % |
| Essai approprié conservé | 12/12, IC 95 % 75,8–100 % | 6/6, IC 95 % 61,0–100 % |
| Bon objectif selon l’annotation | 36/36 | 10/12 |
| Dialogues avec tous les objectifs annotés atteints | 6/6 | 3/4 |
| Faits statiques ciblés | 3/3 | 3/3 et une abstention attendue |
| Validation abusive ciblée, fuite détectée, sortie d’exécution prétendue | 0 événements détectés par les tests | 0 événements détectés par les tests |

Les intervalles de Wilson décrivent l’incertitude par tour. Les tours d’un même dialogue sont dépendants, et ces intervalles ne constituent pas une garantie par famille. Les rubriques de pertinence, lisibilité, répétitions sémantiques et divulgations implicites exigent un regard humain. Le script décompte les répétitions exactes, les réponses absentes et les motifs de divulgation vérifiables. Les cas de preuve abusive n’apparaissent que dans certains tours annotés.

Deux échecs du jeu final sont observés dans le dialogue du compteur. « Pk sa boucle encore ? » ne déclenche pas la lecture structurée, et « Je prévois 0 » ne renseigne pas la prédiction avec les mots utilisés. La bonne valeur attendue est alors enregistrée sans confirmer la vérification. Le test final reste sous les objectifs de 95 % d’intentions et 90 % de déroulements attendus. Les estimations n’établissent pas la fiabilité en classe.

Pour étendre la qualification, définir des spécifications distinctes pour piles, files et parcours d’arbres ou de graphes. Réserver les raisonnements d’algorithmes, fonctions hors maximum et variantes de boucle bornée à des problèmes entiers, avec préconditions, cas limites et oracles propres. Garder les cas de généralisation séparés du développement. [Traces et intervalles détaillés](../p7/preuves/) · [Protocole enseignant](P7_VALIDATION_ENSEIGNANTS.md)
