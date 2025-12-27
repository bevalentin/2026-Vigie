#!/bin/bash

# Script de lancement pour Vigie (Linux/WSL)

# Vérifier si uv est installé
if ! command -v uv &> /dev/null
then
    echo "Erreur : 'uv' n'est pas installé."
    echo "Installez-le avec : curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Synchroniser les dépendances si nécessaire
echo "Vérification des dépendances..."
uv sync

# Lancer l'application
echo "Lancement de Vigie..."
uv run python -m app.main
