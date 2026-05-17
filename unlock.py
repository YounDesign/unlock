import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Unlock! Tracker", layout="wide", page_icon="🎮")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FONCTIONS POUR LES UTILISATEURS ---
def load_users():
    try:
        users_df = conn.read(worksheet="Utilisateurs", ttl=0)
        return users_df.iloc[:, 0].dropna().astype(str).tolist()
    except Exception:
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
    except Exception:
        return False

# --- FONCTIONS POUR LES JEUX ---
def load_game_data():
    try:
        df_loaded = conn.read(ttl=0)
        if df_loaded.empty:
            return pd.DataFrame()
        
        # Normalisation des colonnes
        df_loaded.columns = [str(c).lower().replace(' ', '_').strip() for c in df_loaded.columns]
        
        # RÉCUPÉRATION DES COLONNES D, E, F (Index 3, 4, 5)
        if len(df_loaded.columns) >= 6:
            df_loaded['nom_jeu_1'] = df_loaded.iloc[:, 3]
            df_loaded['nom_jeu_2'] = df_loaded.iloc[:, 4]
            df_loaded['nom_jeu_3'] = df_loaded.iloc[:, 5]
            
        if 'boite_titre' in df_loaded.columns:
            df_loaded = df_loaded.dropna(subset=['boite_titre'])
            
        return df_loaded.fillna("")
    except Exception:
        return pd.DataFrame()

def save_game_data(df_to_save):
    cols_a_virer = ['nom_jeu_1', 'nom_jeu_2', 'nom_jeu_3']
    df_propre = df_to_save.drop(columns=[c for c in cols_a_virer if c in df_to_save.columns])
    conn.update(data=df_propre)
    st.cache_data.clear()

# --- INITIALISATION ---
joueurs = load_users()
df = load_game_data()

# --- SIDEBAR (MENU GAUCHE) ---
with st.sidebar:
    st.title("👤 JOUEURS")
    
    with st.expander("➕ Nouveau Joueur"):
        nouveau_nom = st.text_input("Prénom")
        if st.button("Ajouter"):
            if nouveau_nom and add_new_user(nouveau_nom):
                st.success(f"{nouveau_nom} ajouté !"); st.rerun()

    if joueurs:
        utilisateur = st.selectbox("Qui es-tu ?", joueurs)
    else:
        st.warning("Ajoute un joueur pour commencer.")
        utilisateur = None

    st.divider()
    st.link_button("🌐 Site Unlock (Nouveautés)", "https://www.spacecowboys-games.com/game/unlock/", use_container_width=True)
    if st.button("🔄 Actualiser"):
        st.cache_data.clear(); st.rerun()

# --- INTERFACE PRINCIPALE ---
if not utilisateur:
    st.info("👋 Bonjour ! Ajoute ton prénom dans la barre latérale pour commencer.")
    st.stop()

st.title(f"🎮 Suivi de {utilisateur}")

col_suivi = f"fait_{utilisateur.lower().replace(' ', '_')}"
if col_suivi not in df.columns:
    df[col_suivi] = ""

search = st.text_input("Filtrer les boîtes...", "").lower()
df_display = df[df['boite_titre'].astype(str).str.lower().str.contains(search)] if search else df

# --- AFFICHAGE DES JEUX ---
for idx, row in df_display.iterrows():
    
    # 1. IMAGE RÉDUITE (Moitié de la largeur, centrée)
    url = str(row.get('image_url', '')).strip()
    if url.startswith('http'):
        # On crée 3 colonnes : vide (25%), image (50%), vide (25%)
        # Cela réduit l'image de moitié par rapport à avant
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(url, use_container_width=True)
    else:
        st.info(f"🖼️ {row['boite_titre']} (Image manquante)")

    # 2. TITRE
    st.markdown(f"<h2 style='text-align: center;'>{row['boite_titre']}</h2>", unsafe_allow_html=True)
    
    # 3. LES 3 JEUX (Colonnes D, E, F)
    cols = st.columns(3)
    faits_actuels = [x.strip() for x in str(row.get(col_suivi, "")).split(',') if x.strip()]
    noms_des_scenarios = [row.get('nom_jeu_1', 'Jeu 1'), row.get('nom_jeu_2', 'Jeu 2'), row.get('nom_jeu_3', 'Jeu 3')]

    for i, label_jeu in enumerate(noms_des_scenarios, 1):
        with cols[i-1]:
            label = str(label_jeu).strip() if str(label_jeu).strip() != "" else f"Jeu {i}"
            game_id = f"Jeu{i}"
            is_done = game_id in faits_actuels
            
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
