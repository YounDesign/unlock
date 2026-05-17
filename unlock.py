import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Unlock! Tracker", layout="wide", page_icon="🎮")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_game_data():
    # On lit l'onglet Catalogue (Assurez-vous que le nom est exact dans votre Sheet)
    df_loaded = conn.read(worksheet="Catalogue", ttl=0)
    
    # Nettoyage : On enlève les lignes vides
    if 'boite_titre' in df_loaded.columns:
        df_loaded = df_loaded.dropna(subset=['boite_titre'])
        df_loaded = df_loaded[df_loaded['boite_titre'] != ""]
    
    # Vérification des colonnes nécessaires
    required = ['id', 'boite_titre', 'image_url', 'j1_nom', 'j1_fait', 'j2_nom', 'j2_fait', 'j3_nom', 'j3_fait']
    for col in required:
        if col not in df_loaded.columns:
            df_loaded[col] = "False" if "fait" in col else ""
            
    return df_loaded

def save_game_data(df_to_save):
    conn.update(worksheet="Catalogue", data=df_to_save)
    st.cache_data.clear()

# --- INTERFACE ---
df = load_game_data()

# --- SIDEBAR (LIEN ET ADMIN) ---
with st.sidebar:
    st.title("⚙️ Options")
    
    # LE LIEN POUR VÉRIFIER LES MISES À JOUR
    st.markdown("### 🔍 Vérifier les nouveautés")
    st.link_button("🌐 Aller sur Space Cowboys (Unlock)", "https://www.spacecowboys.fr/unlock-games", use_container_width=True)
    
    st.info("Si vous avez ajouté des jeux dans votre Google Sheet, cliquez ci-dessous :")
    if st.button("🔄 Actualiser l'App", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- CONTENU PRINCIPAL ---
st.title("🎮 Mon Suivi Unlock!")
st.write("Cochez vos jeux faits. Les changements sont enregistrés directement dans votre Sheet.")

# Recherche
search = st.text_input("Filtrer par nom de boîte...", "").lower()
df_display = df[df['boite_titre'].str.lower().str.contains(search)] if search else df

# Affichage des cartes
for idx, row in df_display.iterrows():
    # On prépare l'image
    img = row['image_url'] if row['image_url'] else "https://via.placeholder.com/150"
    
    # Design de la carte
    st.markdown(f"""
    <div style='background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 10px;'>
        <div style='display: flex; align-items: center; gap: 20px;'>
            <img src="{img}" style='width: 70px; height: 70px; border-radius: 5px; object-fit: cover;'>
            <h3 style='margin: 0;'>{row['boite_titre']}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Les 3 jeux (checkboxes)
    cols = st.columns(3)
    for i in range(1, 4):
        with cols[i-1]:
            game_name = row[f'j{i}_nom']
            is_done = str(row[f'j{i}_fait']) == "True"
            
            # Utilisation de l'index de ligne (idx) pour éviter l'erreur de doublon
            new_val = st.checkbox(f"{game_name}", value=is_done, key=f"chk_{idx}_{i}")
            
            if new_val != is_done:
                df.at[idx, f'j{i}_fait'] = str(new_val)
                save_game_data(df)
                st.rerun()
    st.divider()
