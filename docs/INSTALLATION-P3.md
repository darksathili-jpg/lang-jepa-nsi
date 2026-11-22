# Installer le professeur virtuel P3 sur Windows

Le profil vise un poste **Windows x64, 16 Go de RAM, CPU**. Préparer Python **3.12 x64** avec le lanceur `py`. L’application utilise la bibliothèque standard de Python. Chromium ou un navigateur récent sert l’interface. Conserver l’installateur Python si le poste cible ne dispose d’aucune connexion. [Python pour Windows](https://www.python.org/downloads/windows/)

Le **Parcours guidé** fonctionne avec Python 3.12 et le dépôt seul. Exécuter `.\scripts\tutor.ps1` et attendre **Parcours prêt**. Le téléchargement ci-dessous concerne le mode **Conversation locale**.

## Préparation connectée

Récupérer le dépôt `darksathili-jpg/lang-jepa-nsi` sur `main`. Exécuter la commande suivante depuis la racine pour préparer le modèle et l’archive native Windows.

```powershell
py -3.12 -m tutor.install --model smol --platform windows-x64
```

La commande télécharge environ 1,94 Go depuis les dépôts officiels. Elle vérifie la taille du GGUF et les SHA-256 avant d’extraire le moteur. Les fichiers restent dans `models/tutor/`. Prévoir environ 2,2 Go libres pour le modèle, l’archive et le moteur extrait. Les outils Windows peuvent nécessiter le redistribuable Visual C++ x64 selon les bibliothèques déjà présentes. [Release llama.cpp](https://github.com/ggml-org/llama.cpp/releases/tag/b12600) · [Redistribuable Microsoft](https://learn.microsoft.com/fr-fr/cpp/windows/latest-supported-vc-redist)

Le catalogue `p3/models.json` fixe les URL par dépôt, révision et nom de fichier, ainsi que les empreintes. La même préparation peut être lancée depuis Linux avec `python -m tutor.install --model smol --platform windows-x64`. Le paquet extrait doit correspondre au système du poste qui exécutera le moteur. Pour préparer le runtime Linux natif, utiliser `--platform linux-x64` dans un autre dossier d’assets.

## Utilisation hors ligne

Transférer le dépôt, l’installateur Python si nécessaire et `models/tutor/` vers le poste cible. Après l’installation de Python, fermer les connexions Internet. Les deux services écoutent exclusivement en boucle locale. Exécuter les deux commandes suivantes depuis la racine dans PowerShell.

```powershell
.\scripts\check.ps1
.\scripts\tutor.ps1
```

Ouvrir [l’atelier](http://127.0.0.1:8765/atelier). Le parcours guidé est actif par défaut. Pour utiliser le modèle, choisir **Conversation locale** et attendre **Modèle prêt**. L’identité et la révision du modèle sont affichées. La page d’accueil donne aussi accès au [laboratoire scientifique](http://127.0.0.1:8765/). Appuyer sur Ctrl+C dans le terminal pour arrêter les services. Pour changer de port, lancer `py -3.12 -m tutor.server --port 8775`.

Lorsque le moteur est absent, vérifier la présence de `models/tutor/runtime/llama-server.exe` (ou du sous-dossier de release qui le contient) et de `SmolLM3-Q4_K_M.gguf`, puis redémarrer. En cas d’erreur d’empreinte, restaurer le fichier à partir d’une copie préparée et vérifiée. En cas d’échec du binaire, essayer `.\models\tutor\runtime\llama-server.exe --version` dans le terminal et vérifier que l’archive est le paquet CPU x64 prévu.

Sur Linux x64, utiliser `python -m tutor.install --model smol` pendant la préparation, puis `python -m tutor.server` hors ligne. La syntaxe `--assets CHEMIN` fonctionne à l’installation et au lancement. Choisir un autre modèle déjà préparé en passant `--model qwen` ou `--model granite` au serveur. Aucun téléchargement n’est effectué par le serveur d’atelier.

## Restauration et vérification sur le poste cible

Conserver le commit et le bundle Git de `main`, l’installateur Python et une copie du dossier d’assets autorisé. Le navigateur garde le dialogue dans l’onglet. Son seul choix persistant est le thème. Les traces de recette fournies avec le projet utilisent des saisies synthétiques. [Procédure Git de sauvegarde](INSTALLATION-P2.md#sauvegarder-et-restaurer)

Le banc de mesure se lance sur le poste Windows avec Internet coupé.

```powershell
New-Item -ItemType Directory -Force results | Out-Null
py -3.12 -m tutor.benchmark --model smol --threads 2 --output results\windows-smol.jsonl
```

Conserver nom du processeur, version de Windows, RAM, nombre de fils, démarrage, latence médiane, temps maximal et pic de mémoire de travail du moteur. Relancer dans un nouveau fichier de traces avec `--threads 4` si une comparaison locale est souhaitée. Exécuter les scénarios dans les mêmes conditions. [Protocole d’évaluation](EVALUATION-P3.md)
