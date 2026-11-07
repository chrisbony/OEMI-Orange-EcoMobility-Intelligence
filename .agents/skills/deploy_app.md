# Skill: Deploy App & Verify Connectivity (Méthodologie de Déploiement Continu)

## Objective
En tant que **DevOps & Déployeur Master (@devops)**, orchestrer le déploiement continu des applications (Backend et Frontend), administrer les environnements d'infrastructure et exécuter systématiquement la suite des tests de connectivité pré et post-déploiement.

## Gestion des Identifiants & Secrets
- Récupérer les jetons et identifiants de déploiement depuis le fichier de configuration sécurisé `link_repo.txt` ou l'environnement système (clés de plateforme cloud, base de données et gestionnaire de versions).
- Ne jamais coder d'identifiants ou d'URLs en dur dans la compétence.

## Protocole Universel des 4 Tests de Connectivité
À chaque déploiement (en local, staging ou production), exécuter la séquence des 4 tests de connectivité :

1. **Test 1 : Connectivité Base de Données**
   - Validation du handshake réseau et de la couche SSL vers le cluster de base de données.
   - Appel probe sur l'API de supervision/monitoring de la base de données.
   - Exécution d'une requête probe SQL (`SELECT 1;`) via le pool de sessions pour valider la réactivité.
2. **Test 2 : Santé & Disponibilité du Backend**
   - Requête HTTP vers l'endpoint probe de santé (`/health`, `/ready` ou documentation de l'API).
   - Validation du code de statut HTTP 200 et mesure de la latence de réponse.
3. **Test 3 : Connectivité de l'Ensemble des Endpoints API**
   - Découverte et interrogation systématique de l'ensemble des routes déclarées dans le routeur de l'application.
   - Vérification des codes de retour HTTP attendus (succès 200/201 pour les routes publiques, 401 Unauthorized pour les routes protégées par authentification).
4. **Test 4 : Communication Frontend <-> Backend**
   - Requête preflight CORS (`OPTIONS`) simulant l'origine du domaine frontend.
   - Contrôle des en-têtes `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods` et `Access-Control-Allow-Headers`.
   - Validation de la résolution correcte de l'URL cible de l'API côté client et de la transmission des jetons d'autorisation.

## Instructions
1. **Tests Pré-Déploiement** : Lancer la suite des tests de connectivité sur l'environnement de build/staging.
2. **Exécution du Déploiement** : Déployer les artefacts sur la plateforme cloud cible et synchroniser les dépôts de code.
3. **Tests Post-Déploiement** : Re-jouer l'ensemble des 4 tests de connectivité sur les URLs publiques de production.
4. **Gestion des Incidents** : En cas d'échec d'un test post-déploiement, déclencher immédiatement la boucle de retour pour correction.
5. **Rapport de Déploiement** : Fournir à l'utilisateur le récapitulatif des URLs actives et le certificat d'exécution des tests.
