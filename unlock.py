import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="My Game Tracker", layout="wide")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_game_data():
    # On lit l'onglet Catalogue
    df_loaded = conn.read(worksheet="Catalogue", ttl=0)
    
    # Liste des colonnes obligatoires pour éviter les erreurs KeyError
    required_columns = [
        'id', 'boite_titre', 'image_url', 
        'j1_nom', 'j1_fait', 
        'j2_nom', 'j2_fait', 
        'j3_nom', 'j3_fait'
    ]
    
    # Si une colonne manque, on la crée vide
    for col in required_columns:
        if col not in df_loaded.columns:
            df_loaded[col] = "False" if "fait" in col else ""
            
    return df_loaded.fillna("")

def save_game_data(df_to_save):
    # On précise bien l'onglet où sauvegarder
    conn.update(worksheet="Catalogue", data=df_to_save)
    st.cache_data.clear()

# --- COMPOSANT CARTE DE JEU ---
def game_box_card(idx, row, df):
    # Préparation de l'image (si vide, on met un placeholder)
    img_src = row['image_url'] if row['image_url'] != "" else "https://via.placeholder.com/150"
    
    # Calcul de la progression (combien de True sur les 3 jeux)
    faits = [str(row['j1_fait']), str(row['j2_fait']), str(row['j3_fait'])]
    score = faits.count("True")

    # Affichage de l'entête de la boîte (HTML)
    st.markdown(f"""
    <div style='border: 1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px; background-color:white; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);'>
        <div style='display:flex; gap:15px; align-items:center;'>
            <img src="{img_src}" style='width:80px; height:80px; border-radius:5px; object-fit:cover;'>
            <div>
                <h3 style='margin:0;'>{row['boite_titre']}</h3>
                <p style='color:gray; font-size:0.9em; margin:0;'>Progression : {score}/3</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Affichage des 3 jeux avec colonnes Streamlit
    c1, c2, c3 = st.columns(3)
    for i in range(1, 4):
        with [c1, c2, c3][i-1]:
            game_name = row[f'j{i}_nom']
            # On vérifie si c'est fait
            is_done = str(row[f'j{i}_fait']) == "True"
            
            # Checkbox pour marquer comme fait
            # On utilise une clé unique : nom de la boite + index du jeu
            new_val = st.checkbox(f"{game_name}", value=is_done, key=f"chk_{row['boite_titre']}_{i}")
            
            # Si on clique sur la case, on sauvegarde
            if new_val != is_done:
                df.at[idx, f'j{i}_fait'] = str(new_val)
                save_game_data(df)
                st.rerun()

# --- INTERFACE PRINCIPALE ---
df = load_game_data()

st.title("🎮 Suivi de mes Jeux")

# Barre de recherche
search = st.text_input("🔍 Rechercher une boîte...", placeholder="Ex: Mythic Adventures").lower()

if search:
    df_display = df[df['boite_titre'].str.lower().str.contains(search)]
else:
    df_display = df

# Affichage des cartes
if not df_display.empty:
    for idx, row in df_display.iterrows():
        game_box_card(idx, row, df)
        st.divider()
else:
    st.info("Aucun résultat. Vérifiez l'orthographe ou le nom des colonnes dans votre Google Sheet.")

# --- SIDEBAR ADMIN ---
with st.sidebar:
    st.header("⚙️ Admin")
    st.write("Colonnes détectées :")
    st.code(list(df.columns))
    
    if st.button("🔄 Forcer l'actualisation"):
        st.cache_data.clear()
        st.rerun()
