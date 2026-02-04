

## Concept

**Smart Business Directory** transforme l'annuaire d'entreprises classique en outil d'intelligence business grâce à l'IA.
Recherchez, analysez et évaluez n'importe quelle entreprise française en quelques secondes avec des insights prédictifs automatiques.

---

## Démo Live

### Application déployée : [VOTRE-URL-STREAMLIT-ICI]   / à changer !!!!!!!!!!!!!!!!!!!!!!!!

> Testez dès maintenant l'analyse IA d'entreprises en temps réel

---

## Fonctionnalités IA

### Score de Santé (0-100)
Algorithme prédictif multi-critères analysant :
- **Effectif salarié** (30% du score) - Indicateur de maturité
- **Nombre d'établissements** (20% du score) - Diversification géographique
- **Secteur NAF** (bonus/malus) - Risque sectoriel

### Résumés Intelligents
Génération automatique d'analyses contextuelles pour chaque entreprise :
- Positionnement sectoriel
- Évaluation de la structure
- Prédiction de stabilité/croissance

### Analyse Sectorielle
Évaluation des risques et opportunités par code NAF (62 secteurs couverts)

---

## Modes de Recherche

| Mode | Description | Exemple |
|------|-------------|---------|
| **SIREN** | Recherche par numéro SIREN (9 chiffres) | 552032534 (Google France) |
| **SIRET** | Recherche par numéro SIRET (14 chiffres) | 55203253400047 |
| **Code NAF** | Recherche par secteur d'activité | 6201Z (Programmation informatique) |
| **Nom** | Recherche par nom/raison sociale | Capgemini, Total, Carrefour |

### Filtres Avancés (Mode Nom)
- Tranche d'effectif salarié
- Nombre d'établissements (min/max)
- Code NAF spécifique

---

## Technologies

### Backend
- **Python 3.9+** - Langage principal
- **Streamlit** - Framework web interactif
- **Pandas** - Manipulation de données
- **Requests** - Appels API

### APIs & Données
- **API INSEE Sirene** - Données officielles entreprises
- Open source Data.gouv (pas d'utilisation d'API)

### Intelligence Artificielle
- **Algorithmes de scoring** - Prédiction santé entreprise
- **NLP (Natural Language Processing)** - Génération résumés automatiques
- **Analyse sectorielle** - Classification risques NAF

### Cloud & DevOps
- **Streamlit Cloud** - Hébergement cloud-native
- **GitHub Actions** - CI/CD automatisé
- **Architecture AWS-ready** - Containerisation Docker

---

## Installation Locale

### Prérequis
- Python 3.9 
- pip
- Clé API INSEE (https://api.insee.fr))

### Étapes

```bash
# 1. Cloner le repository
git clone https://github.com/[VOTRE-USERNAME]/smart-business-directory.git   / à changer !!!!!!!!!!!!!!!!!!!!!!!!
cd smart-business-directory

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer les variables d'environnement
# Créez un fichier .env à la racine :
echo "INSEE_API_KEY=votre_clé_insee" > .env

# 4. Lancer l'application
streamlit run app.py


Architecture

┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (Streamlit)                    │
│  Interface utilisateur moderne avec IA intégrée         │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Algorithmes  │ │  API INSEE   │ │ API data.gouv│
│     IA       │ │   Sirene     │ │      fr      │
│              │ │              │ │              │
│ -  Scoring    │ │ -  SIREN      │ │ -  Effectifs  │
│ -  NLP        │ │ -  SIRET      │ │ -  Établ.     │
│ -  Prédiction │ │ -  NAF        │ │ -  Filtres    │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┴───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Export Excel avec IA        │
        │   (Score + Résumé + Données)  │
        └───────────────────────────────┘



Structure du Projet


smart-business-directory/
├── app.py                  # Application principale Streamlit
├── requirements.txt        # Dépendances Python
├── .env                    # Variables d'environnement (local)
├── .gitignore             # Fichiers à ignorer par Git
├── README.md              # Documentation (ce fichier)
└── docs/                  # Documentation additionnelle (optionnel)
    ├── architecture.md
    └── api_usage.md


