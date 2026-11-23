# P7 · Performances locales et distribution

Les mesures Linux et Windows Server décrivent leurs machines d’essai. Le poste Windows 10/11 x64, 16 Go, CPU uniquement, n’était pas disponible. **Recette Windows à effectuer sur le poste cible.**

Les essais Linux dans Chromium et le benchmark ont été lancés dans un espace réseau ne contenant que `lo`. Le benchmark mesure le processus llama.cpp et la durée des appels. Sous Windows Server, le navigateur bloque ses requêtes externes. Le runner prépare d’abord les poids puis dialogue sur la boucle locale. Sa connectivité générale n’a pas été désactivée. La recette Windows mesure périodiquement la somme des RSS de Python, llama.cpp et l’arbre Chromium, avec possible double comptage des pages partagées. [Comparatif Linux](P7_BENCHMARK_LLM.md) · [Recette Windows Server](https://github.com/darksathili-jpg/lang-jepa-nsi/actions/runs/45118621433)

La cible indicative est une médiane de moins de 15 secondes pour les tours sollicitant le LLM. Le test final Linux B a mesuré 41,42 s sur un seul appel, pendant d’autres recettes concurrentes. Cette observation indique qu’une mesure de charge sur le poste réel reste nécessaire. [Test final Linux](../p7/preuves/test-final-B.json)

Extracteur, contrôle des empreintes, runtime embarqué, diagnostic et arrêt reprennent la distribution P6.2. Une fois les modèles préparés, le démarrage fonctionne avec les fichiers locaux. Le redistribuable Visual C++ x64 officiel reste une dépendance système s’il est absent. [Installation et diagnostic](P6_1_INSTALLATION.md)

`Exécuter` reste indisponible. Un processus avec délai ne fournit aucune isolation vérifiée. Un interpréteur Python dans un Web Worker nécessiterait des contrôles démontrés sur les capacités Web, la mémoire, les interruptions et le réseau, avant d’être exposé au code libre. La recette P7 utilise des analyses de formes AST et des oracles mathématiques déterministes.

Pour revenir à la version précédente, arrêter 0.7.0 avec `Arreter.cmd`, extraire le ZIP 0.6.2 dans un autre dossier personnel, puis conserver ou préparer les modèles de ce dossier. `Verifier.cmd` confirme l’identité de l’instance et des moteurs. Lancer `Demarrer.cmd` du dossier retenu. Le lanceur authentifie le serveur local et choisit un autre port si une ancienne instance est présente. [ZIP 0.6.2](https://github.com/darksathili-jpg/lang-jepa-nsi/releases/tag/v0.6.2)
