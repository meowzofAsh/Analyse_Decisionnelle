import pandas as pd
import time
import os
import numpy as np 


# 1. CONSTANTES DU PROJET

BUDGET_MAX = 500000

# Chemins des fichiers 
#NOM_DU_FICHIER_TEST = 'data/data_test.csv'
#NOM_DU_FICHIER_DATA1 = 'data/dataset1_Python+P3.csv'
NOM_DU_FICHIER_DATA2 = 'data/dataset2_Python+P3.csv'

 
# 2. FONCTION DE PRÉPARATION DES DONNÉES (CORRIGÉE)


def preparer_donnees(nom_fichier):
    """
    Lit le fichier CSV, nettoie, calcule le profit réel et ajoute le ratio.
    """
    print(f"\n ÉTAPE 1: PRÉPARATION DES DONNÉES ")
    print(f"-> Tentative de lecture du fichier: {nom_fichier}")
    

    if not os.path.exists(nom_fichier):
        print(f"ERREUR FATALE: Fichier '{nom_fichier}' non trouvé. Vérifiez le chemin 'data/' et le nom du fichier.")
        return None
    
    try:
        # Tentative de lecture (latin-1 pour les accent et la langue française)
        df = pd.read_csv(nom_fichier, sep=';', encoding='latin-1')
    except Exception as e:
        # df n'est pas assigné si une erreur survient ici
        print(f"ERREUR: Échec de la lecture du CSV (format ou encodage): {e}")
        return None # Sortie si la lecture échoue

    # 2.1 Renommage des colonnes (gestion des deux formats de fichiers)
    if 'Actions' in df.columns[0] or 'name' in df.columns[0]:
        df.columns = ['id', 'cost_str', 'profit_pct_str']
    else:
        print("Avertissement: Format de colonnes non reconnu. Le script tente de continuer.")

    # 2.2 Conversion et Nettoyage
    
    # Nettoyer et convertir la colonne de coût (enlève les caractères non numériques et convertit en float)
    df['cost'] = df['cost_str'].astype(str).str.replace(r'[^\d.]', '', regex=True) 
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce') 
    
    # Nettoyer et convertir la colonne de pourcentage (enlève %, remplace virgule par point)
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
    
    # Conversion en liste de dictionnaires
    actions = df[['id', 'cost', 'profit_value', 'ratio']].to_dict('records')
    
    print(f"-> {len(actions)} actions retenues pour l'analyse (après nettoyage).")
    return actions


# 
# 3. ALGORITHME GLOUTON (SOLUTION ALTERNATIVE OPTIMISÉE)
# 

def algorithme_glouton(actions, budget_max):
    """
    Résout le problème du Sac à Dos 0/1 en utilisant une stratégie gloutonne 
    basée sur le ratio Profit / Coût. Complexité O(N log N).
    """
    
    # 1. Tri des actions : C'est l'étape clé du glouton.
    actions_triees = sorted(actions, key=lambda x: x['ratio'], reverse=True)
    
    budget_restant = budget_max
    actions_selectionnees = []
    cout_total = 0.0
    profit_total = 0.0
    
    # 2. Remplissage glouton
    for action in actions_triees:
        cost = action['cost']
        profit = action['profit_value']
        
        # Le choix glouton : on prend l'action si elle rentre dans le budget restant.
        if cost <= budget_restant:
            actions_selectionnees.append(action['id'])
            budget_restant -= cost
            cout_total += cost
            profit_total += profit
            
    return actions_selectionnees, cout_total, profit_total


# 
# 4. EXÉCUTION ET AFFICHAGE DES RÉSULTATS
# 

if __name__ == "__main__":
    
    # Utilisons le Dataset 1 pour montrer la rapidité
    fichier_a_utiliser = NOM_DU_FICHIER_DATA2

    # 1. Préparer les données
    actions_a_traiter = preparer_donnees(fichier_a_utiliser)

    if actions_a_traiter:
        
        print(f"\n DÉMARRAGE DE L'ANALYSE PAR ALGORITHME GLOUTON (sur {fichier_a_utiliser}) ")
        
        start_time = time.time()
        
        # 2. Exécuter l'algorithme
        actions_selectionnees, cout_total, profit_total = algorithme_glouton(actions_a_traiter, BUDGET_MAX)
        
        end_time = time.time()
        temps_execution = end_time - start_time
        
        # 3. Afficher les livrables
        print("\n==============================================")
        print("    RÉSULTAT (SOLUTION GLOUTONNE)")
        print("==============================================")
        print(f"Temps d'exécution: {temps_execution:.6f} secondes (Extrêmement rapide)")
        print(f"Fichier de données: {fichier_a_utiliser}")
        print(f"Budget Max. alloué: {BUDGET_MAX:,.2f} F CFA")
        print("-")
        print(f"Coût Total des actions: {cout_total:,.2f} F CFA")
        print(f"Profit Total (après 2 ans): {profit_total:,.2f} F CFA")
        print(f"Nombre d'actions sélectionnées: {len(actions_selectionnees)}")
        
        print("\nListe des actions sélectionnées (premières affichées):")
        for action_id in actions_selectionnees[:10]:
            print(f"- {action_id}")
        if len(actions_selectionnees) > 10:
             print(f"... et {len(actions_selectionnees) - 10} autres actions.")
        print("==============================================")