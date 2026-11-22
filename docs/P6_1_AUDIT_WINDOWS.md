# P6.1 · Audit initial Windows

Base examinée sur `main`, `8d717e743ba778e7251db2338b264bde23fca3dc`. L’historique local et distant concordent au départ. La référence visuelle reste le PNG 1672 × 941 dont le SHA-256 est `29a5bd4c27654317a7926797f40c818e871f03017e00ce08a56d6e463d4f517d`.

| Composant | Situation avant P6.1 |
| --- | --- |
| Archive GitHub, README et scripts | Les archives de source ne contiennent ni Python, ni NumPy, ni les modèles. `tutor.cmd` invoque `py -3.12`, ce qui reproduit l’échec de détection. `tutor.ps1` dépend de la politique de scripts de Windows. |
| Serveur, atelier et tests | `tutor.server` sert les ressources locales, l’analyse AST, l’orchestrateur et une API de boucle locale. Le navigateur rend le HTML, CSS et JS sans autre dépendance. P6 a exercé les vues et les modèles réels sous Linux. |
| SmolLM3 | Le modèle Q4_K_M de 1 915 305 312 octets et llama.cpp b12600 sont en dehors de Git. La préparation P3 vérifie les empreintes et extrait une archive, sans reprise persistante, sans contrôle d’espace et sans inférence d’installation. L’état prêt dépend de `/health`. |
| JEPA P5 | La commande `p5.train` et NumPy entraînent localement `fixe-24`, graine 17, pendant 65 époques sur le corpus P5 versionné. Le chargement vérifie le manifeste, le SHA-256, les bornes et les tenseurs. Aucun poids ne doit entrer dans Git. |
| Exécutables Windows | Python embarqué peut être livré avec sa licence PSF et ses notices. NumPy redistribuable via la roue signée par empreinte PyPI et ses notices. llama.cpp et SmolLM3 restent téléchargés à la demande depuis leurs révisions officielles, sous MIT et Apache-2.0. Le PE de llama.cpp importe aussi le runtime Microsoft Visual C++ x64. |
| Port et arrêt | Le serveur expose un port par défaut, sans identité de build ni vérification de l’instance qui répond. Un navigateur ouvert à la main sur ce port peut retrouver l’ancienne version. La fermeture suivant Ctrl+C arrête le processus natif qui appartient au serveur. |

L’atelier, l’entraînement JEPA et la préparation utilisent Python. Seul le mode avec JEPA requiert NumPy. Le moteur llama.cpp est un exécutable séparé. Un répertoire portable permet de regrouper les sources, le runtime CPython et NumPy. Modèles, journaux et identités d’instance peuvent rester dans des dossiers explicites à côté des commandes. Une vérification distincte du runtime, des fichiers modèle et d’une inférence est nécessaire pour expliquer une installation incomplète.

Le paquet embarqué CPython 3.13.16 x64 est un fichier officiel de 11 439 094 octets. Son SHA-256 correspond au condensat du bundle Sigstore publié. 3.13.18 ne publie pas de paquet Windows embarqué à la date de l’audit. La roue PyPI NumPy 2.3.5 existe pour CPython 3.13 x64. Le passage à CPython 3.13 dans la distribution n’exige aucun Python préinstallé. L’identité des poids reconstruits reste établie par la comparaison avec le SHA-256 P5, indépendamment de la version Python ou de BLAS. [Archive Python officielle](https://www.python.org/ftp/python/3.13.16/) · [NumPy sur PyPI](https://pypi.org/project/numpy/2.3.5/)

Une instance doit authentifier son identité locale et sa révision avant d’ouvrir son URL. Le port de secours doit être attribué par le système à la nouvelle instance lorsque le port historique est occupé. La commande d’arrêt doit elle-même prouver l’identité de l’instance cible. Aucune action d’arrêt sur un serveur inconnu n’est nécessaire.
