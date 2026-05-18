import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Unlock! Tracker", 
    layout="wide", 
    page_icon="🎮",
    initial_sidebar_state="expanded" 
)

# --- MÉMOIRE DE L'APPLICATION ---
if 'user_index' not in st.session_state:
    st.session_state.user_index = None

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CHARGEMENT UTILISATEURS ---
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

# --- CHARGEMENT JEUX ---
def load_game_data():
    df = conn.read(ttl=0)
    return df.fillna("")

def save_game_data(df_to_save):
    conn.update(data=df_to_save)
    st.cache_data.clear()

# --- INITIALISATION ---
joueurs = load_users()
df = load_game_data()

# --- CALCUL DES SCORES POUR LE CLASSEMENT ---
stats_joueurs = []
total_scenarios_possible = len(df) * 3

for j in joueurs:
    col_name = None
    # On cherche la colonne correspondant au joueur
    for c in df.columns:
        if j.lower() in str(c).lower():
            col_name = c
            break
    
    score_j = 0
    if col_name and col_name in df.columns:
        # On compte les éléments séparés par des virgules dans chaque cellule
        for val in df[col_name]:
            score_j += len([x for x in str(val).split(',') if x.strip()])
    
    stats_joueurs.append({"Joueur": j, "Score": score_j})

# Création du DataFrame de classement trié
df_classement = pd.DataFrame(stats_joueurs).sort_values(by="Score", ascending=False)

# --- SIDEBAR (MENU GAUCHE) ---
with st.sidebar:
    st.title("🏆 CLASSEMENT")
    
    # Affichage du podium
    for i, row in enumerate(df_classement.head(5).iterrows(), 1):
        r = row[1]
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
        st.write(f"{emoji} **{r['Joueur']}** : {r['Score']} pts")
    
    st.divider()
    st.subheader("👤 Ton Profil")
    if joueurs:
        default_idx = None
        if st.session_state.user_index is not None and st.session_state.user_index < len(joueurs):
            default_idx = st.session_state.user_index
            
        choice = st.selectbox("Qui es-tu ?", joueurs, index=default_idx, key="user_sel")
        if choice:
            st.session_state.user_index = joueurs.index(choice)
            utilisateur = choice
        else: utilisateur = None
    else:
        st.warning("Ajoute un joueur !")
        utilisateur = None

    with st.expander("➕ Nouveau Joueur"):
        nouveau_nom = st.text_input("Prénom")
        if st.button("Ajouter"):
            if nouveau_nom and add_new_user(nouveau_nom):
                st.success("Ajouté !"); st.rerun()

    st.divider()
    if st.button("🔄 Rafraîchir l'App", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# --- INTERFACE PRINCIPALE ---
if not utilisateur:
    st.markdown("""
        <div style="background-color:#ff4b4b; padding:20px; border-radius:10px; text-align:center;">
            <h2 style="color:white; margin:0;">⬅️ ACTION REQUISE</h2>
            <p style="color:white; font-size:1.2em;">Choisis ton nom dans le menu à gauche.</p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# Score de l'utilisateur actuel
user_score = df_classement[df_classement['Joueur'] == utilisateur]['Score'].values[0]
progress = user_score / total_scenarios_possible if total_scenarios_possible > 0 else 0

st.title(f"🎮 {utilisateur}")
st.metric("Ton Score Total", f"{user_score} / {total_scenarios_possible}")
st.progress(progress)

st.divider()

# Identification de la colonne de suivi
col_suivi = None
for c in df.columns:
    if utilisateur.lower() in str(c).lower():
        col_suivi = c
        break
if col_suivi is None:
    col_suivi = f"fait_{utilisateur.lower()}"
    df[col_suivi] = ""

search = st.text_input("🔍 Rechercher une boîte...", "").lower()
title_col = df.columns[1] 
df_display = df[df[title_col].astype(str).str.lower().str.contains(search)] if search else df

# --- AFFICHAGE DES JEUX ---
for idx, row in df_display.iterrows():
    # Image (Colonne 3)
    url = str(row.iloc[2]).strip()
    if url.startswith('http'):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2: st.image(url, use_container_width=True)

    # Titre (Colonne 2)
    st.markdown(f"<h2 style='text-align: center;'>{row.iloc[1]}</h2>", unsafe_allow_html=True)
    
    # Les 3 jeux (Colonnes 4, 5, 6)
    cols = st.columns(3)
    faits_actuels = [x.strip() for x in str(row[col_suivi]).split(',') if x.strip()]
    
    for i in range(3):
        nom_jeu = str(row.iloc[i+3]).strip()
        if not nom_jeu or nom_jeu == "nan": nom_jeu = f"Jeu {i+1}"
        
        with cols[i]:
            game_id = f"Jeu{i+1}"
            is_done = game_id in faits_actuels
            
            if st.checkbox(nom_jeu, value=is_done, key=f"chk_{utilisateur}_{idx}_{i}"):
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
