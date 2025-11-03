import pandas as pd
import time
import os
import sys
from itertools import combinations 

# ---------------------------------------------
# 0. OUTIL D'ESTIMATION DE L'ESPACE MÉMOIRE
# ---------------------------------------------

def get_deep_size(obj, seen=None):
    """
    Estime la taille mémoire récursive d'un objet en octets.
    """
    if seen is None:
        seen = set()
    
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    
    size = sys.getsizeof(obj)
    
    if isinstance(obj, dict):
        size += sum(get_deep_size(v, seen) + get_deep_size(k, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set)):
        size += sum(get_deep_size(item, seen) for item in obj)
    
    return size


# ---------------------------------------------
# 1. CONSTANTES ET DONNÉES DE RÉFÉRENCE
# ---------------------------------------------
BUDGET_MAX = 500000.0  # Budget maximal en F CFA (float)

# Chemins des fichiers disponibles
FICHIERS_DISPONIBLES = {
    '1': {'nom': 'data_test.csv', 'chemin': 'data/data_test.csv', 'description': 'Petit jeu de test pour validation.'},
    '2': {'nom': 'dataset1_Python+P3.csv', 'chemin': 'data/dataset1_Python+P3.csv', 'description': 'Grand dataset 1 pour test de performance.'},
    '3': {'nom': 'dataset2_Python+P3.csv', 'chemin': 'data/dataset2_Python+P3.csv', 'description': 'Grand dataset 2 pour test de performance.'}
}


# ---------------------------------------------
# 2. SÉLECTION INTERACTIVE DU FICHIER
# ---------------------------------------------

def choisir_fichier():
    """
    Demande à l'utilisateur de choisir l'un des datasets disponibles.
    """
    print("\n==============================================")
    print("      SÉLECTION DU JEU DE DONNÉES")
    print("==============================================")
    
    for key, info in FICHIERS_DISPONIBLES.items():
        print(f"  [{key}] {info['nom']} - ({info['description']})")
    print("  [Q] Quitter l'application")
    print("----------------------------------------------")
    
    choix = ''
    while choix not in FICHIERS_DISPONIBLES and choix.upper() != 'Q':
        choix = input("Entrez le numéro du fichier (1, 2, 3) ou 'Q' : ").upper()
        if choix not in FICHIERS_DISPONIBLES and choix != 'Q':
            print("Choix invalide. Veuillez entrer 1, 2, 3 ou Q.")
    
    if choix == 'Q':
        return None
    
    fichier_info = FICHIERS_DISPONIBLES[choix]
    return fichier_info['chemin']

# ---------------------------------------------
# 3. FONCTION DE PRÉPARATION DES DONNÉES
# ---------------------------------------------

def preparer_donnees(nom_fichier):
    """
    Lit le fichier CSV, nettoie, calcule le profit réel et ajoute le ratio.
    """
    print(f"\n--- ÉTAPE 1: PRÉPARATION DES DONNÉES ---")
    print(f"-> Tentative de lecture du fichier: {nom_fichier}")
    
    if not os.path.exists(nom_fichier):
        print(f"ERREUR FATALE: Fichier '{nom_fichier}' non trouvé. Vérifiez le chemin 'data/' et le nom du fichier.")
        return None
    
    try:
        df = pd.read_csv(nom_fichier, sep=';', encoding='latin-1')
    except Exception as e:
        print(f"ERREUR: Échec de la lecture du CSV (format ou encodage): {e}")
        return None 

    if 'Actions' in df.columns[0] or 'name' in df.columns[0]:
        df.columns = ['id', 'cost_str', 'profit_pct_str']
    
    df['cost'] = df['cost_str'].astype(str).str.replace(r'[^\d.]', '', regex=True) 
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce') 
    
    df['profit_pct'] = df['profit_pct_str'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
    df['profit_pct'] = pd.to_numeric(df['profit_pct'], errors='coerce') / 100.0
    
    df = df.dropna(subset=['cost', 'profit_pct'])
    
    df['profit_value'] = df['cost'] * df['profit_pct']
    
    df = df[(df['cost'] > 0) & (df['cost'] <= BUDGET_MAX)] 
    
    df['ratio'] = df['profit_value'] / df['cost']
    
    actions = df[['id', 'cost', 'profit_value', 'ratio']].to_dict('records')
    
    print(f"-> {len(actions)} actions retenues pour l'analyse (après nettoyage).")
    return actions


# ---------------------------------------------
# 4. ALGORITHME DE FORCE BRUTE
# ---------------------------------------------

def algorithme_force_brute(actions, budget_max):
    """
    Algorithme de Force Brute: Complexité O(2^N * N) en temps, O(N) en espace auxiliaire (stockage du résultat).
    """
    
    N = len(actions)
    meilleur_profit = -1.0
    meilleures_actions = []
    meilleur_cout = 0.0
    
    # Itération sur toutes les combinaisons possibles (2^N)
    for i in range(1, N + 1):
        for combinaison in combinations(actions, i):
            cout_actuel = sum(action['cost'] for action in combinaison)
            
            if cout_actuel <= budget_max:
                profit_actuel = sum(action['profit_value'] for action in combinaison)
                
                if profit_actuel > meilleur_profit:
                    meilleur_profit = profit_actuel
                    meilleur_cout = cout_actuel
                    # Stocker les IDs de la meilleure solution
                    meilleures_actions = [action['id'] for action in combinaison]
    
    # --- CALCUL DE L'ESPACE AUXILIAIRE O(N) ---
    # L'espace O(N) auxiliaire est l'espace nécessaire pour stocker la liste d'IDs de la meilleure solution.
    espace_auxiliaire_bytes = get_deep_size(meilleures_actions)
    
    return meilleures_actions, meilleur_cout, meilleur_profit, espace_auxiliaire_bytes


# ---------------------------------------------
# 5. EXÉCUTION PRINCIPALE
# ---------------------------------------------

if __name__ == "__main__":
    
    en_cours = True
    while en_cours:
        
        # Étape 1: Demander à l'utilisateur de choisir le fichier
        fichier_a_utiliser = choisir_fichier()
        
        if fichier_a_utiliser is None:
            en_cours = False
            continue

        # Étape 2: Préparer les données
        actions_a_traiter = preparer_donnees(fichier_a_utiliser)
        N = len(actions_a_traiter)

        if actions_a_traiter:
            
            # ------------------------------------------------------------------
            # EXÉCUTION DE L'ALGORITHME FORCE BRUTE
            # ------------------------------------------------------------------
            algo_nom = "FORCE BRUTE"
            complexite_temps = "O(2^N * N)"
            complexite_espace = "O(N)"
            
            print(f"\n--- DÉMARRAGE DE L'ANALYSE PAR ALGORITHME {algo_nom} (sur {fichier_a_utiliser}) ---")
            
            # ATTENTION : Avertissement pour les grands datasets
            if N > 20 and 'data_test' not in fichier_a_utiliser:
                 print("\n!!! ATTENTION !!! L'algorithme de Force Brute (O(2^N)) est EXTRÊMEMENT lent pour N > 20. L'exécution va être lancée mais peut prendre beaucoup de temps.")
            
            start_time = time.time()
            actions_selectionnees, cout_total, profit_total, espace_auxiliaire_bytes = algorithme_force_brute(actions_a_traiter, BUDGET_MAX)
            end_time = time.time()
            temps_execution = end_time - start_time
            
            # Afficher les résultats de la Force Brute
            print("\n==============================================")
            print(f"      RÉSULTAT (SOLUTION {algo_nom})")
            print("==============================================")
            print(f"Fichier de données: {fichier_a_utiliser}")
            print(f"Nombre d'actions d'entrée (N): {N}")
            print(f"Budget Max. alloué: {BUDGET_MAX:,.2f} F CFA")
            print("----------------------------------------------")
            print(f"Coût Total des actions: {cout_total:,.2f} F CFA")
            print(f"Profit Total (après 2 ans): {profit_total:,.2f} F CFA")
            print(f"Nombre d'actions sélectionnées: {len(actions_selectionnees)}")
            print("----------------------------------------------")
            print(f"Temps d'exécution (Complexité {complexite_temps}): {temps_execution:.6f} secondes")
            print(f"Espace mémoire auxiliaire (Complexité {complexite_espace}): {espace_auxiliaire_bytes:,} octets") 
            print("==============================================")
            
            print(f"\nListe COMPLÈTE des actions sélectionnées par la {algo_nom}:")
            for action_id in actions_selectionnees:
                print(f"- {action_id}")
            print("==============================================")


        # ------------------------------------------------
        # Choix de continuer ou de quitter après les résultats
        # ------------------------------------------------
        action = ''
        print("\n----------------------------------------------")
        while action.upper() not in ['C', 'Q']:
            action = input("Voulez-vous [C]Choisir un autre fichier ou [Q]Quitter ? ").upper()
        
        if action == 'Q':
            en_cours = False
            print("\n--- Application terminée. Au revoir ! ---")