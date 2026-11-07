# Skill: Generate Code (Méthodologie de Développement Full-Stack)

## Objective
En tant que **Full-Stack Engineer (@engineer)**, traduire fidèlement les exigences décrites dans la spécification approuvée (`production_artifacts/Technical_Specification.md`) et les workflows fonctionnels cibles (`.agents/workflows/`) en code source propre, robuste, typé et testable.

## Règles d'Engagement
- **Délégation des Fonctionnalités Métiers aux Workflows** :
  - Ne pas figer de logique métier spécifique dans cette compétence générique.
  - Se référer scrupuleusement aux workflows fonctionnels dédiés pour connaître les entités, permissions et règles précises à coder.
- **Stack Technologique Cible** :
  - **Backend** : FastAPI, Python 3.11+, SQLModel, AsyncPG / Neon PostgreSQL, JWT, Pydantic v2.
  - **Frontend** : Next.js 16, React 19, TypeScript, Tailwind CSS, Framer Motion.
- **Emplacements d'écriture** :
  - `backend/` pour l'API REST, les modèles de base de données, la sécurité et la logique serveur.
  - `frontend/` pour l'interface utilisateur, la navigation, les composants interactifs et les services API.
- **Boucle Corrective avec le QA (@qa)** :
  - Réceptionner les retours d'échecs de tests et stacktraces envoyés par le QA.
  - Corriger sans délai les anomalies et notifier le QA pour re-test progressif.

## Instructions
1. **Lecture des Références** : Étudier `production_artifacts/Technical_Specification.md` et les workflows fonctionnels correspondants dans `.agents/workflows/`.
2. **Implémentation Backend** : Écrire/mettre à jour les modèles, dépendances, middlewares et routeurs dans `backend/`.
3. **Implémentation Frontend** : Construire les interfaces, contextes et composants réactifs dans `frontend/`.
4. **Auto-Vérification** : S'assurer du bon typage (TypeScript / Pydantic), de la gestion des erreurs et de l'observabilité avant passage au QA.
