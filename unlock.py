import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Unlock! Tracker", layout="wide", page_icon="🎮")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_game_data():
    # Lecture brute
    df_loaded = conn.read(ttl=0)
    
    if df_loaded.empty:
        return pd.DataFrame()

    # NORMALISATION FORCEE DES COLONNES
    # On met tout en minuscule, on retire les espaces et les caractères bizarres
    df_loaded.columns = [str(c).lower().replace(' ', '_').strip() for c in df_loaded.columns]
    
    # On cherche la colonne qui ressemble le plus à "boite_titre"
    # Si elle n'existe pas, on prend la première colonne qui contient du texte
    if 'boite_titre' not in df_loaded.columns:
        return pd.DataFrame() # On s'arrête si on ne trouve pas la colonne principale

    # Nettoyage des lignes vides
    df_loaded = df_loaded.dropna(subset=['boite_titre'])
    df_loaded = df_loaded[df_loaded['boite_titre'].astype(str).str.len() > 1]
    
    return df_loaded.fillna("")

def save_game_data(df_to_save):
    conn.update(data=df_to_save)
    st.cache_data.clear()

# --- CHARGEMENT ---
df = load_game_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 JOUEURS")
    joueurs = ["Papa", "Maman", "Lucas", "Julie", "Thomas", "Sarah", "Antoine", "Emma", "Victor", "Chloe"] 
    utilisateur = st.selectbox("Qui es-tu ?", joueurs)
    
    st.divider()
    st.link_button("🌐 Site Unlock (Nouveautés)", "https://www.spacecowboys-games.com/game/unlock/", use_container_width=True)
    
    if st.button("🔄 Actualiser la page", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # ZONE DE DEBUG (Masquée par défaut)
    with st.expander("🛠 Debug Colonnes"):
        if not df.empty:
            st.write("Colonnes lues :", list(df.columns))
        else:
            st.write("Le fichier semble vide ou illisible.")

# --- INTERFACE PRINCIPALE ---
st.title(f"🎮 Suivi Unlock : {utilisateur}")

if df.empty:
    st.error("⚠️ Impossible de trouver la colonne 'boite_titre' dans ton Google Sheet.")
    st.info("Vérifie que tes titres de colonnes sont bien sur la PREMIÈRE LIGNE de ton fichier.")
    st.stop()

# Gestion de la colonne de suivi
col_suivi = f"fait_{utilisateur.lower()}"
if col_suivi not in df.columns:
    df[col_suivi] = ""

# Recherche
search = st.text_input("Filtrer par nom de boîte...", "").lower()
df_display = df[df['boite_titre'].astype(str).str.lower().str.contains(search)] if search else df

# --- AFFICHAGE DES CARTES ---
for idx, row in df_display.iterrows():
    with st.container():
        c_img, c_txt = st.columns([1, 4])
        
        with c_img:
            # Sécurité sur image_url : on vérifie si la colonne existe
            url = ""
            if 'image_url' in row:
                url = str(row['image_url']).strip()
            
            if url.startswith('http'):
                st.image(url, width=100)
            else:
                st.image("https://via.placeholder.com/100?text=Pas+d'image", width=100)
        
        with c_txt:
            # Sécurité sur boite_titre
            titre = row['boite_titre'] if 'boite_titre' in row else "Sans titre"
            st.subheader(titre)
    
    # Checkboxes
    cols = st.columns(3)
    faits_actuels = [x.strip() for x in str(row[col_suivi]).split(',') if x.strip()]

    for i in range(1, 4):
        with cols[i-1]:
            # Sécurité sur les noms de jeux
            col_nom = f'j{i}_nom'
            game_name = str(row[col_nom]).strip() if col_nom in row and str(row[col_nom]) != "nan" and str(row[col_nom]) != "" else f"Jeu {i}"
            
            game_id = f"Jeu{i}"
            is_done = game_id in faits_actuels
            
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
