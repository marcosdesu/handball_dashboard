import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from scipy.ndimage import gaussian_filter

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Tablero Handball Live", layout="wide")
st.title("📊 Análisis Táctico en Vivo - Selección Nacional Femenil")

IMAGEN_PORTERIA = 'NS_Goal_handball.png'
IMAGEN_CANCHA = 'NS_ui_Balonmano_BL_V_T.jpg'

# URL OFICIAL DE TU GOOGLE SHEET
URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT-7qq_XxqcKG6Lb4YewwOeVF8M1Atyh9qRvG7uqI4lGAQMCSD4pyTNScIQsDVAh_UAScQEG6jPg3W1/pub?gid=0&single=true&output=csv"

# ==========================================
# 1. CONEXIÓN A DATOS (Actualización cada 3s)
# ==========================================
@st.cache_data(ttl=3) 
def load_data(url):
    try:
        # Lee el sheet oficial
        df_temp = pd.read_csv(url)
        # Limpieza básica para evitar errores si hay filas vacías al final
        df_temp = df_temp.dropna(how='all')
        return df_temp
    except Exception as e:
        st.error(f"Error al leer los datos de Google Sheets. Verifica que el documento tenga información. Detalle: {e}")
        # Retorna un DataFrame vacío pero con las columnas correctas para que no se rompa la app
        return pd.DataFrame(columns=['Equipo', 'Fase', 'Resultado', 'Tiempo', 'Periodo', 'Lado', 'Coord Lado', 'Zona', 'Coord Porteria'])

df_vivo = load_data(URL_GOOGLE_SHEET)

# ==========================================
# 2. FILTROS INTERACTIVOS EXACTOS
# ==========================================
st.sidebar.header("Filtros del Partido")

# Listas dinámicas basadas en lo que ya ocurrió en el partido (o vacías si apenas va a empezar)
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

# Aplicar los 4 filtros al DataFrame
df = df_vivo.copy()
if not df.empty:
    if equipo_sel != 'Todos':
        df = df[df['Equipo'] == equipo_sel]
    if fase_sel != 'Todas':
        df = df[df['Fase'] == fase_sel]
    if resultado_sel != 'Todos':
        df = df[df['Resultado'] == resultado_sel]
    if lado_sel != 'Todos':
        df = df[df['Lado'] == lado_sel]

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
    col1.metric("Goles", 0)
    col2.metric("Paradas", 0)
    col3.metric("Fallos", 0)
    col4.metric("Pérdidas", 0)

st.divider()

# ==========================================
# 4. FUNCIONES DE DIBUJO
# ==========================================
def plot_cancha(df_filtrado):
    fig, ax = plt.subplots(figsize=(6, 10))
    try:
        img = mpimg.imread(IMAGEN_CANCHA)
        ax.imshow(img, extent=[0, 100, 100, 0])
    except FileNotFoundError:
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

        ax.scatter(no_goles['PX'], no_goles['PY'], c='white', marker='X', s=100, alpha=0.9, edgecolors='black', label='No Gol')
        ax.scatter(goles['PX'], goles['PY'], c='#00e676', s=120, edgecolors='black', linewidth=1.5, label='Gol')
        ax.legend(loc='upper right', fontsize=10)

    ax.set_title('Mapa de Ataque', fontweight='bold', fontsize=14, pad=15)
    ax.axis('off')
    return fig

def plot_porteria(df_filtrado):
    fig, ax = plt.subplots(figsize=(10, 5))
    try:
        img = mpimg.imread(IMAGEN_PORTERIA)
        ax.imshow(img, extent=[0, 100, 100, 0])
    except FileNotFoundError:
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

            if np.max(heatmap_suave) > 0:
                heatmap_suave = heatmap_suave / np.max(heatmap_suave)
            heatmap_suave[heatmap_suave < 0.05] = np.nan
            ax.imshow(heatmap_suave, extent=[0, 100, 100, 0], cmap='inferno', alpha=0.65)

    ax.set_title('Vulnerabilidad en Portería (Goles)', fontweight='bold', fontsize=14, pad=15)
    ax.set_xlim(0, 100)
    ax.set_ylim(100, 0)
    ax.axis('off')
    return fig

# ==========================================
# 5. RENDERIZADO DE GRÁFICAS EN COLUMNAS
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

# ==========================================
# 6. TABLA DE DATOS CRUDOS
# ==========================================
with st.expander("Ver Base de Datos Cruda"):
    st.dataframe(df)
