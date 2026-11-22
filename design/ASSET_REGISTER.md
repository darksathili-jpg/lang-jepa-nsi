# P6 · Registre des actifs

Les sept empreintes ont été contrôlées avec `sha256sum -c MANIFEST_SHA256.txt` depuis la racine du ZIP extrait. Le manifeste conservé décrit la structure du paquet original. La maquette seule est conservée comme référence publique. [Manifeste original](reference/MANIFEST_SHA256.txt)

| Actif | Dimensions | Provenance et usage |
| --- | --- | --- |
| `REFERENCE_VISUELLE_VALIDEE.png` | 1672 × 941 | Image générée pour la mission, approuvée puis fournie pour reproduction et comparaison. Publiée ici comme preuve de la mission. SHA-256 `29a5bd4c27654317a7926797f40c818e871f03017e00ce08a56d6e463d4f517d`. |
| `REFERENCE_PORTRAIT_SOURCE.png` | 1884 × 2048 | Photographie de référence privée. SHA-256 `e51f2751d782b472e90cedfa374eceb49251189593cdcc15baba57c76ec79f45`. Les droits de redistribution publique ne sont pas établis. |
| `scene-bd.webp` | 881 × 525 | Extrait sans perte de la maquette aux coordonnées x=0, y=86. Seules les lignes de texte de la bulle sont recouvertes. Le contour, les cheveux, les lunettes, le visage, la veste, la main et le décor sont conservés. La bulle HTML ne présente pas le personnage comme la personne réelle. |
| `portrait-bd.webp` | 47 × 51 | Portrait de bande dessinée extrait de la conversation dessinée de la maquette. Sert aux avatars du professeur avec un contour CSS. |
| `illustration-jepa.webp` | 239 × 174 | Illustration neuronale extraite de la colonne droite. Le texte et le lien de la carte sont en HTML. |
| `marque-reseau.webp` | 76 × 76 | Symbole réseau extrait du coin supérieur gauche. L’opacité de fond est retirée. Le nom et le sous-titre restent en HTML. |
| `controls.svg` | Vue logique 24 × 24 par pictogramme | Formes vectorielles dessinées pour le projet. Les noms accessibles et les actions résident dans les contrôles HTML. |
| Typographie | — | Arial et Consolas si installées. Liberation Sans et Liberation Mono comme substituts disponibles sur Linux, puis familles génériques. Aucun fichier de police ne circule et aucun CDN n’est appelé. |

Les actifs dérivés servent uniquement la reproduction demandée. La mention sur l’origine du personnage et l’absence d’affiliation est visible dans l’atelier. Le laboratoire et le parcours ne distribuent aucun poids. [Extraction reproductible](extract_assets.py)
