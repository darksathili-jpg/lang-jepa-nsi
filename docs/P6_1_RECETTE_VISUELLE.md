# P6.1 · Fidélité visuelle et compagnon

La maquette approuvée de 1672 × 941 est identique au fichier de P6, SHA-256 `29a5bd4c27654317a7926797f40c818e871f03017e00ce08a56d6e463d4f517d`. Les mesures sont calculées sur l’image complète sans masque. Les captures de référence sont effectuées à un pixel de périphérique par pixel CSS, avec mouvement réduit. [Maquette](../design/reference/REFERENCE_VISUELLE_VALIDEE.png)

| Zone | Contrôle effectué dans Chromium Linux |
| --- | --- |
| En-tête, scène et personnage | Composition, cadrage et zones colorées de P6. La zone mesurée du personnage en accueil correspond pixel pour pixel à la référence. Les mouvements sont testés séparément en situation pédagogique. |
| Éditeur, exercice et progression | Positions, largeur de l’éditeur, accessibilité des commandes et vérification des contrastes. Les essais intègrent les numéros de ligne, la syntaxe et l’état d’exemple. |
| Conversation | Géométrie de P6 à 1672 × 941. Tests de navigation, clavier, copie et pièces jointes locales. Les textes des vrais dialogues diffèrent du contenu illustratif. |
| Colonne des moteurs | États observés sur les fichiers présents. Le diagnostic détaillé se trouve dans les paramètres. Le statut de disponibilité et l’attribution de chaque intervention sont distincts. |
| Palette, typographies et icônes | Les thèmes sombre, clair et projecteur ont été testés dans sept tailles. Les légères variations de glyphes et les différences de contenu P6 sont toujours documentées. [Rapport P6](P6_RECETTE_VISUELLE.md) |

Écart absolu moyen sur les canaux RVB de **15,894 sur 255**, comme dans la capture P6. Les positions ont été mesurées par les boîtes DOM. [Capture Linux](../design/evidence-p61/atelier-1672x941-sombre.png) · [Côte à côte](../design/evidence-p61/cote-a-cote-1x.png) · [Superposition 50 %](../design/evidence-p61/superposition-50.png) · [Carte](../design/evidence-p61/carte-ecarts.png) · [Écarts](../design/evidence-p61/ecarts.json) · [Géométrie](../design/evidence-p61/geometrie.json)

Formats testés sous Linux Chromium 156 : 1672 × 941, 1920 × 1080, 1440 × 900, 1366 × 768, 1024 × 768, 390 × 844 et 360 × 800. Les contrôles comportent le débordement horizontal, l’éditeur, les commandes et le contraste. [1920 × 1080](../design/evidence-p61/atelier-1920x1080-sombre.png) · [Mobile](../design/evidence-p61/atelier-390x844-sombre.png) · [Clair](../design/evidence-p61/atelier-1672x941-clair.png) · [Projecteur](../design/evidence-p61/atelier-1672x941-projecteur.png)

## Compagnon

Les deux calques séparés sont des découpes du dessin approuvé. Le regard et le geste de la main se déplacent légèrement selon l’état du dialogue. Le cadrage, les lunettes, le visage et la veste restent ancrés dans la scène. Les états déclenchés par un dialogue réel sont l’accueil, le repos, l’écoute, la réflexion, l’explication, la validation d’une réponse correcte et l’encouragement. Le test vérifie une transformation du geste à mi-animation, puis l’absence de mouvement avec `prefers-reduced-motion`. [Registre](../design/ASSET_REGISTER.md) · [Transitions observées](../design/evidence-p61/compagnon-transitions.json) · [Geste d’explication](../design/evidence-p61/compagnon-explication.png)

```text
python tests/p61_browser.py --output results/p61
python design/compare.py --capture results/p61/atelier-1672x941-sombre.png --output results/p61
```

Les captures Linux documentent la composition. La mise à l’échelle Windows du système à 100 %, 125 % et 150 % relève de la recette Windows.
