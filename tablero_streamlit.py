import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from scipy.ndimage import gaussian_filter
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Tablero Handball Live", layout="wide")
st.title("📊 Análisis Táctico en Vivo")

IMAGEN_PORTERIA = 'NS_Goal_handball.png'
IMAGEN_CANCHA = 'NS_ui_Balonmano_BL_V_T.jpg'
COLOR_LOC = 'green'
COLOR_VIS = 'blue'

# URL OFICIAL DE TU GOOGLE SHEET
URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT-7qq_XxqcKG6Lb4YewwOeVF8M1Atyh9qRvG7uqI4lGAQMCSD4pyTNScIQsDVAh_UAScQEG6jPg3W1/pub?gid=0&single=true&output=csv"

# ==========================================
# 0. AUTO-REFRESCO (Cada 5 segundos = 5000 ms)
# ==========================================
st_autorefresh(interval=5000, limit=None, key="data_refresh")

# ==========================================
# 1. CONEXIÓN A DATOS
# ==========================================
@st.cache_data(ttl=2) 
def load_data(url):
    try:
        df_temp = pd.read_csv(url)
        df_temp = df_temp.dropna(how='all')
        return df_temp
    except Exception as e:
        return pd.DataFrame(columns=['Equipo', 'Fase', 'Resultado', 'Tiempo', 'Periodo', 'Lado', 'Coord Lado', 'Zona', 'Coord Porteria'])

df_vivo = load_data(URL_GOOGLE_SHEET)

# ==========================================
# 2. FILTROS INTERACTIVOS
# ==========================================
st.sidebar.header("Filtros del Partido")

if not df_vivo.empty and 'Equipo' in df_vivo.columns:
    lista_equipos = ['Todos'] + [str(x) for x in df_vivo['Equipo'].dropna().unique()]
    lista_fases = ['Todas'] + [str(x) for x in df_vivo['Fase'].dropna().unique()]
    lista_resultados = ['Todos'] + [str(x) for x in df_vivo['Resultado'].dropna().unique()]
    lista_lados = ['Todos'] + [str(x) for x in df_vivo['Lado'].dropna().unique()]
else:
    lista_equipos, lista_fases, lista_resultados, lista_lados = ['Todos'], ['Todas'], ['Todos'], ['Todos']

equipo_sel = st.sidebar.selectbox("1. ¿Quién ataca?", lista_equipos)
fase_sel = st.sidebar.selectbox("2. Fase de Juego", lista_fases)
resultado_sel = st.sidebar.selectbox("3. ¿Qué pasó?", lista_resultados)
lado_sel = st.sidebar.selectbox("4. Lado de la Cancha", lista_lados)

df = df_vivo.copy()
if not df.empty:
    if equipo_sel != 'Todos': df = df[df['Equipo'] == equipo_sel]
    if fase_sel != 'Todas': df = df[df['Fase'] == fase_sel]
    if resultado_sel != 'Todos': df = df[df['Resultado'] == resultado_sel]
    if lado_sel != 'Todos': df = df[df['Lado'] == lado_sel]

# ==========================================
# 3. MÉTRICAS RÁPIDAS
# ==========================================
col1, col2, col3, col4 = st.columns(4)
if not df.empty and 'Resultado' in df.columns:
    col1.metric("Goles", len(df[df['Resultado'] == 'Gol']))
    col2.metric("Paradas", len(df[df['Resultado'] == 'Parada']))
    col3.metric("Fallos", len(df[df['Resultado'] == 'Fallo']))
    col4.metric("Pérdidas", len(df[df['Resultado'] == 'Perdida']))
else:
    col1.metric("Goles", 0); col2.metric("Paradas", 0); col3.metric("Fallos", 0); col4.metric("Pérdidas", 0)

st.divider()

# ==========================================
# 4. FUNCIONES DE DIBUJO (Con Ejes Corregidos)
# ==========================================
def plot_cancha(df_filtrado):
    fig, ax = plt.subplots(figsize=(6, 10))
    try:
        img = mpimg.imread(IMAGEN_CANCHA)
        ax.imshow(img, extent=[0, 100, 100, 0])
    except:
        ax.set_facecolor('black')

    def extraer_coord(val, indice):
        try: return float(str(val).split(',')[indice])
        except: return np.nan
        
    df_cancha = pd.DataFrame()
    if not df_filtrado.empty and 'Coord Lado' in df_filtrado.columns:
        df_filtrado = df_filtrado.copy()
        df_filtrado['PX'] = df_filtrado['Coord Lado'].apply(lambda x: extraer_coord(x, 0))
        df_filtrado['PY'] = df_filtrado['Coord Lado'].apply(lambda x: extraer_coord(x, 1))
        df_cancha = df_filtrado.dropna(subset=['PX', 'PY'])

    if len(df_cancha) > 0:
        heatmap, xedges, yedges = np.histogram2d(df_cancha['PX'], df_cancha['PY'], bins=100, range=[[0, 100], [0, 100]])
        heatmap = heatmap.T
        heatmap_suave = gaussian_filter(heatmap, sigma=4)
        ax.imshow(heatmap_suave, extent=[0, 100, 100, 0], cmap='inferno', alpha=0.55)

        goles = df_cancha[df_cancha['Resultado'] == 'Gol']
        no_goles = df_cancha[df_cancha['Resultado'] != 'Gol']

        ax.scatter(no_goles['PX'], no_goles['PY'], c='white', marker='X', s=100, alpha=0.9, edgecolors='black')
        ax.scatter(goles['PX'], goles['PY'], c='#00e676', s=120, edgecolors='black', linewidth=1.5)

    ax.set_title('Mapa de Ataque', fontweight='bold', fontsize=14, pad=15)
    
    # ¡LA CORRECCIÓN CLAVE! Forzar los ejes para alinear clics con la imagen
    ax.set_xlim(0, 100)
    ax.set_ylim(100, 0)
    ax.axis('off')
    return fig

def plot_porteria(df_filtrado):
    fig, ax = plt.subplots(figsize=(10, 5))
    try:
        img = mpimg.imread(IMAGEN_PORTERIA)
        ax.imshow(img, extent=[0, 100, 100, 0])
    except:
        ax.set_facecolor('gray')

    df_tiros = pd.DataFrame()
    if not df_filtrado.empty and 'Coord Porteria' in df_filtrado.columns:
        df_tiros = df_filtrado[df_filtrado['Coord Porteria'].notna() & (df_filtrado['Coord Porteria'] != '')].copy()
    
    if len(df_tiros) > 0:
        df_tiros['PX'] = df_tiros['Coord Porteria'].apply(lambda x: float(str(x).split(',')[0]) if ',' in str(x) else np.nan)
        df_tiros['PY'] = df_tiros['Coord Porteria'].apply(lambda x: float(str(x).split(',')[1]) if ',' in str(x) else np.nan)
        goles = df_tiros[df_tiros['Resultado'] == 'Gol']

        if len(goles) > 0:
            heatmap, xedges, yedges = np.histogram2d(goles['PX'], goles['PY'], bins=100, range=[[0, 100], [0, 100]])
            heatmap = heatmap.T
            heatmap_suave = gaussian_filter(heatmap, sigma=5)
            if np.max(heatmap_suave) > 0: heatmap_suave = heatmap_suave / np.max(heatmap_suave)
            heatmap_suave[heatmap_suave < 0.05] = np.nan
            ax.imshow(heatmap_suave, extent=[0, 100, 100, 0], cmap='inferno', alpha=0.65)

    ax.set_title('Vulnerabilidad en Portería (Goles)', fontweight='bold', fontsize=14, pad=15)
    
    # CORRECCIÓN DE EJES
    ax.set_xlim(0, 100)
    ax.set_ylim(100, 0)
    ax.axis('off')
    return fig

def plot_momentum(df_all):
    # La gráfica de momentum SIEMPRE lee el partido completo sin importar los filtros de arriba
    df_mom = df_all.copy()
    
    def convertir_a_minutos(row):
        try:
            partes = str(row['Tiempo']).split(':')
            if len(partes) == 3:
                h, m, s = int(partes[0]), int(partes[1]), float(partes[2])
            elif len(partes) == 2:
                h, m, s = 0, int(partes[0]), float(partes[1])
            else:
                return 0
            minutos = h * 60 + m + s / 60
            if str(row['Periodo']).strip().upper() == '2T': minutos += 30
            return minutos
        except: return 0

    df_mom['match_min'] = df_mom.apply(convertir_a_minutos, axis=1)
    goles_df = df_mom[df_mom['Resultado'].astype(str).str.strip().str.lower() == 'gol'].sort_values('match_min')
    
    equipos = df_mom['Equipo'].dropna().unique()
    equipo_local = equipos[0] if len(equipos) > 0 else 'LOC'
    equipo_visitante = equipos[1] if len(equipos) > 1 else 'VIS'

    t_eventos = [0]
    score_loc = [0]
    score_vis = [0]
    momentum = [0]
    marcador_L, marcador_V = 0, 0
    racha_L, racha_V = 0, 0

    for _, row in goles_df.iterrows():
        t = row['match_min']
        eq = str(row['Equipo']).strip()
        
        if eq == equipo_local:
            marcador_L += 1; racha_L += 1; racha_V = 0
        elif eq == equipo_visitante:
            marcador_V += 1; racha_V += 1; racha_L = 0

        if racha_L >= 2: mom_val = racha_L
        elif racha_V >= 2: mom_val = -racha_V
        else: mom_val = 0

        t_eventos.append(t); score_loc.append(marcador_L)
        score_vis.append(marcador_V); momentum.append(mom_val)

    minuto_final = max(60.0, goles_df['match_min'].max() if not goles_df.empty else 60.0)
    t_eventos.append(minuto_final); score_loc.append(marcador_L)
    score_vis.append(marcador_V); momentum.append(momentum[-1])

    t_arr = np.array(t_eventos)
    mom_arr = np.array(momentum)
    mom_positivo = np.where(mom_arr > 0, mom_arr, 0)
    mom_negativo = np.where(mom_arr < 0, mom_arr, 0)

    fig, (ax_marcador, ax_momentum) = plt.subplots(2, 1, figsize=(14, 6), gridspec_kw={'height_ratios': [2, 1]}, sharex=True)
    fig.subplots_adjust(hspace=0.05)

    ax_marcador.step(t_arr, score_loc, where='post', color=COLOR_LOC, label=equipo_local, linewidth=3)
    ax_marcador.step(t_arr, score_vis, where='post', color=COLOR_VIS, label=equipo_visitante, linewidth=3)
    ax_marcador.axvline(x=30, color='black', linestyle='--', alpha=0.5) 
    ax_marcador.set_title(f'Momentum del Partido', fontsize=16, fontweight='bold')
    ax_marcador.set_ylabel('Goles', fontsize=10, fontweight='bold')
    ax_marcador.grid(True, linestyle='--', alpha=0.4)
    ax_marcador.legend(fontsize=10, loc='upper left')

    ax_momentum.fill_between(t_arr, 0, mom_positivo, step='post', facecolor=COLOR_LOC, alpha=0.7)
    ax_momentum.fill_between(t_arr, 0, mom_negativo, step='post', facecolor=COLOR_VIS, alpha=0.7)
    ax_momentum.axvline(x=30, color='black', linestyle='--', alpha=0.5)
    ax_momentum.axhline(y=0, color='black', linewidth=1, alpha=0.8)
    ax_momentum.set_xlabel('Tiempo de Juego Acumulado (Minutos)', fontsize=10, fontweight='bold')
    ax_momentum.set_ylabel('Momentum', fontsize=10, fontweight='bold')
    ax_momentum.grid(True, axis='x', linestyle='--', alpha=0.4)
    
    max_mom = max(abs(mom_arr.min()), abs(mom_arr.max()), 2) + 1
    ax_momentum.set_ylim(-max_mom, max_mom)
    ax_momentum.set_yticks([]) 
    
    ax_marcador.set_xlim(0, minuto_final)
    ax_marcador.set_xticks(np.arange(0, minuto_final + 5, 5))

    return fig

# ==========================================
# 5. RENDERIZADO DE GRÁFICAS EN PANTALLA
# ==========================================
col_izq, col_der = st.columns(2)

with col_izq:
    st.markdown("### 🏟️ Origen de la Acción")
    fig_cancha = plot_cancha(df)
    st.pyplot(fig_cancha)

with col_der:
    st.markdown("### 🥅 Zonas de Definición")
    fig_porteria = plot_porteria(df)
    st.pyplot(fig_porteria)

st.divider()

st.markdown("### 📈 Tendencia y Rachas")
if not df_vivo.empty:
    fig_momentum = plot_momentum(df_vivo)
    st.pyplot(fig_momentum)
else:
    st.info("Esperando goles para calcular el Momentum...")

# ==========================================
# 6. TABLA DE DATOS CRUDOS
# ==========================================
with st.expander("Ver Base de Datos Cruda"):
    st.dataframe(df)
