# Rapport P2 · 21 novembre 2026

## Périmètre et sources

Le dépôt NSI a été repris à `a26516843484a70ded12653d5cc767ee3339f659`. La télécommande Git exposait une seule branche, `main`. Le dépôt contenait une page statique, un quiz, le thème, un statut de disponibilité, deux scripts PowerShell et trois tests. Les trois tests initiaux passaient. [Révision de départ NSI](https://github.com/darksathili-jpg/lang-jepa-nsi/tree/a26516843484a70ded12653d5cc767ee3339f659)

L’amont a été figé à `f6e29a53760e631f12e16922c7300588c61c61d8`. Son architecture comprend un encodeur en ligne, un prédicteur de concept suivant, un encodeur cible EMA pour l’entraînement et un décodeur de reconstruction. Le script de démonstration fait du texte vers concept avec décodeur facultatif. L’adaptateur réutilise les classes d’origine. [Révision LANG-JEPA](https://github.com/jerber/lang-jepa/tree/f6e29a53760e631f12e16922c7300588c61c61d8) · [Démo amont](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/scripts/infer.py)

### Licence

L’arbre amont ne contient aucun fichier de licence. Les métadonnées GitHub déclarent `license: null` et l’API dédiée renvoie 404. Le ticket de demande de licence est ouvert sans réponse publique. La permission de redistribution du code et de futurs poids reste à établir. Le dépôt NSI contient le lanceur et les références d’intégrité, et garde le code d’origine et les poids externes. Clarifier directement avec l’auteur les droits de redistribution avant un paquet distribué aux élèves. Les ressources RoBERTa ont leur propre fiche de licence. [Ticket amont](https://github.com/jerber/lang-jepa/issues/4) · [Licences sur GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository) · [RoBERTa-base](https://huggingface.co/FacebookAI/roberta-base)

### Checkpoints

| Vérification publique | Résultat |
| --- | --- |
| Arbres récursifs des cinq branches de l’amont | Aucun fichier de poids reconnu ni blob de plus de 1 Mio. |
| Arbres des branches par défaut des 21 forks renvoyés par l’API | Aucun fichier de poids reconnu ni blob de plus de 1 Mio. |
| Releases, tags et artefacts GitHub Actions amont | Aucun élément retourné. |
| README, issues et demandes de fusion amont | Le README décrit un entraînement local. Les chemins `logs/lang_jepa/checkpoint-epoch5.pth` et `outputs/decoder/best_decoder.pt` sont des exemples de fichiers produits par cet entraînement. Aucun lien vers une paire compatible repéré. |
| API Hugging Face | Aucun résultat pour `lang-jepa` dans les modèles, jeux et Spaces. Aucun candidat parmi les modèles publics du compte `jerber`. |
| Recherche web par dépôt, nom de modèle et noms de checkpoint | Aucun téléchargement compatible vérifiable identifié. |

Constat limité aux sources publiques consultées. La recherche laisse ouverte l’existence d’un run privé ou d’une publication hors de ces canaux. [Branches](https://api.github.com/repos/jerber/lang-jepa/branches) · [Forks](https://api.github.com/repos/jerber/lang-jepa/forks?per_page=100) · [Releases](https://api.github.com/repos/jerber/lang-jepa/releases) · [Tags](https://api.github.com/repos/jerber/lang-jepa/tags) · [Artefacts](https://api.github.com/repos/jerber/lang-jepa/actions/artifacts) · [Discussions de développement](https://github.com/jerber/lang-jepa/issues?q=is%3Aissue) · [Modèles Hugging Face](https://huggingface.co/api/models?search=lang-jepa)

RoBERTa-base apporte l’architecture, le tokenizer et l’initialisation du run par défaut. Son état public n’inclut ni entraînement LANG-JEPA ni prédicteur ni décodeur. Les cinq fichiers nécessaires à la tokenisation et à la configuration ont été vérifiés à la révision `e2da8e2f811d1448a5b465c236feacd80ffbac7b`. [Configuration amont](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/src/encoder/configs/base_lang_config.yaml) · [Fichiers RoBERTa-base](https://huggingface.co/FacebookAI/roberta-base/tree/e2da8e2f811d1448a5b465c236feacd80ffbac7b)

## CPU et mémoire

L’inférence amont possède une voie CPU et son calcul repose sur les opérateurs PyTorch usuels. L’entraînement mono-processus possède également une voie CPU dans `setup_distributed`. Les dépendances amont sont gérées par Poetry, dont le verrou d’origine inclut Transformers 4.45.2 et Torch 2.5.1. La pile d’entraînement et d’évaluation inclut notamment Datasets, wtpsplit, W&B facultatif, NLTK et ROUGE. Le lanceur P2 utilise un profil distinct et figé pour l’inférence : PyTorch CPU 2.11.0, Transformers 4.57.6, Pydantic, PyYAML et psutil avec leurs dépendances. Il n’installe ni données ni outils d’entraînement. [Dépendances amont](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/pyproject.toml) · [Verrou amont](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/poetry.lock) · [Voie CPU](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/src/common/distributed.py)

Les modules par défaut ont été instanciés avec des tenseurs meta PyTorch et comptés sans allouer les poids. À quatre octets par paramètre FP32 :

| Module | Paramètres | Poids seuls |
| --- | ---: | ---: |
| Encodeur | 124 645 632 | 0,46 Gio |
| Prédicteur | 2 364 672 | 0,009 Gio |
| Décodeur | 306 953 817 | 1,14 Gio |
| Total en prédiction avec décodage | 433 964 121 | 1,62 Gio |

Ces valeurs excluent les états sérialisés, les copies de chargement, les activations, PyTorch, le navigateur et Windows. Le format amont inclut les moments AdamW. En FP32, les archives complètes sont estimées à environ 1,9 Gio pour l’encodeur et 3,4 Gio pour le décodeur, hors marges et métadonnées. Le lanceur mappe ces archives sur disque et libère leur référence après copie des poids utiles. La boucle du décodeur recalcule le préfixe à chaque token, ce qui rend la limite de longueur importante sur CPU. Un essai par lot de 1 sur 16 Go paraît réalisable d’après ces ordres de grandeur. Le pic, la latence et l’absence de pagination restent à mesurer sur le poste Windows avec les poids. [Sauvegarde encodeur](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/src/encoder/utils/checkpoints.py) · [Sauvegarde décodeur](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/src/decoder/train.py) · [Boucle de génération](https://github.com/jerber/lang-jepa/blob/f6e29a53760e631f12e16922c7300588c61c61d8/src/decoder/models.py)

## Obtenir ou entraîner les poids

1. Demander à l’auteur un checkpoint encodeur contenant l’état entraîné et le prédicteur, le YAML exact du run, puis le décodeur entraîné sur cet encodeur. Obtenir les empreintes, la révision de code, l’identifiant de tokenizer, les conditions d’usage et, si possible, les métriques du run. Un encodeur seul permet la première mesure de concept.
2. Si les poids n’existent pas, reproduire les deux étapes de l’amont avec autorisation d’usage. Les réglages par défaut utilisent 10 000 documents FineWeb-Edu `sample-10BT`, cinq époques encodeur, dix époques décodeur, des lots de 32 et des plafonds respectifs de 512 et 128 tokens. Il faut prévoir aussi la préparation des données et le modèle de découpage SaT `sat-3l-sm`. FineWeb-Edu est un corpus éducatif en anglais. Mesurer séparément le français et le Python NSI. [FineWeb-Edu](https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu) · [Recette amont](https://github.com/jerber/lang-jepa/tree/f6e29a53760e631f12e16922c7300588c61c61d8#quickstart-single-gpu)
3. Pour dimensionner l’entraînement, commencer par un pilote mesuré sur un GPU Linux d’au moins 24 Gio de VRAM, avec 32 Gio de RAM système et 50 Gio de SSD libres comme budgets de départ. Choisir des micro-lots de 2 à 4, augmenter l’accumulation pour une taille effective proche de 32 et démarrer à un seul processus. Pour l’encodeur, le BF16 et le gradient checkpointing sont prévus par l’amont. Le décodeur n’active pas BF16 dans son entraînement amont. Son modèle, ses gradients et les deux moments AdamW représentent déjà environ 4,57 Gio, avant l’encodeur gelé, les activations et les temporaires. L’encodeur, son prédicteur et le modèle EMA représentent environ 2,36 Gio pour leurs poids, gradients et états AdamW, hors activations. Ces budgets sont des estimations de préparation.
4. Mesurer le nombre réel de paires après segmentation, le débit en exemples traités par seconde, le temps de préparation et le coût validation/sauvegarde. Estimer chaque durée à partir du nombre d’exemples par époque multiplié par le nombre d’époques et divisé par le débit du pilote. Sur Windows 16 Go sans GPU, réserver au plus le mode debug à un contrôle technique. Le coût complet et les scores du run demeurent inconnus. Activer un lot de validation par document, surveiller le rang effectif et la dispersion de l’encodeur, puis valider la reconstruction du décodeur. Conserver révisions, configurations effectives, métriques et poids. [Diagnostics amont](https://github.com/jerber/lang-jepa/tree/f6e29a53760e631f12e16922c7300588c61c61d8#healthy-training-signals)

## Validation de livraison

| Contrôle | Résultat |
| --- | --- |
| Suite NSI | 9 tests Python réussis, dont les 3 tests initiaux. |
| Analyse JavaScript | `node --check app/app.js` réussi. |
| Recette Chromium | À 1 280 et 390 px, thème, quiz, navigation, saisie des trois champs et statut du tuteur vérifiés. Seuls les trois fichiers statiques locaux ont été demandés. |
| Tests amont | 30 réussis, 2 tests réseau désélectionnés, sous Linux avec Python 3.12 et PyTorch 2.11.0+cpu. |
| Dépôt de paquets Windows | 31 wheels Windows x64 et universelles, soit 161 237 420 octets. Fermeture des dépendances vérifiée pour Windows. Résolution hors ligne avec `--no-index --require-hashes` réussie en simulation de plateforme sous Linux. |
| Chargeur d’origine branché au lanceur P2 | Sous Linux CPU, tests techniques avec états synthétiques non entraînés : chargements stricts, modes reconstruction et prédiction, décodeur, sortie JSON et champs de mesure vérifiés. Les valeurs synthétiques ne sont pas des mesures de performance de LANG-JEPA entraîné. |
| Sauvegarde Git | Création et vérification d’un bundle complet de `main` réussies. |
| Première inférence réelle et performance Windows | Bloquées faute de checkpoint entraîné compatible. Temps de chargement, latence et pic mémoire non mesurés sur la cible. |
| Tuteur NSI | Saisie locale réalisée. Dialogue progressif, diagnostic et contrôle de la divulgation restent à implémenter et à évaluer après les premiers essais du modèle. |

### Reste à livrer

- Obtenir ou produire les checkpoints et clarifier les droits de distribution.
- Vérifier l’installation des wheels, l’inférence et les mesures sur le poste physique Windows x64 de 16 Go, réseau coupé.
- Conserver les sorties réelles, évaluer la reconstruction, la prédiction puis le tutorat en français, et décider de la mise en service selon les résultats.
