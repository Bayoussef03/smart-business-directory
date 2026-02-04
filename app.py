import os
import io
from typing import Optional, Dict, Any, List

import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv


# ================== CONFIG ==================

load_dotenv()
INSEE_API_KEY = os.getenv("INSEE_API_KEY")

INSEE_BASE_URL = "https://api.insee.fr/api-sirene/3.11"
RECHERCHE_ENTREPRISES_URL = "https://recherche-entreprises.api.gouv.fr/search"


# ================== UTILS ==================

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="resultats")
    return output.getvalue()


# ================== FONCTIONS IA ==================

def calculer_score_sante_ia(effectif, nb_etab, naf):
    """Score de santé d'entreprise de 0 à 100"""
    score = 50  # Base
    
    # Analyse effectif (30 points max)
    effectif_scores = {
        "51": 30, "52": 30, "53": 30,  # > 250 salariés
        "42": 25, "41": 20,            # 50-250
        "32": 15, "31": 10,            # 10-50
        "22": 5, "21": 5,              # 3-10
        "12": 2, "11": 2,              # 1-3
        "00": 0, "01": 0, "02": 0, "03": 0
    }
    score += effectif_scores.get(str(effectif), 5)
    
    # Analyse établissements (20 points max)
    if nb_etab:
        try:
            score += min(20, int(nb_etab) * 2)
        except:
            pass
    
    # Analyse secteur NAF (bonus/malus)
    if naf:
        naf_prefix = str(naf)[:2]
        secteur_risques = {
            "47": -5,  # Commerce détail (risque)
            "56": -5,  # Restauration (risque)
            "62": +10, # IT (croissance)
            "63": +10, # Info services
            "72": +10, # R&D
        }
        score += secteur_risques.get(naf_prefix, 0)
    
    return min(100, max(0, score))


def interpreter_score(score):
    """Interprétation du score"""
    if score >= 80:
        return "🟢 Excellente santé", "Entreprise solide avec fort potentiel"
    elif score >= 60:
        return "🟡 Bonne santé", "Entreprise stable"
    elif score >= 40:
        return "🟠 Santé moyenne", "Entreprise à surveiller"
    else:
        return "🔴 Santé fragile", "Entreprise à risque"


def generer_resume_ia(nom, naf, effectif, nb_etab):
    """Génère un résumé intelligent automatique"""
    
    # Mapping secteurs NAF
    secteurs = {
        "01": "agriculture et élevage", "02": "sylviculture", "03": "pêche",
        "05": "extraction minière", "10": "industries agroalimentaires",
        "13": "fabrication de textiles", "14": "industrie de l'habillement",
        "20": "industrie chimique", "21": "industrie pharmaceutique",
        "26": "fabrication de produits électroniques", "27": "fabrication d'équipements électriques",
        "28": "fabrication de machines et équipements", "29": "industrie automobile",
        "30": "fabrication de matériels de transport", "41": "construction de bâtiments",
        "43": "travaux de construction spécialisés", "45": "commerce et réparation automobiles",
        "46": "commerce de gros", "47": "commerce de détail",
        "49": "transports terrestres", "50": "transports par eau", "51": "transports aériens",
        "55": "hébergement", "56": "restauration",
        "58": "édition", "59": "production audiovisuelle", "60": "programmation et diffusion",
        "61": "télécommunications", "62": "programmation et conseil informatique",
        "63": "services d'information", "64": "activités financières",
        "65": "assurance", "66": "activités auxiliaires financières et assurance",
        "68": "activités immobilières", "69": "activités juridiques et comptables",
        "70": "activités de conseil et de gestion", "71": "activités d'architecture et d'ingénierie",
        "72": "recherche-développement scientifique", "73": "publicité et études de marché",
        "74": "autres activités spécialisées", "77": "activités de location",
        "78": "activités liées à l'emploi", "80": "enquêtes et sécurité",
        "85": "enseignement", "86": "activités pour la santé humaine",
        "87": "hébergement médico-social", "88": "action sociale",
        "90": "activités créatives, artistiques et de spectacle",
        "91": "bibliothèques, archives, musées", "93": "activités sportives",
        "95": "réparation d'ordinateurs", "96": "autres services personnels",
    }
    
    secteur_desc = secteurs.get(str(naf)[:2], "activités économiques diversifiées")
    
    # Mapping effectif détaillé
    tailles = {
        "51": ("grande entreprise", "plus de 250 salariés", "d'envergure majeure"),
        "52": ("grande entreprise", "plus de 500 salariés", "d'envergure nationale"),
        "53": ("très grande entreprise", "plus de 2000 salariés", "de dimension internationale"),
        "42": ("entreprise de taille intermédiaire (ETI)", "entre 100 et 199 salariés", "bien structurée"),
        "41": ("entreprise moyenne", "entre 50 et 99 salariés", "en développement soutenu"),
        "32": ("PME", "entre 20 et 49 salariés", "solidement établie"),
        "31": ("PME", "entre 10 et 19 salariés", "en phase de consolidation"),
        "22": ("TPE", "entre 6 et 9 salariés", "à taille humaine"),
        "21": ("TPE", "entre 3 et 5 salariés", "agile et réactive"),
        "12": ("micro-entreprise", "1 à 2 salariés", "de type entrepreneurial"),
        "11": ("micro-entreprise", "1 salarié", "en mode startup"),
        "00": ("structure", "sans salarié déclaré", "en phase de lancement"),
        "01": ("entreprise individuelle", "sans salarié", "indépendante"),
        "02": ("entreprise individuelle", "1 ou 2 salariés", "en croissance"),
        "03": ("petite structure", "3 à 5 salariés", "en développement"),
    }
    
    taille_info = tailles.get(str(effectif), ("entreprise", "effectif variable", "active"))
    taille, detail_effectif, qualificatif = taille_info
    
    # Construction du résumé élaboré
    resume = f"**{nom}** est une {taille} ({detail_effectif}) {qualificatif} spécialisée dans **{secteur_desc}**. "
    
    # Expansion géographique
    try:
        nb = int(nb_etab) if nb_etab else 1
        if nb > 50:
            resume += f"Son réseau de **{nb} établissements** témoigne d'une implantation territoriale exceptionnelle et d'une stratégie d'expansion ambitieuse. "
        elif nb > 20:
            resume += f"Avec **{nb} établissements** répartis sur le territoire, elle bénéficie d'une présence géographique significative. "
        elif nb > 10:
            resume += f"Sa présence à travers **{nb} établissements** illustre une stratégie de développement multi-sites réussie. "
        elif nb > 5:
            resume += f"Disposant de **{nb} établissements**, elle affiche une expansion géographique progressive. "
        elif nb > 1:
            resume += f"Elle opère depuis **{nb} établissements**, permettant une proximité régionale. "
        else:
            resume += "Structure centralisée sur un établissement unique, favorisant une gestion directe et réactive. "
    except:
        resume += "Organisation établie avec une structure opérationnelle cohérente. "
    
    # Analyse prédictive avancée basée sur score
    score = calculer_score_sante_ia(effectif, nb_etab, naf)
    
    if score >= 85:
        resume += "**Les indicateurs structurels révèlent une entreprise au profil exceptionnel**, combinant taille critique, expansion territoriale et positionnement sectoriel favorable, suggérant un **potentiel de croissance élevé** et une **résilience remarquable**."
    elif score >= 70:
        resume += "**L'analyse des données met en évidence des fondamentaux solides**, avec une structure robuste et un positionnement stratégique pertinent, laissant présager une **trajectoire de développement positive** et une **stabilité financière durable**."
    elif score >= 55:
        resume += "**Les critères évalués indiquent une situation stable**, avec des bases saines permettant d'envisager des **opportunités de développement** à moyen terme, sous réserve d'une gestion proactive et adaptée aux évolutions du marché."
    elif score >= 40:
        resume += "**Le profil actuel suggère une phase de vigilance**, nécessitant une attention particulière aux équilibres opérationnels et financiers, avec des **marges d'optimisation identifiées** dans l'organisation ou le positionnement sectoriel."
    else:
        resume += "**Les indicateurs appellent à une surveillance accrue**, dans un contexte où les facteurs structurels (taille, secteur, maillage territorial) présentent des **fragilités potentielles** requérant un pilotage stratégique renforcé."
    
    return resume


# ================== API INSEE ==================

def call_insee(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not INSEE_API_KEY:
        raise RuntimeError("INSEE_API_KEY manquante dans .env")

    url = f"{INSEE_BASE_URL}/{path.lstrip('/')}"
    headers = {
        "X-INSEE-Api-Key-Integration": INSEE_API_KEY,
        "Accept": "application/json",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_unite_legale_by_siren(siren: str):
    return call_insee(f"siren/{siren}")


def get_etablissement_by_siret(siret: str):
    return call_insee(f"siret/{siret}")


def normaliser_naf(naf: str) -> str:
    naf = naf.strip().upper()
    if "*" in naf or "?" in naf:
        return naf
    if "." in naf:
        return naf
    if len(naf) == 5 and naf[:4].isdigit() and naf[-1].isalpha():
        return naf[:2] + "." + naf[2:]
    return naf


def search_by_naf(naf: str, nombre: int = 10):
    naf = normaliser_naf(naf)

    if "*" in naf or "?" in naf:
        q = f"activitePrincipaleUniteLegale:{naf}"
    else:
        q = f"periode(activitePrincipaleUniteLegale:{naf})"

    try:
        return call_insee("siren", params={"q": q, "nombre": nombre})
    except:
        return {"unitesLegales": []}


def extract_infos_unite_legale(ul: Dict[str, Any]):
    periodes = ul.get("periodesUniteLegale") or []
    periode = periodes[0] if periodes else {}

    denomination = (
        periode.get("denominationUniteLegale")
        or periode.get("nomUniteLegale")
        or ul.get("denominationUniteLegale")
        or ul.get("nomUniteLegale")
    )

    naf = periode.get("activitePrincipaleUniteLegale") or ul.get("activitePrincipaleUniteLegale")
    catjur = periode.get("categorieJuridiqueUniteLegale") or ul.get("categorieJuridiqueUniteLegale")

    return denomination, naf, catjur


# ================== API data.gouv ==================

def search_entreprises_by_name(
    texte: str,
    max_results: int = 10,
    tranche_effectif: str = None,
    etab_min: int = None,
    etab_max: int = None,
    code_naf: str = None
) -> List[Dict[str, Any]]:

    results = []
    page = 1
    per_page_api = 25

    while len(results) < max_results:

        params = {
            "q": texte,
            "per_page": per_page_api,
            "page": page,
        }

        if tranche_effectif:
            params["tranche_effectif_salarie"] = tranche_effectif

        if etab_min is not None:
            params["nombre_etablissements_ouverts_min"] = etab_min

        if etab_max is not None:
            params["nombre_etablissements_ouverts_max"] = etab_max

        if code_naf:
            params["activite_principale"] = code_naf

        resp = requests.get(RECHERCHE_ENTREPRISES_URL, params=params, timeout=15)
        resp.raise_for_status()

        data_page = resp.json()
        page_results = data_page.get("results", [])

        if not page_results:
            break

        results.extend(page_results)
        page += 1

    return results[:max_results]


def enrichir_par_datagouv(siren: str):
    params = {"siren": siren, "per_page": 1}

    resp = requests.get(RECHERCHE_ENTREPRISES_URL, params=params, timeout=10)
    if resp.status_code != 200:
        return None

    data = resp.json().get("results", [])
    if not data:
        return None

    r = data[0]

    return {
        "tranche_effectif_salarie": r.get("tranche_effectif_salarie"),
        "nombre_etablissements_ouverts": r.get("nombre_etablissements_ouverts"),
    }


# ================== THEME MODERNE ==================

st.set_page_config(
    page_title="Smart Business Directory - IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Palette de couleurs moderne */
:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --secondary: #8b5cf6;
    --accent: #06b6d4;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --bg-dark: #1e293b;
    --bg-light: #f8fafc;
    --text-dark: #0f172a;
    --text-light: #64748b;
}

/* Arrière-plan général */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Conteneur principal */
.main .block-container {
    background: white;
    border-radius: 20px;
    padding: 2rem 3rem;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    margin-top: 2rem;
    margin-bottom: 2rem;
}

/* Titres */
h1 {
    color: var(--primary) !important;
    font-weight: 800 !important;
    font-size: 3rem !important;
    text-align: center;
    margin-bottom: 1rem !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

h2 {
    color: var(--primary-dark) !important;
    font-weight: 700 !important;
    font-size: 1.8rem !important;
    margin-top: 2rem !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 3px solid var(--accent) !important;
}

h3 {
    color: var(--secondary) !important;
    font-weight: 600 !important;
    font-size: 1.4rem !important;
    margin-top: 1.5rem !important;
}

/* Sidebar */
.css-1d391kg, [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
}

.css-1d391kg h2, [data-testid="stSidebar"] h2 {
    color: white !important;
    border-bottom: 2px solid rgba(255,255,255,0.3) !important;
}

.css-1d391kg .stSelectbox label, [data-testid="stSidebar"] label {
    color: white !important;
    font-weight: 600 !important;
}

/* Boutons */
.stButton>button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
    transition: all 0.3s ease !important;
}

.stButton>button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(99, 102, 241, 0.6) !important;
}

.stDownloadButton>button {
    background: linear-gradient(135deg, var(--accent) 0%, var(--success) 100%) !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4) !important;
}

/* Inputs */
.stTextInput>div>div>input {
    border-radius: 10px !important;
    border: 2px solid var(--primary) !important;
    padding: 0.75rem !important;
    font-size: 1rem !important;
}

.stTextInput>div>div>input:focus {
    border-color: var(--secondary) !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1) !important;
}

/* Metrics (Score) */
[data-testid="stMetricValue"] {
    font-size: 3rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

[data-testid="stMetricDelta"] {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
}

/* Alerts et infos */
.stAlert {
    background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%) !important;
    border-left: 5px solid var(--primary) !important;
    border-radius: 10px !important;
    padding: 1rem 1.5rem !important;
    color: var(--text-dark) !important;
}

.stSuccess {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%) !important;
    border-left: 5px solid var(--success) !important;
}

.stWarning {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
    border-left: 5px solid var(--warning) !important;
}

.stError {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%) !important;
    border-left: 5px solid var(--danger) !important;
}

/* Info boxes (résumé IA) */
.stMarkdown .element-container div[data-testid="stMarkdownContainer"] p {
    line-height: 1.8 !important;
    font-size: 1.05rem !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    color: var(--primary) !important;
    border: 2px solid var(--primary) !important;
}

.streamlit-expanderHeader:hover {
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%) !important;
}

/* Colonnes */
[data-testid="column"] {
    background: var(--bg-light);
    border-radius: 15px;
    padding: 1.5rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

/* Slider */
.stSlider>div>div>div {
    background: var(--primary) !important;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.main .block-container > div {
    animation: fadeIn 0.5s ease-out;
}

/* Scrollbar personnalisée */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary-dark);
}
</style>
""", unsafe_allow_html=True)


# ================== HEADER ==================

st.markdown("""
<div style="text-align:center; margin-bottom:2rem;">
    <h1 style="font-size: 3.5rem; margin-bottom: 0;">🤖 Smart Business Directory</h1>
    <p style="font-size: 1.3rem; color: #64748b; font-weight: 500;">
        L'Annuaire d'Entreprises Augmenté par l'Intelligence Artificielle
    </p>
</div>
""", unsafe_allow_html=True)


# ================== SIDEBAR ==================

st.sidebar.markdown("### 🔍 Mode de recherche")

mode = st.sidebar.selectbox(
    "Choisissez votre méthode",
    [
        "Recherche par SIREN (INSEE)",
        "Recherche par SIRET (INSEE)",
        "Recherche par Code NAF (INSEE)",
        "Recherche par nom (data.gouv)",
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ À propos")
st.sidebar.info(
    """
    **🚀 Nouveautés IA :**
    
    ✨ **Score de Santé (0-100)**  
    Algorithme prédictif multi-critères
    
    ✨ **Résumés Intelligents**  
    Analyses contextuelles automatiques
    
    ✨ **Évaluation Sectorielle**  
    Risques et opportunités par NAF
    
    ---
    
    **📊 Fonctionnalités :**
    - Recherche multi-critères
    - Données officielles INSEE
    - Filtres avancés
    - Export Excel enrichi
    
    ---
    
    **🏆 Hackathon IA Cloud 2026**
    """
)


# ================== MODES DE RECHERCHE ==================

# MODE SIREN
if mode == "Recherche par SIREN (INSEE)":
    st.markdown("## 🔎 Recherche par SIREN")
    st.markdown("*Identifiez une entreprise par son numéro SIREN (9 chiffres)*")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        siren = st.text_input("Numéro SIREN", placeholder="ex: 552032534 (Google France)")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🚀 Rechercher", key="btn_siren", use_container_width=True)

    if search_btn and siren:
        with st.spinner("🔄 Recherche en cours..."):
            try:
                data = get_unite_legale_by_siren(siren)
                ul = data.get("uniteLegale", data)
                info = enrichir_par_datagouv(siren)
                denomination, naf, catjur = extract_infos_unite_legale(ul)

                st.success("✅ Entreprise trouvée avec succès !")
                
                # === ANALYSE IA ===
                st.markdown("---")
                st.markdown("### 🎯 Analyse Intelligente IA")
                
                # Score de santé
                score = calculer_score_sante_ia(
                    effectif=info.get("tranche_effectif_salarie") if info else "00",
                    nb_etab=info.get("nombre_etablissements_ouverts") if info else 0,
                    naf=naf
                )
                statut, description = interpreter_score(score)
                
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    st.metric("📊 Score de Santé", f"{score}/100", delta=statut.split()[0])
                with col2:
                    # Jauge visuelle
                    if score >= 80:
                        st.markdown("### 🟢")
                    elif score >= 60:
                        st.markdown("### 🟡")
                    elif score >= 40:
                        st.markdown("### 🟠")
                    else:
                        st.markdown("### 🔴")
                    st.markdown(f"**{statut.split()[1]}**")
                with col3:
                    st.info(f"**Diagnostic:** {description}")
                
                # Résumé IA
                st.markdown("### 🤖 Résumé Généré par Intelligence Artificielle")
                with st.spinner("🧠 Analyse en cours..."):
                    resume = generer_resume_ia(
                        nom=denomination or "Entreprise",
                        naf=naf or "N/A",
                        effectif=info.get("tranche_effectif_salarie") if info else "N/A",
                        nb_etab=info.get("nombre_etablissements_ouverts") if info else "N/A"
                    )
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%); 
                                padding: 1.5rem; border-radius: 15px; border-left: 5px solid #6366f1;">
                        <p style="font-size: 1.1rem; line-height: 1.8; margin: 0; color: #1e293b;">
                            {resume}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # Informations principales
                st.markdown("---")
                st.markdown("### 📋 Informations Officielles")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🏢 SIREN:** `{ul.get('siren')}`")
                    st.markdown(f"**📝 Dénomination:** {denomination}")
                    st.markdown(f"**🏷️ Code NAF:** `{naf}`")
                with col2:
                    st.markdown(f"**⚖️ Catégorie juridique:** {catjur}")
                    if info:
                        st.markdown(f"**👥 Tranche effectif:** {info.get('tranche_effectif_salarie') or 'N/A'}")
                        st.markdown(f"**🏪 Établissements ouverts:** {info.get('nombre_etablissements_ouverts') or 'N/A'}")

                with st.expander("📄 Voir les données JSON complètes (INSEE)"):
                    st.json(ul)

                # Export Excel
                st.markdown("---")
                rows = [{
                    "SIREN": ul.get("siren"),
                    "Nom / Dénomination": denomination,
                    "Code NAF": naf,
                    "Catégorie juridique": catjur,
                    "Tranche effectif salarié": info.get("tranche_effectif_salarie") if info else None,
                    "Établissements ouverts": info.get("nombre_etablissements_ouverts") if info else None,
                    "Score Santé IA": score,
                    "Statut": statut,
                }]

                df = pd.DataFrame(rows)
                excel_bytes = df_to_excel_bytes(df)
                st.download_button(
                    label="📥 Télécharger le rapport Excel",
                    data=excel_bytes,
                    file_name=f"smart_report_siren_{siren}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"❌ Erreur lors de la recherche : {e}")


# MODE SIRET
elif mode == "Recherche par SIRET (INSEE)":
    st.markdown("## 🔎 Recherche par SIRET")
    st.markdown("*Identifiez un établissement par son numéro SIRET (14 chiffres)*")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        siret = st.text_input("Numéro SIRET", placeholder="ex: 55203253400047")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🚀 Rechercher", key="btn_siret", use_container_width=True)

    if search_btn and siret:
        with st.spinner("🔄 Recherche en cours..."):
            try:
                data = get_etablissement_by_siret(siret)
                etab = data.get("etablissement", data)
                siren_val = etab.get("siren")
                info = enrichir_par_datagouv(siren_val)

                st.success("✅ Établissement trouvé avec succès !")
                
                # === ANALYSE IA ===
                st.markdown("---")
                st.markdown("### 🎯 Analyse Intelligente IA")
                
                score = calculer_score_sante_ia(
                    effectif=info.get("tranche_effectif_salarie") if info else "00",
                    nb_etab=info.get("nombre_etablissements_ouverts") if info else 0,
                    naf=etab.get("activitePrincipaleEtablissement")
                )
                statut, description = interpreter_score(score)
                
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    st.metric("📊 Score de Santé", f"{score}/100", delta=statut.split()[0])
                with col2:
                    if score >= 80:
                        st.markdown("### 🟢")
                    elif score >= 60:
                        st.markdown("### 🟡")
                    elif score >= 40:
                        st.markdown("### 🟠")
                    else:
                        st.markdown("### 🔴")
                    st.markdown(f"**{statut.split()[1]}**")
                with col3:
                    st.info(f"**Diagnostic:** {description}")
                
                # Résumé IA
                st.markdown("### 🤖 Résumé Généré par Intelligence Artificielle")
                with st.spinner("🧠 Analyse en cours..."):
                    resume = generer_resume_ia(
                        nom=f"Établissement {siret}",
                        naf=etab.get("activitePrincipaleEtablissement", "N/A"),
                        effectif=info.get("tranche_effectif_salarie") if info else "N/A",
                        nb_etab=info.get("nombre_etablissements_ouverts") if info else "N/A"
                    )
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%); 
                                padding: 1.5rem; border-radius: 15px; border-left: 5px solid #6366f1;">
                        <p style="font-size: 1.1rem; line-height: 1.8; margin: 0; color: #1e293b;">
                            {resume}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # Informations principales
                st.markdown("---")
                st.markdown("### 📋 Informations Officielles")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🏪 SIRET:** `{etab.get('siret')}`")
                    st.markdown(f"**🏢 SIREN:** `{etab.get('siren')}`")
                    st.markdown(f"**🏷️ Activité principale:** `{etab.get('activitePrincipaleEtablissement')}`")
                with col2:
                    if info:
                        st.markdown(f"**👥 Tranche effectif:** {info.get('tranche_effectif_salarie') or 'N/A'}")
                        st.markdown(f"**🏪 Établissements ouverts:** {info.get('nombre_etablissements_ouverts') or 'N/A'}")

                with st.expander("📄 Voir les données JSON complètes (INSEE)"):
                    st.json(etab)

                # Export Excel
                st.markdown("---")
                rows = [{
                    "SIRET": etab.get("siret"),
                    "SIREN": etab.get("siren"),
                    "Activité principale": etab.get("activitePrincipaleEtablissement"),
                    "Tranche effectif salarié": info.get("tranche_effectif_salarie") if info else None,
                    "Établissements ouverts": info.get("nombre_etablissements_ouverts") if info else None,
                    "Score Santé IA": score,
                    "Statut": statut,
                }]

                df = pd.DataFrame(rows)
                excel_bytes = df_to_excel_bytes(df)
                st.download_button(
                    label="📥 Télécharger le rapport Excel",
                    data=excel_bytes,
                    file_name=f"smart_report_siret_{siret}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"❌ Erreur lors de la recherche : {e}")


# MODE CODE NAF
elif mode == "Recherche par Code NAF (INSEE)":
    st.markdown("## 🔎 Recherche par Code NAF")
    st.markdown("*Trouvez les entreprises d'un secteur d'activité spécifique*")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        naf_input = st.text_input("Code NAF", placeholder="ex: 6201Z, 62.01Z, 62*")
    with col2:
        nombre = st.slider("Nombre max", 1, 50, 10)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🚀 Rechercher", key="btn_naf", use_container_width=True)

    if search_btn and naf_input:
        with st.spinner("🔄 Recherche en cours..."):
            try:
                data = search_by_naf(naf_input, nombre)
                results = data.get("unitesLegales", [])

                rows = []
                total_valides = 0

                for u in results:
                    ul = u.get("uniteLegale", u)
                    siren_val = ul.get("siren")
                    info = enrichir_par_datagouv(siren_val)
                    denomination, naf_code, catjur = extract_infos_unite_legale(ul)
                    
                    score = calculer_score_sante_ia(
                        effectif=info.get("tranche_effectif_salarie") if info else "00",
                        nb_etab=info.get("nombre_etablissements_ouverts") if info else 0,
                        naf=naf_code
                    )
                    statut, _ = interpreter_score(score)

                    rows.append({
                        "SIREN": siren_val,
                        "Nom / Dénomination": denomination,
                        "Code NAF": naf_code,
                        "Catégorie juridique": catjur,
                        "Tranche effectif salarié": info.get("tranche_effectif_salarie") if info else None,
                        "Établissements ouverts": info.get("nombre_etablissements_ouverts") if info else None,
                        "Score Santé IA": score,
                        "Statut": statut,
                    })

                    total_valides += 1

                    with st.expander(f"🏢 {denomination} – `{siren_val}` | Score: **{score}/100** {statut.split()[0]}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Code NAF:** `{naf_code}`")
                            st.markdown(f"**Catégorie juridique:** {catjur}")
                            st.markdown(f"**Score de Santé IA:** {score}/100 - {statut}")
                        with col2:
                            st.markdown(f"**Tranche effectif:** {info.get('tranche_effectif_salarie') if info else 'N/A'}")
                            st.markdown(f"**Établissements:** {info.get('nombre_etablissements_ouverts') if info else 'N/A'}")
                        
                        st.markdown("---")
                        st.markdown("**🤖 Analyse IA :**")
                        with st.spinner("Génération..."):
                            resume = generer_resume_ia(
                                nom=denomination,
                                naf=naf_code,
                                effectif=info.get("tranche_effectif_salarie") if info else "N/A",
                                nb_etab=info.get("nombre_etablissements_ouverts") if info else "N/A"
                            )
                            st.info(resume)
                        
                        # JSON affiché directement (pas d'expander imbriqué)
                        st.markdown("**📄 Données brutes INSEE :**")
                        st.json(ul)

                if total_valides == 0:
                    st.warning("⚠️ Aucun résultat trouvé pour ce code NAF.")
                else:
                    st.success(f"✅ **{total_valides} entreprises** trouvées dans le secteur NAF: {naf_input}")

                if rows:
                    st.markdown("---")
                    df = pd.DataFrame(rows)
                    excel_bytes = df_to_excel_bytes(df)
                    st.download_button(
                        label="📥 Télécharger tous les résultats en Excel",
                        data=excel_bytes,
                        file_name=f"smart_report_naf_{naf_input}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ Erreur lors de la recherche : {e}")


# MODE NOM
elif mode == "Recherche par nom (data.gouv)":
    st.markdown("## 🔎 Recherche par Nom d'Entreprise")
    st.markdown("*Trouvez une entreprise par son nom, raison sociale ou sigle*")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎛️ Filtres Avancés")

    filtre_tranche = st.sidebar.selectbox(
        "Tranche d'effectif salarié",
        ["", "00", "01", "02", "03", "11", "12", "21", "22", "31", "32", "41", "42", "51"],
        format_func=lambda x: "— Tous —" if x == "" else x
    )

    filtre_etab_min = st.sidebar.number_input("Établissements min", 0, 9999, 0)
    filtre_etab_max = st.sidebar.number_input("Établissements max", 0, 9999, 9999)
    code_naf_filtre = st.sidebar.text_input("Code NAF (optionnel)", "")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        texte = st.text_input("Nom de l'entreprise", placeholder="ex: Capgemini, Total, Carrefour...")
    with col2:
        max_results = st.slider("Nb résultats", 5, 100, 10)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🚀 Rechercher", key="btn_nom", use_container_width=True)

    if search_btn and texte:
        with st.spinner("🔄 Recherche en cours..."):
            try:
                results = search_entreprises_by_name(
                    texte,
                    max_results=max_results,
                    tranche_effectif=filtre_tranche if filtre_tranche else None,
                    etab_min=filtre_etab_min,
                    etab_max=filtre_etab_max,
                    code_naf=code_naf_filtre if code_naf_filtre else None
                )

                nb_trouves = len(results)

                if nb_trouves == 0:
                    st.warning("⚠️ Aucun résultat trouvé pour cette recherche.")
                else:
                    st.success(f"✅ **{nb_trouves} entreprises** trouvées pour '{texte}'")

                rows = []
                for r in results:
                    nom_complet = r.get("nom_complet") or "Sans nom"
                    siren = r.get("siren")
                    siege = r.get("siege") or {}
                    adresse = siege.get("adresse")
                    siret_siege = siege.get("siret")
                    naf = r.get("activite_principale")
                    tranche_effectif_api = r.get("tranche_effectif_salarie")
                    nb_etab_ouverts = r.get("nombre_etablissements_ouverts")
                    
                    score = calculer_score_sante_ia(
                        effectif=tranche_effectif_api or "00",
                        nb_etab=nb_etab_ouverts or 0,
                        naf=naf
                    )
                    statut, _ = interpreter_score(score)

                    rows.append({
                        "Nom complet": nom_complet,
                        "SIREN": siren,
                        "SIRET siège": siret_siege,
                        "Adresse siège": adresse,
                        "Code NAF": naf,
                        "Tranche effectif salarié": tranche_effectif_api,
                        "Établissements ouverts": nb_etab_ouverts,
                        "Score Santé IA": score,
                        "Statut": statut,
                    })

                    with st.expander(f"🏢 {nom_complet} – `{siren}` | Score: **{score}/100** {statut.split()[0]}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Adresse siège:** {adresse}")
                            st.markdown(f"**Code NAF:** `{naf}`")
                            st.markdown(f"**Score de Santé IA:** {score}/100 - {statut}")
                        with col2:
                            st.markdown(f"**Tranche effectif:** {tranche_effectif_api or 'N/A'}")
                            st.markdown(f"**Établissements:** {nb_etab_ouverts or 'N/A'}")
                        
                        st.markdown("---")
                        st.markdown("**🤖 Analyse IA :**")
                        with st.spinner("Génération..."):
                            resume = generer_resume_ia(
                                nom=nom_complet,
                                naf=naf or "N/A",
                                effectif=tranche_effectif_api or "N/A",
                                nb_etab=nb_etab_ouverts or "N/A"
                            )
                            st.info(resume)
                        
                        # JSON affiché directement (pas d'expander imbriqué)
                        st.markdown("**📄 Données brutes data.gouv :**")
                        st.json(r)

                if rows:
                    st.markdown("---")
                    df = pd.DataFrame(rows)
                    excel_bytes = df_to_excel_bytes(df)
                    st.download_button(
                        label="📥 Télécharger tous les résultats en Excel",
                        data=excel_bytes,
                        file_name=f"smart_report_{texte.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ Erreur lors de la recherche : {e}")


# ================== FOOTER ==================

st.markdown("---")
st.markdown("""
<div style="text-align:center; color: #64748b; padding: 2rem 0;">
    <p style="font-size: 0.9rem; margin-bottom: 0.5rem;">
        🏆 <strong>Smart Business Directory</strong> - Hackathon IA dans le Cloud 2026
    </p>
    <p style="font-size: 0.8rem; margin: 0;">
        Données officielles : <strong>INSEE</strong> & <strong>data.gouv.fr</strong> | 
        Powered by <strong>AI Algorithms</strong>
    </p>
</div>
""", unsafe_allow_html=True)
