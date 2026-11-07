# Modèle Conceptuel de Données (MCD) - Orange EcoMobility Intelligence (OEMI)

Ce document formalise les entités, associations et cardinalités pour la plateforme d'intelligence territoriale OEMI.

---

## 1. Diagramme Entité-Relation (Merise / ERD)

```mermaid
erDiagram
    ZONE_GEOGRAPHIQUE ||--o{ MOBILITE_AGREGEE : enregistre
    ZONE_GEOGRAPHIQUE ||--o| DEMOGRAPHIE : caracterisee_par
    ZONE_GEOGRAPHIQUE ||--o{ INFRASTRUCTURE_COMMERCE : contient
    ZONE_GEOGRAPHIQUE ||--o| ACCESSIBILITE_ROUTIERE : mesuree_par
    ZONE_GEOGRAPHIQUE ||--o{ PREVISION_FREQUENTATION : anticipee_par
    ZONE_GEOGRAPHIQUE ||--o{ SCORE_IPET_RECOMMANDATION : evaluee_par

    UTILISATEUR ||--o{ JOURNAL_AUDIT : genere
    SCORE_IPET_RECOMMANDATION ||--o{ JOURNAL_AUDIT : exporte_dans

    ZONE_GEOGRAPHIQUE {
        string id PK
        string nom_commune
        string nom_zone
        string type_zone
        geometry geom_polygon
        datetime date_creation
    }

    MOBILITE_AGREGEE {
        string id PK
        string zone_id FK
        date date_observation
        string plage_horaire
        float volume_presence
        float flux_entrants
        float flux_sortants
        boolean est_synthetique
        boolean seuil_k_anonymat_valide
    }

    DEMOGRAPHIE {
        string id PK
        string zone_id FK
        int annee_recensement
        int population_totale
        int nombre_menages
        float densite_hab_km2
        string source_donnees
    }

    INFRASTRUCTURE_COMMERCE {
        string id PK
        string zone_id FK
        string type_activite
        string nom_enseigne
        geometry point_geometrie
        string source_osm
    }

    ACCESSIBILITE_ROUTIERE {
        string id PK
        string zone_id FK
        float score_connectivite
        int nombre_arrets_transport
        int densite_carrefours
    }

    PREVISION_FREQUENTATION {
        string id PK
        string zone_id FK
        datetime date_horizon
        float valeur_estimee
        float borne_inferieure
        float borne_superieure
        string modele_utilise
        float metrique_wape
    }

    SCORE_IPET_RECOMMANDATION {
        string id PK
        string zone_id FK
        string secteur_cible
        float score_ipet
        int rang_classement
        json facteurs_positifs
        json facteurs_limitants
        float taux_completude
        string version_modele
        datetime date_calcul
    }

    UTILISATEUR {
        string id PK
        string email
        string role
        string hash_mot_de_passe
        datetime dernier_acces
    }

    JOURNAL_AUDIT {
        string id PK
        string utilisateur_id FK
        string action_type
        string zone_concernee
        datetime horodatage
        string metadata_export
    }
```
