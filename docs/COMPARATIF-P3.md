# Comparatif des modèles conversationnels P3

Trois candidats et leurs quantifications officielles ont été exécutés localement. Le banc commun comprend six exercices synthétiques de Première et Terminale, avec trois tours chacun, une consigne commune, le même format de sortie, un contexte de 4 096 tokens, une génération gloutonne, un lot conversationnel, deux fils CPU et aucune couche sur GPU. Les poids correspondent aux révisions du catalogue et à leurs empreintes. Aucun fine-tuning n’a été lancé. [Catalogue](../p3/models.json)

## Résultats du banc commun

Linux x86_64, AMD EPYC 9V74, quota de deux CPU et limite de 8 Gio pour l’environnement cloud. Le pic est le maximum de mémoire résidente du processus llama.cpp observé via `VmHWM`. Les chiffres excluent le navigateur, Python et les autres processus. Ils décrivent cette machine et ce profil. [Banc commun et traces](../p3/preuves/comparatif.jsonl)

| Modèle | GGUF Q4_K_M | Démarrage | Médiane / max par tour | Pic moteur | Tours affichables | Dialogues 3/3 | Objectif lexical / question ciblée |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5-1.5B-Instruct | 1,12 Go | 2,80 s | 5,85 / 8,72 s | 2,00 Gio | 15/18 | 3/6 | 12/18 · 7/18 |
| Granite 4.0 Micro | 2,10 Go | 4,96 s | 11,12 / 17,67 s | 4,08 Gio | 15/18 | 3/6 | 11/18 · 9/18 |
| SmolLM3-3B | 1,92 Go | 4,42 s | 13,16 / 20,47 s | 3,80 Gio | 16/18 | 4/6 | 12/18 · 10/18 |

Le démarrage couvre notamment le contrôle SHA-256 et le chargement initial. Les signaux lexicaux repèrent un vocabulaire attendu. Une réponse peut employer ces mots et contenir quand même un diagnostic erroné ou une question redondante. Les signaux de divulgation sont décomptés séparément du contenu des tours affichables.

## Lecture qualitative du même banc

| Candidat | Français et niveau lycéen | Python et consigne socratique |
| --- | --- | --- |
| Qwen | Réponses souvent lisibles et courtes. Répète parfois la liste des notions du cours ou la question de l’élève sans transformer son problème en prochaine action. | Propose des conclusions incohérentes dans le cas du maximum. Sur la récursivité, définit la factorielle et renvoie plusieurs fois la question initiale. Un signal de corrigé brut a été filtré. |
| Granite | Formulations compréhensibles, mais plusieurs reprises de l’énoncé ou du message de l’élève. Les questions sont plus souvent ciblées que chez Qwen selon le signal lexical. | Identifie le cas « toutes négatives » au premier tour sans fournir d’exemple concret. Sur les relances du maximum, reprend les observations et les questions de l’élève. |
| SmolLM3 | Donne souvent un indice concret sur un concept NSI et une question associée. Des maladresses et redites persistent, dont une négation erronée lors d’un essai de consolidation. | Propose précisément `[-4, -2]`, repère l’absence de cas de base et suit plusieurs exercices sur trois tours. Peut confondre absence d’initialisation d’une clé et ajout de cette clé, ou expliquer incorrectement l’échange de deux variables. |

Les trois modèles utilisent des fichiers locaux autonomes pour le tokenizer, le gabarit conversationnel et les poids. Le profil `llama.cpp` est CPU, avec `--offline`. Le runtime est distribué sous licence MIT. Les trois fiches GGUF déclarent Apache-2.0. Une redistribution éventuelle doit conserver les conditions de licence et les notices applicables. Le dépôt ne publie aucun GGUF. [Qwen officiel](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/tree/91cad51170dc346986eccefdc2dd33a9da36ead9) · [Granite officiel](https://huggingface.co/ibm-granite/granite-4.0-micro-GGUF/tree/55cded3dcb8ab9f0fdd5373f4e960ffb7fda1c61) · [SmolLM3 GGUF](https://huggingface.co/ggml-org/SmolLM3-3B-GGUF/tree/4965cb60b150737b68a0408c36aeefb65078f894) · [Licence llama.cpp](https://github.com/ggml-org/llama.cpp/blob/b12600/LICENSE)

**Choix P3.** SmolLM3-3B Q4_K_M est le modèle par défaut, pour sa capacité à produire un exemple discriminant et à soutenir davantage de dialogues complets sur le banc commun. Son pic moteur observé est inférieur à celui de Granite et sa latence est plus élevée que celle de Qwen. Le profil reste interchangeable. Le passage à un déploiement en classe dépend des mesures Windows et de l’évaluation pédagogique. [Rapport P3](RAPPORT-P3.md)
