# P6.1 · Recette Windows et mesures

La recette native automatisée utilise GitHub Actions `windows-2022`. Elle exerce le runtime CPython 3.13.16, NumPy 2.3.5, les .cmd et Chromium. Le scénario de lancement retire Python du PATH du processus testé. Les ressources sont téléchargées explicitement, puis l’atelier continue avec ses fichiers locaux. La qualification sur poste Windows 10/11 d’établissement est détaillée en fin de rapport. [Recette native réussie avec modèles](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45061146459) · [Archive CI avec captures, traces et mesures](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45061146459/artifacts/14769965016)

| Scénario | Contrôle |
| --- | --- |
| Installation neuve | Extraction du ZIP avec le runtime inclus, entraînement local JEPA, démarrage via `Demarrer.cmd` dans un chemin avec espaces. Le navigateur en test utilise l’adresse d’atelier vérifiée. |
| Ancienne version ou port occupé | Deux dossiers de test démarrent sur un autre port quand un serveur occupe le port demandé. Le second lancement du même dossier réutilise la même instance et le processus occupant le port n’a reçu aucune demande d’arrêt. |
| Modèles absents | États lus par l’atelier et profil hybride indisponible. Le parcours guidé reste utilisable. |
| Téléchargement interrompu | Tests automatisés de lecture tronquée, reprise HTTP contrôlée, récupération quand le serveur repart de zéro et erreur d’empreinte. Reprise HTTPS réelle à partir de 1 Mio après interruption sous Linux, réponse HTTP 206 et empreinte vérifiée. Une coupure physique sur le PC cible reste à vérifier. [Trace HTTPS](../design/evidence-p61/reprise-https.json) |
| Mode hybride | Préparation réussie en 55,64 s sur le runner, transfert inclus. Les deux moteurs répondent aux sondes. Sur 30 tours, quatre questions sont reclassées par JEPA et deux reformulations de SmolLM3 sont affichées. |
| Hors ligne | Les tours de recette sous Linux ont été exécutés dans un espace réseau avec la seule boucle locale. La recette Chromium refuse toute requête externe. La coupure réseau du poste Windows cible reste à vérifier. |
| Arrêt | Rejet vérifié d’un arrêt non authentifié. `Arreter.cmd` confirme la fermeture du serveur et de son moteur. |
| Interface | Chromium natif dans les trois thèmes et sept tailles, avec captures et comparaison à 1672 × 941. Les facteurs 125 % et 150 % sont ceux du navigateur d’essai. Ils ne remplacent pas la mise à l’échelle du système Windows. |

Les premières exécutions ont révélé la conversion CRLF du corpus et la possibilité pour deux serveurs de partager une adresse avec `SO_REUSEADDR` sous Windows. Le corpus est verrouillé en LF canonique et le serveur utilise une liaison Windows exclusive avant d’essayer un port libre. Le contrôle du presse-papiers compare les fins de ligne LF et CRLF. Après un premier arrêt qui rendait la main avant la fin du processus serveur, le lanceur attend désormais la fin effective du processus Windows authentifié. [Premier diagnostic](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45059876999) · [Arrêt initial](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45060522627) · [Arrêt vérifié](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45061146459)

## Mesures Windows Server x64

Windows Server 2022 `10.0.20348`, quatre processeurs logiques, 17 174 360 064 octets de RAM. Les mesures sont celles du runner. Le pic de mémoire additionne les ensembles résidents du serveur, de llama.cpp et de l’arbre du navigateur de test, avec un possible double comptage des pages partagées.

| Indicateur | Observation Windows |
| --- | ---: |
| Démarrage du serveur | 0,375 s |
| Intégrité du modèle et du moteur | 1,481 s |
| Chargement SmolLM3 puis sonde d’inférence | 1,944 s puis 2,095 s |
| Chargement et sonde JEPA | 0,0552 s |
| Latence médiane des 10 tours sollicitant le LLM | 10,576 s |
| Latence maximale sur les 30 tours | 12,32 s |
| Pic RSS agrégé | 4,00 Gio |
| Pic CPU rapporté à un cœur logique | 256,8 % |
| Processus actifs après l’arrêt | 0 |

La médiane tous tours confondus est de 0,001 s. Vingt tours ont utilisé uniquement la progression locale et le moteur de sélection. Le journal de préparation et `windows-mesures/mesures.json` détaillent les contrôles et les traces sans données d’élèves. [Archive CI de la recette Windows](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45061146459/artifacts/14769965016)

## Mesures Linux isolées

AMD EPYC 9V74 x64, quota de deux CPU et cgroup de 8 Gio, Chromium 156. La somme des RSS des processus échantillonnés inclut le serveur, llama.cpp, Chromium et son arbre de processus de test. Les pages partagées peuvent être comptées plusieurs fois.

| Indicateur | Observation Linux |
| --- | ---: |
| Démarrage du serveur | 0,273 s |
| Intégrité du modèle et du moteur | 1,426 s |
| Chargement SmolLM3 puis sonde d’inférence | 2,217 s puis 2,399 s |
| Chargement et sonde JEPA | 0,0415 s |
| Latence médiane des 10 tours sollicitant le LLM | 12,722 s |
| Latence maximale sur les 30 tours | 14,841 s |
| Pic RSS agrégé | 4,35 Gio |
| Pic CPU rapporté à un cœur logique | 219,5 % |
| Processus actifs après l’arrêt | 0 |

La médiane tous tours confondus est de 0,001 s, car 20 tours n’ont pas sollicité le LLM. [Mesures brutes](../design/evidence-p61/mesures.json) · [Trace des 30 tours](../design/evidence-p61/hybride.jsonl) · [Régression P4 de 14 tours](../design/evidence-p61/maximum-p4.jsonl)

Pour rejouer sur le poste cible, préparer l’archive, vérifier les deux moteurs, déconnecter l’accès réseau puis lancer la recette. Mesurer l’ouverture du navigateur par le lanceur avec la configuration du poste et fermer via `Arreter.cmd`. Tester la mise à l’échelle Windows à 100 %, 125 % et 150 %. [Installation](P6_1_INSTALLATION.md)

**Recette Windows à effectuer sur le poste cible Windows 10/11 x64 de 16 Go.**
