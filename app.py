"""
Simulador de IPE por Cruzamento – Recife
Versão Python com Streamlit + Folium

Autor: Adaptado do HTML original
Inclui: Filtro de distância, raio de cobertura, limite de cobertura por logradouro,
        verificação de alagamentos, histórico de sinistros e estatísticas detalhadas
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
    page_title="Otimizador do Videomonitoramento – Recife",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS CUSTOMIZADO - Layout compacto
# ============================================================
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    .main-header {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
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
    .section-title {
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.8rem 0 0.3rem 0;
        padding-bottom: 0.2rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.3);
    }
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
    .chip {
        display: inline-block;
        background: rgba(79, 70, 229, 0.3);
        border: 1px solid rgba(129, 140, 248, 0.5);
        border-radius: 999px;
        padding: 0.1rem 0.5rem;
        font-size: 0.75rem;
        margin: 0.1rem;
    }
    .stSlider {
        padding-top: 0.2rem;
        padding-bottom: 0.2rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none !important;}
    [data-testid="stSidebarCollapseButton"] {display: none !important;}
    section[data-testid="stSidebar"] {
        transform: none !important;
        visibility: visible !important;
        position: relative !important;
    }
    iframe {
        border-radius: 8px;
    }
    .coverage-warning {
        background: rgba(234, 179, 8, 0.2);
        border: 1px solid rgba(234, 179, 8, 0.5);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
        color: #fbbf24;
    }
    .info-box {
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
        color: #93c5fd;
    }
    .alert-box {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
        color: #fca5a5;
    }
    .success-box {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.4);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
        color: #86efac;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTES - LISTAS DE ALAGAMENTOS E SINISTROS
# ============================================================
ALAGAMENTOS_ALVO = [
    "AVENIDA CRUZ CABUGA / AVENIDA DR JAYME DA FONTE",
    "AVENIDA CRUZ CABUGA / AVENIDA NORTE MIGUEL ARRAES DE ALENCAR",
    "RUA ARARIPINA / RUA DA AURORA",
    "AVENIDA DANTAS BARRETO / RUA SÃO JOÃO",
    "AVENIDA DANTAS BARRETO / RUA DO PEIXOTO",
    "RUA CAPITÃO TEMUDO / PRAÇA GOVERNADOR PAULO GUERRA / AV. ENGENHEIRO JOSÉ ESTELITA",
    "AVENIDA SUL GOV. CID SAMPAIO / RUA S D 4038",
    "RUA ITAPIRA / RUA IMPERIAL",
    "RUA DOS COELHOS / RUA DOUTOR JOSÉ MARIANO",
    "RUA QUARENTA E OITO / AVENIDA NORTE MIGUEL ARRAES DE ALENCAR",
    "RUA ARÃO BOTLER / AVENIDA CIDADE DE MONTEIRO",
    "AVENIDA GOVERNADOR AGAMENON MAGALHÃES",
    "RUA JOSÉ BENTO BATISTA / AVENIDA CORREIA DE BRITO",
    "RUA DR BANDEIRA FILHO /AVENIDA GOVERNADOR AGAMENON MAGALHÃES",
    "RUA DA MANGABEIRA / AVENIDA NORTE MIGUEL ARRAES DE ALENCAR",
    "RUA IDA / AVENIDA NORTE MIGUEL ARRAES DE ALENCAR",
    "AVENIDA DA RECUPERAÇÃO / ENTRADA COMPLEXO DA MACAXEIRA",
    "RUA CERRO AZUL / RUA NOVA DESCOBERTA / RUA CÓRREGO DA AREIA",
    "RUA DELMIRO GOUVEIA / AVENIDA ENGENHEIRO ABDIAS DE CARVALHO",
    "RUA BENFICA / AVENIDA SPORT CLUBE DO RECIFE",
    "RUA HÉRCULES FLORENCE / AVENIDA ENGENHEIRO ABDIAS DE CARVALHO",
    "RUA AMÁLIA / AVENIDA GENERAL SAN MARTIN",
    "RUA GOMES TABORDA / RUA QUATRO DE OUTUBRO",
    "AVENIDA GENERAL SAN MARTIN / AVENIDA CAXANGÁ",
    "RUA REAL DA TORRE / RUA PROFESSORA ANUNCIADA DA ROCHA MELO",
    "AVENIDA PROFESSOR MORAES REGO / AVENIDA CAXANGÁ",
    "AVENIDA BARÃO DE BONITO / AVENIDA CAXANGÁ",
    "RUA BENFICA / PRAÇA DO INTERNACIONAL",
    "AVENIDA ENGENHEIRO ABDIAS DE CARVALHO / AVENIDA GENERAL SAN MARTIN",
    "AVENIDA SUL GOV. CID SAMPAIO / RUA NICOLAU PEREIRA",
    "RUA NICOLAU PEREIRA / RUA DO ACRE",
    "RUA VISCONDE DE PELOTAS / RUA VISCONDE DE INHAUMA",
    "AVENIDA CENTRAL / RUA VISCONDE DE PELOTAS",
    "AVENIDA JOÃO CABRAL DE MELO NETO / AVENIDA RECIFE",
    "ENTRADA DA RUA DOUTOR JOSÉ RUFINO / AVENIDA DOUTOR JOSÉ RUFINO / RODOVIA BR 101",
    "RUA DOMINGOS TEOTONIO /AVENIDA DOUTOR JOSÉ RUFINO",
    "RUA JOÃO TEIXEIRA / AVENIDA DOUTOR JOSÉ RUFINO",
    "RUA LORENA / RUA LEANDRO BARRETO",
    "AVENIDA CONSELHEIRO AGUIAR / AVENIDA ANTÔNIO DE GOES",
    "RUA ZEFERINO PINHO / RUA OLIVIA MENELAU",
    "AVENIDA MARECHAL MASCARENHAS DE MORAES / RUA CÔNEGO LIRA",
    "AVENIDA MARECHAL MASCARENHAS DE MORAES / RUA ANTÔNIO EDUARDO AMORIM",
    "RUA PAMPULHA / AVENIDA MARECHAL MASCARENHAS DE MORAES",
    "RUA ADERBAL DE MELO / AVENIDA RECIFE",
    "RUA HÉLIO BRANDÃO / RUA SÃO NICOLAU",
    "RUA PINTOR AGENOR DE ALBUQUERQUE CÉSAR / AVENIDA DOIS RIOS",
    "RUA VISCONDE DE JEQUITINHONHA / RUA RIBEIRO DE BRITO",
    "RUA AMÁLIA BERNARDINO DE SOUZA / RUA ERNESTO DE PAULA SANTOS",
    "AVENIDA CONSELHEIRO AGUIAR / RUA PADRE CARAPUCEIRO",
    "RUA PROFESSOR JOSÉ BRANDÃO / AVENIDA CONSELHEIRO AGUIAR"
]

RUAS_SINISTROS_ALVO = [
    "AVENIDA ENGENHEIRO ABDIAS DE CARVALHO", "ESTRADA VELHA DE AGUA FRIA", "AVENIDA BRASILIA FORMOSA",
    "AVENIDA MARECHAL MASCARENHAS DE MORAES", "RUA SAO MATEUS", "AVENIDA HERCULANO BANDEIRA",
    "RUA EMILIO MONTEIRO FONSECA", "RUA PAISSANDU", "ESTRADA DE BELEM", "AVENIDA GOVERNADOR AGAMENON MAGALHAES",
    "RUA SAO MIGUEL", "AVENIDA NORTE MIGUEL ARRAES DE ALENCAR", "RUA JOSE BONIFACIO", "PONTE GREGORIO BEZERRA",
    "RUA SOUZA BANDEIRA", "RUA FALCAO DE LACERDA", "AVENIDA MAURICIO DE NASSAU", "RUA JOAO LIRA",
    "AVENIDA PROFESSOR JOSE DOS ANJOS", "RUA GASTAO VIDIGAL", "AVENIDA DOUTOR JOSE RUFINO", "1A TRAVESSA SAO MIGUEL",
    "AVENIDA ENGENHEIRO DOMINGOS FERREIRA", "RUA PROFESSOR ANTONIO COELHO", "RUA GENERAL JOAQUIM INACIO",
    "RUA LEONARDO BEZERRA CAVALCANTI", "RUA JOAQUIM BANDEIRA", "PONTE GOVERNADOR PAULO GUERRA", "AVENIDA DOIS RIOS",
    "RUA PRINCESA ISABEL", "AVENIDA RUI BARBOSA", "AVENIDA VISCONDE DE ALBUQUERQUE", "AVENIDA BOA VIAGEM",
    "AVENIDA AFONSO OLINDENSE", "RUA DA HARMONIA", "AVENIDA RECIFE", "RUA ITAJAI", "RUA PEREIRA COUTINHO FILHO",
    "RUA OLIVIA MENELAU", "RUA DE APIPUCOS", "RUA GASPAR PEREZ", "AVENIDA SUL GOVERNADOR CID SAMPAIO",
    "RUA PADRE TEOFILO TWORZ", "RUA FLORIANO PEIXOTO", "RUA DONA JULIETA", "RUA GENERAL POLIDORO",
    "RUA PROFESSOR AURELIO DE CASTRO CAVALCANTI", "RUA DEZ DE JULHO", "AVENIDA HILDEBRANDO DE VASCONCELOS",
    "RUA CAPITAO ANTONIO MANHAES DE MATTOS", "AVENIDA GENERAL SAN MARTIN", "RUA GOMES TABORDA", "AVENIDA CRUZ CABUGA",
    "RUA JOSE OSORIO", "AVENIDA DEZESSETE DE AGOSTO", "RUA BARAO DE SOUZA LEAO", "RUA VISCONDE DE JEQUITINHONHA",
    "RUA FERNANDO CESAR", "RUA ALBERTO PAIVA", "AVENIDA MARIA IRENE", "RUA DESENHISTA EULINO SANTOS",
    "AVENIDA GENERAL MAC ARTHUR", "RUA CAPITAO TEMUDO", "RUA RAUL POMPEIA", "RUA JOAQUIM NABUCO",
    "VIADUTO PAPA JOAO PAULO II", "AVENIDA ARMINDO MOURA", "AVENIDA BEBERIBE SANTA CRUZ FUTEBOL CLUBE",
    "PRACA DA REPUBLICA", "CAIS DE SANTA RITA", "RUA REAL DA TORRE", "RUA RIBEIRO DE BRITO", "RUA PADRE LEMOS",
    "RUA DESEMBARGADOR MARTINS PEREIRA", "AVENIDA CONSELHEIRO AGUIAR", "AVENIDA CAXANGA", "AVENIDA DOM JOAO VI",
    "AVENIDA DANTAS BARRETO", "PRACA DAS CINCO PONTAS", "RUA JUNDIA", "RUA JOAO IVO DA SILVA", "RUA EMILIANO BRAGA",
    "ESTRADA DO BONGI ARMANDO DA FONTE", "AVENIDA CELSO FURTADO", "RUA BOLIVAR", "RUA CORONEL URBANO RIBEIRO DE SENA",
    "RUA DA ENCOSTA", "RUA IMPERIAL", "RUA POTENGY", "RUA DONA BENVINDA DE FARIAS", "RUA BENFICA",
    "CORREGO DO BARTOLOMEU", "AVENIDA PREFEITO ARTUR LIMA CAVALCANTI", "AVENIDA JOSE GONCALVES DE MEDEIROS",
    "RUA SANTA EDWIRGES", "RUA RIO MARANHAO", "ESTRADA DO ARRAIAL", "VIADUTO ENGENHEIRO ANTONIO DE QUEIROZ GALVAO",
    "AVENIDA JOAO DE BARROS", "AVENIDA JOAO CABRAL DE MELO NETO", "AVENIDA PROFESSOR LUIZ FREIRE", "RUA TABAIARES",
    "RUA MANOEL DE BRITO", "RUA MANUEL DE BARROS LIMA", "AVENIDA INACIO MONTEIRO", "AVENIDA PRESIDENTE DUTRA",
    "RUA AMELIA", "RUA PROFESSOR CHAVES BATISTA", "RUA TENENTE ROLAND RITTMISTER", "RUA CHA DE ALEGRIA",
    "RUA ITACARI", "RUA GENERAL GOES MONTEIRO", "RUA JOAO DIAS MARTINS", "RUA GUANABARA", "ESTRADA DOS REMEDIOS",
    "AVENIDA SERRA DA MANTIQUEIRA", "RUA DOIS IRMAOS", "RUA CORREGO DO EUCLIDES", "RUA DOM PAULO II",
    "TRAVESSA DO RAPOSO", "PONTE MARECHAL HUMBERTO CASTELO BRANCO", "RUA CAPITAO ZUZINHA", "AVENIDA GUARARAPES",
    "RUA CRUZEIRO DO FORTE", "RUA QUARENTA E OITO", "AVENIDA JORNALISTA COSTA PORTO", "RUA JACOB", "RUA DA SOLEDADE",
    "AVENIDA SANTOS DUMONT", "RUA BOMBA DO HEMETERIO", "RUA CARLOS FERNANDES", "AVENIDA ENGENHEIRO JOSE ESTELITA",
    "RUA SOUZA DE ANDRADE", "AVENIDA JOSE AMERICO DE ALMEIDA", "RUA CONEGO JOSE FERNANDES MACHADO",
    "RUA MARECHAL DEODORO", "AVENIDA RIO LARGO", "RUA ALVARES DE AZEVEDO", "AVENIDA ENCANTA MOCA", "RUA MOTOCOLOMBO",
    "TRAVESSA HERMILIO GOMES", "RUA SEBASTIAO MALTA ARCOVERDE", "RUA JACK AYRES", "RUA CATULO DA PAIXAO CEARENSE",
    "RUA DA CONCORDIA", "RUA EXPEDICIONARIO TEODORO SATIVA", "PONTE DE AFOGADOS", "AVENIDA MANOEL GONCALVES DA LUZ",
    "RUA FREI CASSIMIRO", "RUA VINTE E UM DE ABRIL", "AVENIDA DOM HELDER CAMARA", "RUA PROFESSOR AUGUSTO LINS E SILVA",
    "RUA JOAO UZEDA LUNA", "RUA PARIS", "RUA JOAO TUDE DE MELO", "RUA SETUBAL", "RUA DO VEIGA", "RUA MANUEL DE MEDEIROS",
    "PONTE VICE PRESIDENTE JOSE ALENCAR", "RUA DOS PALMARES", "RUA ALTO JOSE BONIFACIO", "RUA IMPERADOR DOM PEDRO II",
    "PONTE JOSE DE BARROS LIMA", "ESTRADA DO FORTE DO ARRAIAL NOVO DO BOM JESUS", "RUA JERONIMO VILELA", "RUA DO SOL",
    "RUA BARAO DE VERA CRUZ", "RUA JEAN EMILE FAVRE", "RUA DO HOSPICIO", "AVENIDA GOVERNADOR CARLOS DE LIMA CAVALCANTI",
    "RUA BARAO DE MURIBECA", "RUA CONSELHEIRO PERETTI", "RUA ALEGRE", "RUA CONSELHEIRO PORTELA",
    "AVENIDA CIDADE DE MONTEIRO", "RUA ARTHUR BRUNO SCHWAMBACH", "AVENIDA SPORT CLUBE DO RECIFE",
    "RUA AMAURI DE MEDEIROS", "AVENIDA FLOR DE SANTANA", "RUA DO MACHADO", "RUA TREZE DE MAIO", "AVENIDA MARIO MELO",
    "RUA OSCAR DE BARROS", "TRAVESSA DA RECUPERACAO", "RUA PROFESSOR JOAQUIM XAVIER DE BRITO", "ESTRADA DO ENCANAMENTO",
    "AVENIDA SENADOR ROBERT KENNEDY", "RUA ONZE DE AGOSTO", "CANAL DO JORDAO", "RUA JOAO CARDOSO AIRES",
    "RUA PROFESSOR JOSE AMARINO DOS REIS", "CAIS DO APOLO", "RUA REZENDE",
    "AVENIDA DOUTOR DIRCEU VELLOSO TOSCANO DE BRITO", "AVENIDA PROFESSOR ESTEVAO FRANCISCO DA COSTA",
    "AVENIDA DA RECUPERACAO", "RUA PADRE ROMA", "RUA PROFESSOR MARIO CASTRO", "RUA ANTONIO CURADO",
    "AVENIDA VEREADOR OTACILIO AZEVEDO", "RUA BARAO DE ITAMARACA", "RUA ODORICO MENDES", "RUA DESEMBARGADOR LUIZ SALAZAR",
    "RUA BARAO DE AGUA BRANCA", "PRACA MIGUEL DE CERVANTES", "AVENIDA REPUBLICA DO LIBANO", "RUA DA ESPERANCA",
    "RUA SANTO ELIAS", "RUA IPOJUCA", "RUA CAMPOS TABAIARES", "RUA ERNESTO DE PAULA SANTOS", "AVENIDA LIBERDADE",
    "RUA DAS MOCAS", "RUA SANT'ANNA", "VIADUTO PRESIDENTE TANCREDO NEVES", "RUA ITABORA",
    "RUA PROFESSOR TRAJANO DE MENDONCA", "RUA MARCILIO DIAS", "RUA JOSE DE ALENCAR", "AVENIDA ESTANCIA",
    "RUA FREI MATIAS TEVIS", "AVENIDA VISCONDE DE SUASSUNA", "RUA WILFRID RUSSEL SHORTO", "RUA AURORA CACOTE",
    "RUA OCIDENTAL", "RUA DAS CREOULAS", "ESTRADA DO BARBALHO", "RUA ALBINO MEIRA", "RUA RIO TAPADO", "RUA DOM BOSCO",
    "RUA DO PRINCIPE", "VIADUTO DAS CINCO PONTAS", "RUA ZUMBI DOS PALMARES", "RUA ROSARIO DA BOA VISTA",
    "RUA PAULA BATISTA", "AVENIDA SAO PAULO", "RUA VASCO DA GAMA", "RUA CONSELHEIRO NABUCO", "PRACA DA RUA GOMES TABORDA",
    "RUA ENGENHEIRO JOSE BRANDAO CAVALCANTE", "RUA CLOVIS BEVILAQUA", "PRACA DO ENTRONCAMENTO",
    "AVENIDA PREFEITO LIMA CASTRO", "RUA DO ESPINHEIRO", "AVENIDA ANTONIO DE GOES", "RUA MARQUES AMORIM",
    "RUA DA REGENERACAO", "RUA DOUTOR GASTAO DA SILVEIRA", "RUA CLAUDIO BROTHERHOOD", "AVENIDA JOAQUIM RIBEIRO",
    "RUA MANOEL DE ALBUQUERQUE FERNANDES", "AVENIDA MILITAR", "RUA DOIS DE JULHO", "AVENIDA PROFESSOR ARTUR DE SA",
    "RUA ROMULO PESSOA", "RUA COSME VIANA", "RUA HIPOLITO BRAGA", "PRACA ABELARDO RIJO", "RUA ESTADO DE ISRAEL",
    "RUA ARQUITETO LUIZ NUNES", "RUA DAS CALCADAS", "RUA PASCOAL SIVINI", "AVENIDA CONDE DA BOA VISTA",
    "AVENIDA MARTINS DE BARROS", "RUA PRESIDENTE HONORIO HERMETO", "RUA JAMAICA", "PONTE DO MOTOCOLOMBO",
    "RUA DO FUTURO", "RUA JUNDIAI", "RUA DOS NAVEGANTES", "RUA DESEMBARGADOR OTILIO NEIVA", "AVENIDA CHAPADA DO ARARIPE",
    "AVENIDA DOUTOR JAYME DA FONTE", "AVENIDA BEIRA RIO DEPUTADO OSVALDO COELHO", "RUA BALTAZAR PASSOS",
    "RUA JACO VELOSINO", "AVENIDA CHAGAS FERREIRA", "RUA VALE DO ITAJAI", "RUA DOUTOR EUDES COSTA", "RUA EDSON ALVARES",
    "AVENIDA IZABEL DE GOES", "RUA PAULINO DE FARIAS", "AVENIDA TAPAJOS", "RUA DONA MAGINA PONTUAL",
    "2A TRAVESSA MARQUES DE BAIPENDI", "RUA SENADOR JOSE HENRIQUE", "RUA PARATIBE", "RUA FELIX DE BRITO E MELO",
    "AVENIDA ANTONIO TORRES GALVAO", "RUA VIRGINIA LORETO", "RUA NOGUEIRA DE SOUZA", "RUA GALVAO RAPOSO",
    "RUA COMENDADOR MORAIS", "RUA CARLOS GOMES", "RUA MARQUES DE MARICA", "RUA MARQUES DE BAIPENDI", "RUA CAMBOIM",
    "AVENIDA MANOEL BORBA", "RUA PROFESSOR ARNALDO CARNEIRO LEAO", "RUA MINISTRO MARIO ANDREAZZA", "RUA RIO TOCANTINS",
    "RUA VALE DO SIRIJI", "AVENIDA SEBASTIAO SALAZAR", "RUA PROFESSOR JOSE BRANDAO", "RUA COUTO MAGALHAES",
    "RUA SA E SOUZA", "RUA HENRIQUE CAPITULINO", "RUA AGRICOLANDIA", "RUA CANAVIEIRA", "RUA AMARO COUTINHO",
    "RUA DO PEIXOTO", "RUA SAO SEBASTIAO", "RUA DOUTOR CARLOS MAVIGNIER", "RUA CLARA", "RUA MARQUES DE VALENCA",
    "RUA PROFESSOR JERONIMO GUEIROS", "RUA URIEL DE HOLANDA", "AVENIDA CENTENARIO ALBERTO SANTOS DUMONT",
    "RUA DA AURORA", "RUA HONORIO CORREIA", "RUA DOUTOR ALVARO FERRAZ", "RUA BADEJO", "RUA TELES JUNIOR",
    "RUA PINTOR ANTONIO ALBUQUERQUE", "RUA AMALIA BERNARDINO DE SOUZA", "RUA PRUDENTE DE MORAES", "RUA PADRE MIGUELINHO",
    "RUA EVARISTO DA VEIGA", "RUA DO POMBAL", "CAIS DO PORTO DO RECIFE", "RUA QUITERIO INACIO DE MELO",
    "RUA NOVA DESCOBERTA", "RUA JORNALISTA EDMUNDO BITTENCOURT", "RUA DOUTOR VICENTE GOMES", "LADEIRA DA COHAB",
    "PONTE PRINCESA IZABEL", "RUA PADRE LANDIM", "RUA BLUMENAU", "AVENIDA PARNAMIRIM", "AVENIDA SATURNINO DE BRITO",
    "AVENIDA CORREIA DE BRITO", "RUA RAIMUNDO FREIXEIRA", "RUA GERVASIO FIORAVANTE", "RUA GOIANESIA",
    "PONTE ESTACIO COIMBRA", "RUA MARECHAL MANOEL LUIS OSORIO", "AVENIDA FERNANDO SIMOES BARBOSA",
    "RUA MARQUES DO PARANA", "PRACA JORNALISTA FRANCISCO PESSOA DE QUEIROZ", "AVENIDA CONSELHEIRO ROSA E SILVA",
    "RUA GUAIANAZES", "RUA NESTOR SILVA", "PONTE DO LIMOEIRO", "RUA CRISTOVAO JAQUES", "RUA MEM DE SA",
    "RUA JOSE NATARIO", "RUA ANTONIO FALCAO", "RUA PAMPULHA", "RUA FRANCISCO ALVES", "RUA ALMIRANTE TAMANDARE",
    "RUA DAS GRACAS", "RUA ALTO DO RESERVATORIO", "AVENIDA DONA CARENTINA", "TRAVESSA DO CAIS DA DETENCAO",
    "AVENIDA DESEMBARGADOR GUERRA BARRETO", "AVENIDA DESEMBARGADOR JOSE NEVES", "PRACA DO DERBY",
    "RUA DEMOCRITO DE SOUZA FILHO", "RUA PEDRO AFONSO", "AVENIDA CAMPO VERDE", "RUA JOAO FRANCISCO LISBOA",
    "RUA DOUTOR GEORGE WILLIAM BUTLER", "RUA VALE DO CARIRI", "RUA TAQUARITINGA", "PRACA DA BANDEIRA",
    "RUA PADRE CARAPUCEIRO", "RUA SARGENTO SILVINO MACEDO", "RUA MAURICEIA", "RUA DA FELICIDADE", "RUA SANTA CECILIA",
    "RUA FARIAS NEVES", "RUA BELA VISTA", "AVENIDA PROFESSOR JOAO MEDEIROS", "RUA PADRE DEHON",
    "RUA COMENDADOR BENTO AGUIAR", "RUA DOS COELHOS", "RUA HELIO BRANDAO", "RUA DESEMBARGADOR GOIS CAVALCANTE",
    "RUA DA GUIA", "RUA LEANDRO BARRETO", "RUA JOSE DOMINGUES DA SILVA", "RUA ANDRE BEZERRA", "RUA MARAGOGI",
    "RUA ISAAC MARKMAN", "RUA DOS PRAZERES", "RUA RIO XINGU", "RUA NOSSA SENHORA DA SAUDE", "RUA DAS NINFAS",
    "RUA ERNANI BRAGA", "AVENIDA DOZE DE JUNHO", "RUA PROFESSOR FRANCISCO DA TRINDADE", "RUA DELMIRO GOUVEIA",
    "RUA VISCONDE DE CAIRU", "RUA OUREM", "RUA ARTUR COUTINHO", "RUA RIBEIRO PESSOA", "RUA PROFESSORA ROSILDA COSTA",
    "RUA DOM MANOEL DA COSTA", "RUA DE SANTA RITA", "RUA SETE PECADOS", "PRACA GENERAL ABREU E LIMA",
    "RUA DOUTOR JOAO ELISIO", "RUA DA SANTA CRUZ", "AVENIDA RAIMUNDO DINIZ", "RUA OSCAR PINTO", "RUA S D 9806",
    "RUA TEOLANDIA", "RUA JOAO FERNANDES VIEIRA", "RUA PREFEITO JORGE MARTINS", "RUA REGUEIRA COSTA", "RUA PIRACANJUBA",
    "AVENIDA SANTA FE", "AVENIDA BARBOSA LIMA", "RUA ADERBAL DE MELO", "RUA ANITA",
    "RUA DEPUTADO JOSE FRANCISCO DE MELO CAVALCANTI", "RUA FRANKLIN TAVORA", "RUA EDUARDO JORGE",
    "RUA ACADEMICO HELIO RAMOS", "RUA GOUVEIA DE BARROS", "RUA DA UNIAO", "RUA CONEGO BARATA", "PRACA FARIAS NEVES",
    "RUA PADRE CABRAL", "RUA TRES DE AGOSTO", "RUA TOME GIBSON", "RUA PETRONILA BOTELHO", "RUA CAFESOPOLIS",
    "RUA SANTOS ARAUJO", "RUA FONSECA OLIVEIRA"
]

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


def verificar_alagamentos(df_selecionados: pd.DataFrame) -> list:
    """Verifica quais cruzamentos selecionados são pontos de alagamento"""
    alagamentos_encontrados = []
    if df_selecionados.empty:
        return alagamentos_encontrados
    
    lista_alvo_norm = [x.strip().upper() for x in ALAGAMENTOS_ALVO]
    for _, row in df_selecionados.iterrows():
        l1 = str(row['log1']).strip().upper()
        l2 = str(row['log2']).strip().upper()
        comb1 = f"{l1} / {l2}"
        comb2 = f"{l2} / {l1}"
        if comb1 in lista_alvo_norm:
            alagamentos_encontrados.append(comb1)
        elif comb2 in lista_alvo_norm:
            alagamentos_encontrados.append(comb2)
    
    return alagamentos_encontrados


def verificar_sinistros(df_selecionados: pd.DataFrame) -> list:
    """Verifica quais ruas dos cruzamentos selecionados têm histórico de sinistros"""
    sinistros_encontrados = []
    if df_selecionados.empty:
        return sinistros_encontrados
    
    lista_sinistros_norm = set([x.strip().upper() for x in RUAS_SINISTROS_ALVO])
    ruas_unicas_encontradas = set()
    
    for _, row in df_selecionados.iterrows():
        l1 = str(row['log1']).strip().upper()
        l2 = str(row['log2']).strip().upper()
        
        if l1 in lista_sinistros_norm:
            ruas_unicas_encontradas.add(l1)
        if l2 in lista_sinistros_norm:
            ruas_unicas_encontradas.add(l2)
    
    return sorted(list(ruas_unicas_encontradas))


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


def filtrar_por_cobertura_e_distancia(df: pd.DataFrame, cobertura_frac: float, min_dist: float, 
                                       max_cruzamentos: int = None, raio_cobertura: float = 50,
                                       limite_cobertura_logradouro: float = None) -> tuple:
    """
    Filtra cruzamentos mantendo a cobertura alvo mesmo com filtro de distância.
    
    Args:
        df: DataFrame com cruzamentos ordenados por IPE
        cobertura_frac: Fração de cobertura alvo (0-1)
        min_dist: Distância mínima entre cruzamentos DO MESMO LOGRADOURO em metros
        max_cruzamentos: Limite máximo de cruzamentos (None = sem limite)
        raio_cobertura: Raio de cobertura de cada câmera NO MESMO LOGRADOURO em metros
        limite_cobertura_logradouro: Fração máxima de cobertura por logradouro (0-1, None = sem limite)
    
    Retorna: (DataFrame selecionados, cobertura_real, alvo_atingido, motivo_limite, ids_cobertos)
    """
    if df.empty:
        return pd.DataFrame(), 0.0, True, None, set()
    
    ipe_total = df['ipe_cruz'].sum()
    if ipe_total <= 0:
        return pd.DataFrame(), 0.0, True, None, set()
    
    # Calcular IPE total por logradouro (para limite de cobertura por rua)
    ipe_por_logradouro = {}
    if limite_cobertura_logradouro is not None:
        for _, c in df.iterrows():
            ipe = c['ipe_cruz']
            for cod_log in [c['cod_log1'], c['cod_log2']]:
                ipe_por_logradouro[cod_log] = ipe_por_logradouro.get(cod_log, 0) + ipe
    
    # Rastrear cobertura acumulada por logradouro
    cobertura_por_logradouro = {}
    
    # Pré-indexar cruzamentos por logradouro
    cruzamentos_por_logradouro = {}
    cruz_por_id = {}
    
    for _, c in df.iterrows():
        cruz_id = c['id']
        lat, lon = c['lat'], c['lon']
        ipe = c['ipe_cruz']
        cod_log1, cod_log2 = c['cod_log1'], c['cod_log2']
        
        cruz_por_id[cruz_id] = {
            'lat': lat, 'lon': lon, 'ipe': ipe,
            'cod_log1': cod_log1, 'cod_log2': cod_log2
        }
        
        for cod_log in [cod_log1, cod_log2]:
            if cod_log not in cruzamentos_por_logradouro:
                cruzamentos_por_logradouro[cod_log] = []
            cruzamentos_por_logradouro[cod_log].append((cruz_id, lat, lon, ipe))
    
    cameras_por_logradouro = {}
    
    def camera_muito_perto_no_logradouro(lat, lon, cod_log1, cod_log2):
        if min_dist <= 0:
            return False
        for cod_log in [cod_log1, cod_log2]:
            if cod_log in cameras_por_logradouro:
                for cam_lat, cam_lon in cameras_por_logradouro[cod_log]:
                    if distancia_metros(lat, lon, cam_lat, cam_lon) < min_dist:
                        return True
        return False
    
    def registrar_camera_nos_logradouros(lat, lon, cod_log1, cod_log2):
        for cod_log in [cod_log1, cod_log2]:
            if cod_log not in cameras_por_logradouro:
                cameras_por_logradouro[cod_log] = []
            cameras_por_logradouro[cod_log].append((lat, lon))
    
    def calcular_cobertura_por_logradouro(cam_lat, cam_lon, cam_cod_log1, cam_cod_log2, ids_cobertos_atual):
        novos_cobertos = set()
        for cod_log in [cam_cod_log1, cam_cod_log2]:
            if cod_log in cruzamentos_por_logradouro:
                for cruz_id, lat, lon, ipe in cruzamentos_por_logradouro[cod_log]:
                    if cruz_id not in ids_cobertos_atual and cruz_id not in novos_cobertos:
                        if distancia_metros(cam_lat, cam_lon, lat, lon) <= raio_cobertura:
                            novos_cobertos.add(cruz_id)
        return novos_cobertos
    
    def violaria_limite_logradouro(cruz_id, novos_cobertos, cod_log1, cod_log2):
        if limite_cobertura_logradouro is None:
            return False
        
        ipe_adicional = {cod_log1: 0, cod_log2: 0}
        ipe_cruz = cruz_por_id[cruz_id]['ipe']
        ipe_adicional[cod_log1] += ipe_cruz
        ipe_adicional[cod_log2] += ipe_cruz
        
        for cob_id in novos_cobertos:
            if cob_id != cruz_id and cob_id in cruz_por_id:
                cob_info = cruz_por_id[cob_id]
                cob_ipe = cob_info['ipe']
                cob_log1, cob_log2 = cob_info['cod_log1'], cob_info['cod_log2']
                
                if cob_log1 not in ipe_adicional:
                    ipe_adicional[cob_log1] = 0
                if cob_log2 not in ipe_adicional:
                    ipe_adicional[cob_log2] = 0
                    
                ipe_adicional[cob_log1] += cob_ipe
                ipe_adicional[cob_log2] += cob_ipe
        
        for cod_log in [cod_log1, cod_log2]:
            ipe_total_log = ipe_por_logradouro.get(cod_log, 0)
            if ipe_total_log <= 0:
                continue
            
            ipe_atual = cobertura_por_logradouro.get(cod_log, 0)
            ipe_novo = ipe_atual + ipe_adicional.get(cod_log, 0)
            
            if ipe_novo / ipe_total_log > limite_cobertura_logradouro:
                return True
        
        return False
    
    def atualizar_cobertura_logradouros(cruz_id, novos_cobertos, cod_log1, cod_log2):
        if limite_cobertura_logradouro is None:
            return
        
        processados = set()
        ipe_cruz = cruz_por_id[cruz_id]['ipe']
        cobertura_por_logradouro[cod_log1] = cobertura_por_logradouro.get(cod_log1, 0) + ipe_cruz
        cobertura_por_logradouro[cod_log2] = cobertura_por_logradouro.get(cod_log2, 0) + ipe_cruz
        processados.add(cruz_id)
        
        for cob_id in novos_cobertos:
            if cob_id not in processados and cob_id in cruz_por_id:
                cob_info = cruz_por_id[cob_id]
                cob_ipe = cob_info['ipe']
                cob_log1, cob_log2 = cob_info['cod_log1'], cob_info['cod_log2']
                
                cobertura_por_logradouro[cob_log1] = cobertura_por_logradouro.get(cob_log1, 0) + cob_ipe
                cobertura_por_logradouro[cob_log2] = cobertura_por_logradouro.get(cob_log2, 0) + cob_ipe
                processados.add(cob_id)
    
    selecionados = []
    ids_cobertos = set()
    ipe_coberto = 0.0
    motivo_limite = None
    
    for _, c in df.iterrows():
        if max_cruzamentos is not None and len(selecionados) >= max_cruzamentos:
            motivo_limite = 'quantidade'
            break
        
        cobertura_atual = ipe_coberto / ipe_total
        if max_cruzamentos is None and cobertura_atual >= cobertura_frac:
            break
        
        lat, lon = c['lat'], c['lon']
        cruz_id = c['id']
        cod_log1, cod_log2 = c['cod_log1'], c['cod_log2']
        
        if camera_muito_perto_no_logradouro(lat, lon, cod_log1, cod_log2):
            continue
        
        novos_cobertos = calcular_cobertura_por_logradouro(lat, lon, cod_log1, cod_log2, ids_cobertos)
        if cruz_id not in ids_cobertos:
            novos_cobertos.add(cruz_id)
        
        if violaria_limite_logradouro(cruz_id, novos_cobertos, cod_log1, cod_log2):
            continue
        
        selecionados.append(c.to_dict())
        registrar_camera_nos_logradouros(lat, lon, cod_log1, cod_log2)
        atualizar_cobertura_logradouros(cruz_id, novos_cobertos, cod_log1, cod_log2)
        
        for cob_id in novos_cobertos:
            if cob_id in cruz_por_id and cob_id not in ids_cobertos:
                ipe_coberto += cruz_por_id[cob_id]['ipe']
        ids_cobertos.update(novos_cobertos)
    
    if not selecionados:
        return pd.DataFrame(), 0.0, False, None, set()
    
    df_result = pd.DataFrame(selecionados)
    cobertura_real = ipe_coberto / ipe_total
    df_result['cobertura_acum'] = df_result['ipe_cruz'].cumsum() / ipe_total
    
    alvo_atingido = cobertura_real >= cobertura_frac * 0.99
    if not alvo_atingido and motivo_limite is None:
        motivo_limite = 'restricoes'
    
    return df_result, cobertura_real, alvo_atingido, motivo_limite, ids_cobertos


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
                <b>Ruas:</b> {c['log1']} x {c['log2']}<br/>
                <b>Camera:</b> {tipo}<br/>
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


def gerar_estatisticas_equipamentos(df_equipamentos: pd.DataFrame, nota_min: int) -> dict:
    """Gera estatísticas detalhadas dos equipamentos"""
    if df_equipamentos.empty:
        return None
    
    df_eq = df_equipamentos[df_equipamentos['peso'] >= nota_min].copy()
    total_filtrado = len(df_eq)
    
    if total_filtrado == 0:
        return {'total': 0, 'tipos': {}, 'agrupados': {}, 'prioridades': {}}
    
    # Tratamentos
    df_eq['primeira_palavra'] = df_eq['tipo'].astype(str).apply(
        lambda x: x.split(' ')[0] if len(x) > 0 else "Outros"
    )
    
    mapa_semelhantes = {
        "2ª": "2ª Jardim", "Primeira": "Parque", "Maria": "Rua", "Skate,": "Skatepark",
        "3ª": "3ª Jardim", "1º": "1ª Jardim", "Administração": "Pátio", "AVENIDA": "AVENIDA",
        "CAIXA": "Caixa Cultural", "Casa": "Casa dos Patrimônios", "Novo": "Skatepark",
        "ANTIGO": "Hotel", "CASA": "Casa da Cultura", "BURACO": "Praia", "POLO": "Polo",
        "Numa": "Rua", "PARQUE": "Parque"
    }
    df_eq['agrupado'] = df_eq['primeira_palavra'].apply(lambda x: mapa_semelhantes.get(x, x))
    
    contagem_tipos = df_eq['tipo'].value_counts().to_dict()
    contagem_agrupada = df_eq['agrupado'].value_counts().to_dict()
    contagem_pesos = df_eq['peso'].value_counts().sort_index(ascending=False).to_dict()
    
    return {
        'total': total_filtrado,
        'tipos': contagem_tipos,
        'agrupados': contagem_agrupada,
        'prioridades': contagem_pesos
    }


# ============================================================
# SIDEBAR - CONTROLES
# ============================================================
with st.sidebar:
    st.markdown("## 🎛️ Controles")
    
    # 1. Excel de cruzamentos
    st.markdown('<div class="section-title">1a. Excel de cruzamentos</div>', unsafe_allow_html=True)
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
    
    nota_min_equip = st.slider("Nota minima equipamentos", 1, 5, 4, key='nota_equip')
    
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
    st.markdown('<div class="section-title">2a. Alvo de Cobertura IPE</div>', unsafe_allow_html=True)
    cobertura_pct = st.slider("Cobertura (%)", 5, 100, 40, key='cobertura')
    
    # 2b. Quantidade maxima
    st.markdown('<div class="section-title">2b. Quantidade maxima de pontos (opcional)</div>', unsafe_allow_html=True)
    usar_limite_qtd = st.checkbox("Limitar quantidade de pontos", value=False, key='usar_limite_qtd')
    if usar_limite_qtd:
        max_cruzamentos = st.number_input("Maximo de pontos", min_value=1, max_value=5000, value=100, step=10, key='max_cruz',
                                          help="Quando definido, o sistema usa TODOS os pontos ate este limite")
    else:
        max_cruzamentos = None
    
    # 3. Distancia minima
    st.markdown('<div class="section-title">3a. Distancia minima entre câmeras</div>', unsafe_allow_html=True)
    dist_min = st.slider("Distancia (m)", 0, 1000, 150, step=50, key='dist_min', help="Distancia minima entre câmeras que compartilham o mesmo logradouro")
    
    # 3b. Raio de cobertura
    st.markdown('<div class="section-title">3b. Raio de cobertura das cameras</div>', unsafe_allow_html=True)
    raio_cobertura = st.slider("Raio (m)",0, 200, 50, step=10, key='raio_cobertura')
    
    # 3c. Limite de cobertura por logradouro
    st.markdown('<div class="section-title">4a. Limite de cobertura por logradouro</div>', unsafe_allow_html=True)
    usar_limite_log = st.checkbox("Limitar cobertura por rua", value=False, key='usar_limite_log',
                                   help="Evita concentracao de cameras em uma unica rua")
    if usar_limite_log:
        limite_cob_log = st.slider("Maximo por logradouro (%)", 10, 100, 50, step=5, key='limite_log',
                                    help="Limita quanto do IPE de cada rua pode ser coberto") / 100
        st.markdown(f"""<div class="info-box">
            ℹ️ Cada rua tera no maximo <b>{limite_cob_log*100:.0f}%</b> do seu IPE coberto
        </div>""", unsafe_allow_html=True)
    else:
        limite_cob_log = None
    
    # 5. Pesos
    st.markdown('<div class="section-title">5. Pesos dos eixos</div>', unsafe_allow_html=True)
    peso_seg = st.slider("Seguranca", 0, 100, 50, key='peso_seg')
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


# ============================================================
# PROCESSAMENTO
# ============================================================
cobertura_real = 0.0
alvo_atingido = True
motivo_limite = None
ids_cobertos = set()

if not st.session_state.logs.empty and not st.session_state.cruzamentos.empty:
    st.session_state.cruzamentos_calculados = calcular_ipe_cruzamentos(
        st.session_state.logs, st.session_state.cruzamentos, w_seg, w_lct, w_com, w_mob
    )

if not st.session_state.cruzamentos_calculados.empty:
    st.session_state.ultimo_selecionados, cobertura_real, alvo_atingido, motivo_limite, ids_cobertos = filtrar_por_cobertura_e_distancia(
        st.session_state.cruzamentos_calculados, cobertura_pct / 100, dist_min, 
        max_cruzamentos, raio_cobertura, limite_cob_log
    )

# ============================================================
# AREA PRINCIPAL - MAPA E RESUMOS
# ============================================================
st.markdown('<h1 class="main-header">Otimizador do Videomonitoramento - Recife</h1>', unsafe_allow_html=True)

# Alerta se cobertura alvo nao foi atingida
if not st.session_state.cruzamentos_calculados.empty and not alvo_atingido and max_cruzamentos is None:
    restricoes_ativas = []
    if dist_min > 0:
        restricoes_ativas.append(f"distancia minima de {dist_min}m")
    if limite_cob_log is not None:
        restricoes_ativas.append(f"limite de {limite_cob_log*100:.0f}% por logradouro")
    
    restricoes_texto = " e ".join(restricoes_ativas) if restricoes_ativas else "as restricoes configuradas"
    
    st.markdown(f"""<div class="coverage-warning">
        ⚠️ <b>Exibindo cobertura maxima possivel:</b> {cobertura_real*100:.1f}% (alvo: {cobertura_pct}%)<br/>
        <small>Com {restricoes_texto}, nao e possivel atingir {cobertura_pct}%. O mapa mostra o maximo atingivel.</small>
    </div>""", unsafe_allow_html=True)

# Layout: Mapa a esquerda, estatisticas a direita
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
    # ============================================================
    # ESTATÍSTICAS DOS CRUZAMENTOS (lado direito do mapa)
    # ============================================================
    if not st.session_state.cruzamentos_calculados.empty:
        df_calc = st.session_state.cruzamentos_calculados
        df_sel = st.session_state.ultimo_selecionados
        
        total_cruz = len(df_calc)
        total_sel = len(df_sel)
        total_cobertos = len(ids_cobertos)
        
        # Cobertura por eixo
        t_seg = df_calc['ipe_cruz_seg'].sum() or 1
        t_lct = df_calc['ipe_cruz_lct'].sum() or 1
        t_com = df_calc['ipe_cruz_com'].sum() or 1
        t_mob = df_calc['ipe_cruz_mob'].sum() or 1
        
        if ids_cobertos:
            df_cobertos = df_calc[df_calc['id'].isin(ids_cobertos)]
            cov_seg = df_cobertos['ipe_cruz_seg'].sum() / t_seg * 100
            cov_lct = df_cobertos['ipe_cruz_lct'].sum() / t_lct * 100
            cov_com = df_cobertos['ipe_cruz_com'].sum() / t_com * 100
            cov_mob = df_cobertos['ipe_cruz_mob'].sum() / t_mob * 100
        else:
            cov_seg = cov_lct = cov_com = cov_mob = 0
        
        # ============================================================
        # CÁLCULO DE CUSTO (Lógica 50/30/20)
        # ============================================================
        
        # Definição das quantidades de pontos por categoria
        qtd_pontos_3cam = int(total_cobertos * 0.50)
        qtd_pontos_2cam = int(total_cobertos * 0.30)
        # O restante vai para 1 câmera para garantir que a soma bata com o total exato
        qtd_pontos_1cam = total_cobertos - qtd_pontos_3cam - qtd_pontos_2cam

        # Cálculo do total de câmeras físicas
        total_cameras_fisicas = (qtd_pontos_3cam * 3) + (qtd_pontos_2cam * 2) + (qtd_pontos_1cam * 1)
        
        # Cálculo financeiro
        custo_unitario = 838
        custo_total_geral = total_cameras_fisicas * custo_unitario

        # ============================================================
        # EXIBIÇÃO - Pontos Monitorados
        # ============================================================
        st.markdown("#### 📊 Pontos Monitorados")
        
        stats_html = f"""<div class="stat-box">
            <div class="stat-row"><span>Total de pontos (Input):</span><span class="stat-value">{total_cruz:,}</span></div>"""
        
        if max_cruzamentos is not None:
            stats_html += f"""
            <div class="stat-row"><span>Limite definido:</span><span class="stat-value">{max_cruzamentos:,}</span></div>"""

        stats_html += f"""
            <div class="stat-row" style="border-top: 1px solid rgba(255,255,255,0.1); margin-top:5px; padding-top:5px;">
                <span><b>Pontos Selecionados:</b></span><span class="stat-value" style="color:#a5b4fc;">{total_cobertos:,}</span>
            </div>
            <div class="stat-row"><span>Raio de cobertura:</span><span class="stat-value">{raio_cobertura}m</span></div>"""
        
        if limite_cob_log is not None:
            stats_html += f"""
            <div class="stat-row"><span>Limite por logradouro:</span><span class="stat-value">{limite_cob_log*100:.0f}%</span></div>"""
        
        stats_html += f"""
            <div class="stat-row"><span>Cobertura IPE atingida:</span><span class="stat-value" style="color: {'#4ade80' if cobertura_real >= cobertura_pct/100 else '#fbbf24'};">{cobertura_real*100:.1f}%</span></div>
        </div>"""
        
        st.markdown(stats_html, unsafe_allow_html=True)
        
        st.markdown("#### 📈 Cobertura por Eixo")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row"><span>Segurança:</span><span class="stat-value">{cov_seg:.1f}%</span></div>
            <div class="stat-row"><span>LCT:</span><span class="stat-value">{cov_lct:.1f}%</span></div>
            <div class="stat-row"><span>Comercial:</span><span class="stat-value">{cov_com:.1f}%</span></div>
            <div class="stat-row"><span>Mobilidade:</span><span class="stat-value">{cov_mob:.1f}%</span></div>
        </div>""", unsafe_allow_html=True)

        # ============================================================
        # EXIBIÇÃO - Custos e Quantitativos
        # ============================================================
        st.markdown("#### 💰 Estimativa de Custos")
        
        # Formatando valor para moeda BRL
        custo_formatado = f"R$ {custo_total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        html_custos = f"""
        <div class="stat-box">
            <div class="stat-row" style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 5px;">
                Distribuição Estimada (Regra 50-30-20):
            </div>
            <div class="stat-row">
                <span>3 Câmeras ({qtd_pontos_3cam} pts):</span>
                <span class="stat-value">{qtd_pontos_3cam * 3} cams</span>
            </div>
            <div class="stat-row">
                <span>2 Câmeras ({qtd_pontos_2cam} pts):</span>
                <span class="stat-value">{qtd_pontos_2cam * 2} cams</span>
            </div>
            <div class="stat-row">
                <span>1 Câmera ({qtd_pontos_1cam} pts):</span>
                <span class="stat-value">{qtd_pontos_1cam * 1} cams</span>
            </div>
            <div class="stat-row" style="border-top: 1px solid rgba(255,255,255,0.1); margin-top: 5px; padding-top: 5px;">
                <span><b>Total de Câmeras:</b></span>
                <span class="stat-value" style="color: #60a5fa;">{total_cameras_fisicas:,}</span>
            </div>
            <div class="stat-row" style="margin-top: 5px; font-size: 1rem;">
                <span><b>Custo Total:</b></span>
                <span class="stat-value" style="color: #4ade80;">{custo_formatado}</span>
            </div>
             <div class="stat-row" style="font-size: 0.7rem; color: #64748b;">
                Base: Custo unitário de {custo_unitario}
            </div>
        </div>
        """
        st.markdown(html_custos, unsafe_allow_html=True)

        # Download
        csv_data = gerar_csv_download(df_calc, df_sel)
        st.download_button("📥 Baixar CSV", csv_data, "ipe_cruzamentos.csv", "text/csv", use_container_width=True)
    else:
        st.info("👆 Carregue o Excel de cruzamentos na sidebar para iniciar.")

# ============================================================
# SEÇÃO ABAIXO DO MAPA - Equipamentos, Alagamentos e Sinistros
# ============================================================
st.markdown("---")

# Três colunas para as seções abaixo do mapa
col_equip, col_alag, col_sinist = st.columns(3)

# Coluna 1: Equipamentos (Dividido em LCT/SEG e COMERCIAL)
with col_equip:
    if not st.session_state.equipamentos.empty:
        # Preparação dos dados: filtrar por EIXO
        df_full = st.session_state.equipamentos
        
        # Normaliza para garantir que a comparação funcione (maiusculo e sem espaços)
        df_full['eixo_norm'] = df_full['eixo'].astype(str).str.strip().str.upper()
        
        # Separa os DataFrames
        df_lct_seg = df_full[df_full['eixo_norm'].isin(['LCT', 'SEG'])].copy()
        df_comercial = df_full[df_full['eixo_norm'] == 'COM'].copy()
        
        # Gera estatísticas para ambos ANTES de renderizar, para ter o Total Geral
        stats_main = gerar_estatisticas_equipamentos(df_lct_seg, nota_min_equip)
        stats_com = gerar_estatisticas_equipamentos(df_comercial, nota_min_equip)
        
        # Totais absolutos
        total_main = stats_main['total'] if stats_main else 0
        total_com = stats_com['total'] if stats_com else 0
        total_geral_filtros = total_main + total_com # Denominador comum

        # Porcentagens dos grupos em relação ao total geral
        pct_grupo_main = (total_main / total_geral_filtros * 100) if total_geral_filtros > 0 else 0
        pct_grupo_com = (total_com / total_geral_filtros * 100) if total_geral_filtros > 0 else 0
        
        # --- TABELA 1: LCT e SEG ---
        if total_main > 0:
            html_main = ""
            # Itens internos (SEM porcentagem, apenas quantidade absoluta)
            for nome, qtd in stats_main['tipos'].items():
                if nome and str(nome).strip() != "":
                    html_main += f'<div class="stat-row"><span>{nome}:</span><span class="stat-value">{qtd}</span></div>'
            
            st.markdown(f"#### 🏢 Equipamentos")
            st.markdown(f"""<div class="stat-box" style="margin-bottom: 1rem;">
                <div style="max-height: 150px; overflow-y: auto; padding-right: 5px;">{html_main}</div>
                <div class="stat-row" style="border-top: 1px solid rgba(148, 163, 184, 0.3); margin-top: 5px; padding-top: 5px;">
                    <span><b>Total (LCT/SEG):</b></span><span class="stat-value">{total_main} ({pct_grupo_main:.1f}%)</span>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"#### 🏢 Equipamentos")
            st.markdown("""<div class="stat-box"><div class="stat-row"><span>Nenhum equipamento LCT/SEG neste filtro.</span></div></div>""", unsafe_allow_html=True)

        # --- TABELA 2: COMERCIAL ---
        if total_com > 0:
            html_com = ""
            # Itens internos (SEM porcentagem, apenas quantidade absoluta)
            for nome, qtd in stats_com['tipos'].items():
                if nome and str(nome).strip() != "":
                    html_com += f'<div class="stat-row"><span>{nome}:</span><span class="stat-value">{qtd}</span></div>'
            
            st.markdown(f"#### 🏪 Comercial")
            st.markdown(f"""<div class="stat-box" style="margin-bottom: 1rem;">
                <div style="max-height: 150px; overflow-y: auto; padding-right: 5px;">{html_com}</div>
                <div class="stat-row" style="border-top: 1px solid rgba(148, 163, 184, 0.3); margin-top: 5px; padding-top: 5px;">
                    <span><b>Total Comercial:</b></span><span class="stat-value">{total_com} ({pct_grupo_com:.1f}%)</span>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"#### 🏪 Comercial")
            st.markdown("""<div class="stat-box"><div class="stat-row"><span>Nenhum equipamento Comercial neste filtro.</span></div></div>""", unsafe_allow_html=True)
            
        # Exibe o totalzão global para conferência (opcional, ajuda a validar o 100%)
        if total_geral_filtros > 0:
             st.markdown(f"""<div style="font-size: 0.75rem; color: #94a3b8; text-align: right; margin-top: -10px;">
                Total Geral Visualizado: {total_geral_filtros} (100%)
            </div>""", unsafe_allow_html=True)

    else:
        st.markdown("#### 🏢 Equipamentos")
        st.markdown("""<div class="stat-box">
            <div class="stat-row"><span>Carregue o arquivo de equipamentos.</span></div>
        </div>""", unsafe_allow_html=True)

# Coluna 2: Alagamentos
with col_alag:
    if not st.session_state.cruzamentos_calculados.empty:
        df_sel = st.session_state.ultimo_selecionados
        alagamentos_encontrados = verificar_alagamentos(df_sel)
        
        # Cálculo da porcentagem em relação ao TOTAL de alvos possíveis
        total_alvos_alagamento = len(ALAGAMENTOS_ALVO)
        qtd_alag = len(alagamentos_encontrados)
        pct_alag = (qtd_alag / total_alvos_alagamento * 100) if total_alvos_alagamento > 0 else 0
        
        html_alagamentos = ""
        if alagamentos_encontrados:
            for alag in alagamentos_encontrados:
                html_alagamentos += f'<div class="stat-row" style="justify-content: flex-start;"><span style="color:#fbbf24;">⚠️ {alag}</span></div>'
        else:
            html_alagamentos = '<div class="stat-row"><span>Nenhum ponto de alagamento nos filtros atuais.</span></div>'
        
        st.markdown("#### 🌊 Pontos de Alagamento")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                <span><b>Cobertura de Alagamentos:</b></span><span class="stat-value">{qtd_alag} ({pct_alag:.1f}%)</span>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                Calculado sobre {total_alvos_alagamento} pontos mapeados.
            </div>
            <div style="max-height: 200px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                {html_alagamentos}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🌊 Pontos de Alagamento")
        st.markdown("""<div class="stat-box">
            <div class="stat-row"><span>Carregue os dados para visualizar.</span></div>
        </div>""", unsafe_allow_html=True)

# Coluna 3: Sinistros
with col_sinist:
    if not st.session_state.cruzamentos_calculados.empty:
        df_sel = st.session_state.ultimo_selecionados
        sinistros_encontrados = verificar_sinistros(df_sel)
        
        # Cálculo da porcentagem em relação ao TOTAL de ruas alvo (usando set para garantir unicidade)
        total_ruas_sinistros = len(set([x.strip().upper() for x in RUAS_SINISTROS_ALVO]))
        qtd_sinist = len(sinistros_encontrados)
        pct_sinist = (qtd_sinist / total_ruas_sinistros * 100) if total_ruas_sinistros > 0 else 0
        
        html_sinistros = ""
        if sinistros_encontrados:
            for rua in sinistros_encontrados:
                html_sinistros += f'<div class="stat-row" style="justify-content: flex-start;"><span style="color:#f87171;">🚗 {rua}</span></div>'
        else:
            html_sinistros = '<div class="stat-row"><span>Nenhuma rua com histórico de sinistros.</span></div>'
        
        st.markdown("#### 🚗 Histórico de Sinistros")
        st.markdown(f"""<div class="stat-box">
            <div class="stat-row" style="border-bottom: 1px solid rgba(148, 163, 184, 0.3); padding-bottom: 5px; margin-bottom: 5px;">
                <span><b>Cobertura de Sinistros:</b></span><span class="stat-value">{qtd_sinist} ({pct_sinist:.1f}%)</span>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-bottom: 5px;">
                Calculado sobre {total_ruas_sinistros} ruas mapeadas.
            </div>
            <div style="max-height: 200px; overflow-y: auto; padding-right: 5px; font-size: 0.75rem;">
                {html_sinistros}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("#### 🚗 Histórico de Sinistros")
        st.markdown("""<div class="stat-box">
            <div class="stat-row"><span>Carregue os dados para visualizar.</span></div>
        </div>""", unsafe_allow_html=True)
