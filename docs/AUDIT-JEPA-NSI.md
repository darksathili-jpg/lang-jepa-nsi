# Reprise scientifique LANG-JEPA NSI

Le mandat du 22 novembre 2026 reprend une branche `main` propre à `a5bc5fb`. L’ancêtre demandé `06a88b2` contient le lanceur P2, l’audit public et les ressources figées. La branche inclut aussi l’atelier CPU SmolLM3 de la livraison précédente, ses comparaisons et ses résultats. Les 20 tests Python de départ passent. La préparation P2 d’un paquet Windows et les mesures Linux de SmolLM3 restent valides dans leur périmètre. [P2](RAPPORT-P2.md) · [Recette du mode conversationnel](RAPPORT-P3.md)

## Ressources et droits

L’archive amont `f6e29a53760e631f12e16922c7300588c61c61d8`, le tokenizer RoBERTa-base `e2da8e2f811d1448a5b465c236feacd80ffbac7b` et la pile CPU P2 sont déjà disponibles localement. Le pilote suit l’exemple public d’itération locale courte publié par l’auteur, avec une source amont vérifiée, extraite localement et conservée en dehors de Git. Le dépôt et la recette ne redistribuent ni cette source, ni les poids qui en résultent. Le ticket demandant une licence reste ouvert sans réponse publique. Les conditions de distribution de l’amont restent à clarifier. Les poids originaux prêts à l’emploi ne figurent pas parmi les ressources identifiées par P2. [Recette d’itération publiée par l’auteur](https://github.com/jerber/lang-jepa/tree/f6e29a53760e631f12e16922c7300588c61c61d8#quickstart-single-gpu) · [Ticket de licence](https://github.com/jerber/lang-jepa/issues/4)

Le pilote réutilise PyTorch CPU 2.11.0+cpu (BSD-3-Clause), Transformers 4.57.6 (Apache-2.0), PyYAML 6.0.3 et Pydantic 2.12.5 (MIT), et psutil 7.2.2 (BSD-3-Clause). Le tokenizer a son propre dépôt. Les exemples ont été rédigés pour cette mission et ne contiennent ni copie d’élève ni corpus récupéré. Le paquet d’entraînement complet amont, FineWeb, le modèle de segmentation et les services de télémétrie sont superflus dans ce protocole. [Verrou CPU P2](../requirements/p2-windows-x64.lock) · [Fiche RoBERTa-base](https://huggingface.co/FacebookAI/roberta-base)

## Critères par lot

| Lot | Critère d’acceptation |
| --- | --- |
| P3.1 | État Git, tests initiaux, ressources locales et décisions de licence documentés. |
| P3.2 | Corpus français synthétique segmenté, répartition par document, parcours Première et Terminale avec spécification, objectifs, erreurs typiques, tests et indices. |
| P3.3 | Architecture et pertes d’origine, entraînement CPU de taille bornée avec graines fixées, poids privés, traces et contrôles lexicaux, stabilité et comparaison de décodage hors échantillon. |
| P3.4 | Parcours du maximum sans exécution du code élève, avec provenance distincte et règle de décision explicite pour la participation éventuelle du modèle. |
| P3.5 | Tests unitaires et d’intégration, analyse des limites, mesure Linux qualifiée, recette navigateur en réseau isolé et livraison sur `main`. |

Le pilote teste la capacité technique et les métriques sur un petit jeu synthétique. Sur la cible, la RAM totale et la latence restent à mesurer sous Windows natif. Les ressources Linux observées sont deux CPU alloués et un plafond de 8 Gio.
