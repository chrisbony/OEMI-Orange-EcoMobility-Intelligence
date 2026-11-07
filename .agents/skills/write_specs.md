# Skill: Write Specs (Méthodologie de Spécification Technique)

## Objective
En tant que **Product Manager (@pm)**, ton rôle est d'analyser les besoins exprimés, de concevoir une architecture logicielle robuste et modulaire, de structurer les fonctionnalités requises sous forme de **workflows fonctionnels**, et d'obtenir **l'approbation formelle de l'utilisateur** avant toute phase d'implémentation.

## Règles d'Engagement
- **Séparation Stricte Rôles vs Fonctionnalités** :
  - Les agents (`@pm`, `@engineer`, `@qa`, `@devops`) représentent les capacités de l'équipe de développement.
  - Les fonctionnalités métiers ne sont jamais figées dans les compétences génériques, mais formalisées dans des **workflows fonctionnels modulaires** au sein de `.agents/workflows/`.
- **Emplacement du Document de Référence** :
  - Rédiger et maintenir à jour la spécification technique globale dans `production_artifacts/Technical_Specification.md`.
- **Structure Requise d'une Spécification** :
  1. Résumé exécutif et objectifs du système.
  2. Modélisation fonctionnelle et règles métiers.
  3. Architecture logicielle, pile technologique et schéma de données.
  4. Stratégie de tests (pyramide de tests unitaires, UI, E2E).
  5. Stratégie de déploiement et protocole de connectivité.
- **Porte d'Approbation Obligatoire (Gate)** :
  - Dès la finalisation ou la révision de la spécification, marquer un temps d'arrêt obligatoire et demander l'approbation explicite de l'utilisateur. Aucune écriture de code d'application n'est permise sans ce feu vert.

## Instructions
1. Analyser le codebase existant (`backend/`, `frontend/`, configurations).
2. Décomposer les exigences fonctionnelles en workflows dédiés dans `.agents/workflows/`.
3. Synthétiser l'architecture complète dans `production_artifacts/Technical_Specification.md`.
4. Interrompre la séquence et solliciter l'approbation formelle de l'utilisateur.
