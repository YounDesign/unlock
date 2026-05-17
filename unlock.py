import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Unlock! Tracker", layout="wide", page_icon="🎮")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FONCTIONS UTILISATEURS ---
def load_users():
    try:
        users_df = conn.read(worksheet="Utilisateurs", ttl=0)
        return users_df.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return []

def add_new_user(new_name):
    try:
        current_users = load_users()
        if new_name not in current_users:
            current_users.append(new_name)
            new_df = pd.DataFrame(current_users, columns=["Noms"])
            conn.update(worksheet="Utilisateurs", data=new_df)
            st.cache_data.clear()
            return True
        return False
    except:
        return False

# --- FONCTIONS JEUX ---
def load_game_data():
    try:
        df_loaded = conn.read(ttl=0)
        if df_loaded.empty: return pd.DataFrame()
        
        # Normalisation des noms de colonnes pour le code
        orig_cols = list(df_loaded.columns)
        df_loaded.columns = [str(c).lower().replace(' ', '_').strip() for c in df_loaded.columns]
        
        # On s'assure d'identifier les colonnes D, E, F (index 3, 4, 5) 
        # au cas où les noms j1_nom ne seraient pas exacts
        if len(df_loaded.columns) >= 6:
            df_loaded['jeu_1_titre'] = df_loaded.iloc[:, 3] # Colonne D
            df_loaded['jeu_2_titre'] = df_loaded.iloc[:, 4] # Colonne E
            df_loaded['jeu_3_titre'] = df_loaded.iloc[:, 5] # Colonne F
            
        if 'boite_titre' in df_loaded.columns:
            df_loaded = df_loaded.dropna(subset=['boite_titre'])
            
        return df_loaded.fillna("")
    except:
        return pd.DataFrame()

def save_game_data(df_to_save):
    # On retire les colonnes de calcul temporaires avant de sauvegarder
    cols_to_drop = ['jeu_1_titre', 'jeu_2_titre', 'jeu_3_titre']
    df_db = df_to_save.drop(columns=[c for c in cols_to_drop if c in df_to_save.columns])
    conn.update(data=df_db)
    st.cache_data.clear()

# --- INITIALISATION ---
joueurs = load_users()
df = load_game_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 JOUEURS")
    with st.expander("➕ Nouveau joueur"):
        nouveau_nom = st.text_input("Nom")
        if st.button("Ajouter"):
            if nouveau_nom and add_new_user(nouveau_nom):
                st.success("Ajouté !"); st.rerun()

    if joueurs:
        utilisateur = st.selectbox("Qui es-tu ?", joueurs)
    else:
        st.warning("Ajoute un joueur !"); utilisateur = None

    st.divider()
    st.link_button("🌐 Site Unlock", "https://www.spacecowboys-games.com/game/unlock/", use_container_width=True)
    if st.button("🔄 Actualiser"):
        st.cache_data.clear(); st.rerun()

# --- INTERFACE PRINCIPALE ---
if not utilisateur:
    st.info("👋 Ajoute un joueur à gauche pour commencer.")
    st.stop()

st.title(f"🎮 Suivi Unlock : {utilisateur}")

# Colonne de suivi
col_suivi = f"fait_{utilisateur.lower().replace(' ', '_')}"
if col_suivi not in df.columns:
    df[col_suivi] = ""

search = st.text_input("Filtrer par nom de boîte...", "").lower()
df_display = df[df['boite_titre'].astype(str).str.lower().str.contains(search)] if search else df

# --- AFFICHAGE ---
for idx, row in df_display.iterrows():
    # 1. IMAGE EN GRAND
    url = str(row.get('image_url', '')).strip()
    if url.startswith('http'):
        st.image(url, use_container_width=True)
    else:
        st.info(f"🖼️ {row['boite_titre']} (Lien image manquant dans la colonne image_url)")

    # 2. TITRE DE LA BOITE
    st.subheader(row['boite_titre'])
    
    # 3. LES 3 JEUX (Colonnes D, E, F)
    cols = st.columns(3)
    faits_actuels = [x.strip() for x in str(row.get(col_suivi, "")).split(',') if x.strip()]

    # On utilise les colonnes D, E, F qu'on a mappé au chargement
    noms_jeux = [row['jeu_1_titre'], row['jeu_2_titre'], row['jeu_3_titre']]

    for i, game_label in enumerate(noms_jeux, 1):
        with cols[i-1]:
            # Sécurité si le nom est vide
            label = str(game_label).strip() if str(game_label).strip() != "" else f"Jeu {i}"
            
            game_id = f"Jeu{i}"
            is_done = game_id in faits_actuels
            
            # Affichage de la case à cocher
            if st.checkbox(label, value=is_done, key=f"{utilisateur}_{idx}_{i}"):
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
