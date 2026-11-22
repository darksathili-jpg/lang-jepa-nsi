# P6.1 · Rapport de livraison

**Mission partiellement réalisée.** La distribution a été vérifiée sous Windows Server x64 en intégration continue. **Recette Windows à effectuer sur le poste cible** Windows 10/11 x64, 16 Go de RAM, CPU uniquement.

## A. Version livrée

Version `0.6.1`, build `4a1c05072388b44e38c02b2ad4e72f46cc951e42`, sur `main`, dans la continuité de P6 (`8d717e7`). Le rapport et la publication des preuves ont leurs propres commits. [Code du paquet](https://github.com/darksathili-jpg/lang-jepa-nsi/commit/4a1c05072388b44e38c02b2ad4e72f46cc951e42)

## B. Distribution Windows

Le ZIP portable de 25 113 859 octets contient CPython 3.13.16 et NumPy 2.3.5. Les quatre commandes du dossier utilisent ce Python sans modifier le PATH global. Les modèles sont préparés séparément, avec consentement, contrôle de taille, empreinte et reprise des fichiers partiels. [ZIP Windows x64](https://raw.githubusercontent.com/darksathili-jpg/lang-jepa-nsi/main/releases/0.6.1/LANG-JEPA-NSI-0.6.1-Windows-x64.zip) · [SHA-256](https://raw.githubusercontent.com/darksathili-jpg/lang-jepa-nsi/main/releases/0.6.1/SHA256SUMS.txt) · [Architecture](P6_1_ARCHITECTURE_DISTRIBUTION.md)

## C. Installation

1. Extraire tout le ZIP dans un dossier personnel.
2. Avec Internet, lancer `Installer-Modeles.cmd` et confirmer. Prévoir au moins 2,2 Go disponibles.
3. Lancer `Demarrer.cmd`. Le parcours guidé s’ouvre par défaut. Sélectionner le profil hybride expérimental pour solliciter les modèles.
4. Lancer `Arreter.cmd` à la fin. Le diagnostic détaillé est disponible dans les paramètres de l’atelier et via `Verifier.cmd`.

Sur un poste où le redistribuable Visual C++ x64 est absent, suivre les règles de l’établissement pour installer ce prérequis du moteur. [Guide Windows](P6_1_INSTALLATION.md)

## D. Ressources vérifiées

| Ressource | Provenance et licence | SHA-256 |
| --- | --- | --- |
| SmolLM3-3B Q4_K_M, 1 915 305 312 octets | `ggml-org/SmolLM3-3B-GGUF`, révision `4965cb60b150737b68a0408c36aeefb65078f894`, Apache-2.0 | `8334b850b7bd46238c16b0c550df2138f0889bf433809008cc17a8b05761863e` |
| llama.cpp CPU Windows x64 b12600 | `ggml-org/llama.cpp`, commit `29b52d398`, MIT | `a31a14f1630408422228d02ff2a3fc41c06a6b3b3849d8d2782c37f0f6e30951` |
| JEPA P5 `fixe-24`, graine 17, 65 époques | Reconstruction locale avec les sources, la configuration et le corpus du dépôt. Les poids sont produits lors de la préparation. | Référence P5 et reconstruction Linux `f4e854fcb1b973e2fbda8b60acdb9404ad1e68f2700b2930b36e88e627adad68` |

La sonde appelle réellement SmolLM3, et la préparation vérifie une prédiction latente JEPA utilisable par le module de sélection. L’empreinte de la reconstruction JEPA dans la recette Windows publiée est `c70aa1329633c999c557fd1408b644c21c8c2afa4c7640123e6d7ef2df5401db`. [Audit et licences](P6_1_AUDIT_WINDOWS.md) · [Verrou des ressources](../distribution/lock.json)

## E. Fonctionnement hybride

La recette rejoue 30 tours synthétiques avec des cas limites et des demandes de corrigé. Quatre questions ont été reclassées par JEPA sur chacun des deux environnements. SmolLM3 a fourni deux formulations affichées sous Windows et quatre sous Linux. Le parcours guidé reste le profil par défaut et l’interface affiche **Hybride expérimental** lorsque les deux sondes réussissent et que ce profil est sélectionné. Le laboratoire porte la mention **Bénéfice JEPA non démontré**. [Trace Windows](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45061146459/artifacts/14769965016) · [Trace Linux hors Internet](../design/evidence-p61/hybride.jsonl) · [Régression P4 avec SmolLM3](../design/evidence-p61/maximum-p4.jsonl)

## F. Fidélité graphique

Le dossier de preuves Windows contient la capture Chromium à 1672 × 941 avec son côte à côte, sa superposition à 50 %, la carte sans masque et les mesures géométriques. Les contrôles couvrent aussi les trois thèmes et les petits écrans. La maquette approuvée conserve son empreinte. Les écarts mesurés par zone et la part liée aux états des moteurs et aux textes dynamiques figurent dans le rapport. [Preuves Windows](https://raw.githubusercontent.com/darksathili-jpg/lang-jepa-nsi/main/releases/0.6.1/LANG-JEPA-NSI-0.6.1-Preuves-Windows.zip) · [Rapport visuel](P6_1_RECETTE_VISUELLE.md)

## G. Compagnon

Le personnage conserve le dessin approuvé. Deux calques de regard et de geste animent le repos, l’accueil, l’écoute, la réflexion, l’encouragement, l’explication et la validation d’une réponse correcte. Les transitions ont été vérifiées dans Chromium avec un dialogue et la préférence de mouvement réduit. [Transitions observées](../design/evidence-p61/compagnon-transitions.json) · [Geste d’explication](../design/evidence-p61/compagnon-explication.png)

## H. Performances

Sous Windows Server, le démarrage du serveur a pris 0,375 s et les 10 tours qui ont sollicité SmolLM3 ont eu une latence médiane de 10,576 s, un maximum de 12,32 s et un pic RSS agrégé de 4,00 Gio. Sous Linux isolé, la médiane du LLM est de 12,722 s, le maximum de 14,841 s et le pic RSS agrégé de 4,35 Gio. Les deux exécutions se sont achevées sans processus actif. [Mesures et conditions](P6_1_RECETTE_WINDOWS.md)

## I. Tests

52 tests Python sur Windows et Linux. La recette native couvre le lancement sans Python sur le PATH, un port occupé par une autre instance, les trois thèmes, le dialogue, les deux modèles et l’arrêt. La recette Linux avec les modèles réels a tourné avec la seule boucle locale, et le test Chromium détecte toute demande externe. La reprise réelle d’un transfert HTTPS officiel après interruption a été contrôlée sous Linux. [GitHub Actions Windows](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45061146459) · [Reprise HTTP 206](../design/evidence-p61/reprise-https.json) · [Détail des erreurs corrigées](P6_1_RECETTE_WINDOWS.md)

## J. Limites

La recette physique doit vérifier la coupure d’Internet en cours de séance, la mise à l’échelle Windows 100/125/150 %, le navigateur par défaut et les performances sur le matériel de 16 Go. Les données de test sont synthétiques. L’analyse du code Python de l’élève reste statique. Le résultat d’une comparaison pédagogique plus large reste à établir avant d’attribuer un bénéfice au mode hybride. [Recette Windows](P6_1_RECETTE_WINDOWS.md) · [Rapport P5](P5_RECETTE_FINALE.md)
