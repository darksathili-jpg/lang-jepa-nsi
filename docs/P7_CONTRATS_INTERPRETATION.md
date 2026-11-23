# P7 · Contrats d’interprétation

| Contrat `schema = 1` | Champs principaux |
| --- | --- |
| Message interprété | Liste d’intentions, entrées d’essai, assertions et rôles, ambiguïtés, notion demandée, provenance de lecture. Une demande et des preuves distinctes peuvent coexister. |
| Assertion | Rôle `prediction`, `observation` ou `resultat_attendu`, valeur typée et extrait. Les rôles restent distincts dans l’état serveur. |
| Essai | Entrée, auteur, précondition, attendu mathématique, preuve statique, prédiction, déclaration, résultat exécuté, empreinte AST de la version et niveau de preuve. `execute` vaut `null`. |
| Proposition LLM | Objet JSON de clés exactes `schema`, `intention`, `citation`. Quatre intentions admissibles et abstention. La citation exacte doit fournir un indice textuel indépendant. |
| État de progression | Objectif, acquis justifiés, difficultés, essai actif et précédents, relances, besoin de précision et décision expérimentale optionnelle. |

La lecture couvre les demandes d’explication, de définition, d’indice ou de corrigé, l’incompréhension, le changement de notion, le test, la prédiction, l’observation, le résultat attendu, la justification et la proposition de correction. Des phrases ambiguës déclenchent une clarification ou une abstention. Les réponses courtes dépendent de la question et du numéro de tour mémorisés par le serveur. Il conserve la différence entre une réponse à une condition et une affirmation concernant l’entier `m`.

Un appel de test doit désigner la fonction de l’exercice avec un seul argument littéral. Les formes acceptées sont l’entier signé d’amplitude au plus 1000 ou une liste littérale d’au plus 20 entiers ou chaînes selon la spécification. Les chaînes admises comptent de 1 à 28 caractères. Les appels imbriqués, les booléens entendus comme entiers, les expressions dynamiques et les appels composés sont refusés. `ast.parse` sert au décodage de syntaxe. Des contrôles de taille, de profondeur et de nœuds bornent la lecture.

Exemple avec `maximum([-3, -4, -1])` sur la forme initiale. L’entrée devient l’essai actif, l’attendu mathématique vaut `-1` et la valeur déduite de la forme reconnue vaut `0`. « Je pense que ça renvoie 0 » renseigne la prédiction. « J’obtiens 0 » renseigne la déclaration sur cette version. `execute` reste nul dans les trois tours.

La qualification couvre des formes exactes d’accumulation, de décrément, d’accès de dictionnaire et de récursion arithmétique. Le système s’abstient de donner une sortie statique si la forme n’est pas reconnue. Les fautes de langue et les formulations absentes des critères restent des sources d’erreur mesurées. [Contrats Python](../pedagogy/cases.py) · [Lecture du message](../pedagogy/interpretation.py)
