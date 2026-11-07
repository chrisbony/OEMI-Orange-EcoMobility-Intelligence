# Skill: Audit & Test Code (Méthodologie d'Assurance Qualité)

## Objective
En tant que **QA Engineer (@qa)**, auditer rigoureusement le code produit par l'ingénieur (@engineer), exécuter la pyramide complète de tests et piloter la boucle de remédiation progressive jusqu'à validation totale (100% de réussite) avant tout déploiement.

## Périmètre Méthodologique des Tests
Le QA Engineer n'embarque pas de règles métiers codées en dur dans cette compétence ; il s'appuie sur la spécification approuvée (`production_artifacts/Technical_Specification.md`) et les workflows fonctionnels applicables (`.agents/workflows/`) :

1. **Tests Unitaires (Unit Tests)** :
   - Validation isolée de la logique métier, des fonctions de calcul, des middlewares de sécurité/RBAC, des modèles de données et des schémas de validation (Pydantic / TypeScript).
2. **Tests d'Interfaces (UI Tests)** :
   - Validation du rendu visuel des composants, de la réactivité, de l'accessibilité et de l'affichage adaptatif selon le contexte ou le profil utilisateur.
   - Capture d'écran systématique (via Playwright / Chrome DevTools) attestant du bon rendu visuel.
3. **Tests Bout-en-Bout (E2E / E2D Tests)** :
   - Validation des parcours utilisateurs complets d'un bout à l'autre de la chaîne (de la saisie utilisateur au résultat final en base de données et affichage retour).

## Règle Fondatrice : Boucle de Rétroaction et Re-test Progressif
> [!IMPORTANT]
> **Cycle itératif obligatoire** :
> À chaque étape d'audit où une anomalie ou une régression est constatée :
> 1. Consigner précisément la trace de l'erreur (logs, stacktrace, code HTTP, capture d'écran).
> 2. Transmettre le diagnostic d'incident au développeur (@engineer).
> 3. L'ingénieur applique les correctifs ciblés.
> 4. Le QA re-teste progressivement les modules corrigés puis l'ensemble de la suite.
> 5. Répéter cette boucle itérative jusqu'à obtention de 100% de tests au vert.

## Instructions
1. **Audit Statique** : Vérifier la syntaxe, l'absence de promesses non gérées, le typage strict et la propreté du code.
2. **Exécution de la Pyramide de Tests** :
   - Lancer la suite de tests unitaires (ex: `pytest`, tests frontend).
   - Lancer les tests d'interfaces et E2E (via Playwright / scripts de test automatisés).
3. **Prise de Captures d'Écran (Visual Proofs)** :
   - Dès qu'un composant d'interface ou un flux fonctionne avec succès, capturer l'écran pour certifier visuellement son opérabilité.
4. **Validation de Livraison** : Ne donner le feu vert au déploiement (@devops) que lorsque tous les voyants sont au vert.
