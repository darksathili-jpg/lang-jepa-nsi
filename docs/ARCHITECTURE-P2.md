# Architecture P2

Depuis P3, l’expérimentation LANG-JEPA reste indépendante et le professeur virtuel utilise un moteur conversationnel local. Ce document conserve l’architecture et les résultats de la mission P2. [Architecture du tuteur P3](ARCHITECTURE-P3.md)

Le laboratoire conserve son point d’entrée `app/index.html`, servi sur l’interface de bouclage. Les champs énoncé, code et question restent dans le navigateur. La politique de sécurité de contenu interdit toute connexion du formulaire. Le bouton de disponibilité donne l’état explicite du tuteur. Le navigateur ne lance aucun code Python fourni par l’élève.

Le lanceur `scripts/lang_jepa_cpu.py` est le point d’entrée de l’expérimentation. Il prend un texte UTF-8 local, le chemin d’un bundle et un nouveau chemin de résultat. Il vérifie d’abord la révision, les empreintes, la provenance déclarée et l’association encodeur-décodeur. Il extrait l’archive amont vérifiée dans un répertoire temporaire. La source de l’auteur reste hors du dépôt NSI. [Révision d’origine](https://github.com/jerber/lang-jepa/tree/f6e29a53760e631f12e16922c7300588c61c61d8)

Le lanceur charge la configuration et le tokenizer depuis des fichiers locaux avec le Hub en mode hors ligne. Il instancie `TextTransformer` avec la forme du modèle du run et charge strictement son état JEPA entier. Le profil P2 prend en charge le tokenizer RoBERTa-base d’origine. Les poids RoBERTa d’initialisation sont superflus après le chargement de l’état entraîné. Les chargements ciblent le CPU et utilisent `weights_only=True`. La seule classe de sérialisation ajoutée à la liste d’autorisation pour le décodeur est `DecoderConfig` de l’amont. L’absence ou l’incompatibilité d’un fichier demandé interrompt l’essai avant l’écriture d’un résultat.

| Mode | Calcul réalisé |
| --- | --- |
| `reconstruction` | Encodeur puis `ConceptExtractor` d’origine, avec moyenne masquée et normalisation L2. L’option `--decode` demande la reconstruction du texte conditionnée par le concept. |
| `prediction` | Encodeur puis `TextPredictor` d’origine, avec normalisation L2 comme à l’entraînement. L’option `--decode` teste la génération à partir du concept prédit. |

La reconstruction suit la démo amont. La prédiction suivie d’un décodage teste la composition des deux étapes, alors que le décodeur a été entraîné sur des concepts extraits du texte cible. Les deux expériences sauvegardent le vecteur complet, le texte décodé lorsqu’il existe, le texte d’entrée, les paramètres, les empreintes et les mesures. [Démo amont](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/scripts/infer.py) · [Entraînement de l’encodeur](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/src/encoder/train.py) · [Entraînement du décodeur](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/main_decoder.py)

## Évaluation du futur tuteur

Commencer par la reconstruction d’un court texte de référence en anglais. Tester ensuite les entrées NSI en français et la prédiction du concept suivant. Les deux fichiers `p2/probe-*.txt` fixent les premières entrées. Une reconstruction intelligible démontre une capacité de reconstruction. La qualité de la prédiction et la capacité de tutorat demandent des évaluations séparées.

Pour le tutorat, constituer un jeu d’exercices inédit pour le modèle, hors données d’entraînement, avec au moins deux exemples par famille :

| Famille | Comportement attendu |
| --- | --- |
| Parcours de liste | Repérer le cas limite pertinent, par exemple les valeurs toutes négatives, et demander à l’élève de tracer l’état d’une variable. |
| Indices et boucles | Faire identifier l’itération et l’indice qui déclenchent l’erreur. |
| Récursivité | Faire examiner le cas de base et la progression de l’argument. |
| Tests et spécification | Proposer une petite entrée discriminante avec une question sur la sortie attendue. |
| Saisie ambiguë | Demander une précision lorsque le contexte laisse plusieurs diagnostics plausibles. |
| Demande de corrigé | Poursuivre avec un indice ciblé, sans délivrer le programme ni le corrigé complet. |

Évaluer au moins trois tours par cas avec un script de réponses de l’élève préparé à l’avance. Un enseignant relève par tour la justesse du diagnostic, la pertinence de la question, la progression des indices et toute divulgation. Conserver les sorties brutes, publier les scores par critère et examiner les échecs. Fixer les seuils d’acceptation avec la personne responsable de la pédagogie avant la campagne. Une fuite de solution dans les cas de demande de corrigé doit être traitée avant la mise en service.

Après validation seulement, prévoir un service local à contrat borné pour consommer le formulaire et conserver l’état des tours en mémoire. Le futur service soumettra des données textuelles à l’adaptateur, contrôlera la politique d’indices et ne fera aucune exécution de code de l’élève. L’architecture prédictive et reconstructive amont ne fournit pas en elle-même une politique de dialogue.
