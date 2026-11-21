# Installation et restauration P2

## Laboratoire Windows

Installer Python 3 avec le lanceur `py`. Depuis la racine du dépôt, exécuter `.\scripts\check.ps1`, puis `.\scripts\dev.ps1`. Ouvrir `http://127.0.0.1:8765`. Pour une installation sur un poste déjà hors ligne, conserver préalablement le programme d’installation Python depuis le site officiel et l’installer avant ces commandes. [Python pour Windows](https://www.python.org/downloads/windows/)

Sous Linux, les équivalents sont `python -m unittest discover -s tests -v` et `python -m http.server 8765 --bind 127.0.0.1 --directory app`, depuis la racine du dépôt. La recette facultative `python tests/browser_smoke.py` utilise Playwright et Chromium. Pour un Chromium déjà installé, ajouter `--chromium CHEMIN`.

## Préparer les fichiers sur une machine connectée

Le profil du lanceur est **Windows x64, CPython 3.12**. Conserver le programme d’installation x64 utilisé, avec son empreinte, pour restaurer la même version corrective. Préparer si nécessaire le redistribuable Visual C++ x64 utilisé par PyTorch. [PyTorch sous Windows](https://docs.pytorch.org/docs/stable/notes/windows.html) · [Redistribuable Microsoft](https://learn.microsoft.com/fr-fr/cpp/windows/latest-supported-vc-redist)

Depuis la racine du dépôt, sur un Windows x64 avec Python 3.12 :

```powershell
py -3.12 -m pip download --only-binary=:all: --require-hashes --dest .\wheelhouse --extra-index-url https://download.pytorch.org/whl/cpu -r .\requirements\p2-windows-x64.lock
if ($LASTEXITCODE -ne 0) { throw "Préparation des paquets interrompue." }
```

`p2/upstream.json` fournit les URL et les empreintes SHA-256 de l’archive source amont et des cinq fichiers de configuration et de tokenisation RoBERTa-base. Pour constituer une copie locale sur un poste autorisé à utiliser ces ressources :

```powershell
$lock = Get-Content .\p2\upstream.json -Raw | ConvertFrom-Json
foreach ($file in $lock.files.PSObject.Properties) {
    $target = Join-Path .\models\p2 $file.Name
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    Invoke-WebRequest -ErrorAction Stop -UseBasicParsing -Uri $file.Value.url -OutFile $target
    if ((Get-FileHash -Algorithm SHA256 $target).Hash -ine $file.Value.sha256) {
        throw "Empreinte invalide pour $target"
    }
}
```

Quand les checkpoints seront disponibles, placer dans `models/p2/` :

| Fichier | Contenu |
| --- | --- |
| `encoder.pth` | Checkpoint PyTorch ZIP avec `encoder` et, pour la prédiction, `predictor`. |
| `encoder_config.yaml` | YAML effectif du run, par exemple `logs/lang_jepa/config.yaml`. |
| `decoder.pt` | Facultatif. Checkpoint PyTorch ZIP avec `model_state_dict` et la dataclass amont `DecoderConfig`. |
| `checkpoints.json` | Copie renseignée de `p2/checkpoints.example.json` avec provenance et empreintes SHA-256 en minuscules. Omettre `decoder` en l’absence de décodeur. |

Vérifier les droits et la provenance auprès de la source. Utiliser l’empreinte de l’encodeur réellement utilisé pour entraîner le décodeur. Une empreinte calculée à la réception sert à vérifier l’intégrité des copies ultérieures. L’archive amont, les checkpoints, leur configuration, le manifeste renseigné et les résultats locaux restent en dehors de Git.

## Installer et vérifier hors ligne

Transférer le dépôt NSI, `wheelhouse/` et le contenu autorisé de `models/p2/` sur le poste Windows. Après avoir installé Python hors ligne, couper les connexions réseau et ouvrir PowerShell à la racine du dépôt.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check --no-index --find-links .\wheelhouse --only-binary=:all: --require-hashes -r .\requirements\p2-windows-x64.lock
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe .\scripts\lang_jepa_cpu.py --verify-only
```

Ajouter `--decode` à la vérification pour exiger le décodeur. Un code de retour 1 signale une ressource indisponible ou invalide. Une vérification réussie confirme les fichiers et leurs empreintes. Le chargement et les mesures sont effectués par la commande suivante.

## Première expérience avec des poids entraînés

Sur le poste cible, avec le réseau toujours coupé :

```powershell
New-Item -ItemType Directory -Force results | Out-Null
.\.venv\Scripts\python.exe .\scripts\lang_jepa_cpu.py --input .\p2\probe-en.txt --output .\results\concept-en-1.json --threads 4
.\.venv\Scripts\python.exe .\scripts\lang_jepa_cpu.py --input .\p2\probe-en.txt --output .\results\reconstruction-en-1.json --threads 4 --decode
.\.venv\Scripts\python.exe .\scripts\lang_jepa_cpu.py --input .\p2\probe-nsi.txt --output .\results\prediction-nsi-1.json --threads 4 --mode prediction --decode
```

Les deux dernières commandes exigent le décodeur. Utiliser des chemins de sortie distincts et répéter chaque mesure au moins trois fois à paramètres identiques. Documenter le processeur, la RAM, la version de Windows, la disponibilité du fichier d’échange et la distinction entre première lecture après redémarrage et lectures suivantes. Conserver les JSON intacts. Rapporter la première mesure, la médiane des suivantes, le plus haut pic mémoire et les éventuels échecs. L’encodeur reçoit au plus 128 tokens par défaut, marqueurs inclus. Le décodeur produit au plus 24 nouveaux tokens, arrêt anticipé au marqueur de fin.

## Sauvegarder et restaurer

Depuis `main`, sauvegarder l’historique Git et conserver l’identifiant exact du commit. L’exemple écrit sur un volume de sauvegarde déjà créé :

```powershell
git rev-parse main
git bundle create E:\sauvegarde\lang-jepa-nsi-main.bundle main
git bundle verify E:\sauvegarde\lang-jepa-nsi-main.bundle
git bundle list-heads E:\sauvegarde\lang-jepa-nsi-main.bundle
Get-FileHash -Algorithm SHA256 E:\sauvegarde\lang-jepa-nsi-main.bundle
```

Sauvegarder séparément les installateurs, `wheelhouse/`, les ressources autorisées de `models/p2/`, les résultats d’évaluation à conserver et leurs empreintes. Recréer `.venv` à partir de `wheelhouse/` à chaque restauration.

En cas de perte de la copie de travail, vérifier l’empreinte du bundle et reconstruire une copie locale du dépôt existant :

```powershell
git clone --single-branch --branch main E:\sauvegarde\lang-jepa-nsi-main.bundle lang-jepa-nsi
Set-Location lang-jepa-nsi
git remote set-url origin https://github.com/darksathili-jpg/lang-jepa-nsi.git
git rev-parse HEAD
.\scripts\check.ps1
```

Comparer `HEAD` au commit sauvegardé. Restaurer les fichiers locaux autorisés, relancer l’installation hors ligne, puis vérifier le laboratoire et le bundle P2. Une restauration locale préserve la branche GitHub et son historique.
