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
        # On tente de lire l'onglet "Utilisateurs"
        users_df = conn.read(worksheet="Utilisateurs", ttl=0)
        # On récupère la première colonne
        noms = users_df.iloc[:, 0].dropna().astype(str).tolist()
        # Si la liste est vide, on met des noms par défaut
        return noms if noms else ["Papa", "Maman", "Lucas"]
    except:
        # Si l'onglet n'existe pas, liste de secours
        return ["Papa", "Maman", "Lucas", "Julie"]

# --- CHARGEMENT DES JEUX ---
def load_game_data():
    try:
        # Lit le premier onglet (Catalogue)import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Unlock! Tracker", layout="wide", page_icon="🎮")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FONCTIONS POUR LES UTILISATEURS ---
def load_users():
    try:
        # Lit l'onglet "Utilisateurs" (doit exister dans ton Sheet)
        users_df = conn.read(worksheet="Utilisateurs", ttl=0)
        return users_df.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return []

def add_new_user(new_name):
    try:
        # Charger les utilisateurs actuels
        current_users = load_users()
        if new_name not in current_users:
            current_users.append(new_name)
            # Créer un nouveau DataFrame et sauvegarder dans l'onglet "Utilisateurs"
            new_df = pd.DataFrame(current_users, columns=["Noms"])
            conn.update(worksheet="Utilisateurs", data=new_df)
            st.cache_data.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erreur lors de l'ajout : {e}")
        return False

# --- FONCTIONS POUR LES JEUX ---
def load_game_data():
    try:
        # Lit le premier onglet (Catalogue)
        df_loaded = conn.read(ttl=0)
        if df_loaded.empty: return pd.DataFrame()
        df_loaded.columns = [str(c).lower().replace(' ', '_').strip() for c in df_loaded.columns]
        if 'boite_titre' in df_loaded.columns:
            df_loaded = df_loaded.dropna(subset=['boite_titre'])
        return df_loaded.fillna("")
    except:
        return pd.DataFrame()

def save_game_data(df_to_save):
    # Sauvegarde dans l'onglet par défaut (le premier)
    conn.update(data=df_to_save)
    st.cache_data.clear()

# --- INITIALISATION ---
joueurs = load_users()
df = load_game_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("👥 Gestion des Joueurs")
    
    # 1. Ajouter un utilisateur
    with st.expander("➕ Ajouter un joueur"):
        nouveau_nom = st.text_input("Nom du nouveau joueur")
        if st.button("Enregistrer le joueur"):
            if nouveau_nom:
                if add_new_user(nouveau_nom):
                    st.success(f"{nouveau_nom} ajouté !")
                    st.rerun()
                else:
                    st.warning("Ce nom existe déjà.")
            else:
                st.error("Écris un nom !")

    st.divider()

    # 2. Choisir l'utilisateur
    if joueurs:
        utilisateur = st.selectbox("Qui es-tu ?", joueurs)
    else:
        st.warning("Aucun joueur. Ajoute-en un au-dessus !")
        utilisateur = None

    st.divider()
    st.link_button("🌐 Site Unlock", "https://www.spacecowboys-games.com/game/unlock/", use_container_width=True)
    
    if st.button("🔄 Actualiser l'App"):
        st.cache_data.clear()
        st.rerun()

# --- INTERFACE PRINCIPALE ---
if not utilisateur:
    st.info("👋 Bienvenue ! Commence par ajouter un joueur dans la barre latérale à gauche.")
    st.stop()

st.title(f"🎮 Suivi Unlock : {utilisateur}")

if df.empty:
    st.error("⚠️ Aucun jeu trouvé dans l'onglet Catalogue.")
    st.stop()

# Gestion de la colonne de suivi pour le joueur actuel
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
            url = str(row.get('image_url', '')).strip()
            if url.startswith('http'):
                st.image(url, width=100)
            else:
                st.image("https://via.placeholder.com/100?text=No+Image", width=100)
        with c_txt:
            st.subheader(row.get('boite_titre', 'Sans titre'))
    
    cols = st.columns(3)
    faits_actuels = [x.strip() for x in str(row.get(col_suivi, "")).split(',') if x.strip()]

    for i in range(1, 4):
        with cols[i-1]:
            col_nom = f'j{i}_nom'
            game_label = str(row.get(col_nom, "")).strip()
            if not game_label or game_label == "nan": game_label = f"Scénario {i}"
            
            game_id = f"Jeu{i}"
            is_done = game_id in faits_actuels
            
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
        df_loaded = conn.read(ttl=0)
        if df_loaded.empty: return pd.DataFrame()

        # Normalisation des colonnes : minuscules et pas d'espaces
        df_loaded.columns = [str(c).lower().replace(' ', '_').strip() for c in df_loaded.columns]
        
        # On garde les lignes avec un titre
        if 'boite_titre' in df_loaded.columns:
            df_loaded = df_loaded.dropna(subset=['boite_titre'])
            df_loaded = df_loaded[df_loaded['boite_titre'].astype(str).str.strip() != ""]
        return df_loaded.fillna("")
    except:
        return pd.DataFrame()

def save_game_data(df_to_save):
    try:
        conn.update(data=df_to_save)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

# --- INITIALISATION ---
joueurs = load_users()
df = load_game_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 JOUEURS")
    
    # Sécurité si joueurs est vide
    if not joueurs: joueurs = ["Joueur 1"]
    
    utilisateur_brut = st.selectbox("Qui es-tu ?", joueurs)
    # On transforme en texte pour éviter l'AttributeError
    utilisateur = str(utilisateur_brut) if utilisateur_brut else "Joueur"
    
    st.divider()
    st.markdown("### 🔍 Liens")
    st.link_button("🌐 Site Unlock (Nouveautés)", "https://www.spacecowboys-games.com/game/unlock/", use_container_width=True)
    
    if st.button("🔄 Actualiser les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title(f"🎮 Suivi Unlock : {utilisateur}")

if df.empty:
    st.error("⚠️ Impossible de lire les jeux. Vérifie ton onglet 'Catalogue' ou que la colonne 'boite_titre' existe.")
    st.stop()

# Nom de la colonne de suivi pour le joueur actuel
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
            # Gestion image avec row.get pour éviter les erreurs si la colonne manque
            url = str(row.get('image_url', '')).strip()
            if url.startswith('http'):
                st.image(url, width=100)
            else:
                st.image("https://via.placeholder.com/100?text=Image+Manquante", width=100)
        
        with c_txt:
            st.subheader(row.get('boite_titre', 'Sans titre'))
    
    # Les 3 scénarios
    cols = st.columns(3)
    # Récupération sécurisée des jeux faits
    suivi_data = str(row.get(col_suivi, ""))
    faits_actuels = [x.strip() for x in suivi_data.split(',') if x.strip()]

    for i in range(1, 4):
        with cols[i-1]:
            # RECUPERATION DU NOM DU JEU (ex: j1_nom)
            col_nom = f'j{i}_nom'
            game_label = str(row.get(col_nom, "")).strip()
            
            # Si le nom est vide dans ton Google Sheet
            if not game_label or game_label == "nan":
                game_label = f"Scénario {i}"
            
            game_id = f"Jeu{i}"
            is_done = game_id in faits_actuels
            
            # Case à cocher avec le vrai nom du jeu
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
