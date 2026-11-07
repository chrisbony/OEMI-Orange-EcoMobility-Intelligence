# Diagrammes d'Activité (UML Activity) - Christmas Party

Ce document modélise les flux décisionnels et les algorithmes métiers de l'application, conçu par **The System Designer & Modeler (@designer)**.

---

## 1. Flux d'Activité : Cycle de Contrôle d'Accès & Cloisonnement Multi-Tenant

```mermaid
flowchart TD
    REQ["Requête API entrante"] --> AUTH{"Jeton JWT valide ?"}
    AUTH -- "Non" --> E401["HTTP 401 Unauthorized"]
    AUTH -- "Oui" --> IDENT["Identification Utilisateur & Rôle"]

    IDENT --> ADMIN_CHECK{"Rôle == ADMIN ?"}
    ADMIN_CHECK -- "Oui" --> ALLOW_ALL["Accès Global Accorde (Toutes équipes / Toutes tables)"]

    ADMIN_CHECK -- "Non" --> SCOPE{"Ressource demandée dans son périmètre d'équipe ?"}
    SCOPE -- "Non (Autre équipe)" --> E403["HTTP 403 Forbidden (Violation isolation équipe)"]
    SCOPE -- "Oui" --> ROLE_OP{"Opération permise pour ce rôle ?"}

    ROLE_OP -- "Leader : Modifier/Supprimer membre" --> E403_OP["HTTP 403 Forbidden (Réservé au Super Leader / Admin)"]
    ROLE_OP -- "Leader : Inscrire membre / CRUD paiement équipe" --> EXEC["Exécution Requête avec filtre team_id"]
    ROLE_OP -- "Super Leader : CRUD membre / Valider paiement" --> EXEC
    ROLE_OP -- "Bloomer : Mon profil / Ma photo / Mon QR / Ma déclaration" --> EXEC

    EXEC --> DB_SYNC["Persistance Neon PostgreSQL"]
    DB_SYNC --> RES200["HTTP 200/201 Success"]
```

---

## 2. Flux d'Activité : Parcours du Didacticiel Interactif Onboarding

```mermaid
flowchart TD
    LOGIN["Connexion réussie de l'utilisateur"] --> FETCH_PROFILE["Chargement du profil utilisateur & rôle"]
    FETCH_PROFILE --> CHECK_TUTORIAL{"tutorial_completed == true ?"}

    CHECK_TUTORIAL -- "Oui" --> DASHBOARD["Affichage Direct du Tableau de Bord"]
    CHECK_TUTORIAL -- "Non" --> START_TOUR["Démarrage Didacticiel Guidé"]

    START_TOUR --> SELECT_STEPS["Sélection des étapes selon le rôle (Admin, Super Leader, Leader, Bloomer)"]
    SELECT_STEPS --> STEP_DISPLAY["Surbrillance de l'élément cible & affichage Popover"]

    STEP_DISPLAY --> ACTION{"Action Utilisateur"}
    ACTION -- "Bouton Suivant" --> NEXT_STEP{"Dernière étape atteinte ?"}
    NEXT_STEP -- "Non" --> STEP_DISPLAY
    NEXT_STEP -- "Oui" --> COMPLETE["Marquer tutorial_completed = true"]

    ACTION -- "Bouton Passer" --> COMPLETE

    COMPLETE --> SAVE_LOCAL["Sauvegarde dans localStorage"]
    SAVE_LOCAL --> SAVE_API["PATCH /api/users/me (tutorial_completed: true)"]
    SAVE_API --> DASHBOARD
```
