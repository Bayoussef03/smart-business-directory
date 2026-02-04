"""
Modèle IA - Smart Business Directory
Système de scoring rule-based pour l'évaluation d'entreprises

Déployable sur AWS Lambda comme API serverless
"""

def calculer_score_sante_ia(effectif, nb_etab, naf):
    """
    Calcule un score de santé d'entreprise (0-100)
    
    Algorithme : Scoring pondéré sur 3 critères
    - Effectif (30% du score) : Indicateur de maturité
    - Établissements (20% du score) : Expansion géographique
    - Secteur NAF (bonus/malus) : Risque sectoriel
    
    Args:
        effectif (str): Code tranche effectif INSEE
        nb_etab (int): Nombre d'établissements ouverts
        naf (str): Code NAF de l'activité
    
    Returns:
        int: Score entre 0 et 100
    """
    score = 50
    
    effectif_scores = {
        "51": 30, "52": 30, "53": 30,
        "42": 25, "41": 20,
        "32": 15, "31": 10,
        "22": 5, "21": 5,
        "12": 2, "11": 2,
        "00": 0, "01": 0, "02": 0, "03": 0
    }
    score += effectif_scores.get(str(effectif), 5)
    
    if nb_etab:
        try:
            score += min(20, int(nb_etab) * 2)
        except:
            pass
    
    if naf:
        naf_prefix = str(naf)[:2]
        secteur_risques = {
            "47": -5, "56": -5,
            "62": +10, "63": +10, "72": +10,
        }
        score += secteur_risques.get(naf_prefix, 0)
    
    return min(100, max(0, score))


def interpreter_score(score):
    """Interprétation du score"""
    if score >= 80:
        return "Excellente santé", "Entreprise solide avec fort potentiel"
    elif score >= 60:
        return "Bonne santé", "Entreprise stable"
    elif score >= 40:
        return "Santé moyenne", "Entreprise à surveiller"
    else:
        return "Santé fragile", "Entreprise à risque"


# ===== AWS LAMBDA HANDLER =====

def lambda_handler(event, context):
    """
    Point d'entrée pour AWS Lambda
    
    Event structure (JSON):
    {
        "effectif": "51",
        "nb_etab": 10,
        "naf": "6201Z"
    }
    
    Returns (JSON):
    {
        "statusCode": 200,
        "body": {
            "score": 85,
            "statut": "Excellente santé",
            "description": "Entreprise solide"
        }
    }
    """
    try:
        score = calculer_score_sante_ia(
            effectif=event.get('effectif'),
            nb_etab=event.get('nb_etab'),
            naf=event.get('naf')
        )
        statut, description = interpreter_score(score)
        
        return {
            'statusCode': 200,
            'body': {
                'score': score,
                'statut': statut,
                'description': description
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }


# Test local (si exécuté directement)
if __name__ == "__main__":
    # Test 1
    score = calculer_score_sante_ia("51", 15, "6201Z")
    print(f"Test 1 - Score : {score}/100")
    
    # Test 2 - Simulation Lambda
    event = {"effectif": "51", "nb_etab": 15, "naf": "6201Z"}
    result = lambda_handler(event, None)
    print(f"Test 2 - Lambda : {result}")
