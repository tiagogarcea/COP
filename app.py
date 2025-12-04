"""
Simulador de IPE por Cruzamento – Recife
Versão Python com Streamlit + Folium

Autor: Adaptado do HTML original
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import json
import math

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Simulador de IPE por Cruzamento – Recife",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS CUSTOMIZADO - Layout compacto
# ============================================================
st.markdown("""
<style>
    /* Remove padding padrão do Streamlit */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    
    /* Header compacto */
    .main-header {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    
    /* Sidebar maior e com scroll */
    [data-testid="stSidebar"] {
        min-width: 400px;
        width: 400px;
        overflow-y: auto;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        width: 400px;
        overflow-y: auto;
        height: 100vh;
    }
    
    /* Seções compactas */
    .section-title {
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.8rem 0 0.3rem 0;
        padding-bottom: 0.2rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.3);
    }
    
    /* Métricas compactas */
    .stat-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.2rem 0;
        font-size: 0.8rem;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 0.15rem 0;
    }
    
    .stat-value {
        color: #a5b4fc;
        font-weight: 600;
    }
    
    /* Chips de pesos */
    .chip {
        display: inline-block;
        background: rgba(79, 70, 229, 0.3);
        border: 1px solid rgba(129, 140, 248, 0.5);
        border-radius: 999px;
        padding: 0.1rem 0.5rem;
        font-size: 0.75rem;
        margin: 0.1rem;
    }
    
    /* Reduzir espaçamento dos sliders */
    .stSlider {
        padding-top: 0.2rem;
        padding-bottom: 0.2rem;
    }
    
    /* Esconder elementos desnecessários */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Esconder botão de colapsar sidebar - múltiplos seletores */
    [data-testid="collapsedControl"] {display: none !important;}
    [data-testid="stSidebarCollapseButton"] {display: none !important;}
    .st-emotion-cache-1dp5vir {display: none !important;}
    .st-emotion-cache-eczf16 {display: none !important;}
    button[kind="headerNoPadding"] {display: none !important;}
    section[data-testid="stSidebar"] > div:first-child > button {display: none !important;}
    div[data-testid="stSidebarCollapsedControl"] {display: none !important;}
    
    /* Forçar sidebar sempre visível */
    section[data-testid="stSidebar"] {
        transform: none !important;
        visibility: visible !important;
        position: relative !important;
    }
    
    /* Ajustar altura do mapa */
    iframe {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INICIALIZAÇÃO DO SESSION STATE
# ============================================================
if 'logs' not in st.session_state:
    st.session_state.logs = pd.DataFrame()
if 'cruzamentos' not in st.session_state:
    st.session_state.cruzamentos = pd.DataFrame()
if 'cruzamentos_calculados' not in st.session_state:
    st.session_state.cruzamentos_calculados = pd.DataFrame()
if 'equipamentos' not in st.session_state:
    st.session_state.equipamentos = pd.DataFrame()
if 'bairros_geojson' not in st.session_state:
    st.session_state.bairros_geojson = None
if 'ultimo_selecionados' not in st.session_state:
    st.session_state.ultimo_selecionados = pd.DataFrame()

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distância geodésica em metros usando fórmula de Haversine"""
    R = 6371000
    to_rad = math.pi / 180
    d_lat = (lat2 - lat1) * to_rad
    d_lon = (lon2 - lon1) * to_rad
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(lat1 * to_rad) * math.cos(lat2 * to_rad) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def sugerir_tipo_camera(seg_tot: float, lct_tot: float, com_tot: float, mob_tot: float) -> str:
    """Sugere tipo de câmera baseado nos eixos predominantes"""
    candidatos = [("PTZ", seg_tot), ("360", lct_tot), ("FIXA", com_tot), ("LPR", mob_tot)]
    candidatos.sort(key=lambda x: x[1], reverse=True)
    return candidatos[0][0] if candidatos[0][1] > 0 else "FIXA"


def carregar_excel_cruzamentos(file) -> tuple:
    """Carrega e processa o Excel de cruzamentos"""
    try:
        xls = pd.ExcelFile(file)
        
        if "MODELO" not in xls.sheet_names or "cruzamentos_100%" not in xls.sheet_names:
            return None, None, "Abas 'MODELO' e 'cruzamentos_100%' não encontradas."
        
        df_modelo = pd.read_excel(file, sheet_name="MODELO", header=None)
        
        idx_header = None
        for i, row in df_modelo.iterrows():
            if row.iloc[0] == "RANKING_IPE":
                idx_header = i
                break
        
        if idx_header is None:
            return None, None, "Cabeçalho da aba MODELO não identificado."
        
        df_logs = df_modelo.iloc[idx_header + 1:].copy()
        df_logs.columns = df_modelo.iloc[idx_header].values
        df_logs = df_logs.dropna(subset=[df_logs.columns[1]])
        
        logs = pd.DataFrame({
            'cod_log': pd.to_numeric(df_logs.iloc[:, 1], errors='coerce'),
            'nome': df_logs.iloc[:, 2].astype(str),
            'seg': pd.to_numeric(df_logs.iloc[:, 3], errors='coerce').fillna(0),
            'lct': pd.to_numeric(df_logs.iloc[:, 4], errors='coerce').fillna(0),
            'com': pd.to_numeric(df_logs.iloc[:, 5], errors='coerce').fillna(0),
            'mob': pd.to_numeric(df_logs.iloc[:, 6], errors='coerce').fillna(0)
        }).dropna(subset=['cod_log'])
        
        df_cruz = pd.read_excel(file, sheet_name="cruzamentos_100%", header=0)
        
        cruz_dict = {}
        id_counter = 1
        
        for _, row in df_cruz.iterrows():
            cod1, cod2 = row.iloc[0], row.iloc[4]
            if pd.isna(cod1) or pd.isna(cod2):
                continue
            
            cod1, cod2 = int(cod1), int(cod2)
            log1 = str(row.iloc[2]) if not pd.isna(row.iloc[2]) else ""
            log2 = str(row.iloc[6]) if not pd.isna(row.iloc[6]) else ""
            lat = float(row.iloc[11]) if not pd.isna(row.iloc[11]) else 0
            lon = float(row.iloc[12]) if not pd.isna(row.iloc[12]) else 0
            
            if cod1 < cod2:
                cod_min, cod_max, log_min, log_max = cod1, cod2, log1, log2
            else:
                cod_min, cod_max, log_min, log_max = cod2, cod1, log2, log1
            
            chave = f"{cod_min}|{cod_max}"
            
            if chave not in cruz_dict:
                cruz_dict[chave] = {
                    'id': id_counter, 'cod_log1': cod_min, 'log1': log_min,
                    'cod_log2': cod_max, 'log2': log_max, 'lat': lat, 'lon': lon
                }
                id_counter += 1
            elif lat != 0 and lon != 0:
                cruz_dict[chave]['lat'] = (cruz_dict[chave]['lat'] + lat) / 2
                cruz_dict[chave]['lon'] = (cruz_dict[chave]['lon'] + lon) / 2
        
        cruzamentos = pd.DataFrame(list(cruz_dict.values()))
        return logs, cruzamentos, f"✓ {len(logs)} logradouros, {len(cruzamentos)} cruzamentos"
    
    except Exception as e:
        return None, None, f"Erro: {str(e)}"


def carregar_excel_equipamentos(file) -> tuple:
    """Carrega o Excel de equipamentos"""
    try:
        df = pd.read_excel(file, header=0)
        cols_necessarias = ["LATITUDE COM PONTO", "LONGITUDE COM PONTO", "PESO"]
        for col in cols_necessarias:
            if col not in df.columns:
                return None, f"Coluna '{col}' não encontrada."
        
        equip = pd.DataFrame({
            'eixo': df.get("EIXO", pd.Series([""] * len(df))).astype(str),
            'tipo': df.get("TIPO DE EQUIPAMENTO", pd.Series([""] * len(df))).astype(str),
            'log': df.get("LOG_CORRIGIDO", pd.Series([""] * len(df))).astype(str),
            'lat': pd.to_numeric(df["LATITUDE COM PONTO"], errors='coerce'),
            'lon': pd.to_numeric(df["LONGITUDE COM PONTO"], errors='coerce'),
            'peso': pd.to_numeric(df["PESO"], errors='coerce').fillna(0)
        }).dropna(subset=['lat', 'lon'])
        
        return equip, f"✓ {len(equip)} equipamentos"
    except Exception as e:
        return None, f"Erro: {str(e)}"


def calcular_ipe_cruzamentos(logs: pd.DataFrame, cruzamentos: pd.DataFrame, 
                              w_seg: float, w_lct: float, w_com: float, w_mob: float) -> pd.DataFrame:
    """Calcula IPE para todos os cruzamentos"""
    if logs.empty or cruzamentos.empty:
        return pd.DataFrame()
    
    logs_dict = logs.set_index('cod_log').to_dict('index')
    resultados = []
    
    for _, c in cruzamentos.iterrows():
        cod1, cod2 = c['cod_log1'], c['cod_log2']
        if cod1 not in logs_dict or cod2 not in logs_dict:
            continue
        
        l1, l2 = logs_dict[cod1], logs_dict[cod2]
        
        ipe1 = w_seg * l1['seg'] + w_lct * l1['lct'] + w_com * l1['com'] + w_mob * l1['mob']
        ipe2 = w_seg * l2['seg'] + w_lct * l2['lct'] + w_com * l2['com'] + w_mob * l2['mob']
        ipe_cruz = ipe1 + ipe2
        
        seg_tot = l1['seg'] + l2['seg']
        lct_tot = l1['lct'] + l2['lct']
        com_tot = l1['com'] + l2['com']
        mob_tot = l1['mob'] + l2['mob']
        
        resultados.append({
            'id': c['id'], 'cod_log1': cod1, 'log1': c['log1'],
            'cod_log2': cod2, 'log2': c['log2'], 'lat': c['lat'], 'lon': c['lon'],
            'ipe_log1': ipe1, 'ipe_log2': ipe2, 'ipe_cruz': ipe_cruz,
            'seg_tot': seg_tot, 'lct_tot': lct_tot, 'com_tot': com_tot, 'mob_tot': mob_tot,
            'ipe_cruz_seg': w_seg * seg_tot, 'ipe_cruz_lct': w_lct * lct_tot,
            'ipe_cruz_com': w_com * com_tot, 'ipe_cruz_mob': w_mob * mob_tot,
            'camera_tipo': sugerir_tipo_camera(seg_tot, lct_tot, com_tot, mob_tot)
        })
    
    if not resultados:
        return pd.DataFrame()
    
    df = pd.DataFrame(resultados).sort_values('ipe_cruz', ascending=False).reset_index(drop=True)
    
    total_ipe = df['ipe_cruz'].sum()
    if total_ipe > 0:
        df['perc_ipe'] = df['ipe_cruz'] / total_ipe
        df['cobertura_acum'] = df['ipe_cruz'].cumsum() / total_ipe
    else:
        df['perc_ipe'] = 0
        df['cobertura_acum'] = 0
    
    return df


def filtrar_por_cobertura_e_distancia(df: pd.DataFrame, cobertura_frac: float, min_dist: float) -> pd.DataFrame:
    """Filtra cruzamentos por cobertura e distância mínima"""
    if df.empty:
        return pd.DataFrame()
    
    candidatos = df[df['cobertura_acum'] <= cobertura_frac].copy()
    
    if min_dist <= 0:
        return candidatos
    
    selecionados = []
    for _, c in candidatos.iterrows():
        muito_perto = False
        for s in selecionados:
            if distancia_metros(c['lat'], c['lon'], s['lat'], s['lon']) < min_dist:
                muito_perto = True
                break
        if not muito_perto:
            selecionados.append(c.to_dict())
    
    return pd.DataFrame(selecionados)


def criar_mapa(cruzamentos_selecionados: pd.DataFrame, equipamentos: pd.DataFrame, 
               nota_min_equip: int, bairros_geojson=None) -> folium.Map:
    """Cria o mapa com os cruzamentos e equipamentos"""
    m = folium.Map(location=[-8.05, -34.91], zoom_start=12, tiles='OpenStreetMap')
    
    if bairros_geojson is not None:
        folium.GeoJson(bairros_geojson, style_function=lambda x: {
            'fillColor': 'transparent', 'color': '#6b7280', 'weight': 2, 'fillOpacity': 0
        }).add_to(m)
    
    if not cruzamentos_selecionados.empty:
        for _, c in cruzamentos_selecionados.iterrows():
            tipo = c.get('camera_tipo', 'FIXA')
            popup_html = f"""<div style="font-size:0.8rem; min-width:180px;">
                <strong>Cruzamento {int(c['id'])}</strong><br/>
                <b>Ruas:</b> {c['log1']} × {c['log2']}<br/>
                <b>Câmera:</b> {tipo}<br/>
                <b>IPE:</b> {c['ipe_cruz']:.4f}<br/>
                <b>Cobertura:</b> {c['cobertura_acum']*100:.2f}%
            </div>"""
            folium.CircleMarker(
                location=[c['lat'], c['lon']], radius=5, color="#3b82f6",
                fill=True, fillColor="#3b82f6", fillOpacity=0.85, weight=1,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)
    
    if not equipamentos.empty:
        for _, e in equipamentos[equipamentos['peso'] >= nota_min_equip].iterrows():
            popup_html = f"""<div style="font-size:0.8rem;">
                <strong>{e['tipo'] or 'Equipamento'}</strong><br/>
                <b>Log:</b> {e['log']}<br/><b>Peso:</b> {e['peso']}
            </div>"""
            folium.CircleMarker(
                location=[e['lat'], e['lon']], radius=5, color="#dc2626",
                fill=True, fillColor="#ef4444", fillOpacity=0.85, weight=1,
                popup=folium.Popup(popup_html, max_width=200)
            ).add_to(m)
    
    return m


def gerar_csv_download(df_calculados: pd.DataFrame, df_selecionados: pd.DataFrame) -> bytes:
    """Gera CSV para download"""
    if df_calculados.empty:
        return b""
    
    ids_sel = set(df_selecionados['id'].values) if not df_selecionados.empty else set()
    df_export = df_calculados.copy()
    df_export['selecionado_no_mapa'] = df_export['id'].apply(lambda x: 1 if x in ids_sel else 0)
    
    cols = ['id', 'cod_log1', 'log1', 'cod_log2', 'log2', 'lat', 'lon',
            'ipe_log1', 'ipe_log2', 'ipe_cruz', 'perc_ipe', 'cobertura_acum',
            'camera_tipo', 'selecionado_no_mapa']
    
    df_export = df_export[cols]
    for col in ['ipe_log1', 'ipe_log2', 'ipe_cruz', 'perc_ipe', 'cobertura_acum']:
        df_export[col] = df_export[col].apply(lambda x: f"{x:.6f}")
    
    return df_export.to_csv(index=False, sep=';').encode('utf-8')


# ============================================================
# SIDEBAR - CONTROLES (com scroll)
# ============================================================
with st.sidebar:
    st.markdown("## 🎛️ Controles")
    
    # 1. Excel de cruzamentos
    st.markdown('<div class="section-title">1. Excel de cruzamentos</div>', unsafe_allow_html=True)
    file_cruz = st.file_uploader("Cruzamentos", type=['xlsx', 'xls'], key='file_cruz', label_visibility='collapsed')
    if file_cruz:
        logs, cruzamentos, msg = carregar_excel_cruzamentos(file_cruz)
        if logs is not None:
            st.session_state.logs = logs
            st.session_state.cruzamentos = cruzamentos
            st.success(msg)
        else:
            st.error(msg)
    
    # 1b. Excel de equipamentos
    st.markdown('<div class="section-title">1b. Excel de equipamentos</div>', unsafe_allow_html=True)
    file_equip = st.file_uploader("Equipamentos", type=['xlsx', 'xls'], key='file_equip', label_visibility='collapsed')
    if file_equip:
        equip, msg = carregar_excel_equipamentos(file_equip)
        if equip is not None:
            st.session_state.equipamentos = equip
            st.success(msg)
        else:
            st.error(msg)
    
    nota_min_equip = st.slider("Nota mínima equipamentos", 1, 5, 4, key='nota_equip')
    
    # 1c. GeoJSON
    st.markdown('<div class="section-title">1c. Bairros (GeoJSON)</div>', unsafe_allow_html=True)
    file_bairros = st.file_uploader("GeoJSON", type=['json', 'geojson'], key='file_bairros', label_visibility='collapsed')
    if file_bairros:
        try:
            st.session_state.bairros_geojson = json.load(file_bairros)
            st.success("✓ Fronteira carregada")
        except Exception as e:
            st.error(f"Erro: {str(e)}")
    
    # 2. Cobertura
    st.markdown('<div class="section-title">2. Cobertura de IPE</div>', unsafe_allow_html=True)
    cobertura_pct = st.slider("Cobertura (%)", 5, 100, 40, key='cobertura')
    
    # 3. Distância mínima
    st.markdown('<div class="section-title">3. Distância mínima</div>', unsafe_allow_html=True)
    dist_min = st.slider("Distância (m)", 0, 1000, 150, step=50, key='dist_min')
    
    # 4. Pesos
    st.markdown('<div class="section-title">4. Pesos dos eixos</div>', unsafe_allow_html=True)
    peso_seg = st.slider("Segurança", 0, 100, 50, key='peso_seg')
    peso_lct = st.slider("LCT", 0, 100, 20, key='peso_lct')
    peso_com = st.slider("Comercial", 0, 100, 15, key='peso_com')
    peso_mob = st.slider("Mobilidade", 0, 100, 15, key='peso_mob')
    
    soma_pesos = peso_seg + peso_lct + peso_com + peso_mob or 1
    w_seg, w_lct = peso_seg / soma_pesos, peso_lct / soma_pesos
    w_com, w_mob = peso_com / soma_pesos, peso_mob / soma_pesos
    
    st.markdown(f"""<div class="stat-box">
        <span class="chip">Seg {w_seg*100:.0f}%</span>
        <span class="chip">LCT {w_lct*100:.0f}%</span>
        <span class="chip">Com {w_com*100:.0f}%</span>
        <span class="chip">Mob {w_mob*100:.0f}%</span>
    </div>""", unsafe_allow_html=True)
    
    # 5. Preços
    st.markdown('<div class="section-title">5. Preços (R$)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        preco_ptz = st.number_input("PTZ", 0, value=25000, step=1000, key='preco_ptz')
        preco_fixa = st.number_input("Fixa", 0, value=8000, step=500, key='preco_fixa')
    with c2:
        preco_360 = st.number_input("360°", 0, value=20000, step=1000, key='preco_360')
        preco_lpr = st.number_input("LPR", 0, value=15000, step=1000, key='preco_lpr')

# ============================================================
# PROCESSAMENTO
# ============================================================
if not st.session_state.logs.empty and not st.session_state.cruzamentos.empty:
    st.session_state.cruzamentos_calculados = calcular_ipe_cruzamentos(
        st.session_state.logs, st.session_state.cruzamentos, w_seg, w_lct, w_com, w_mob
    )

if not st.session_state.cruzamentos_calculados.empty:
    st.session_state.ultimo_selecionados = filtrar_por_cobertura_e_distancia(
        st.session_state.cruzamentos_calculados, cobertura_pct / 100, dist_min
    )

# ============================================================
# ÁREA PRINCIPAL - MAPA E RESUMOS (sem scroll)
# ============================================================
st.markdown('<h1 class="main-header">Simulador de IPE por Cruzamento – Recife</h1>', unsafe_allow_html=True)

# Layout: Mapa à esquerda, estatísticas à direita
col_mapa, col_stats = st.columns([2, 1])

with col_mapa:
    mapa = criar_mapa(
        st.session_state.ultimo_selecionados,
        st.session_state.equipamentos,
        nota_min_equip,
        st.session_state.bairros_geojson
    )
    st_folium(mapa, width=None, height=520, returned_objects=[])

with col_stats:
    if not st.session_state.cruzamentos_calculados.empty:
        df_calc = st.session_state.cruzamentos_calculados
        df_sel = st.session_state.ultimo_selecionados
        
        total_cruz = len(df_calc)
        total_cand = len(df_calc[df_calc['cobertura_acum'] <= cobertura_pct/100])
        total_sel = len(df_sel)
        
        # Cobertura por eixo
        t_seg = df_calc['ipe_cruz_seg'].sum() or 1
        t_lct = df_calc['ipe_cruz_lct'].sum() or 1
        t_com = df_calc['ipe_cruz_com'].sum() or 1
        t_mob = df_calc['ipe_cruz_mob'].sum() or 1
        
        if not df_sel.empty:
            cov_seg = df_sel['ipe_cruz_seg'].sum() / t_seg * 100
            cov_lct = df_sel['ipe_cruz_lct'].sum() / t_lct * 100
            cov_com = df_sel['ipe_cruz_com'].sum() / t_com * 100
            cov_mob = df_sel['ipe_cruz_mob'].sum() / t_mob * 100
        else:
            cov_seg = cov_lct = cov_com = cov_mob = 0
        
        # Contagem e custo
        cont = df_sel['camera_tipo'].value_counts().to_dict() if not df_sel.empty else {}
        qtd_ptz, qtd_360 = cont.get('PTZ', 0), cont.get('360', 0)
        qtd_fixa, qtd_lpr = cont.get('FIXA', 0), cont.get('LPR', 0)
        
        custo_total = qtd_ptz*preco_ptz + qtd_360*preco_360 + qtd_fixa*preco_fixa + qtd_lpr*preco_lpr
        total_cams = qtd_ptz + qtd_360 + qtd_fixa + qtd_lpr
        
        # Exibir estatísticas compactas
        st.markdown("#### 📊 Cruzamentos")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row"><span>Total:</span><span class="stat-value">{total_cruz:,}</span></div>
            <div class="stat-row"><span>Cobertura {cobertura_pct}%:</span><span class="stat-value">{total_cand:,}</span></div>
            <div class="stat-row"><span>Filtro distância:</span><span class="stat-value">{total_sel:,}</span></div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("#### 📈 Cobertura por Eixo")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row"><span>Segurança:</span><span class="stat-value">{cov_seg:.1f}%</span></div>
            <div class="stat-row"><span>LCT:</span><span class="stat-value">{cov_lct:.1f}%</span></div>
            <div class="stat-row"><span>Comercial:</span><span class="stat-value">{cov_com:.1f}%</span></div>
            <div class="stat-row"><span>Mobilidade:</span><span class="stat-value">{cov_mob:.1f}%</span></div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("#### 💰 Custo Estimado")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row"><span>PTZ ({qtd_ptz}):</span><span class="stat-value">R$ {qtd_ptz*preco_ptz:,.0f}</span></div>
            <div class="stat-row"><span>360° ({qtd_360}):</span><span class="stat-value">R$ {qtd_360*preco_360:,.0f}</span></div>
            <div class="stat-row"><span>Fixa ({qtd_fixa}):</span><span class="stat-value">R$ {qtd_fixa*preco_fixa:,.0f}</span></div>
            <div class="stat-row"><span>LPR ({qtd_lpr}):</span><span class="stat-value">R$ {qtd_lpr*preco_lpr:,.0f}</span></div>
            <div class="stat-row" style="border-top:1px solid #444; margin-top:4px; padding-top:4px;">
                <span><b>Total ({total_cams}):</b></span><span class="stat-value"><b>R$ {custo_total:,.0f}</b></span></div>
        </div>""", unsafe_allow_html=True)
        
        # Download
        csv_data = gerar_csv_download(df_calc, df_sel)
        st.download_button("📥 Baixar CSV", csv_data, "ipe_cruzamentos.csv", "text/csv", use_container_width=True)
    else:
        st.info("👆 Carregue o Excel de cruzamentos na sidebar para iniciar.")