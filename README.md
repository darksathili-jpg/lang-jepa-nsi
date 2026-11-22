# LANG-JEPA NSI — Professeur virtuel Python et laboratoire scientifique

**Un atelier local pour apprendre Python en Première et Terminale NSI, accompagné d'un laboratoire de recherche sur LANG-JEPA.**

Le projet propose trois expériences **distinctes** :

| Mode | Fonction | Modèle à télécharger ? |
| --- | --- | --- |
| **Parcours guidé** (par défaut) | Exercices Python, analyse statique et indices pédagogiques progressifs | **Non** |
| **Conversation locale** | Dialogue avec le modèle de langage SmolLM3 sur votre ordinateur | **Oui**, préparation initiale d'environ 1,94 Go |
| **Laboratoire LANG-JEPA** | Consultation des expériences sur les représentations latentes et essais scientifiques | Les résultats publiés sont consultables ; une nouvelle inférence nécessite des ressources compatibles |

> **À savoir :** le parcours guidé ne prétend pas être une IA générative. Le modèle conversationnel est **SmolLM3**, et non LANG-JEPA. Les expériences LANG-JEPA ont été menées sur un modèle miniature ; elles n'ont pas démontré un bénéfice fiable pour choisir les indices pédagogiques. [Résultats et limites](docs/EXPERIENCE-JEPA-NSI.md).

## Sommaire

1. [Configuration requise](#1-configuration-requise)
2. [Installer Python 3.12 sur Windows](#2-installer-python-312-sur-windows)
3. [Récupérer le projet](#3-récupérer-le-projet)
4. [Démarrer l'atelier sans script PowerShell](#4-démarrer-latelier-sans-script-powershell)
5. [Tester le parcours guidé](#5-tester-le-parcours-guidé)
6. [Activer la conversation locale avec SmolLM3](#6-activer-la-conversation-locale-avec-smollm3)
7. [Utiliser le laboratoire LANG-JEPA](#7-utiliser-le-laboratoire-lang-jepa)
8. [Dépannage Windows](#8-dépannage-windows)
9. [Tests et validation](#9-tests-et-validation)
10. [Confidentialité, limites et documentation](#10-confidentialité-limites-et-documentation)

## 1. Configuration requise

- **Windows 10/11 x64** (cible du projet) ; Linux x64 est également documenté.
- **Python 3.12 en version 64 bits** pour les commandes de ce guide.
- Un navigateur récent : Edge, Chrome ou Firefox.
- **16 Go de RAM recommandés** pour tester le mode conversationnel sur CPU ; le parcours guidé ne charge pas de modèle de langage.
- Pour le parcours guidé : aucun poids de modèle, aucun service cloud ni installation de dépendances Python tierces.
- Pour la conversation locale : connexion Internet **uniquement lors de la préparation initiale** des fichiers du modèle et du moteur ; prévoir environ **2,2 Go d'espace disque libre** pour ces ressources.

**État des validations :** le parcours et les modèles ont été testés sous Linux hors réseau ; l'installation et les performances sur un véritable poste Windows 16 Go restent **à confirmer**. Ne considérez pas les performances Linux comme garanties sur votre machine.

## 2. Installer Python 3.12 sur Windows

Ouvrez **PowerShell** (pas besoin du mode administrateur) et vérifiez les versions détectées :

```powershell
py --list
```

Si `-3.12` n'apparaît pas, installez Python 3.12 depuis [python.org — téléchargements Windows](https://www.python.org/downloads/windows/) ou, si `winget` est disponible :

```powershell
winget install --id Python.Python.3.12 -e
```

Fermez puis rouvrez PowerShell. Vérifiez :

```powershell
py -3.12 --version
```

**Résultat attendu :** `Python 3.12.x`. Si le message `No suitable Python runtime found` apparaît, Python 3.12 n'est pas encore détecté : revenez à cette étape. Une autre version installée ne remplace pas automatiquement la version demandée par les scripts.

## 3. Récupérer le projet

Sur [le dépôt GitHub](https://github.com/darksathili-jpg/lang-jepa-nsi), cliquez sur **Code → Download ZIP**. Décompressez l'archive dans un dossier de votre choix.

Ouvrez le dossier **qui contient directement** `README.md`, `scripts`, `tutor` et `app`. Attention : l'extraction d'une archive peut créer deux dossiers imbriqués nommés `lang-jepa-nsi-main`.

Dans l'Explorateur Windows, cliquez sur la **barre d'adresse** du bon dossier, saisissez `powershell`, puis appuyez sur Entrée.

Pour confirmer que vous êtes au bon endroit :

```powershell
Test-Path .\tutor\server.py
```

**Résultat attendu :** `True`. Si `False`, ouvrez le dossier intérieur du projet avant de poursuivre.

## 4. Démarrer l'atelier sans script PowerShell

**Méthode recommandée**, notamment sur les postes scolaires dont la politique interdit les scripts non signés :

```powershell
py -3.12 -m tutor.server
```

Le serveur doit afficher une adresse du type :

```text
Professeur virtuel : http://127.0.0.1:8765/atelier
```

Ouvrez ensuite **http://127.0.0.1:8765/atelier** dans votre navigateur.

- Gardez la fenêtre PowerShell ouverte : fermer la fenêtre arrête le serveur.
- Pour arrêter proprement le serveur, utilisez **Ctrl+C**.
- L'adresse `127.0.0.1` désigne **votre propre ordinateur**, pas un site Internet.
- Le **Parcours guidé** est disponible sans télécharger de modèle.

**Alternative facultative :** `.\scripts\tutor.ps1` lance le même serveur, mais peut être bloqué par la politique de sécurité PowerShell. Vous n'avez **pas besoin** de modifier cette politique : la commande Python ci-dessus suffit.

## 5. Tester le parcours guidé

1. Ouvrez **http://127.0.0.1:8765/atelier**.
2. Choisissez le niveau **Première NSI** et le mode **Parcours guidé**.
3. Sélectionnez l'exercice sur le maximum d'une liste.
4. Examinez le code suivant :

```python
def maximum(tab):
    m = 0
    for valeur in tab:
        if valeur > m:
            m = valeur
    return m
```

5. Suivez les questions et proposez vos propres tests. Essayez notamment `[-4, -2]`.
6. Vérifiez que les indices vous amènent à comprendre le problème de l'initialisation de `m` **sans donner immédiatement le programme corrigé**.
7. Examinez ensuite la question de la liste vide : la précondition de l'exercice doit être distinguée du comportement d'une fonction sur une entrée non autorisée.

**Autres exercices :** le catalogue comprend également un décompte, un exercice sur les dictionnaires et un exercice de récursivité pour la Terminale.

**Ce que vous évaluez ici :** la pertinence des indices rédigés et de l'analyse statique Python, **pas** les capacités génératives de LANG-JEPA.

## 6. Activer la conversation locale avec SmolLM3

Cette étape est **facultative**. Elle nécessite Internet pendant la préparation et peut prendre plusieurs minutes selon la connexion.

Arrêtez le serveur avec **Ctrl+C**, puis exécutez dans le dossier du projet :

```powershell
py -3.12 -m tutor.install --model smol --platform windows-x64
```

Le programme prépare le moteur CPU et le modèle quantifié **SmolLM3-3B Q4_K_M**, en vérifiant les empreintes des fichiers. Les ressources sont placées dans `models/tutor/`. Le téléchargement représente environ **1,94 Go**.

Redémarrez le serveur :

```powershell
py -3.12 -m tutor.server
```

Retournez sur **http://127.0.0.1:8765/atelier**, choisissez **Conversation locale** et attendez l'état **« Modèle prêt »**.

Exemple de question à poser :

> Ma fonction maximum renvoie 0 lorsque tous les nombres sont négatifs. Aide-moi à comprendre avec des questions, sans donner directement le corrigé.

Le mode conversationnel utilise un **modèle de langage local**, distinct de LANG-JEPA. Ses réponses peuvent être imprécises, trop directes ou incorrectes : **vérifiez-les avant tout usage autonome avec des élèves**.

Une fois les ressources installées, coupez Internet pour vérifier le fonctionnement local. Les services sont conçus pour écouter uniquement sur l'interface de bouclage.

## 7. Utiliser le laboratoire LANG-JEPA

La page d'accueil du serveur, **http://127.0.0.1:8765/**, présente le laboratoire scientifique et les résultats de l'expérimentation.

Les essais publiés reposent sur deux entraînements CPU d'une **configuration miniature initialisée de zéro**. Pour la recherche d'indices, les scores observés sont de **4/8 et 2/8** contre **4/8** pour la référence TF-IDF. Le décodeur ne produit pas de phrases exploitables pour un tutorat.

Il ne faut pas confondre ce pilote avec un modèle LANG-JEPA complet entraîné sur un grand corpus. Pour reproduire l'expérience, consultez [le protocole et les commandes](docs/EXPERIENCE-JEPA-NSI.md) ainsi que [l'installation scientifique P2](docs/INSTALLATION-P2.md). **La reproduction nécessite des ressources supplémentaires**, contrairement à la simple consultation des résultats.

## 8. Dépannage Windows

### « Le fichier tutor.ps1 n'est pas signé numériquement »

PowerShell bloque l'exécution d'un script non signé. **N'abaissez pas la politique de sécurité de votre machine pour démarrer l'atelier.** Exécutez simplement :

```powershell
py -3.12 -m tutor.server
```

Cette méthode évite entièrement le fichier `.ps1`.

### « No suitable Python runtime found »

La version 3.12 n'est pas détectée par le lanceur Python. Vérifiez :

```powershell
py --list
```

Installez Python 3.12 x64, rouvrez PowerShell, puis vérifiez `py -3.12 --version`.

### « No module named tutor » ou fichier introuvable

Vous êtes probablement dans le mauvais dossier. Exécutez :

```powershell
Test-Path .\tutor\server.py
```

Le résultat doit être `True`. Si nécessaire, ouvrez le dossier qui contient directement `README.md`.

### Le navigateur ne parvient pas à ouvrir l'atelier

Vérifiez que le serveur affiche son adresse et que PowerShell est toujours ouvert. Utilisez **http://127.0.0.1:8765/atelier** (avec **http**, et non https).

Si le port 8765 est occupé, arrêtez l'autre instance ou choisissez un autre port :

```powershell
py -3.12 -m tutor.server --port 8775
```

Ouvrez alors **http://127.0.0.1:8775/atelier**.

### Le Parcours guidé fonctionne mais le modèle conversationnel reste absent

C'est normal **avant l'installation de SmolLM3**. Suivez la section 6. Le parcours guidé ne dépend pas de ces fichiers.

### Le modèle ne démarre pas après téléchargement

Vérifiez la fin du journal d'installation et la présence des ressources dans `models/tutor/`. Le moteur Windows peut nécessiter le [redistribuable Microsoft Visual C++ x64](https://learn.microsoft.com/fr-fr/cpp/windows/latest-supported-vc-redist). N'effacez pas les fichiers avant d'avoir relevé le message d'erreur.

### Le serveur répond lentement

La génération sur CPU peut prendre plusieurs secondes. Sur la machine de test Linux, SmolLM3 a eu une latence médiane d'environ **12,87 s** et un pic résident du processus natif d'environ **3,92 Gio**. **Ces chiffres ne sont pas des garanties pour Windows.** Commencez par le parcours guidé si le modèle conversationnel est trop lent.

### Signaler un problème efficacement

Ouvrez une [issue GitHub](https://github.com/darksathili-jpg/lang-jepa-nsi/issues) en indiquant :

- Version de Windows et de Python (`py -3.12 --version`).
- Mode utilisé : Parcours guidé, Conversation locale ou Laboratoire.
- Commande exécutée et message d'erreur **copié en texte**.
- Résultat attendu et résultat observé.
- Si possible, capture d'écran **sans données personnelles d'élèves**.

Ne publiez jamais de clés, de données personnelles ni de copies de travaux identifiables.

## 9. Tests et validation

Depuis le dossier du projet, les tests Python du dépôt peuvent être lancés **sans script PowerShell** :

```powershell
py -3.12 -m unittest discover -s tests -v
```

Les tests automatiques ne remplacent pas une vérification pédagogique en classe ni une recette sur le PC Windows cible.

Pour une évaluation manuelle, vérifiez au minimum :

- [ ] Le serveur démarre avec `py -3.12 -m tutor.server`.
- [ ] Le Parcours guidé fonctionne sans modèle installé.
- [ ] Le scénario `maximum(tab)` progresse sans divulguer immédiatement le corrigé.
- [ ] Les modes clair, sombre et projecteur restent lisibles.
- [ ] La Conversation locale affiche clairement l'identité du modèle.
- [ ] Après installation, la conversation fonctionne avec Internet coupé.
- [ ] Le serveur s'arrête avec Ctrl+C.

Consultez la [recette P3 scientifique](docs/RECETTE-JEPA-NSI.md) et le [rapport de validation conversationnelle](docs/RAPPORT-P3.md) pour distinguer les contrôles effectués et les limites restantes.

## 10. Confidentialité, limites et documentation

- L'atelier fonctionne localement et son serveur écoute sur `127.0.0.1`.
- Le code élève est traité par **analyse statique** dans le parcours ; il n'est pas exécuté comme un programme arbitraire dans le processus serveur.
- Les modèles conversationnels peuvent donner des réponses erronées ou divulguer une solution malgré les consignes.
- Le pilote LANG-JEPA **n'a pas démontré** qu'il pouvait enseigner seul ou améliorer la sélection des indices.
- Les droits de redistribution du code amont LANG-JEPA et de certains poids expérimentaux restent à clarifier ; **n'en déduisez pas une autorisation de redistribution**.

### Documentation technique

- [Installation détaillée Windows et hors ligne](docs/INSTALLATION-P3.md)
- [Architecture du professeur virtuel](docs/ARCHITECTURE-P3.md)
- [Comparatif des modèles conversationnels](docs/COMPARATIF-P3.md)
- [Rapport de validation du modèle conversationnel](docs/RAPPORT-P3.md)
- [Expérience scientifique LANG-JEPA : protocole et résultats](docs/EXPERIENCE-JEPA-NSI.md)
- [Recette de la reprise scientifique](docs/RECETTE-JEPA-NSI.md)
- [Audit et limites de LANG-JEPA](docs/AUDIT-JEPA-NSI.md)
- [Règles de développement](AGENTS.md)

---

**Conseil aux nouveaux testeurs : commencez toujours par les sections 2 à 5.** Vous pourrez découvrir l'atelier sans télécharger de modèle, puis décider si vous souhaitez installer la conversation locale.
