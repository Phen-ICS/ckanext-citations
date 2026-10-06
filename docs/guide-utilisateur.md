# Guide utilisateur : le bloc « FAIR & Impact »

Written for: chercheurs et curateurs FAIR3R qui consultent ou éditent un dataset.

Ce guide explique les chiffres affichés sur la page d'un dataset dans le bloc
**FAIR & Impact**, en bas de la page, et comment les lire.

## Quand le bloc apparaît

Le bloc est visible sur tout dataset public et actif. Pour les citations, il faut
en plus que le dataset ait un **DOI publié**. Sans DOI publié, le bloc indique
« Pas encore vérifié » : les citations ne sont pas suivies.

## Complétude

Une barre colorée indique à quel point les métadonnées du dataset sont renseignées.

| Couleur | Score |
|---|---|
| Rouge | moins de 50 % |
| Orange | de 50 % à 79 % |
| Vert | 80 % ou plus |

Le score est une moyenne pondérée des champs qui s'appliquent au dataset :

- les champs **obligatoires** comptent double, les autres comptent une fois ;
- les champs de base (titre, description, tags, licence) comptent aussi ;
- un champ masqué par une autre réponse (par exemple « transgène » quand la case
  « cross-species » n'est pas cochée) n'est pas compté.

Une case à cocher non cochée n'est pas un champ manquant : ne pas la cocher est une
réponse valide.

La liste « Champs manquants » indique, par section, ce qui reste à remplir.
Les champs obligatoires sont marqués d'une étoile (*).

## Citations

Le nombre de **citations** est le nombre d'œuvres qui citent le DOI du dataset,
d'après OpenAlex. Quand OpenAlex ne connaît pas encore le DOI, le nombre vient de
DataCite Event Data.

La liste **Citing works** donne les œuvres citantes, avec titre, auteurs, année,
revue et lien DOI.

## Indice de disruption

Il va de **−1** à **+1**, selon la méthode de Wu, Wang & Evans (2019) :

- proche de **+1** : les œuvres qui citent le dataset tendent à le remplacer ;
- proche de **−1** : elles s'appuient aussi sur les mêmes références que le dataset.

Il se calcule à partir des références du dataset (ses liens « References » ou
« Cites » dans les métadonnées) et des œuvres qui citent ces références.

**Limite à connaître** : pour rester rapide, le calcul ne prend qu'un nombre limité
de références et de citants par référence. Quand les références sont très citées,
l'indice reste donc proche de 0. Il sert à comparer des datasets entre eux, pas à
donner une valeur absolue.

Sans citation, l'indice n'est pas calculé (« pas assez de données pour l'instant »).

## S-index

Le S-index d'un auteur est le nombre de **chercheurs distincts** qui ont écrit au
moins une œuvre citant un des datasets FAIR3R de cet auteur. Les chercheurs sont
identifiés par leur ORCID, ou par leur nom quand ils n'ont pas d'ORCID.

- Le score est **cumulatif** : une personne n'est jamais retirée, même si sa
  citation disparaît plus tard.
- Quand un dataset a plusieurs co-auteurs avec ORCID, le bloc affiche le S-index
  le plus élevé, et le détail par co-auteur est dépliable.

Le S-index mesure l'étendue du réseau de chercheurs atteints, pas la qualité des
citations.

## Quand les chiffres changent

Les citations et les indices sont recalculés une fois par semaine (dimanche, en
nuit). Un dataset est recalculé seulement s'il n'a pas été vérifié depuis 7 jours.
La date de dernière vérification est affichée à côté du nombre de citations.
