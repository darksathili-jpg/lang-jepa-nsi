# P5 · Guide Windows et mesures CPU

## Lancer l’atelier

Sur Windows x64 avec Python 3.12 x64 et son lanceur `py`, ouvrir le dossier du dépôt et double-cliquer sur **scripts/tutor.cmd**. Ouvrir l’adresse locale imprimée dans le terminal. Le **Parcours guidé** fonctionne avec les fichiers du dépôt. Pour arrêter le serveur et le moteur, revenir dans le terminal et appuyer sur Ctrl+C. Le lanceur affiche un diagnostic lorsque la version de Python ou l’architecture est incompatible. Il n’utilise pas PowerShell pour démarrer l’application. [Guide Windows général](../README.md)

## Préparer les ressources sur un poste connecté

Les commandes suivantes s’exécutent depuis la racine, dans l’Invite de commandes. Pour le Parcours guidé, la préparation du modèle et de NumPy est facultative. Pour la Conversation locale P4, seuls les poids et le runtime SmolLM3 sont nécessaires.

```bat
py -3.12 -m tutor.install --model smol --platform windows-x64
py -3.12 -m pip download --platform win_amd64 --python-version 3.12 --implementation cp --abi cp312 --only-binary=:all: --require-hashes -r p5\requirements.txt -d wheelhouse
```

Le fichier GGUF SmolLM3, la version de llama.cpp et la roue NumPy sont figés. Le modèle et l’archive CPU sont vérifiés par le préparateur. Le téléchargement sur un autre système doit cibler explicitement Windows. Prévoir environ 2,2 Go pour les ressources SmolLM3 et au moins 13 Mio pour la roue Windows NumPy. Certains postes nécessitent le redistribuable Visual C++ x64. [Guide des ressources](INSTALLATION-P3.md) · [Empreintes de NumPy](../p5/requirements.txt)

## Installer et entraîner hors ligne

Transférer le dépôt, `models/tutor/`, `wheelhouse/` et les installateurs nécessaires. Déconnecter le poste d’Internet avant de lancer les commandes suivantes depuis la racine.

```bat
py -3.12 -m venv .venv-p5
.venv-p5\Scripts\python.exe -m pip install --no-index --only-binary=:all: --require-hashes --find-links wheelhouse -r p5\requirements.txt
set OPENBLAS_NUM_THREADS=1
.venv-p5\Scripts\python.exe -m p5.train --output results\p5
scripts\tutor.cmd --p5 c --jepa results\p5\fixe-24-17
```

Dans le navigateur, sélectionner **Conversation locale**. Le profil C signale séparément **Modèle prêt** et **JEPA prêt**. Le profil B se lance avec `scripts\tutor.cmd --p5 b`. Le double-clic ordinaire conserve le parcours stable. Le mode C reste expérimental. Son choix d’interventions n’a pas montré de bénéfice. Pour reproduire les tests navigateur, ajouter Playwright et un Chromium compatible aux ressources préparées sur le poste connecté. [Comparaison P5](P5_EVALUATION_ABC.md)

## Dépannage

| Symptôme | Vérification |
| --- | --- |
| « Python 3.12 et son lanceur py sont requis » | Exécuter `py -0p` dans l’Invite de commandes. Installer Python 3.12 x64 avec le lanceur si absent. |
| « Modèle absent » | Vérifier `models\tutor\SmolLM3-Q4_K_M.gguf` et l’unique exécutable `llama-server.exe` dans `models\tutor\runtime`. |
| JEPA absent ou indisponible | Vérifier que l’option `--jepa` pointe sur un répertoire avec `manifest.json` et `weights.npz`. Vérifier l’installation NumPy. Recréer les poids dans un répertoire de sortie neuf si l’empreinte diffère. |
| Erreur de port | Ajouter `--port 8775` à la commande et ouvrir l’adresse imprimée. |
| Réponses trop lentes | Revenir au parcours guidé. Comparer deux et quatre fils avec `--threads 2` puis `--threads 4` en conservant le même dialogue. |

## Recette à effectuer sur le poste cible

Sur un Windows x64 représentatif, couper Wi-Fi et Ethernet. Contrôler les deux démarrages, la disponibilité des modèles, les trois thèmes et les trois scénarios de dialogue. Mesurer le pic résident total simultané de Python, llama.cpp et Chromium sur 30 tours, puis vérifier dans le Gestionnaire des tâches que le moteur appartient aux processus arrêtés après Ctrl+C. Noter les versions, processeur, RAM, durée de démarrage, latence médiane et maximale, erreurs et éventuels processus restants. Le banc CLI permet déjà de comparer les pics du processus Python et du moteur séparément.

```bat
.venv-p5\Scripts\python.exe -m p5.compare --weights results\p5\fixe-24-17 --dialogues maximum-30 --modes b c --output results\windows-30.jsonl
```

Les cibles indicatives sont un pic total inférieur à 8 Gio, une médiane inférieure à 15 s, 30 tours sans épuisement mémoire et la fermeture sans processus orphelin. Le paquet Windows et son SHA-256 ont été vérifiés à la préparation. **Le lancement et les performances Windows n’ont pas été mesurés**, faute de machine Windows dans l’environnement d’exécution.

## Mesures Linux de développement

Le banc a utilisé Linux x86-64, AMD EPYC 9V74, deux fils CPU, un quota de deux CPU et une limite mémoire de 8 Gio. Le moteur de l’essai C a démarré en environ 5,02 s au début de la série et atteint un pic résident de 3,66 Gio. Le pic du processus Python du banc est d’environ 27 Mio. La médiane de réponse de C est de 11,50 s. Ces données décrivent des processus distincts et ne comprennent pas Chromium. Elles n’établissent pas le pic total Windows. [Rapport A/B/C](P5_EVALUATION_ABC.md)
