# Diagrammes de Séquences (UML Sequence) - OEMI

Ce document détaille la chronologie des flux d'échanges entre l'utilisateur, l'interface 3D (Next.js / Three.js / shadcn/ui), le backend FastAPI, la base PostGIS et les modèles d'IA.

---

## 1. Flux de Calcul et Visualisation 3D d'une Recommandation IPET

```mermaid
sequenceDiagram
    autonumber
    actor User as Décideur Métier
    participant UI as Frontend Next.js (shadcn/ui + Three.js)
    participant API as Backend FastAPI
    participant DB as PostgreSQL / PostGIS
    participant Model as Moteur IPET & IA

    User->>UI: Sélectionne la commune (ex: Cocody) & Cas "Supermarché"
    UI->>API: GET /api/v1/zones?commune=Cocody
    API->>DB: SELECT id, nom_zone, ST_AsGeoJSON(geom) FROM zones_geographiques
    DB-->>API: Polygones géométriques des zones
    API-->>UI: GeoJSON des zones de Cocody
    
    UI->>UI: Initialisation du Canvas 3D (Three.js) & Extrusion des volumes

    User->>UI: Demande le classement IPET
    UI->>API: POST /api/v1/recommendations/score { secteur: "SUPERMARCHE", weights: default }
    API->>DB: Récupération indicateurs (Présence, Démographie RGPH 2021, POI OSM)
    DB-->>API: Données spatiales & séries temporelles
    API->>Model: Calcul IPET normalisé (0-100) & Explicabilité (Top 3 facteurs)
    Model-->>API: Scores calculés + Piliers 3D de hauteur + Facteurs SHAP
    API->>DB: Journalisation de l'évaluation dans journaux_audit
    API-->>UI: Classement des zones, hauteurs 3D & métriques
    
    UI->>UI: Rendu des colonnes 3D de potentiel sur la carte d'Abidjan
    UI->>User: Affiche la carte 3D interactive et la table de classement
```

---

## 2. Flux de Téléchargement de Rapport Décisionnel (PDF/Excel)

```mermaid
sequenceDiagram
    autonumber
    actor User as Décideur Métier
    participant UI as Frontend (shadcn/ui)
    participant API as Backend FastAPI
    participant Reporter as Moteur d'Export (ReportLab / OpenPyXL)
    participant DB as Base de Données

    User->>UI: Clique sur "Exporter le Rapport d'Implantation (PDF)"
    UI->>API: POST /api/v1/reports/export { zone_id: "cocody-angre", format: "pdf" }
    API->>DB: Vérification de l'habilitation utilisateur
    API->>Reporter: Génération du PDF structuré (Cartouche sources, IPET, facteurs, avertissements)
    Reporter-->>API: Fichier binaire PDF
    API->>DB: Enregistrement dans journaux_audit (Action: EXPORT_PDF, User, Horodatage)
    API-->>UI: Fichier PDF en flux binaire téléchargeable
    UI->>User: Téléchargement automatique du fichier OEMI_Rapport_Cocody.pdf
```
