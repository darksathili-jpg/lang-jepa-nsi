# P6 · Recette visuelle de l’atelier

Le travail part de `main` à `ec62e83f0c4e2872f7ae7ed528d75afeabf6eee6`. Le dépôt distant ne contenait aucun commit postérieur lors de l’audit. La sauvegarde Git locale a été vérifiée dans `/tmp/lang-jepa-nsi-avant-p6.bundle`, SHA-256 `6a1463073ae310d659411c4b6d4824e9dfc8949143844ee4ace381e6c9c8f6d5`. Les deux images du ZIP ont été vérifiées. La référence publique est la maquette approuvée. [Registre des actifs](../design/ASSET_REGISTER.md)

La mise en œuvre est identifiée par le commit [`e243946`](https://github.com/darksathili-jpg/lang-jepa-nsi/commit/e243946).

## Preuves à 1672 × 941

| Preuve | Cadrage |
| --- | --- |
| [Maquette approuvée](../design/reference/REFERENCE_VISUELLE_VALIDEE.png) | PNG fourni, 1672 × 941 |
| [Atelier avant P6](../design/evidence/avant-p6.png) | Chromium, mode sombre, 1672 × 941 |
| [Atelier P6](../design/evidence/atelier-1672x941-sombre.png) | Chromium, mode sombre, 1672 × 941 |
| [Côte à côte](../design/evidence/cote-a-cote.png) · [Côte à côte à l’échelle 1](../design/evidence/cote-a-cote-1x.png) | Maquette à gauche, capture à droite, sans recadrage. Aperçu dans une toile de 1672 × 941 et paire grandeur réelle de 3344 × 941. |
| [Superposition à 50 %](../design/evidence/superposition-50.png) | Mélange des deux PNG, 1672 × 941 |
| [Carte des écarts](../design/evidence/carte-ecarts.png) | 1672 × 941, noir pour l’identité et rouge à jaune pour l’écart croissant |
| [Coordonnées et mesures](../design/evidence/geometrie.json) · [Écarts par zone](../design/evidence/ecarts.json) | Boîtes DOM mesurées et coordonnées de référence en pixels et en fractions du viewport |

Chromium 156.0.8078.79 sous Linux x64, zoom 100 %, un pixel de périphérique par pixel CSS, capture à l’origine de la fenêtre. La comparaison couvre tous les pixels. Les textes changent avec l’énoncé, le dialogue, le niveau et la disponibilité des moteurs. Aucun masque n’a été appliqué. L’image de référence montre un exemple pédagogique et deux moteurs affichés prêts. La capture de base montre le parcours guidé avec les états observés sans modèles installés. Le dialogue statique de démonstration porte la mention « Exemple de dialogue » et disparaît dès le premier échange.

## Inspection et corrections

| Zone | Relevé et décision |
| --- | --- |
| En-tête | Barre de 86 px et navigation répartie sur une ligne au grand format. Les pictogrammes redessinés et les contrôles de thème, de plein écran et de paramètres ont des libellés accessibles. Le bouton projecteur est supplémentaire. |
| Scène et personnage | Extrait sans perte à sa place, avec le même cadrage. La silhouette, les cheveux poivre et sel, les lunettes et la veste brune ont été comparés au PNG. La zone de texte a été resserrée après inspection pour préserver la chevelure et le contour de la bulle. La formulation française identifie un professeur virtuel. |
| Éditeur Python | Bord violet, gouttière, numéros et coloration alignés. La version canonique du parcours emploie `valeur` comme variable de boucle. Le bleu des boutons a été assombri pour le contraste de leur libellé. |
| Exercice et progression | Panneaux, titres et cinq jalons à leurs positions. Le sélecteur d’exercice et le texte éditable remplacent les éléments peints de la maquette. L’état d’exemple est signalé, puis remplacé par les acquis retournés par le serveur. Les intitulés mobiles ont été redimensionnés pour éviter les collisions. |
| Dialogue | Colonne, avatars et ancrage de la zone de réponse alignés. La graisse et les retours à la ligne peuvent varier avec la police et les échanges. Le niveau par défaut est Première. Le modèle est crédité uniquement sur les formulations affichées. |
| Colonne droite | Les trois panneaux conservent leur ordre. Les retouches de hauteur ont remonté la carte neuronale à son repère. Les états moteurs, le choix de mode et le verdict P5 prennent la place des libellés hypothétiques. |
| Thèmes et formats réduits | Clair et projecteur utilisent des panneaux sur fond clair. Le projecteur agrandit le texte. À 1024 px les commandes de l’éditeur restent groupées et les cartes moteurs passent sous les deux colonnes. Sur mobile les panneaux s’empilent, le dialogue reste défilable et la bulle d’accueil est abrégée. |

La composition à 1672 × 941 emploie la police système. De petits écarts de glyphes, de pictogrammes et de dégradés subsistent entre les deux images. Les écarts de texte indiqués dans le tableau sont liés à la sécurité, à la lisibilité, à l’origine du personnage ou à l’état réel du logiciel.

Les bords des panneaux principaux sont alignés à environ un pixel près. Dans la zone du personnage définie de `(22, 175)` à `(515, 610)`, les pixels coïncident. L’écart moyen par canal RVB, sur 255, passe de **51,00 avant P6** à **15,89**. Les plus grands écarts moyens se trouvent dans les blocs de texte des moteurs et des explications, dont le contenu a été corrigé pour refléter P5. [Écarts chiffrés et coordonnées](../design/evidence/ecarts.json)

## Captures complémentaires

- [1440 × 900](../design/evidence/atelier-1440x900-sombre.png) · [1366 × 768](../design/evidence/atelier-1366x768-sombre.png)
- [Tablette 1024 × 768](../design/evidence/atelier-1024x768-sombre.png) · [Mobile 390 × 844](../design/evidence/atelier-390x844-sombre.png) · [Mobile 360 × 800](../design/evidence/atelier-360x800-sombre.png)
- [Clair](../design/evidence/atelier-1672x941-clair.png) · [Projecteur](../design/evidence/atelier-1672x941-projecteur.png)
- [Hybride expérimental avec les moteurs réels](../design/evidence/hybride-reel.png)

Les vues sur tablette, mobile et en mode projecteur montrent la page entière au viewport indiqué.

## Contrôles

| Porte | Statut | Preuve et limite |
| --- | --- | --- |
| G0 · Actifs | PASS | `sha256sum -c MANIFEST_SHA256.txt` sur le ZIP extrait. Photo source conservée dans l’espace privé. |
| G1 · Structure | PASS | Mesures DOM à 1672 × 941 et inspection de la capture. |
| G2 · Fidélité | PASS | Comparaison côte à côte, superposition et carte des écarts sans masque. Inspection de la silhouette, des bords de la bulle et des zones corrigées. |
| G3 · Fonctionnement | PASS | Navigation, clavier, édition, copie, réinitialisations, joignabilité locale des fichiers, envoi, panneau enseignant, niveaux, plein écran et erreur moteur. **Exécuter** indique l’indisponibilité de l’exécution Python. |
| G4 · Personnage | PASS | Dessin extrait et conservé. Bulle et état d’activité en CSS, animation légère de l’hologramme et test de `prefers-reduced-motion`. Mention d’indépendance visible. |
| G5 · Responsive | PASS | Six tailles × trois thèmes, contrôle du débordement, de la largeur de l’éditeur, des commandes et du contraste. |
| G6 · Transparence | PASS | Parcours guidé par défaut, états passifs et réels distingués. Badge hybride uniquement si le profil est sélectionné et si les deux moteurs sont prêts. Attribution au tour d’après la génération affichée et le reclassement enregistré. |
| G7 · Recette | PASS Linux | 44 tests Python, syntaxe JavaScript, Chromium 156, traces et commandes ci-dessous. Recette Windows à effectuer. |

Recette automatisée et inspection visuelle par Codex le 22 novembre 2026. Le test des moteurs sous Linux a isolé le réseau dans un espace ne contenant que la boucle locale. Les photographies privées, les modèles et les poids sont restés hors du dépôt.

Le rejeu de `maximum(tab)` a passé **14 tours** en conversation locale avec SmolLM3, puis **30 tours** avec le JEPA P5 et SmolLM3. Le parcours hybride a affiché quatre indices de SmolLM3 et quatre reclassements enregistrés. Le laboratoire affiche **Bénéfice JEPA non démontré**. [Trace conversation locale](../design/evidence/maximum-reel.jsonl) · [Trace hybride](../design/evidence/hybride-30-tours.jsonl)

## Reproduction hors ligne

Préparer Python 3.12, Playwright et Chromium, ainsi que Pillow et NumPy pour la comparaison. Le lancement ordinaire utilise simplement `scripts\tutor.cmd` sous Windows. La recette avec moteurs utilise les ressources locales de P5. [Guide de préparation](P5_PERFORMANCES_WINDOWS.md)

```bash
python -m unittest discover -s tests -v
node --check app/tutor.js
python tests/p6_browser.py --output results/p6 --assets models/tutor --weights results/p5/fixe-24-17
python design/compare.py --capture results/p6/atelier-1672x941-sombre.png --output results/p6
python tests/guided_browser.py
python tests/browser_smoke.py
python tests/tutor_browser.py
python tests/socratic_browser.py --assets models/tutor --output results/p6/maximum-reel.jsonl
python tests/hybrid_browser.py --assets models/tutor --weights results/p5/fixe-24-17 --dialogue maximum-30 --output results/p6/hybride-30-tours.jsonl
```

Sans les deux chemins de poids, `tests/p6_browser.py` exécute les contrôles d’interface et omet la capture hybride. Ajouter `--chromium CHEMIN` pour utiliser un Chromium déjà installé.

**Recette Windows à effectuer.** Aucun poste Windows x64 de 16 Go n’était disponible pour mesurer le lancement, les polices, le rendu projecteur et la fluidité sur la cible.
