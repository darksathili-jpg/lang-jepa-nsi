# P6.1 · Distribution Windows portable

| Option | Taille et démarrage | Maintenance et contrôle |
| --- | --- | --- |
| CPython embarqué officiel | Archive de 11,44 Mo. Démarre avec le module local de l’atelier. NumPy fournit une roue de 12,78 Mo. | Versions, fichiers et notices séparés. La construction compare les SHA-256. L’enseignant utilise quatre commandes .cmd et le runtime reste dans le dossier extrait. |
| Exécutable gelé | Taille non mesurée. Le gel ajouterait la collecte des extensions NumPy, des fichiers HTML et des ressources de diagnostic. | Le travail devrait être refait à chaque mise à jour du moteur Python. Le mode portable facilite le diagnostic des DLL et des révisions. |
| Python installé ou venv déplacé | Dépend de l’installation de l’utilisateur ou du chemin d’origine de l’environnement. | Les deux erreurs de terrain touchent déjà cette méthode. |

Le ZIP emploie CPython embarqué officiel 3.13.16 x64 et NumPy 2.3.5 pour CPython 3.13. Le fichier `python313._pth` limite les imports à l’environnement extrait et à l’application. Les avis de licence PSF, NumPy et des bibliothèques fournies restent dans leurs dossiers. Le code et le corpus proviennent d’un commit Git identifié par `application/distribution/build.json`. Le ZIP ne contient ni les poids ni les exécutables de llama.cpp. [Verrou des ressources](../distribution/lock.json) · [Catalogue SmolLM3](../p3/models.json)

**Préparation.** La commande d’installation demande une confirmation avant de récupérer les archives officielles. Elle calcule l’espace nécessaire et vérifie les tailles et SHA-256. Un téléchargement reprend à l’offset présent si la réponse HTTP confirme exactement la plage. Une réponse complète recommence le transfert. Les fichiers partiels sont confinés à `.part`. Les fichiers finis sont vérifiés avant promotion. Le contrôle du moteur vérifie aussi les fichiers décompressés, sa version, son processus et une vraie réponse locale à une question synthétique.

**JEPA.** `fixe-24`, graine 17, 65 époques sur le corpus P5 fixé. Le programme compare l’empreinte reconstruite à celle de P5 et affiche le résultat. Il vérifie ensuite le manifeste, les poids, la prédiction latente et son acceptation par une sélection pédagogique réelle. Le modèle reste expérimental. Les poids générés sont dans le dossier de l’enseignant.

**Lancement et arrêt.** Le lanceur utilise un verrou de dossier et confirme le nom, la version, le build, le dossier d’installation et un identifiant d’instance sur la boucle locale. Si le port demandé est occupé, la nouvelle instance demande un port libre au système. Le navigateur s’ouvre sur l’adresse vérifiée. L’arrêt repose sur une clé d’instance dédiée, suivie de la fermeture du serveur et de llama.cpp. Sous Windows, un Job Object rattache le moteur à son processus serveur. La clé d’arrêt reste dans le dossier local d’installation. [Implémentation du lanceur](../distribution/launcher.py)

**Prérequis Windows.** Le moteur natif officiel b12600 utilise les DLL du redistribuable Visual C++ x64. Le paquet utilise la version installée par Windows ou par l’établissement. Il affiche une incompatibilité si l’exécutable échoue à démarrer. L’ajout éventuel du redistribuable officiel peut nécessiter l’administrateur. [Guide utilisateur](P6_1_INSTALLATION.md)

```text
python -m distribution.build_windows --ref <commit> --cache results/archives --output results/paquet
```

L’assembleur construit le runtime à partir des archives officielles verrouillées, produit le manifeste de build, convertit les commandes au format CRLF et fournit `SHA256SUMS.txt`.
