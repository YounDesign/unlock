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
    
    # NETTOYAGE : On supprime toutes les lignes où le titre est vide
    if 'boite_titre' in df_loaded.columns:
        df_loaded = df_loaded.dropna(subset=['boite_titre'])
        df_loaded = df_loaded[df_loaded['boite_titre'].str.strip() != ""]
    
    return df_loaded.fillna("")

def save_game_data(df_to_save):
    conn.update(data=df_to_save)
    st.cache_data.clear()

# --- CHARGEMENT ---
df = load_game_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("👥 Joueurs")
    # Liste des joueurs (Tu peux en ajouter d'autres ici)
    joueurs = ["Papa", "Maman", "Lucas", "Julie", "Ami1", "Ami2"] 
    utilisateur = st.selectbox("Qui es-tu ?", joueurs)
    
    st.divider()
    st.markdown("### 🔍 Liens Utiles")
    st.link_button("🌐 Site Unlock (Nouveautés)", "https://www.spacecowboys-games.com/game/unlock/", use_container_width=True)
    
    if st.button("🔄 Actualiser la page", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title(f"🎮 Suivi de {utilisateur}")

# Nom de la colonne pour ce joueur
col_suivi = f"Fait_{utilisateur}"
if col_suivi not in df.columns:
    df[col_suivi] = ""

# Recherche
search = st.text_input("Filtrer par nom de boîte...", "").lower()
df_display = df[df['boite_titre'].str.lower().str.contains(search)] if search else df

if df_display.empty:
    st.warning("Aucune donnée trouvée dans ton fichier Google Sheets. Vérifie que la colonne 'boite_titre' est bien remplie.")

for idx, row in df_display.iterrows():
    # Affichage de la boîte
    with st.container():
        c_img, c_txt = st.columns([1, 5])
        
        with c_img:
            url = str(row['image_url']).strip()
            if url.startswith('http'):
                st.image(url, width=100)
            else:
                # Image par défaut si le lien est mort ou vide
                st.image("https://via.placeholder.com/100?text=Pas+d'image", width=100)
        
        with c_txt:
            st.subheader(row['boite_titre'])
    
    # Gestion des 3 jeux
    cols = st.columns(3)
    faits_actuels = [x.strip() for x in str(row[col_suivi]).split(',') if x.strip()]

    for i in range(1, 4):
        with cols[i-1]:
            # On récupère le nom du jeu. S'il est vide, on met un nom par défaut pour éviter l'erreur
            game_name = str(row[f'j{i}_nom']).strip()
            if not game_name:
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
                    faits_actuels.remove(game_id)
                    df.at[idx, col_suivi] = ",".join(faits_actuels)
                    save_game_data(df)
                    st.rerun()
    st.divider()
