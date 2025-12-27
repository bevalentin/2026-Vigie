# Guide Utilisateur - Vigie

## Introduction
Vigie permet de gérer la comptabilité d'une indivision immobilière.

## Initialisation
1.  **Créer les Lots** : Définissez les appartements ou locaux.
2.  **Créer les Propriétaires** : Ajoutez les membres de l'indivision.
3.  **Définir les Quote-Parts** : Pour chaque lot, indiquez les parts de chaque propriétaire. La somme doit faire 1 (ex: 1/3 chacun pour 3 propriétaires).
    *   *Note*: Les parts ont une date de début. En cas de vente, clôturez les anciennes parts (date de fin) et créez-en de nouvelles.

## Comptes Bancaires
La gestion des comptes se fait dans l'onglet "Configuration". Vous pouvez ajouter vos différents comptes bancaires (Compte courant, Livret...).

## Saisie des Opérations
Allez dans le "Journal".
1.  Cliquez sur "+" pour ajouter une entrée (recette) ou une sortie (dépense).
2.  Sélectionnez le Lot, le Compte Bancaire, la Date, et le Montant.
3.  Le système calcule automatiquement la part de chacun.

## Distributions aux Propriétaires (Reversements)
Lors d'une distribution d'argent à un ou plusieurs membres de l'indivision :
1. **Créer l'Opération** : Saisissez une nouvelle **SORTIE**.
2. **Catégorie** : Sélectionnez `REVERSEMENT`.
3. **Lot** (Important) :
   - Si c'est une distribution générale (selon les tantièmes) : Sélectionnez le **Lot** concerné.
   - Si c'est un versement spécifique à une personne (hors lot) : Laissez le champ **Lot** vide.
4. **Répartition / Bénéficiaire** :
   - Si le champ **Lot** est vide, précisez le **Propriétaire Bénéficiaire** dans le sélecteur dédié.
   - Si un **Lot** est sélectionné, la répartition se fera automatiquement selon les parts de chacun.
5. **Impact** : Le solde individuel du propriétaire sera réduit du montant versé dans la "Matrice de Répartition".

## Rapports
*   **Tableau de bord** : Vue globale de l'année.
*   **Matrice de Répartition** : Détail des soldes de chaque propriétaire après charges et distributions.
*   **Décomptes** : Générez les fichiers pour l'assemblée générale.
