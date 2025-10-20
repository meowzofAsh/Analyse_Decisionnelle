import pandas as pd
import time
from itertools import combinations
import os


# 1. CONSTANTES DU PROJET

BUDGET_MAX = 500000

NOM_DU_FICHIER_TEST = 'data/data_test.csv' 

# 
# 2. FONCTION DE PRÉPARATION DES DONNÉES
# 

def preparer_donnees(nom_fichier):
    """
    Lit le fichier CSV, effectue le nettoyage des données et calcule le profit réel
    pour chaque action.
    """
    print(f"\n ÉTAPE 1: PRÉPARATION DES DONNÉES ")
    print(f"-> Tentative de lecture du fichier: {nom_fichier}")
    
    # Vérifie si le fichier existe
    if not os.path.exists(nom_fichier):
        print(f"ERREUR FATALE: Fichier '{nom_fichier}' non trouvé. Vérifiez le chemin : {os.path.abspath(nom_fichier)}")
        return None
    
    try:
        # CORRECTION DE L'ENCODAGE : Utiliser 'latin-1' (ou 'ISO-8859-1') pour les accents français.
        # Nous utilisons aussi 'header=0' pour s'assurer que Pandas prend la première ligne comme en-tête.
        df = pd.read_csv(nom_fichier, sep=';', encoding='latin-1', header=0)
    except Exception as e:
        print(f"ERREUR: Échec de la lecture du CSV (problème d'encodage ou de format): {e}")
        return None
    
    # Assigner/renommer les colonnes selon le format d'entrée attendu
    # Nous devons les renommer car les noms dans le fichier contiennent des espaces et des accents.
    df.columns = ['id', 'cost_str', 'profit_pct_str']
    
    # 2.1 Conversion et nettoyage des données
    
    # Nettoyer et convertir la colonne de coût (cost_str)
    # Remplacer les virgules éventuelles par des points si ce sont des décimales
    df['cost'] = pd.to_numeric(df['cost_str'], errors='coerce') 
    
    # Nettoyer et convertir la colonne de pourcentage (profit_pct_str)
    # 1. Enlever le symbole '%'
    # 2. Convertir en numérique, puis diviser par 100
    df['profit_pct'] = df['profit_pct_str'].str.replace('%', '', regex=False)
    df['profit_pct'] = pd.to_numeric(df['profit_pct'], errors='coerce') / 100.0
    
    # Suppression des lignes contenant des NaN (données invalides)
    df = df.dropna()
    
    # 2.2 Calcul du bénéfice réel
    # Profit = cost * profit_pct
    df['profit_value'] = df['cost'] * df['profit_pct']
    
    # 2.3 Application de la contrainte budgétaire initiale
    df = df[df['cost'] <= BUDGET_MAX]
    
    # Conversion en liste de dictionnaires pour l'algorithme
    actions = df[['id', 'cost', 'profit_value']].to_dict('records')
    
    print(f"-> {len(actions)} actions retenues pour l'analyse (après nettoyage).")
    return actions


# 
# 3. ALGORITHME DE FORCE BRUTE (SOLUTION 1)
# 

def force_brute_optimale(actions):
    """
    Implémentation de l'algorithme de Force Brute (Sac à Dos 0/1).
    """
    meilleur_profit = 0.0
    meilleur_cout = 0.0
    meilleure_combinaison = []

    N = len(actions) 
    
    print(f"\n ÉTAPE 2: EXÉCUTION DE L'ALGORITHME ")
    print(f"-> Nombre d'actions (N): {N}")
    print(f"-> Nombre de combinaisons à tester (2^N): {2**N:,}")

    # Itérer sur toutes les tailles de combinaisons, de 1 à N actions
    for k in range(1, N + 1):
        
        # Générateur de combinaisons
        for combinaison in combinations(actions, k):
            
            # Calculer le coût total et le profit total
            cout_actuel = sum(action['cost'] for action in combinaison)
            profit_actuel = sum(action['profit_value'] for action in combinaison)
            
            # Vérification de la contrainte budgétaire
            if cout_actuel <= BUDGET_MAX:
                
                # Mise à jour de l'optimum
                if profit_actuel > meilleur_profit:
                    meilleur_profit = profit_actuel
                    meilleur_cout = cout_actuel
                    meilleure_combinaison = list(combinaison)

    # Extraction des noms d'actions
    noms_actions_selectionnees = [action['id'] for action in meilleure_combinaison]
    
    return noms_actions_selectionnees, meilleur_cout, meilleur_profit


# 
# 4. EXÉCUTION ET AFFICHAGE DES RÉSULTATS
# 

if __name__ == "__main__":
    
    # 1. Préparer les données 
    actions_a_traiter = preparer_donnees(NOM_DU_FICHIER_TEST)

    if actions_a_traiter:
        
        start_time = time.time()
        
        # 2. Exécuter l'algorithme
        actions_selectionnees, cout_total, profit_total = force_brute_optimale(actions_a_traiter)
        
        end_time = time.time()
        temps_execution = end_time - start_time
        
        # 3. Afficher les livrables
        print("\n==============================================")
        print("    RÉSULTAT OPTIMAL (SOLUTION FORCE BRUTE)")
        print("==============================================")
        print(f"Temps d'exécution: {temps_execution:.4f} secondes")
        print(f"Budget Max. alloué: {BUDGET_MAX:,.2f} F CFA")
        print("-")
        print(f"Coût Total des actions: {cout_total:,.2f} F CFA")
        print(f"Profit Total (après 2 ans): {profit_total:,.2f} F CFA")
        print(f"Nombre d'actions sélectionnées: {len(actions_selectionnees)}")
        
        print("\nListe des actions sélectionnées:")
        for action_id in actions_selectionnees:
            print(f"- {action_id}")
        print("==============================================")