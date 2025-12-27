# Vigie — Agent Documentation

## Context
**Vigie** is a lightweight property management application for co-ownership (indivision), built for a small number of owners (~6) and a limited number of lots.

## Technology Stack
*   **Language**: Python 3.10+
*   **Framework**: NiceGUI (Web UI)
*   **Authentication**: Custom session-based auth using `bcrypt` and NiceGUI `app.storage.user`.
*   **Database**: SQLModel (SQLite).
*   **Precision**: `decimal.Decimal` for amounts, Rational fractions for ownership (Numerator/Denominator).

## Database Digest
*   `Owner`: Includes `password_hash` and `role` (READ, WRITE, ADMIN).
*   `Lot`, `BankAccount`, `Operation`: Standard property management entities.
*   `QuotePart`: Ownership fractions handling.
*   `Allocation`: Read-only historical record of expense distribution.

## Security
*   **Hashing**: Bcrypt.
*   **Roles**:
    *   `READ`: View only.
    *   `WRITE`: CRUD operations (typical owner).
    *   `ADMIN`: Full access + Config (future).
*   **Audit**: File-based logging in `logs/audit.log`.

## Core Principles
1.  **Exact Math**: No floating point approximations.
2.  **Time-Travel Ownership**: Ownership fractions (QuoteParts) have `start_date` and `end_date`. Operations are allocated based on the active fractions *at the date of operation*.
3.  **Traceability**: Allocations are stored as separate records at the time of creation/validation to preserve history.

## Database Schema Digest
*   **Lot**: Property unit.
*   **Owner**: Individual.
*   **QuotePart**: Link Table (Lot <-> Owner) with `numerator`/`denominator` and `dates`. Constraint: Sum(fractions) for a Lot at any T must be 1.
*   **BankAccount**: Financial account.
*   **Operation**: Transaction (Income/Expense) linked to Lot and BankAccount.
*   **Allocation**: Split of an Operation per Owner.

## Future Instructions
*   When modifying the allocation logic, ALWAYS verify the sum of parts equals the total operation amount.
*   Ensure UI components are responsive and user-friendly (using NiceGUI native components).
*   Always put comment in the code to explain the logic.
*   Always update the README.md, USER_GUIDE.md, and agents.md files accordingly when adding new features or modifying existing ones.

## Interdictions
*   **Pas de JavaScript** : Aucun code JavaScript ne doit être ajouté à cette application. Toutes les fonctionnalités doivent être implémentées en Python via NiceGUI ou des solutions serveur.
