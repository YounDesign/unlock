import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_game_data():
    df_loaded = conn.read(ttl=0)
    # On s'assure que les colonnes "fait" sont bien traitées comme des booléens ou strings propres
    for i in range(1, 4):
        col = f'jeu{i}_fait'
        if col not in df_loaded.columns: df_loaded[col] = "False"
    return df_loaded

def save_game_data(df_to_save):
    conn.update(data=df_to_save)
    st.cache_data.clear()

# --- COMPOSANT CARTE DE JEU ---
def game_box_card(idx, row):
    # Style de la boîte
    st.markdown(f"""
    <div style='border: 1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px; background-color:white; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);'>
        <div style='display:flex; gap:15px;'>
            <img src="{row['image_url']}" style='width:100px; height:100px; border-radius:5px; object-fit:cover;'>
            <div>
                <h3 style='margin:0;'>{row['boite_titre']}</h3>
                <p style='color:gray; font-size:0.9em;'>Progression : {sum([1 for i in range(1,4) if str(row[f'jeu{i}_fait']) == 'True'])}/3</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Affichage des 3 jeux avec colonnes
    c1, c2, c3 = st.columns(3)
    
    for i, col_ui in enumerate([c1, c2, c3], 1):
        with col_ui:
            game_name = row[f'jeu{i}_nom']
            is_done = str(row[f'jeu{i}_fait']) == "True"
            
            # Checkbox pour marquer comme fait
            new_val = st.checkbox(f"{game_name}", value=is_done, key=f"check_{idx}_{i}")
            
            if new_val != is_done:
                df.at[idx, f'jeu{i}_fait'] = str(new_val)
                save_game_data(df)
                st.rerun()

# --- INTERFACE PRINCIPALE ---
st.set_page_config(page_title="My Game Tracker", layout="wide")
df = load_game_data()

st.title("🎮 Suivi de mes Jeux")

# Barre de recherche
search = st.text_input("Rechercher une boîte...").lower()
if search:
    df_display = df[df['boite_titre'].str.lower().str.contains(search)]
else:
    df_display = df

# Affichage des cartes
if not df_display.empty:
    for idx, row in df_display.iterrows():
        game_box_card(idx, row)
        st.divider()
else:
    st.info("Aucun jeu trouvé.")

# --- SECTION SCRAPER (Optionnel) ---
with st.sidebar:
    st.header("Admin")
    if st.button("🔄 Lancer le Scraper"):
        st.write("Connexion au site...")
        # Ici tu peux appeler ta fonction de scraping vue précédemment
        # puis faire un pd.concat() avec le df actuel et save_game_data(df)
        st.success("Données mises à jour !")