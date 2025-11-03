import pandas as pd
import time
import os
import sys # Ajout pour l'estimation de la mémoire

# ---------------------------------------------
# 0. OUTIL D'ESTIMATION DE L'ESPACE MÉMOIRE
# ---------------------------------------------

def get_deep_size(obj, seen=None):
    """
    Estime la taille mémoire récursive d'un objet en octets.
    Nécessaire pour calculer la taille réelle d'une liste de dictionnaires.
    """
    if seen is None:
        seen = set()
    
    # Évite les références circulaires (important en Python)
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    
    # Taille de l'objet lui-même
    size = sys.getsizeof(obj)
    
    # Si c'est un conteneur, ajoute la taille de ses éléments
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
    '1': {'nom': 'data_test.csv', 'chemin': 'data/data_test.csv', 'description': 'Petit jeu de test (N=20) pour validation.'},
    '2': {'nom': 'dataset1_Python+P3.csv', 'chemin': 'data/dataset1_Python+P3.csv', 'description': 'Grand dataset 1 (N=958) pour test de performance.'},
    '3': {'nom': 'dataset2_Python+P3.csv', 'chemin': 'data/dataset2_Python+P3.csv', 'description': 'Grand dataset 2 (N=781) pour test de performance.'}
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
    
    # Affichage des options
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
        return None  # Signal pour quitter
    
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
        # Lecture avec encodage latin-1 pour gérer les caractères spéciaux
        df = pd.read_csv(nom_fichier, sep=';', encoding='latin-1')
    except Exception as e:
        print(f"ERREUR: Échec de la lecture du CSV (format ou encodage): {e}")
        return None 

    # Renommage des colonnes (gestion des deux formats de fichiers)
    if 'Actions' in df.columns[0] or 'name' in df.columns[0]:
        df.columns = ['id', 'cost_str', 'profit_pct_str']
    
    # 2.2 Conversion et Nettoyage
    
    # Nettoyage et conversion de la colonne de coût
    df['cost'] = df['cost_str'].astype(str).str.replace(r'[^\d.]', '', regex=True) 
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce') 
    
    # Nettoyage et conversion de la colonne de pourcentage
    df['profit_pct'] = df['profit_pct_str'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
    df['profit_pct'] = pd.to_numeric(df['profit_pct'], errors='coerce') / 100.0
    
    # Supprimer les lignes incomplètes ou invalides
    df = df.dropna(subset=['cost', 'profit_pct'])
    
    # 2.3 Calcul et Application des Contraintes
    
    # Calcul du bénéfice réel
    df['profit_value'] = df['cost'] * df['profit_pct']
    
    # Application des contraintes (coût > 0 et coût <= BUDGET_MAX)
    df = df[(df['cost'] > 0) & (df['cost'] <= BUDGET_MAX)] 
    
    # Calcul du critère Glouton : Ratio Profit/Coût
    df['ratio'] = df['profit_value'] / df['cost']
    
    # Conversion en liste de dictionnaires pour l'algorithme
    actions = df[['id', 'cost', 'profit_value', 'ratio']].to_dict('records')
    
    print(f"-> {len(actions)} actions retenues pour l'analyse (après nettoyage).")
    return actions


# ---------------------------------------------
# 4. ALGORITHME GLOUTON (SOLUTION OPTIMISÉE)
# ---------------------------------------------

def algorithme_glouton(actions, budget_max):
    """
    Résout le problème du Sac à Dos 0/1 en utilisant une stratégie gloutonne 
    basée sur le ratio Profit / Coût. Complexité O(N log N).
    
    Args:
        actions (list): Liste des actions (dictionnaires).
        budget_max (float): Budget maximum disponible.
        
    Returns:
        tuple: (IDs d'actions sélectionnées, coût total, profit total, espace_trie_bytes).
    """
    
    # 1. Tri des actions : Clé de l'algorithme glouton (O(N log N) en temps, O(N) en espace auxiliaire)
    # Tri par ratio décroissant (du meilleur rendement au moins bon)
    actions_triees = sorted(actions, key=lambda x: x['ratio'], reverse=True)
    
    # --- CALCUL DE L'ESPACE AUXILIAIRE O(N) ---
    # La liste triée est la structure qui consomme le plus d'espace auxiliaire dans l'algorithme.
    # C'est l'espace O(N) car on crée une copie triée de la liste d'entrée.
    espace_trie_bytes = get_deep_size(actions_triees)
    
    budget_restant = budget_max
    actions_selectionnees = []
    cout_total = 0.0
    profit_total = 0.0
    
    # 2. Remplissage glouton
    for action in actions_triees:
        cost = action['cost']
        profit = action['profit_value']
        
        # On prend l'action la plus "rentable" si elle rentre dans le budget
        if cost <= budget_restant:
            actions_selectionnees.append(action['id'])
            budget_restant -= cost
            cout_total += cost
            profit_total += profit
            
    return actions_selectionnees, cout_total, profit_total, espace_trie_bytes


# ---------------------------------------------
# 5. EXÉCUTION PRINCIPALE
# ---------------------------------------------

if __name__ == "__main__":
    
    en_cours = True
    while en_cours:
        
        # Étape 1: Demander à l'utilisateur de choisir le fichier
        fichier_a_utiliser = choisir_fichier()
        
        if fichier_a_utiliser is None:
            en_cours = False # L'utilisateur a choisi de quitter
            continue

        # Étape 2: Préparer les données
        actions_a_traiter = preparer_donnees(fichier_a_utiliser)
        N = len(actions_a_traiter)

        if actions_a_traiter:
            
            print(f"\n--- DÉMARRAGE DE L'ANALYSE PAR ALGORITHME GLOUTON (sur {fichier_a_utiliser}) ---")
            
            start_time = time.time()
            
            # Étape 3: Exécuter l'algorithme
            actions_selectionnees, cout_total, profit_total, espace_trie_bytes = algorithme_glouton(actions_a_traiter, BUDGET_MAX)
            
            end_time = time.time()
            temps_execution = end_time - start_time
            
            # Le calcul de l'espace O(N) est déjà fait dans la fonction
            
            # Étape 4: Afficher les résultats du Glouton
            print("\n==============================================")
            print("      RÉSULTAT (SOLUTION GLOUTONNE)")
            print("==============================================")
            print(f"Fichier de données: {fichier_a_utiliser}")
            print(f"Nombre d'actions d'entrée (N): {N}")
            print(f"Budget Max. alloué: {BUDGET_MAX:,.2f} F CFA")
            print("----------------------------------------------")
            print(f"Coût Total des actions: {cout_total:,.2f} F CFA")
            print(f"Profit Total (après 2 ans): {profit_total:,.2f} F CFA")
            print(f"Nombre d'actions sélectionnées: {len(actions_selectionnees)}")
            print("----------------------------------------------")
            print(f"Temps d'exécution (Complexité O(N log N)): {temps_execution:.6f} secondes")
            # AFFICHAGE DE L'ESPACE MÉMOIRE AUXILIAIRE O(N)
            print(f"Espace mémoire auxiliaire (Complexité O(N)): {espace_trie_bytes:,} octets") 
            print("----------------------------------------------")
            
            print("\nListe COMPLÈTE des actions sélectionnées par le Glouton:")
            # Affiche la liste des actions sélectionnées
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