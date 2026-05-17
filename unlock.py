import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Unlock! Tracker", layout="wide", page_icon="🎮")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_game_data():
    # Lit la première feuille
    df_loaded = conn.read(ttl=0)
    
    # NETTOYAGE DES COLONNES : on met tout en minuscules et on remplace les espaces par des _
    df_loaded.columns = [str(c).lower().replace(' ', '_').strip() for c in df_loaded.columns]
    
    # Liste des colonnes dont on a ABSOLUMENT besoin
    required = ['boite_titre', 'image_url', 'j1_nom', 'j2_nom', 'j3_nom']
    for col in required:
        if col not in df_loaded.columns:
            df_loaded[col] = "" # Crée la colonne vide si elle manque
    
    # On supprime les lignes où le titre est vide
    df_loaded = df_loaded.dropna(subset=['boite_titre'])
    df_loaded = df_loaded[df_loaded['boite_titre'].astype(str).str.strip() != ""]
    
    return df_loaded.fillna("")

def save_game_data(df_to_save):
    # On ne sauvegarde pas les colonnes temporaires de calcul
    conn.update(data=df_to_save)
    st.cache_data.clear()

# --- CHARGEMENT ---
try:
    df = load_game_data()
except Exception as e:
    st.error(f"Erreur lors du chargement du Google Sheet : {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("👥 Joueurs")
    # Liste des joueurs
    joueurs = ["Papa", "Maman", "Lucas", "Julie", "Ami1", "Ami2", "Ami3", "Ami4", "Ami5", "Ami6"] 
    utilisateur = st.selectbox("Qui es-tu ?", joueurs)
    
    st.divider()
    st.markdown("### 🔍 Liens")
    st.link_button("🌐 Site Unlock (Vérifier nouveautés)", "https://www.spacecowboys-games.com/game/unlock/", use_container_width=True)
    
    if st.button("🔄 Actualiser l'App", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title(f"🎮 Suivi de {utilisateur}")

# Nom de la colonne pour ce joueur
col_suivi = f"fait_{utilisateur.lower()}"
if col_suivi not in df.columns:
    df[col_suivi] = ""

# Recherche
search = st.text_input("Filtrer par nom de boîte...", "").lower()
df_display = df[df['boite_titre'].astype(str).str.lower().str.contains(search)] if search else df

if df_display.empty:
    st.info("Aucune boîte trouvée. Vérifie ton fichier Google Sheet !")
    st.write("Colonnes détectées dans ton fichier :", list(df.columns))

for idx, row in df_display.iterrows():
    # Affichage de la boîte
    with st.container():
        c_img, c_txt = st.columns([1, 5])
        
        with c_img:
            url = str(row['image_url']).strip()
            if url.startswith('http'):
                st.image(url, width=100)
            else:
                st.image("https://via.placeholder.com/100?text=Lien+Image+HS", width=100)
        
        with c_txt:
            st.subheader(row['boite_titre'])
    
    # Gestion des 3 jeux
    cols = st.columns(3)
    # On nettoie la liste des jeux faits
    faits_actuels = [x.strip() for x in str(row[col_suivi]).split(',') if x.strip()]

    for i in range(1, 4):
        with cols[i-1]:
            # Sécurité sur le nom du jeu
            col_name = f'j{i}_nom'
            game_name = str(row[col_name]).strip() if col_name in row else f"Jeu {i}"
            if not game_name or game_name == "nan":
                game_name = f"Jeu {i}"
                
            game_id = f"Jeu{i}"
            is_done = game_id in faits_actuels
            
            # Checkbox
            if st.checkbox(game_name, value=is_done, key=f"{utilisateur}_{idx}_{i}"):
                if not is_done:
                    faits_actuels.append(game_id)
                    df.at[idx, col_suivi] = ",".join(faits_actuels)
                    save_game_data(df)
                    st.rerun()
            else:
                if is_done:
                    if game_id in faits_actuels: faits_actuels.remove(game_id)
                    df.at[idx, col_suivi] = ",".join(faits_actuels)
                    save_game_data(df)
                    st.rerun()
    st.divider()
