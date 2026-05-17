import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Unlock! Tracker", layout="wide", page_icon="🎮")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CHARGEMENT DES UTILISATEURS ---
def load_users():
    try:
        # Lit l'onglet "Utilisateurs"
        users_df = conn.read(worksheet="Utilisateurs", ttl=0)
        # On prend la première colonne et on enlève les vides
        return users_df.iloc[:, 0].dropna().tolist()
    except:
        # Liste de secours si l'onglet n'est pas trouvé
        return ["Papa", "Maman", "Lucas"]

# --- CHARGEMENT DES JEUX ---
def load_game_data():
    # Lit l'onglet principal (Catalogue)
    df_loaded = conn.read(ttl=0)
    
    if df_loaded.empty:
        return pd.DataFrame()

    # Normalisation des colonnes (minuscules, sans espaces)
    df_loaded.columns = [str(c).lower().replace(' ', '_').strip() for c in df_loaded.columns]
    
    # On garde seulement les lignes avec un titre de boîte
    if 'boite_titre' in df_loaded.columns:
        df_loaded = df_loaded.dropna(subset=['boite_titre'])
        df_loaded = df_loaded[df_loaded['boite_titre'].astype(str).str.len() > 1]
    
    return df_loaded.fillna("")

def save_game_data(df_to_save):
    conn.update(data=df_to_save)
    st.cache_data.clear()

# --- INITIALISATION ---
joueurs = load_users()
df = load_game_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 JOUEURS")
    utilisateur = st.selectbox("Qui es-tu ?", joueurs)
    
    st.divider()
    st.markdown("### 🔍 Liens")
    st.link_button("🌐 Site Unlock (Nouveautés)", "https://www.spacecowboys-games.com/game/unlock/", use_container_width=True)
    
    if st.button("🔄 Actualiser les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title(f"🎮 Suivi Unlock : {utilisateur}")

if df.empty:
    st.error("⚠️ Impossible de lire les jeux. Vérifie ton onglet 'Catalogue'.")
    st.stop()

# Gestion de la colonne de suivi pour le joueur
col_suivi = f"fait_{utilisateur.lower().replace(' ', '_')}"
if col_suivi not in df.columns:
    df[col_suivi] = ""

# Recherche
search = st.text_input("Rechercher une boîte...", "").lower()
df_display = df[df['boite_titre'].astype(str).str.lower().str.contains(search)] if search else df

# --- AFFICHAGE ---
for idx, row in df_display.iterrows():
    with st.container():
        c_img, c_txt = st.columns([1, 4])
        
        with c_img:
            # Affichage image
            url = str(row['image_url']).strip() if 'image_url' in row else ""
            if url.startswith('http'):
                st.image(url, width=100)
            else:
                st.image("https://via.placeholder.com/100?text=No+Image", width=100)
        
        with c_txt:
            st.subheader(row['boite_titre'])
    
    # Les 3 scénarios
    cols = st.columns(3)
    faits_actuels = [x.strip() for x in str(row[col_suivi]).split(',') if x.strip()]

    for i in range(1, 4):
        with cols[i-1]:
            # RECUPERATION DU VRAI NOM DU JEU
            col_nom = f'j{i}_nom'
            if col_nom in row and str(row[col_nom]).strip() != "" and str(row[col_nom]) != "nan":
                game_label = str(row[col_nom])
            else:
                game_label = f"Scénario {i} (vide)"
            
            game_id = f"Jeu{i}"
            is_done = game_id in faits_actuels
            
            # Case à cocher avec le vrai nom
            if st.checkbox(game_label, value=is_done, key=f"{utilisateur}_{idx}_{i}"):
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
