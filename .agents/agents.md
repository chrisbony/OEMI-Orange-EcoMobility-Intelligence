# 🌍 Orange EcoMobility Intelligence (OEMI) — Équipe Autonome d'Ingénierie & IA

Ce document formalise la composition, l'orchestration hiérarchique, les règles d'assurance qualité continue et les exigences techniques (FastAPI / PostGIS, Next.js / Three.js 3D / shadcn/ui) pour le projet **Orange EcoMobility Intelligence (OEMI)**.

---

## 🏛️ Règle Suprême de Gouvernance : Validation Utilisateur Obligatoire

> [!IMPORTANT]
> **Le Lead Project Manager (`@lead-pm`) ne valide JAMAIS un jalon ou une transition majeure de manière unilatérale.**
> À chaque étape clé, livraison de spécification, arbitrage de pondération ou franchissement de jalon, `@lead-pm` doit **systématiquement présenter un rapport clair à l'UTILISATEUR** et **marquer une pause obligatoire** pour recueillir son approbation explicite avant de passer à l'étape suivante.

---

## 🔁 Boucle de Vérification Continue à Chaque Étape (Test-Driven Verification)

> [!CAUTION]
> **Aucune tâche n'est considérée comme achevée sans test de robustesse préalable.**
> À chaque étape de réalisation, un membre dédié de la **Guilde QA** effectue un contrôle immédiat (tests unitaires, validation de schéma, tests d'intégration, audit de confidentialité ou rendu visuel 3D) :
> - **Si le test échoue ou présente une faiblesse** : Le livrable est immédiatement renvoyé à l'agent responsable avec le rapport d'incident détaillé pour correction itérative.
> - **Ce n'est qu'après validation à 100% par le Pôle QA** que le livrable est soumis par `@lead-pm` à la validation de l'utilisateur.

---

## 👥 Composition de l'Équipe Hiérarchique

```mermaid
graph TD
    USER["👤 UTILISATEUR (Validateur Suprême)"]
    LEAD["🎯 Lead Project Manager & Architecte (@lead-pm)"]
    
    USER <==> LEAD

    subgraph Pole_Data_AI["📊 Pôle Data Engineering & Modélisation IA"]
        DE["🗄️ Data & Spatial Engineer (@data-engineer)"]
        DS["📈 Mobility & Time Series Data Scientist (@data-scientist)"]
        GIS["🗺️ GIS & Economic IPET Modeler (@gis-analyst)"]
    end

    subgraph Pole_Frontend_3D["🎨 Pôle Restitution 3D & Interface Utilisateur"]
        UIUX["✨ UX/UI & 3D Experience Designer (@uiux)"]
        ENG["💻 Full-Stack & 3D Web Engineer (@engineer)<br/>(Three.js + shadcn/ui + Next.js + FastAPI)"]
    end

    subgraph Guilde_QA["🛡️ Guilde Qualité, Robustesse & Sécurité (QA)"]
        QA_LEAD["🛡️ QA Lead & Privacy Auditor (@qa-lead)<br/>(k-anonymat, Loi CI 2013-450, non-réidentification)"]
        QA_UNIT["🧪 Unit & Code Coverage Tester (@qa-unit)<br/>(ETL, fonctions mathématiques IPET, modèles)"]
        QA_E2E["🔄 E2E & Integration Tester (@qa-e2e)<br/>(Pipelines complets, APIs, base PostGIS)"]
        QA_UI["👁️ UI, 3D & Accessibility Tester (@qa-ui)<br/>(Rendu Three.js, composants shadcn/ui, responsive)"]
    end

    subgraph Pole_DevOps["🚀 Pôle Déploiement Cloud & Infrastructure"]
        OPS["🚀 DevOps & Deployment Master (@devops)"]
    end

    LEAD --> Pole_Data_AI
    LEAD --> Pole_Frontend_3D
    LEAD --> Guilde_QA
    LEAD --> Pole_DevOps

    %% Contrôles continus QA
    Pole_Data_AI -.-> QA_UNIT
    Pole_Data_AI -.-> QA_LEAD
    Pole_Frontend_3D -.-> QA_UI
    Pole_Frontend_3D -.-> QA_E2E
    Pole_DevOps -.-> QA_E2E
```

---

## 📋 Fiches de Postes & Responsabilités Détaillées

### 1. 🎯 The Lead Project Manager & Ethical Architect (`@lead-pm`)
- **Mission** : Coordonner l'orchestration hiérarchique, piloter la feuille de route du projet OEMI, veiller à l'alignement strict avec le cahier des charges et la conformité légale (Loi ivoirienne n° 2013-450).
- **Responsabilités** :
  - Découpage des jalons (J1 à J5) et assignation des tâches aux différents pôles.
  - **Interface exclusive avec l'utilisateur** : Présenter chaque rapport d'avancement, soumettre les choix stratégiques (ex: choix des communes d'Abidjan, pondérations IPET) et attendre l'autorisation explicite pour avancer.
  - Réceptionner les bilans de tests du Pôle QA avant de solliciter l'utilisateur.

---

### 2. 📊 Pôle Data Engineering & Modélisation IA

#### 🗄️ The Data & Geospatial Engineer (`@data-engineer`)
- **Mission** : Ingestion, nettoyage, normalisation et structuration de toutes les données spatiales et temporelles.
- **Responsabilités** :
  - Modélisation de la base PostgreSQL avec l'extension **PostGIS** (tables `zones_geographiques`, `mobilite_agregee`, `demographie`, etc.).
  - Harmonisation des géométries et systèmes de projection (WGS84 EPSG:4326 / UTM 30N).
  - Génération de jeux de données synthétiques réalistes de fréquentation (conformément à la stratégie de repli du CdC), strictement étiquetés comme simulés.
- **Outils & MCP** : PostgreSQL, PostGIS, GeoPandas, Shapely, `neon-postgres`.

#### 📈 The Mobility & Time Series Data Scientist (`@data-scientist`)
- **Mission** : Analyse exploratoire (EDA) temporelle et modélisation prédictive de la fréquentation.
- **Responsabilités** :
  - Analyse des dynamiques temporelles (pics horaires, variations jours ouvrés vs week-ends).
  - Implémentation du protocole d'évaluation chronologique (sans fuite d'information).
  - Entraînement et comparaison rigoureuse : Référence naïve (J-7), Prophet et XGBoost.
  - Calcul des métriques de précision : MAE, RMSE, WAPE et estimation des plages d'incertitude.

#### 🗺️ The GIS & Economic Modeler (`@gis-analyst`)
- **Mission** : Analyse spatiale, segmentation territoriale et moteur de calcul de l'IPET.
- **Responsabilités** :
  - Extraction et traitement des données OpenStreetMap (réseau viaire, commerces, supermarchés existants) via Overpass API / OSMnx.
  - Intégration des données démographiques INS/RGPH 2021.
  - Segmentation non-supervisée des zones territoriales (K-Means avec méthode du coude et silhouette score).
  - Conception et calibration du moteur **IPET** (Indice de Potentiel Économique Territorial) avec matrice de pondération multicritère et explicabilité (facteurs favorables vs défavorables).

---

### 3. 🎨 Pôle Restitution 3D & Interface Utilisateur

#### ✨ The UX/UI & 3D Experience Designer (`@uiux`)
- **Mission** : Concevoir l'expérience de navigation spatio-temporelle et les maquettes d'interface haute fidélité.
- **Responsabilités** :
  - Design des flux d'aide à la décision (sélection commune -> filtres temporels -> carte 3D -> fiche explicative IPET -> export).
  - Conception du design system basé sur **shadcn/ui** (palette moderne, typographie soignée, composants Radix UI, mode sombre/clair).
  - Scénarisation de l'expérience cartographique 3D (extrusion des bâtiments, cônes/piliers de densité de fréquentation en 3D, animations de flux).

#### 💻 The Full-Stack & 3D Web Engineer (`@engineer`)
- **Mission** : Implémenter l'application web complète (Backend FastAPI et Frontend Next.js / Three.js).
- **Responsabilités** :
  - **Backend** : FastAPI, SQLModel/PostGIS, endpoints d'analyse, prévision, calcul IPET et exports (PDF/Excel).
  - **Frontend** : Next.js (App Router), React, Tailwind CSS, **shadcn/ui**.
  - **Rendu Cartographique 3D** : Intégration de **Three.js** (via React Three Fiber / Drei / Maplibre 3D / Deck.gl) pour visualiser en 3D les volumes de population, la hauteur de fréquentation par zone et les axes de mobilité sur le territoire d'Abidjan.
  - Connexion fluide avec les API REST et gestion des états réactifs.

---

### 4. 🛡️ Guilde Qualité, Robustesse & Sécurité (Pôle QA Étendu)

#### 🛡️ The QA Lead & Privacy Auditor (`@qa-lead`)
- **Mission** : Garantir la conformité légale, la confidentialité des données et l'arbitrage qualité global.
- **Responsabilités** :
  - Audit d'anonymisation et de non-réidentification (vérification des seuils k-anonymat : masquage de toute zone sous le seuil minimal de personnes).
  - Conformité stricte à la Loi ivoirienne n° 2013-450 sur la protection des données personnelles.
  - Contrôle qu'aucune donnée identifiante (PII, numéros, coordonnées brutes individuelles) n'est ingérée ou exposée.
  - Validation finale de la conformité avant transmission au `@lead-pm`.

#### 🧪 The Unit & Code Coverage Tester (`@qa-unit`)
- **Mission** : Tester le code source au niveau fonctionnel et algorithmique.
- **Responsabilités** :
  - Tests unitaires systématiques (Pytest pour le backend / Jest pour le frontend).
  - Validation des fonctions de nettoyage ETL, harmonisation de coordonnées et calculs de pondération IPET.
  - Vérification de la reproductibilité des classements et du non-débordement des scores (bornes 0-100).
  - Couverture de test minimale cible : 85%+.

#### 🔄 The E2E & Integration Tester (`@qa-e2e`)
- **Mission** : Tester les intégrations système et le parcours nominal complet.
- **Responsabilités** :
  - Tests des flux complets : Requête API -> Interrogation PostGIS -> Inférence modèle -> Restitution Frontend.
  - Validation de la performance : temps de réponse inférieur à 5 secondes sur les requêtes types.
  - Tests des modules d'exportation de rapports PDF et Excel (intégrité des métadonnées, dates, avertissements).

#### 👁️ The UI, 3D & Accessibility Tester (`@qa-ui`)
- **Mission** : Tester la robustesse graphique, le rendu 3D et l'ergonomie.
- **Responsabilités** :
  - Validation du pipeline de rendu **Three.js** (gestion des pertes de contexte WebGL, fps stables, adaptabilité responsive).
  - Contrôle visuel et accessibilité des composants **shadcn/ui** (contrastes WCAG, états de chargement, gestion des erreurs d'affichage).
  - Prise de captures d'écran automatisées de validation via Playwright / Chrome DevTools.

---

### 5. 🚀 Pôle Déploiement Cloud & Infrastructure

#### 🚀 The DevOps & Deployment Master (`@devops`)
- **Mission** : Automatisation du build, intégration continue (CI/CD) et hébergement résilient.
- **Responsabilités** :
  - Configuration de la base de données PostgreSQL/PostGIS (Neon / Docker).
  - Déploiement Vercel (Frontend Next.js) et Cloud/Container (Backend FastAPI).
  - Gestion des variables d'environnement sécurisées (`.env`).
  - Suite de 4 tests de connectivité obligatoires pré et post-déploiement.

---

## 🛠️ Outillage MCP (Model Context Protocol) Mobilisé

| Serveur MCP | Agents | Usage opérationnel |
| :--- | :--- | :--- |
| **`neon-postgres`** | `@data-engineer`, `@qa-e2e` | Gestion du schéma spatial PostGIS, index `GIST`, requêtes spatiales et intégrité. |
| **`github`** | Toute l'équipe | Gestion des branches par fonctionnalités, revues de code automatisées et issues. |
| **`chrome-devtools-plugin`** | `@qa-ui`, `@uiux` | Inspection du canvas Three.js, profiling WebGL (fps, mémoire GPU) et captures visuelles. |
| **`osm-overpass-mcp` / fetch** | `@gis-analyst` | Récupération en temps réel des couches géographiques et points d'intérêts sur Abidjan. |
