import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
import secrets
import hashlib
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import qrcode
from PIL import Image

#Configuração da Página
st.set_page_config(
    page_title="SESI Conecta", 
    page_icon="Sesisaude.png", 
    layout="wide"
)

# CSS Customizado para Visual Profissional - DARK MODE
st.markdown("""
<style>
    /* Dark Mode Global */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Animações suaves */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* Cards com hover effect */
    .stMarkdown div[style*="background"] {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Botões mais modernos */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    /* Tabs mais bonitas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 14px 28px;
        font-weight: 700;
        font-size: 1.05em;
        background-color: #1e2530;
        color: #8b92a8;
        transition: all 0.3s;
        border: 1px solid #2d3748;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #2d3748;
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
    }
    
    /* Progress bar customizada */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #11998e 50%, #38ef7d 100%);
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.4);
        height: 20px !important;
        border-radius: 10px;
    }
    
    /* Dataframes mais bonitos */
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        background-color: #1e2530;
    }
    
    /* Expanders com estilo */
    .streamlit-expanderHeader {
        border-radius: 12px;
        background: #1e2530;
        font-weight: 700;
        font-size: 1.1em;
        padding: 15px 20px;
        transition: all 0.3s;
        border: 1px solid #2d3748;
        color: #e0e0e0;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateX(5px);
    }
    
    /* Sidebar mais bonita */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #0e1117 100%);
        border-right: 1px solid #2d3748;
    }
    
    /* Inputs mais modernos */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #2d3748;
        background-color: #1e2530;
        color: #e0e0e0;
        transition: all 0.3s;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        background-color: #252d3d;
    }
    
    /* Text areas */
    .stTextArea textarea {
        background-color: #1e2530;
        color: #e0e0e0;
        border: 2px solid #2d3748;
        border-radius: 10px;
    }
    
    /* Select boxes */
    .stSelectbox [data-baseweb="select"] {
        background-color: #1e2530;
        border-radius: 10px;
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: #1e2530;
        border-radius: 12px;
        border: 2px dashed #2d3748;
    }
    
    /* Divider */
    hr {
        border-color: #2d3748;
    }
    
    /* Info boxes */
    .stAlert {
        background-color: #1e2530;
        border-radius: 12px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Banco de dados SQLite

def get_db_connection():
    """Conecta ao banco de dados SQLite"""
    conn = sqlite3.connect('sesi_conecta.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def criar_sessao_persistente(empresa_id):
    """Cria uma sessão persistente no banco de dados"""
    # Gerar token único
    token = secrets.token_urlsafe(32)
    expiracao = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Criar tabela de sessões se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            empresa_id TEXT NOT NULL,
            data_criacao TEXT NOT NULL,
            data_expiracao TEXT NOT NULL,
            FOREIGN KEY (empresa_id) REFERENCES empresas (empresa_id)
        )
    ''')
    
    # Inserir nova sessão
    cursor.execute('''
        INSERT INTO sessoes (token, empresa_id, data_criacao, data_expiracao)
        VALUES (?, ?, ?, ?)
    ''', (token, empresa_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), expiracao))
    
    conn.commit()
    conn.close()
    return token

def validar_sessao(token):
    """Valida token de sessão e retorna empresa_id se válido"""
    if not token:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se tabela existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessoes'")
    if not cursor.fetchone():
        conn.close()
        return None
    
    cursor.execute('''
        SELECT empresa_id, data_expiracao
        FROM sessoes
        WHERE token = ?
    ''', (token,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        empresa_id, expiracao = result[0], result[1]
        # Verificar se não expirou
        if datetime.now() < datetime.strptime(expiracao, '%Y-%m-%d %H:%M:%S'):
            return empresa_id
    
    return None

def buscar_empresa_por_login(usuario, senha):
    """Busca empresa no banco de dados por credenciais"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT empresa_id, nome, cnpj, contrato, vidas, setor
        FROM empresas
        WHERE usuario = ? AND senha = ?
    ''', (usuario, senha))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    return None

def buscar_empresa_por_id(empresa_id):
    """Busca dados da empresa pelo ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT empresa_id, nome, cnpj, contrato, vidas, setor
        FROM empresas
        WHERE empresa_id = ?
    ''', (empresa_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    return None

def buscar_status_contrato(empresa_id):
    """Busca status do contrato da empresa"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT status_atual, pgr_gerado
        FROM status_contratos
        WHERE empresa_id = ?
    ''', (empresa_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    return {'status_atual': 'Aguardando M1', 'pgr_gerado': 0}

def atualizar_status_contrato(empresa_id, novo_status, pgr_gerado=None):
    """Atualiza status do contrato"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if pgr_gerado is not None:
        cursor.execute('''
            UPDATE status_contratos
            SET status_atual = ?, pgr_gerado = ?, data_atualizacao = ?
            WHERE empresa_id = ?
        ''', (novo_status, pgr_gerado, data_atual, empresa_id))
    else:
        cursor.execute('''
            UPDATE status_contratos
            SET status_atual = ?, data_atualizacao = ?
            WHERE empresa_id = ?
        ''', (novo_status, data_atual, empresa_id))
    
    conn.commit()
    conn.close()

def buscar_historico(empresa_id):
    """Busca histórico de eventos da empresa"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data, evento, status
        FROM historico_processos
        WHERE empresa_id = ?
        ORDER BY id ASC
    ''', (empresa_id,))
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]

def adicionar_historico_db(empresa_id, evento, status):
    """Adiciona evento no histórico do banco"""
    conn = get_db_connection()
    cursor = conn.cursor()
    data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    cursor.execute('''
        INSERT INTO historico_processos (empresa_id, data, evento, status)
        VALUES (?, ?, ?, ?)
    ''', (empresa_id, data_hoje, evento, status))
    
    conn.commit()
    conn.close()

def salvar_agendamento(empresa_id, dados_agendamento):
    """Salva agendamento de exame no banco de dados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    exames_str = ','.join(dados_agendamento['exames'])
    
    cursor.execute('''
        INSERT INTO agendamentos_exames 
        (empresa_id, colaborador, cargo, cpf, tipo_exame, data_exame, horario, 
         local, exames_complementares, observacoes, status, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (empresa_id, dados_agendamento['colaborador'], dados_agendamento.get('cargo', ''),
          dados_agendamento.get('cpf', ''), dados_agendamento['tipo'], 
          dados_agendamento['data'], dados_agendamento['horario'],
          dados_agendamento['local'], exames_str, 
          dados_agendamento.get('observacoes', ''), 'Agendado', data_atual))
    
    conn.commit()
    conn.close()

def buscar_agendamentos(empresa_id):
    """Busca todos os agendamentos de uma empresa"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, colaborador, cargo, cpf, tipo_exame, data_exame, horario,
               local, exames_complementares, observacoes, status
        FROM agendamentos_exames
        WHERE empresa_id = ?
        ORDER BY data_exame, horario
    ''', (empresa_id,))
    results = cursor.fetchall()
    conn.close()
    
    agendamentos = []
    for row in results:
        agendamentos.append({
            'id': row[0],
            'colaborador': row[1],
            'cargo': row[2],
            'cpf': row[3],
            'tipo': row[4],
            'data': row[5],
            'horario': row[6],
            'local': row[7],
            'exames': row[8].split(',') if row[8] else [],
            'observacoes': row[9],
            'status': row[10]
        })
    
    return agendamentos

def cancelar_agendamento_db(agendamento_id):
    """Cancela um agendamento no banco de dados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM agendamentos_exames
        WHERE id = ?
    ''', (agendamento_id,))
    conn.commit()
    conn.close()

def init_session():
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False
    
    if 'empresa_logada' not in st.session_state:
        st.session_state['empresa_logada'] = None
    
    # Carregar dados do banco se empresa está logada
    if st.session_state['autenticado'] and st.session_state['empresa_logada']:
        # Carregar status do contrato
        if 'status_contrato' not in st.session_state:
            status_db = buscar_status_contrato(st.session_state['empresa_logada'])
            st.session_state['status_contrato'] = status_db['status_atual']
            st.session_state['pgr_gerado'] = bool(status_db['pgr_gerado'])
        
        # Carregar histórico
        if 'historico' not in st.session_state:
            st.session_state['historico'] = buscar_historico(st.session_state['empresa_logada'])
    else:
        if 'status_contrato' not in st.session_state:
            st.session_state['status_contrato'] = 'Aguardando M1'
        # Estados: 'Aguardando M1', 'Em Análise (Segurança)', 'PGR Validado', 'PCMSO Em Elaboração', 'Concluído'
        st.session_state['status_contrato'] = 'Aguardando M1' 
    
    if 'dados_m1' not in st.session_state:
        st.session_state['dados_m1'] = None

    if 'historico' not in st.session_state:
        st.session_state['historico'] = [
            {"data": "28/11/2025", "evento": "Contrato Assinado", "status": "ok"}
        ]
    
    if 'timeline_evolucao' not in st.session_state:
        # Dados para o gráfico de evolução
        st.session_state['timeline_evolucao'] = [
            {"data": "2025-11-28", "fase": "Contrato", "progresso": 10}
        ]
    
    if 'pgr_gerado' not in st.session_state:
        st.session_state['pgr_gerado'] = False
    
    if 'pcmso_gerado' not in st.session_state:
        st.session_state['pcmso_gerado'] = False
    
    if 'balloons_mostrados' not in st.session_state:
        st.session_state['balloons_mostrados'] = False

# Lógica de negócio

def processar_m1(uploaded_file):
    """
    Validação Poka-Yoke da planilha M1.
    Verifica presença de colunas obrigatórias antes de processar.
    """
    try:
        # Tenta ler Excel ou CSV
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Colunas obrigatórias baseadas na necessidade do eSocial/SESI
        colunas_obrigatorias = ['Nome Completo', 'CPF', 'Cargo', 'Data Nascimento', 'Descrição da Atividade']
        
        # Verifica colunas ausentes
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            return False, f"❌ Erro de Validação: Sua planilha não contém as colunas obrigatórias: {colunas_faltantes}. Por favor, ajuste e reenvie."
        
        # Simula processamento inteligente (Normalização)
        return True, df
        
    except Exception as e:
        return False, f"Erro ao ler arquivo: {str(e)}"

def avancar_fluxo():
    """Avança o status do processo entre as etapas do fluxo"""
    status_atual = st.session_state['status_contrato']
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    if status_atual == 'Aguardando M1':
        st.session_state['status_contrato'] = 'Aguardando Visita SESI'
        adicionar_historico("M1 Recebida e Validada", "ok")
        st.session_state['timeline_evolucao'].append(
            {"data": hoje, "fase": "M1 Validada", "progresso": 20}
        )
        atualizar_status_contrato(st.session_state['empresa_logada'], 'Aguardando Visita SESI')
    
    elif status_atual == 'Aguardando Visita SESI':
        st.session_state['status_contrato'] = 'Em Análise (Segurança)'
        adicionar_historico("Visita SESI agendada e realizada", "ok")
        st.session_state['timeline_evolucao'].append(
            {"data": hoje, "fase": "Visita Realizada", "progresso": 35}
        )
        atualizar_status_contrato(st.session_state['empresa_logada'], 'Em Análise (Segurança)')
        
    elif status_atual == 'Em Análise (Segurança)':
        st.session_state['status_contrato'] = 'PGR Aguardando Validação'
        st.session_state['pgr_gerado'] = True
        adicionar_historico("PGR Elaborado - Aguardando validação do cliente", "info")
        st.session_state['timeline_evolucao'].append(
            {"data": hoje, "fase": "PGR Elaborado", "progresso": 50}
        )
        atualizar_status_contrato(st.session_state['empresa_logada'], 'PGR Aguardando Validação', pgr_gerado=1)

    elif status_atual == 'PGR Aguardando Validação':
        # Este estado será avançado manualmente pelos botões de aprovação
        pass
    
    elif status_atual == 'PGR Validado':
        st.session_state['status_contrato'] = 'PCMSO Em Elaboração'
        adicionar_historico("PGR Validado - Iniciando PCMSO", "ok")
        st.session_state['timeline_evolucao'].append(
            {"data": hoje, "fase": "PCMSO Iniciado", "progresso": 70}
        )
        atualizar_status_contrato(st.session_state['empresa_logada'], 'PCMSO Em Elaboração')

    elif status_atual == 'PCMSO Em Elaboração':
        st.session_state['status_contrato'] = 'PCMSO Aguardando Validação'
        st.session_state['pcmso_gerado'] = True
        adicionar_historico("PCMSO Elaborado - Aguardando validação do cliente", "info")
        st.session_state['timeline_evolucao'].append(
            {"data": hoje, "fase": "PCMSO Elaborado", "progresso": 85}
        )
        atualizar_status_contrato(st.session_state['empresa_logada'], 'PCMSO Aguardando Validação')
    
    elif status_atual == 'PCMSO Aguardando Validação':
        # Este estado será avançado manualmente pelos botões de aprovação
        pass
    
    elif status_atual == 'PCMSO Validado':
        st.session_state['status_contrato'] = 'Concluído'
        adicionar_historico("PCMSO Validado. Exames disponíveis.", "ok")
        st.session_state['timeline_evolucao'].append(
            {"data": hoje, "fase": "Concluído", "progresso": 100}
        )
        atualizar_status_contrato(st.session_state['empresa_logada'], 'Concluído')

def adicionar_historico(evento, tipo):
    data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
    # Adicionar no session_state
    st.session_state['historico'].append({"data": data_hoje, "evento": evento, "status": tipo})
    # Salvar no banco de dados
    if st.session_state['empresa_logada']:
        adicionar_historico_db(st.session_state['empresa_logada'], evento, tipo)

def validar_pgr():
    """Aprova o PGR elaborado"""
    st.session_state['status_contrato'] = 'PGR Validado'
    adicionar_historico("✅ PGR aprovado pelo cliente", "ok")
    hoje = datetime.now().strftime("%Y-%m-%d")
    st.session_state['timeline_evolucao'].append(
        {"data": hoje, "fase": "PGR Validado", "progresso": 60}
    )
    atualizar_status_contrato(st.session_state['empresa_logada'], 'PGR Validado')

def rejeitar_pgr(motivo):
    """Rejeita o PGR e solicita reelaboração"""
    st.session_state['status_contrato'] = 'Em Análise (Segurança)'
    adicionar_historico(f"❌ PGR rejeitado - Motivo: {motivo}", "warning")
    adicionar_historico("🔄 PGR em reelaboração pelo SESI", "info")
    atualizar_status_contrato(st.session_state['empresa_logada'], 'Em Análise (Segurança)')

def validar_pcmso():
    """Aprova o PCMSO elaborado"""
    st.session_state['status_contrato'] = 'PCMSO Validado'
    adicionar_historico("✅ PCMSO aprovado pelo cliente", "ok")
    hoje = datetime.now().strftime("%Y-%m-%d")
    st.session_state['timeline_evolucao'].append(
        {"data": hoje, "fase": "PCMSO Validado", "progresso": 95}
    )
    atualizar_status_contrato(st.session_state['empresa_logada'], 'PCMSO Validado')
    # Avançar para concluído
    avancar_fluxo()

def rejeitar_pcmso(motivo):
    """Rejeita o PCMSO e solicita reelaboração"""
    st.session_state['status_contrato'] = 'PCMSO Em Elaboração'
    adicionar_historico(f"❌ PCMSO rejeitado - Motivo: {motivo}", "warning")
    adicionar_historico("🔄 PCMSO em reelaboração pelo SESI", "info")
    atualizar_status_contrato(st.session_state['empresa_logada'], 'PCMSO Em Elaboração')

def fazer_login(usuario, senha):
    """Valida credenciais no banco de dados e cria sessão persistente"""
    empresa_dados = buscar_empresa_por_login(usuario, senha)
    if empresa_dados:
        # Criar token de sessão persistente
        token = criar_sessao_persistente(empresa_dados['empresa_id'])
        return empresa_dados['empresa_id'], empresa_dados, token
    return None, None, None

def fazer_logout():
    """Encerra sessão e limpa dados temporários"""
    st.session_state['autenticado'] = False
    st.session_state['empresa_logada'] = None
    st.session_state['status_contrato'] = 'Aguardando M1'
    st.session_state['dados_m1'] = None
    st.session_state['historico'] = [{"data": "28/11/2025", "evento": "Contrato Assinado", "status": "ok"}]
    st.session_state['timeline_evolucao'] = [{"data": "2025-11-28", "fase": "Contrato", "progresso": 10}]
    st.session_state['pgr_gerado'] = False
    # Limpar token da URL
    st.query_params.clear()

def gerar_pdf_pgr():
    """Gera um PDF profissional do PGR usando ReportLab"""
    buffer = BytesIO()
    
    # Configuração do documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo customizado para título
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitulo_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal
    texto_style = styles['Normal']
    texto_style.fontSize = 10
    texto_style.leading = 14
    
    # Conteúdo do PDF
    elementos = []
    
    # Título principal
    elementos.append(Paragraph("PROGRAMA DE GERENCIAMENTO DE RISCOS - PGR", titulo_style))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Informações da empresa
    empresa_atual = buscar_empresa_por_id(st.session_state['empresa_logada'])
    data_elaboracao = datetime.now()
    data_validade = data_elaboracao + timedelta(days=730)
    
    info_empresa = [
        ['Empresa:', empresa_atual['nome']],
        ['CNPJ:', empresa_atual['cnpj']],
        ['Contrato:', empresa_atual['contrato']],
        ['Setor:', empresa_atual['setor']],
        ['Data de Elaboração:', data_elaboracao.strftime('%d/%m/%Y')],
        ['Validade:', data_validade.strftime('%d/%m/%Y') + ' (24 meses)']
    ]
    
    tabela_info = Table(info_empresa, colWidths=[5*cm, 12*cm])
    tabela_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e0e0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elementos.append(tabela_info)
    elementos.append(Spacer(1, 1*cm))
    
    # Seção 1: Identificação dos Perigos
    elementos.append(Paragraph("1. IDENTIFICAÇÃO DOS PERIGOS", subtitulo_style))
    
    perigos_texto = """
    <b>Ruído ocupacional (Setor: Produção)</b><br/>
    - Nível médio: 85 dB(A)<br/>
    - Exposição: 8 horas/dia<br/><br/>
    
    <b>Riscos mecânicos (Máquinas e equipamentos)</b><br/>
    - Prensas, serras, tornos<br/>
    - Pontos de prensagem e corte<br/><br/>
    
    <b>Agentes químicos (Soldagem e pintura)</b><br/>
    - Fumos metálicos<br/>
    - Solventes e tintas<br/><br/>
    
    <b>Ergonômicos (Levantamento de cargas)</b><br/>
    - Movimentação manual de cargas até 25kg<br/>
    - Posturas inadequadas
    """
    elementos.append(Paragraph(perigos_texto, texto_style))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Seção 2: Avaliação de Riscos
    elementos.append(Paragraph("2. AVALIAÇÃO DE RISCOS", subtitulo_style))
    
    dados_riscos = [
        ['Risco', 'Probabilidade', 'Severidade', 'Nível'],
        ['Ruído', 'Alta', 'Média', 'MÉDIO'],
        ['Mecânico', 'Média', 'Alta', 'ALTO'],
        ['Químico', 'Média', 'Média', 'MÉDIO'],
        ['Ergonômico', 'Alta', 'Baixa', 'BAIXO']
    ]
    
    tabela_riscos = Table(dados_riscos, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    tabela_riscos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    elementos.append(tabela_riscos)
    elementos.append(Spacer(1, 0.5*cm))
    
    # Seção 3: Medidas de Controle
    elementos.append(Paragraph("3. MEDIDAS DE CONTROLE RECOMENDADAS", subtitulo_style))
    
    medidas_texto = """
    <b>→ Fornecimento de EPIs:</b><br/>
    • Protetor auricular tipo concha<br/>
    • Luvas de segurança específicas<br/>
    • Óculos de proteção<br/>
    • Máscaras respiratórias<br/><br/>
    
    <b>→ Treinamentos obrigatórios:</b><br/>
    • NR-12 (Segurança em máquinas)<br/>
    • NR-06 (Uso correto de EPIs)<br/>
    • NR-17 (Ergonomia)<br/><br/>
    
    <b>→ Adequações técnicas:</b><br/>
    • Manutenção preventiva de equipamentos<br/>
    • Enclausuramento de fontes de ruído<br/>
    • Ventilação local exaustora<br/>
    • Ajuste ergonômico de estações de trabalho
    """
    elementos.append(Paragraph(medidas_texto, texto_style))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Seção 4: Cronograma
    elementos.append(Paragraph("4. CRONOGRAMA DE IMPLEMENTAÇÃO", subtitulo_style))
    
    cronograma_texto = """
    <b>Mês 1-2:</b> Aquisição e distribuição de EPIs<br/>
    <b>Mês 2-3:</b> Realização de treinamentos<br/>
    <b>Mês 3-6:</b> Adequações de engenharia<br/>
    <b>Contínuo:</b> Monitoramento e avaliações periódicas
    """
    elementos.append(Paragraph(cronograma_texto, texto_style))
    elementos.append(Spacer(1, 1*cm))
    
    # Gerar QR Code para dashboard público
    empresa_atual = buscar_empresa_por_id(st.session_state['empresa_logada'])
    # Usar Network URL para funcionar em celulares na mesma rede
    import socket
    hostname = socket.gethostbyname(socket.gethostname())
    dashboard_url = f"http://{hostname}:8501/?empresa={empresa_atual['empresa_id']}&view=dashboard"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(dashboard_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Salvar QR Code em buffer
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Adicionar QR Code ao PDF
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("📱 Acesse o Dashboard do Programa:", subtitulo_style))
    qr_image = RLImage(qr_buffer, width=4*cm, height=4*cm)
    elementos.append(qr_image)
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("<i>Escaneie o QR Code para acompanhar métricas e agendamentos em tempo real</i>", texto_style))
    
    # Rodapé
    elementos.append(Spacer(1, 0.5*cm))
    rodape_texto = """
    ___________________________________________<br/>
    <b>Eng. de Segurança do Trabalho SESI</b><br/>
    CREA 12345/SP<br/><br/>
    <i>Este documento foi gerado automaticamente pelo sistema SESI Conecta.</i>
    """
    elementos.append(Paragraph(rodape_texto, texto_style))
    
    # Gera o PDF
    doc.build(elementos)
    buffer.seek(0)
    
    return buffer.getvalue()

def gerar_pdf_pcmso():
    """Gera PDF do PCMSO conforme NR-07"""
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    texto_style = styles['Normal']
    texto_style.fontSize = 10
    texto_style.leading = 14
    
    elementos = []
    
    # Título
    elementos.append(Paragraph("PROGRAMA DE CONTROLE MÉDICO DE SAÚDE OCUPACIONAL - PCMSO", titulo_style))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Informações da empresa
    empresa_atual = buscar_empresa_por_id(st.session_state['empresa_logada'])
    data_elaboracao = datetime.now()
    data_validade = data_elaboracao + timedelta(days=365)
    
    info_empresa = [
        ['Empresa:', empresa_atual['nome']],
        ['CNPJ:', empresa_atual['cnpj']],
        ['Contrato:', empresa_atual['contrato']],
        ['Setor:', empresa_atual['setor']],
        ['Data de Elaboração:', data_elaboracao.strftime('%d/%m/%Y')],
        ['Vigência:', data_validade.strftime('%d/%m/%Y') + ' (12 meses)']
    ]
    
    tabela_info = Table(info_empresa, colWidths=[5*cm, 12*cm])
    tabela_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f2f6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elementos.append(tabela_info)
    elementos.append(Spacer(1, 1*cm))
    
    # Seção 1: Objetivo
    elementos.append(Paragraph("1. OBJETIVO", subtitulo_style))
    
    objetivo_texto = """
    Este programa tem como objetivo a promoção e preservação da saúde dos trabalhadores,
    através de exames médicos ocupacionais, de acordo com a NR-07 do Ministério do Trabalho
    e Emprego, estabelecendo diretrizes para monitoramento da exposição aos riscos
    identificados no Programa de Gerenciamento de Riscos (PGR).
    """
    elementos.append(Paragraph(objetivo_texto, texto_style))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Seção 2: Responsabilidades
    elementos.append(Paragraph("2. RESPONSABILIDADES", subtitulo_style))
    
    resp_texto = """
    Empregador: Custear todos os procedimentos relacionados ao PCMSO, garantir
    execução conforme estabelecido, indicar médico coordenador.<br/><br/>
    
    Médico Coordenador: Realizar exames admissionais, periódicos, de retorno ao trabalho,
    de mudança de função e demissionais. Emitir ASO (Atestado de Saúde Ocupacional).<br/><br/>
    
    Trabalhadores: Colaborar e participar da implantação e execução do PCMSO.
    """
    elementos.append(Paragraph(resp_texto, texto_style))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Seção 3: Quadro de Exames
    elementos.append(Paragraph("3. EXAMES MÉDICOS OCUPACIONAIS", subtitulo_style))
    
    dados_exames = [
        ['Tipo de Exame', 'Periodicidade', 'Exames Complementares'],
        ['Admissional', 'Antes da admissão', 'Hemograma, Audiometria, Acuidade Visual'],
        ['Periódico', 'Anual', 'Hemograma, Audiometria, Espirometria'],
        ['Retorno ao Trabalho', 'Após 30 dias afastado', 'Conforme avaliação médica'],
        ['Mudança de Função', 'Antes da mudança', 'Conforme novo risco ocupacional'],
        ['Demissional', 'Até a data da homologação', 'Audiometria, Acuidade Visual']
    ]
    
    tabela_exames = Table(dados_exames, colWidths=[5*cm, 4.5*cm, 6.5*cm])
    tabela_exames.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elementos.append(tabela_exames)
    elementos.append(Spacer(1, 0.5*cm))
    
    # Seção 4: Riscos Ocupacionais
    elementos.append(Paragraph("4. PRINCIPAIS RISCOS OCUPACIONAIS MONITORADOS", subtitulo_style))
    
    riscos_texto = """
    Ruído: Monitoramento através de audiometria tonal limiar anual<br/>
    Agentes Químicos: Avaliação clínica e exames laboratoriais específicos<br/>
    Ergonômicos: Avaliação postural e osteomuscular<br/>
    Mecânicos: Avaliação de integridade física e capacidade laboral
    """
    elementos.append(Paragraph(riscos_texto, texto_style))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Seção 5: Critérios de Aptidão
    elementos.append(Paragraph("5. CRITÉRIOS DE INTERPRETAÇÃO E CONDUTA", subtitulo_style))
    
    criterios_texto = """
    Apto: Trabalhador está em condições de exercer suas funções<br/>
    Apto com restrições: Trabalhador pode exercer função com limitações especificadas no ASO<br/>
    Inapto temporário: Trabalhador temporariamente impedido de exercer função<br/>
    Inapto: Trabalhador impedido definitivamente de exercer a função
    """
    elementos.append(Paragraph(criterios_texto, texto_style))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Seção 6: Registros
    elementos.append(Paragraph("6. REGISTROS E DOCUMENTAÇÃO", subtitulo_style))
    
    registros_texto = """
    Todos os exames e ASO serão arquivados por no mínimo 20 anos após o desligamento
    do trabalhador. Os dados serão mantidos em sigilo conforme determina a legislação
    vigente e o Código de Ética Médica.
    """
    elementos.append(Paragraph(registros_texto, texto_style))
    elementos.append(Spacer(1, 1*cm))
    
    # Gerar QR Code para dashboard público
    import socket
    hostname = socket.gethostbyname(socket.gethostname())
    empresa_atual = buscar_empresa_por_id(st.session_state['empresa_logada'])
    dashboard_url = f"http://{hostname}:8501/?empresa={empresa_atual['empresa_id']}&view=dashboard"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(dashboard_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Salvar QR Code em buffer
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Adicionar QR Code ao PDF
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("📱 Acesse o Dashboard do Programa:", subtitulo_style))
    qr_image = RLImage(qr_buffer, width=4*cm, height=4*cm)
    elementos.append(qr_image)
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("<i>Escaneie o QR Code para acompanhar exames agendados e métricas de saúde ocupacional</i>", texto_style))
    
    # Rodapé
    elementos.append(Spacer(1, 0.5*cm))
    rodape_texto = """
    ___________________________________________<br/>
    Médico Coordenador do PCMSO<br/>
    Dr. Roberto Silva Santos<br/>
    CRM 123456/SP<br/><br/>
    <i>Documento gerado pelo sistema SESI Conecta em conformidade com a NR-07.</i>
    """
    elementos.append(Paragraph(rodape_texto, texto_style))
    
    doc.build(elementos)
    buffer.seek(0)
    
    return buffer.getvalue()

# Interface de usuário

init_session()

# ============================================
# DASHBOARD PÚBLICO (via QR Code)
# ============================================
# Verificar se há parâmetros de URL para dashboard público
query_params = st.query_params
if "empresa" in query_params and "view" in query_params:
    empresa_id = query_params["empresa"]
    
    # Buscar dados da empresa
    empresa_dados = buscar_empresa_por_id(empresa_id)
    status_dict = buscar_status_contrato(empresa_id)
    status_atual = status_dict['status_atual'] if status_dict else 'Aguardando M1'
    
    if empresa_dados:
        # Dashboard público (sem autenticação)
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {display: none;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Animações suaves */
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .animated {
                animation: fadeInUp 0.6s ease-out;
            }
            
            /* Remover padding padrão */
            .block-container {
                padding-top: 2rem !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Header minimalista
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 50px; animation: fadeInUp 0.8s ease-out;">
            <img src="app/static/Sesisaude.png" style="width: 100px; border-radius: 50%; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(102,126,234,0.3);" />
            <h1 style="color: #e0e0e0; font-size: 2em; margin: 0; font-weight: 300;">
                {empresa_dados['nome']}
            </h1>
            <div style="display: inline-block; margin-top: 15px; padding: 8px 20px; 
                        background: #1e2530; border-radius: 20px; font-size: 0.9em; color: #8b92a8; border: 1px solid #2d3748;">
                📍 {status_atual}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Métricas de progresso
        mapa_progresso = {
            'Aguardando M1': 10,
            'Aguardando Visita SESI': 20,
            'Em Análise (Segurança)': 35,
            'PGR Aguardando Validação': 50,
            'PGR Validado': 60,
            'PCMSO Em Elaboração': 70,
            'PCMSO Aguardando Validação': 85,
            'PCMSO Validado': 95,
            'Concluído': 100
        }
        progresso = mapa_progresso.get(status_atual, 10)
        
        # Cálculos de ROI
        total_funcionarios = empresa_dados['vidas']
        custo_acidente_medio = 50000
        taxa_prevencao = 0.75
        acidentes_estimados_ano = max(1, total_funcionarios // 100)
        economia_acidentes = acidentes_estimados_ano * custo_acidente_medio * taxa_prevencao
        
        multa_nr_media = 25000
        conformidade_score = progresso
        economia_multas = multa_nr_media * (conformidade_score / 100)
        roi_total = economia_acidentes + economia_multas
        
        # Cards de métricas - Design clean e minimalista
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e2530 0%, #252d3d 100%); padding: 25px; border-radius: 12px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.4); text-align: center;
                        border-top: 4px solid #3498db; border: 1px solid #2d3748;">
                <div style="font-size: 2.5em; margin-bottom: 10px;">💰</div>
                <div style="font-size: 2em; font-weight: 700; color: #e0e0e0; margin-bottom: 5px;">
                    R$ {roi_total:,.0f}
                </div>
                <div style="color: #8b92a8; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px;">
                    Economia Total
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e2530 0%, #252d3d 100%); padding: 25px; border-radius: 12px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.4); text-align: center;
                        border-top: 4px solid #2ecc71; border: 1px solid #2d3748;">
                <div style="font-size: 2.5em; margin-bottom: 10px;">🛡️</div>
                <div style="font-size: 2em; font-weight: 700; color: #e0e0e0; margin-bottom: 5px;">
                    R$ {economia_acidentes:,.0f}
                </div>
                <div style="color: #8b92a8; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px;">
                    Prevenção
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e2530 0%, #252d3d 100%); padding: 25px; border-radius: 12px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.4); text-align: center;
                        border-top: 4px solid #e74c3c; border: 1px solid #2d3748;">
                <div style="font-size: 2.5em; margin-bottom: 10px;">🚫</div>
                <div style="font-size: 2em; font-weight: 700; color: #e0e0e0; margin-bottom: 5px;">
                    R$ {economia_multas:,.0f}
                </div>
                <div style="color: #8b92a8; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px;">
                    Multas Evitadas
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e2530 0%, #252d3d 100%); padding: 25px; border-radius: 12px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.4); text-align: center;
                        border-top: 4px solid #9b59b6; border: 1px solid #2d3748;">
                <div style="font-size: 2.5em; margin-bottom: 10px;">✓</div>
                <div style="font-size: 2em; font-weight: 700; color: #e0e0e0; margin-bottom: 5px;">
                    {conformidade_score}%
                </div>
                <div style="color: #8b92a8; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px;">
                    Conformidade
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Progresso do programa - Design clean
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="color: #e0e0e0; font-weight: 300; font-size: 1.3em;">Progresso do Programa</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.progress(progresso / 100)
        st.markdown(f"""
        <div style="text-align: center; margin-top: 10px;">
            <span style="font-size: 1.5em; font-weight: 700; color: #e0e0e0;">{progresso}%</span>
            <span style="color: #8b92a8; margin-left: 10px;">completo</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Agendamentos de exames - Design clean
        st.markdown("""
        <div style="text-align: center; margin: 50px 0 25px 0;">
            <h3 style="color: #e0e0e0; font-weight: 300; font-size: 1.3em;">Exames Agendados</h3>
        </div>
        """, unsafe_allow_html=True)
        
        agendamentos = buscar_agendamentos(empresa_id)
        
        if agendamentos:
            df_agendamentos = pd.DataFrame(agendamentos)
            df_agendamentos = df_agendamentos[['colaborador', 'tipo_exame', 'data_exame', 'horario', 'status']]
            
            # Mapear status para emoji
            status_map = {
                'Agendado': '🟢 Agendado',
                'Concluído': '✅ Concluído',
                'Cancelado': '❌ Cancelado'
            }
            df_agendamentos['status'] = df_agendamentos['status'].map(status_map)
            
            st.dataframe(df_agendamentos, use_container_width=True, hide_index=True)
        else:
            st.markdown("""
            <div style="background: #1e2530; padding: 40px; border-radius: 12px; text-align: center;
                        border: 1px solid #2d3748; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
                <div style="font-size: 2.5em; margin-bottom: 15px; opacity: 0.5;">📅</div>
                <div style="color: #8b92a8; font-size: 1em;">Nenhum exame agendado</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Informações de contato - Design clean
        st.markdown("""
        <div style="text-align: center; margin-top: 60px; padding: 30px; 
                    background: #1e2530; border-radius: 12px; border: 1px solid #2d3748; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
            <div style="color: #e0e0e0; font-size: 1.1em; font-weight: 600; margin-bottom: 10px;">
                SESI Saúde Ocupacional
            </div>
            <div style="color: #8b92a8; font-size: 0.95em;">
                📞 0800-123-4567 • 📧 saudeocupacional@sesi.org.br
            </div>
            <div style="color: #6b7280; font-size: 0.85em; margin-top: 15px; font-style: italic;">
                Dashboard acessível via QR Code
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.stop()  # Impede que continue para a tela de login

# ============================================
# TELA DE LOGIN
# ============================================

# Verificar se há token de sessão nos query params
query_params = st.query_params
if "session" in query_params and not st.session_state['autenticado']:
    token = query_params["session"]
    empresa_id = validar_sessao(token)
    if empresa_id:
        st.session_state['autenticado'] = True
        st.session_state['empresa_logada'] = empresa_id
        st.rerun()

if not st.session_state['autenticado']:
    # Esconde sidebar e menu
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
    
    # Layout centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Logo SESI Saúde oficial centralizada
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            st.markdown("""
            <style>
            .logo-circle {
                border-radius: 50%;
                display: block;
                margin: 0 auto;
            }
            </style>
            """, unsafe_allow_html=True)
            st.image("Sesisaude.png", width=250)
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            <h2 style="color: #1f77b4; font-size: 2em;">CONECTA</h2>
            <p style="color: #8b92a8; font-size: 1.2em; margin-top: 10px;">Plataforma de Gestão de Saúde e Segurança do Trabalho</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Seção de Casos de Sucesso - Design mais limpo
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <h3 style="color: #667eea; font-size: 1.5em; margin-bottom: 5px;">✨ Resultados Comprovados</h3>
            <p style="color: #8b92a8; font-size: 0.95em;">Empresas que transformaram segurança em economia real</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Cards de validação das 3 empresas - mais compactos
        col_case1, col_case2, col_case3 = st.columns(3)
        
        with col_case1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                        padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 12px;">
                    <span style="font-size: 2.5em;">🏭</span>
                    <h4 style="color: white; margin: 8px 0 3px 0; font-size: 1.1em;">MetalCorp</h4>
                    <p style="color: rgba(255,255,255,0.9); font-size: 0.8em; margin: 0;">Metalúrgica • 150 funcionários</p>
                </div>
                <div style="background: rgba(255,255,255,0.95); padding: 15px; border-radius: 8px;">
                    <p style="color: #11998e; font-weight: bold; font-size: 1.2em; margin: 0 0 10px 0; text-align: center;">
                        R$ 81.250/ano
                    </p>
                    <p style="color: #1a1f2e; font-size: 0.85em; line-height: 1.4; margin: 0; text-align: center;">
                        "Reduzimos acidentes em 68% nos primeiros 8 meses"
                    </p>
                    <p style="color: #6b7280; font-size: 0.75em; margin: 10px 0 0 0; text-align: center; font-style: italic;">
                        - Roberto Santos
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_case2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 12px;">
                    <span style="font-size: 2.5em;">💻</span>
                    <h4 style="color: white; margin: 8px 0 3px 0; font-size: 1.1em;">TechBrasil</h4>
                    <p style="color: rgba(255,255,255,0.9); font-size: 0.8em; margin: 0;">Tecnologia • 80 funcionários</p>
                </div>
                <div style="background: rgba(255,255,255,0.95); padding: 15px; border-radius: 8px;">
                    <p style="color: #f093fb; font-weight: bold; font-size: 1.2em; margin: 0 0 10px 0; text-align: center;">
                        R$ 55.000/ano
                    </p>
                    <p style="color: #1a1f2e; font-size: 0.85em; line-height: 1.4; margin: 0; text-align: center;">
                        "Métricas reais que justificam investimentos ao board"
                    </p>
                    <p style="color: #6b7280; font-size: 0.75em; margin: 10px 0 0 0; text-align: center; font-style: italic;">
                        - Ana Paula Costa
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_case3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                        padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 12px;">
                    <span style="font-size: 2.5em;">🍕</span>
                    <h4 style="color: white; margin: 8px 0 3px 0; font-size: 1.1em;">AlimentosBR</h4>
                    <p style="color: rgba(255,255,255,0.9); font-size: 0.8em; margin: 0;">Alimentos • 200 funcionários</p>
                </div>
                <div style="background: rgba(255,255,255,0.95); padding: 15px; border-radius: 8px;">
                    <p style="color: #fa709a; font-weight: bold; font-size: 1.2em; margin: 0 0 10px 0; text-align: center;">
                        R$ 100.000/ano
                    </p>
                    <p style="color: #1a1f2e; font-size: 0.85em; line-height: 1.4; margin: 0; text-align: center;">
                        "100% de conformidade e zero acidentes graves"
                    </p>
                    <p style="color: #6b7280; font-size: 0.75em; margin: 10px 0 0 0; text-align: center; font-style: italic;">
                        - Carlos Mendes
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Card de login
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
            <h2 style="color: white; text-align: center; margin-bottom: 20px;">🔑 Área da Indústria</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            usuario = st.text_input("👤 Usuário", placeholder="Seu nome de usuário")
            senha = st.text_input("🔒 Senha", type="password", placeholder="Sua senha")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_btn = st.form_submit_button("➡️ Entrar", use_container_width=True)
            with col_btn2:
                demo_btn = st.form_submit_button("🎯 Modo Demo", use_container_width=True)
        
        if login_btn and usuario and senha:
            empresa_id, dados_empresa, token = fazer_login(usuario, senha)
            if empresa_id:
                st.session_state['autenticado'] = True
                st.session_state['empresa_logada'] = empresa_id
                st.success(f"Bem-vindo(a), {dados_empresa['nome']}!")
                # Redirecionar com token de sessão na URL
                import socket
                hostname = socket.gethostbyname(socket.gethostname())
                st.markdown(f"**Redirecionando...**")
                st.markdown(f"Salve este link para acessar de qualquer dispositivo:")
                st.code(f"http://{hostname}:8501/?session={token}", language="text")
                time.sleep(2)
                st.query_params["session"] = token
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos!")
        
        if demo_btn:
            # Criar token para demo também
            token_demo = criar_sessao_persistente('metalurgica')
            st.session_state['autenticado'] = True
            st.session_state['empresa_logada'] = 'metalurgica'
            st.query_params["session"] = token_demo
            st.rerun()
     
    st.stop()  # Para a execução aqui se não estiver autenticado

# ============================================
# INTERFACE PRINCIPAL (APÓS LOGIN)
# ============================================

# Busca dados da empresa logada
empresa_atual = buscar_empresa_por_id(st.session_state['empresa_logada'])

# Carregar status do banco de dados (persistente)
status_dict = buscar_status_contrato(st.session_state['empresa_logada'])
if status_dict:
    st.session_state['status_contrato'] = status_dict['status_atual']
    st.session_state['pgr_gerado'] = status_dict['pgr_gerado'] == 1
    st.session_state['pcmso_gerado'] = status_dict.get('pcmso_gerado', 0) == 1

# Carregar histórico do banco de dados
historico_db = buscar_historico(st.session_state['empresa_logada'])
if historico_db:
    st.session_state['historico'] = historico_db

# Barra Lateral (Simula o usuário logado)
with st.sidebar:
    # Logo SESI Saúde oficial
    st.markdown("""
    <style>
    .stImage img {
        border-radius: 50%;
    }
    </style>
    """, unsafe_allow_html=True)
    st.image("Sesisaude.png", width=180)
    
    st.title("Área da Indústria")
    
    # Dados da empresa logada
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
        <p style="margin: 0; font-size: 0.9em; color: #666;">Empresa Logada:</p>
        <p style="margin: 5px 0; font-weight: bold; color: #1f77b4;">{empresa_atual['nome']}</p>
        <p style="margin: 0; font-size: 0.85em; color: #666;">CNPJ: {empresa_atual['cnpj']}</p>
        <p style="margin: 0; font-size: 0.85em; color: #666;">Contrato: {empresa_atual['contrato']}</p>
        <p style="margin: 0; font-size: 0.85em; color: #666;">Setor: {empresa_atual['setor']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Controles para o Juiz testar o fluxo
    st.subheader("🛠️ Painel de Controle (Demo)")
    if st.button("Simular Avanço Interno SESI"):
        avancar_fluxo()
    
    if st.button("Resetar Simulação"):
        # Resetar status no banco de dados
        atualizar_status_contrato(
            st.session_state['empresa_logada'], 
            'Aguardando M1', 
            pgr_gerado=0
        )
        
        # Limpar histórico no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM historico_processos WHERE empresa_id = ?', 
                      (st.session_state['empresa_logada'],))
        cursor.execute('''
            INSERT INTO historico_processos (empresa_id, data, evento, status)
            VALUES (?, '28/11/2025', 'Contrato Assinado', 'ok')
        ''', (st.session_state['empresa_logada'],))
        conn.commit()
        conn.close()
        
        # Limpar agendamentos no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM agendamentos_exames WHERE empresa_id = ?', 
                      (st.session_state['empresa_logada'],))
        conn.commit()
        conn.close()
        
        # Resetar session_state
        st.session_state['status_contrato'] = 'Aguardando M1'
        st.session_state['historico'] = [{"data": "28/11/2025", "evento": "Contrato Assinado", "status": "ok"}]
        st.session_state['dados_m1'] = None
        st.session_state['pgr_gerado'] = False
        st.session_state['pcmso_gerado'] = False
        st.session_state['balloons_mostrados'] = False
        st.session_state['mostrar_motivo_pgr'] = False
        st.session_state['mostrar_motivo_pcmso'] = False
        
        st.success("✅ Simulação resetada! Todos os dados foram limpos.")
        st.rerun()
    
    st.divider()
    
    # Botão de logout
    if st.button("🚪 Sair da Conta", type="secondary", use_container_width=True):
        fazer_logout()
        st.rerun()

# Cabeçalho Principal com Logo
col_logo, col_title = st.columns([1, 5])

with col_logo:
    st.markdown("""
    <style>
    .header-logo img {
        border-radius: 50%;
    }
    </style>
    <div class="header-logo">
    """, unsafe_allow_html=True)
    st.image("Sesisaude.png", width=120)
    st.markdown("</div>", unsafe_allow_html=True)

with col_title:
    st.markdown(f"""
    <div style="animation: fadeIn 0.8s ease-in;">
        <h1 style="color: #1f77b4; margin-bottom: 5px; font-size: 2.5em;">
            🏭 SESI Conecta
        </h1>
        <p style="color: #8b92a8; font-size: 1.1em; margin-top: 0;">
            <b style="color: #1f77b4;">{empresa_atual['nome']}</b> • Transparência total na jornada de Saúde e Segurança
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Layout de Abas
aba1, aba2, aba3, aba4 = st.tabs([
    "📊 Visão Geral", 
    "⚡ Ações Pendentes", 
    "📅 Agendamento de Exames", 
    "🤖 Assistente IA"
])

with aba1:
    # DASHBOARD VISUAL SIMPLIFICADO
    st.subheader("📊 Painel de Controle - Visão Executiva")
    
    # Mapeamento do progresso para barra visual
    mapa_progresso = {
        'Aguardando M1': 10,
        'Aguardando Visita SESI': 20,
        'Em Análise (Segurança)': 35,
        'PGR Aguardando Validação': 50,
        'PGR Validado': 60,
        'PCMSO Em Elaboração': 70,
        'PCMSO Aguardando Validação': 85,
        'PCMSO Validado': 95,
        'Concluído': 100
    }
    progresso = mapa_progresso.get(st.session_state['status_contrato'], 10)
    
    # Cálculos de ROI e Economia
    total_funcionarios = len(st.session_state['dados_m1']) if st.session_state['dados_m1'] is not None else empresa_atual['vidas']
    custo_acidente_medio = 50000  # R$ 50 mil por acidente grave
    taxa_prevencao = 0.75  # 75% de redução de acidentes com PGR/PCMSO
    acidentes_estimados_ano = max(1, total_funcionarios // 100)  # 1 acidente a cada 100 funcionários/ano
    economia_acidentes = acidentes_estimados_ano * custo_acidente_medio * taxa_prevencao
    
    multa_nr_media = 25000  # Multa média por descumprimento de NR
    conformidade_score = progresso  # Score de 0-100
    economia_multas = multa_nr_media * (conformidade_score / 100)
    
    roi_total = economia_acidentes + economia_multas
    
    # CARDS DE ROI E ECONOMIA
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h3 style="color: #1f77b4; font-size: 1.8em; margin-bottom: 5px;">💰 Impacto Financeiro do Programa</h3>
        <p style="color: #8b92a8; font-size: 1em;">Economia projetada com gestão profissional de SST</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_roi1, col_roi2, col_roi3, col_roi4 = st.columns(4)
    
    with col_roi1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 30px; border-radius: 20px; text-align: center; color: white;
                    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
                    transform: translateY(0);
                    transition: all 0.3s ease;">
            <div style="font-size: 3.5em; margin-bottom: 15px;">💎</div>
            <h1 style="margin: 0; font-size: 2.5em; font-weight: 800;">R$ {roi_total:,.0f}</h1>
            <h3 style="margin: 15px 0 5px 0; font-weight: 600; letter-spacing: 1px;">ECONOMIA TOTAL</h3>
            <p style="margin: 0; font-size: 1em; opacity: 0.9;">Retorno estimado/ano</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_roi2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                    padding: 30px; border-radius: 20px; text-align: center; color: white;
                    box-shadow: 0 10px 30px rgba(17, 153, 142, 0.4);
                    transition: all 0.3s ease;">
            <div style="font-size: 3.5em; margin-bottom: 15px;">🛡️</div>
            <h1 style="margin: 0; font-size: 2.5em; font-weight: 800;">R$ {economia_acidentes:,.0f}</h1>
            <h3 style="margin: 15px 0 5px 0; font-weight: 600; letter-spacing: 1px;">PREVENÇÃO</h3>
            <p style="margin: 0; font-size: 1em; opacity: 0.9;">Acidentes evitados</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_roi3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 30px; border-radius: 20px; text-align: center; color: white;
                    box-shadow: 0 10px 30px rgba(240, 147, 251, 0.4);
                    transition: all 0.3s ease;">
            <div style="font-size: 3.5em; margin-bottom: 15px;">🚫</div>
            <h1 style="margin: 0; font-size: 2.5em; font-weight: 800;">R$ {economia_multas:,.0f}</h1>
            <h3 style="margin: 15px 0 5px 0; font-weight: 600; letter-spacing: 1px;">MULTAS EVITADAS</h3>
            <p style="margin: 0; font-size: 1em; opacity: 0.9;">Conformidade NR</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_roi4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 30px; border-radius: 20px; text-align: center; color: white;
                    box-shadow: 0 10px 30px rgba(250, 112, 154, 0.4);
                    transition: all 0.3s ease;">
            <div style="font-size: 3.5em; margin-bottom: 15px;">✅</div>
            <h1 style="margin: 0; font-size: 2.5em; font-weight: 800;">{conformidade_score}%</h1>
            <h3 style="margin: 15px 0 5px 0; font-weight: 600; letter-spacing: 1px;">CONFORMIDADE</h3>
            <p style="margin: 0; font-size: 1em; opacity: 0.9;">Score NR atual</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CARDS DE STATUS
    st.markdown("### 🎯 Indicadores de Processo")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cor_status = "🟢" if progresso == 100 else "🟡" if progresso >= 60 else "🔴"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px; border-radius: 15px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 3em;">{cor_status}</h1>
            <h3 style="margin: 10px 0 0 0;">Status</h3>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">{st.session_state['status_contrato']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 25px; border-radius: 15px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 3em;">{progresso}%</h1>
            <h3 style="margin: 10px 0 0 0;">Progresso</h3>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Conclusão do fluxo</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        dias_decorridos = len(st.session_state['historico'])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 25px; border-radius: 15px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 3em;">{dias_decorridos}</h1>
            <h3 style="margin: 10px 0 0 0;">Marcos</h3>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Etapas concluídas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 25px; border-radius: 15px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 3em;">{total_funcionarios}</h1>
            <h3 style="margin: 10px 0 0 0;">Vidas</h3>
            <p style="margin: 5px 0 0 0; font-size: 0.9em;">Funcionários cadastrados</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # LINHA DO TEMPO VISUAL
    st.markdown("""
    <div style="text-align: center; margin: 40px 0 30px 0;">
        <h2 style="color: #1f77b4; font-size: 2em; margin-bottom: 10px;">🚀 Jornada de Compliance</h2>
        <p style="color: #8b92a8; font-size: 1.1em;">Acompanhe cada etapa do processo de certificação</p>
    </div>
    """, unsafe_allow_html=True)
    
    fases = [
        {"nome": "Contrato", "prog": 10, "icon": "📝", "desc": "Assinado"},
        {"nome": "M1 Validada", "prog": 40, "icon": "✅", "desc": "Dados OK"},
        {"nome": "PGR", "prog": 60, "icon": "🛡️", "desc": "Riscos"},
        {"nome": "PCMSO", "prog": 80, "icon": "🏥", "desc": "Saúde"},
        {"nome": "Concluído", "prog": 100, "icon": "🎉", "desc": "100%"}
    ]
    
    cols = st.columns(5)
    for idx, fase in enumerate(fases):
        with cols[idx]:
            ativo = progresso >= fase['prog']
            if ativo:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                            padding: 25px; border-radius: 15px; text-align: center; color: white;
                            box-shadow: 0 8px 20px rgba(17, 153, 142, 0.4);
                            transform: scale(1.05);
                            animation: pulse 2s infinite;">
                    <div style="font-size: 3em; margin-bottom: 10px;">{fase['icon']}</div>
                    <div style="font-weight: 700; font-size: 1.1em; margin-bottom: 5px;">{fase['nome']}</div>
                    <div style="font-size: 0.9em; opacity: 0.9;">{fase['desc']}</div>
                    <div style="margin-top: 10px; font-size: 1.2em; font-weight: 700;">✓</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 25px; border-radius: 15px; 
                            text-align: center; color: #999; border: 2px dashed #ddd;">
                    <div style="font-size: 3em; margin-bottom: 10px; opacity: 0.5;">{fase['icon']}</div>
                    <div style="font-weight: 600; font-size: 1.1em; margin-bottom: 5px;">{fase['nome']}</div>
                    <div style="font-size: 0.9em;">{fase['desc']}</div>
                    <div style="margin-top: 10px; font-size: 1.2em;">⏳</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    
    # Gráfico de Evolução Temporal
    st.subheader("📈 Evolução do Processo")
    
    df_evolucao = pd.DataFrame(st.session_state['timeline_evolucao'])
    df_evolucao['data'] = pd.to_datetime(df_evolucao['data'])
    
    # Criar gráfico com Plotly
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_evolucao['data'],
        y=df_evolucao['progresso'],
        mode='lines+markers',
        name='Progresso',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=10, color='#1f77b4'),
        hovertemplate='<b>%{text}</b><br>Data: %{x|%d/%m/%Y}<br>Progresso: %{y}%<extra></extra>',
        text=df_evolucao['fase']
    ))
    
    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Progresso (%)",
        yaxis=dict(range=[0, 105]),
        height=350,
        hovermode='closest',
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Timeline Vertical (Histórico)
    st.markdown("""
    <div style="text-align: center; margin: 40px 0 30px 0;">
        <h2 style="color: #1f77b4; font-size: 1.8em; margin-bottom: 10px;">📋 Histórico de Atividades</h2>
        <p style="color: #8b92a8; font-size: 1em;">Registro completo de todas as etapas concluídas</p>
    </div>
    """, unsafe_allow_html=True)
    
    for idx, item in enumerate(reversed(st.session_state['historico'])):
        icon = "✅" if item['status'] == 'ok' else "⚠️" if item['status'] == 'pendente' else "ℹ️"
        cor_borda = "#11998e" if item['status'] == 'ok' else "#f5576c" if item['status'] == 'pendente' else "#667eea"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e2530 0%, #252d3d 100%);
                    padding: 20px; border-radius: 12px; margin-bottom: 15px;
                    border-left: 5px solid {cor_borda};
                    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
                    transition: transform 0.2s; border: 1px solid #2d3748;">
            <div style="display: flex; align-items: center;">
                <div style="font-size: 2em; margin-right: 15px;">{icon}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 1.1em; color: #e0e0e0; margin-bottom: 5px;">
                        {item['evento']}
                    </div>
                    <div style="color: #8b92a8; font-size: 0.95em;">
                        📅 {item['data']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with aba2:
    st.subheader("O que precisamos de você agora?")
    
    status = st.session_state['status_contrato']
    
    if status == 'Aguardando M1':
        st.info("**Ação Necessária:** Para iniciarmos o PGR, precisamos dos dados dos seus colaboradores.")
        
        st.markdown("""
        **Poka-Yoke (Anti-Erro):** Aceitamos qualquer planilha Excel, desde que contenha as colunas: 
        `Nome Completo`, `CPF`, `Cargo`, `Data Nascimento`, `Descrição da Atividade`.
        """)
        
        arquivo = st.file_uploader("Arraste sua planilha de funcionários aqui", type=['xlsx', 'csv'])
        
        if arquivo:
            sucesso, resultado = processar_m1(arquivo)
            
            if sucesso:
                st.success("Validação Poka-Yoke: Sucesso! Dados estruturados corretamente.")
                st.dataframe(resultado.head()) # Mostra preview
                if st.button("Confirmar Envio da M1"):
                    st.session_state['dados_m1'] = resultado
                    avancar_fluxo()
                    st.rerun()
            else:
                st.error(resultado) # Mostra mensagem de erro do Poka-Yoke
    
    elif status == 'Aguardando Visita SESI':
        st.info("**Agendamento de Visita SESI**")
        st.markdown("""
        Precisamos realizar uma visita técnica em sua empresa para:
        - Avaliar in loco os riscos ocupacionais
        - Realizar medições ambientais (ruído, iluminação, etc.)
        - Mapear processos e atividades
        - Elaborar o PGR de forma personalizada
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            data_visita = st.date_input("📆 Data desejada para visita", min_value=datetime.now())
        with col2:
            horario_visita = st.selectbox("🕐 Horário", ["08:00", "09:00", "10:00", "14:00", "15:00", "16:00"])
        
        observacoes = st.text_area("💬 Observações (opcional)", placeholder="Ex: Solicitar acesso ao setor de produção...")
        
        if st.button("✅ Confirmar Agendamento da Visita"):
            adicionar_historico(f"Visita agendada para {data_visita.strftime('%d/%m/%Y')} às {horario_visita}", "ok")
            st.success(f"Visita agendada com sucesso para {data_visita.strftime('%d/%m/%Y')} às {horario_visita}!")
            time.sleep(1)
            avancar_fluxo()
            st.rerun()
    
    elif status == 'PGR Aguardando Validação':
        st.warning("**PGR Elaborado - Aguardando sua aprovação**")
        st.markdown("""
        O Programa de Gerenciamento de Riscos (PGR) foi elaborado pela equipe técnica do SESI.
        Por favor, revise o documento abaixo e aprove ou solicite alterações.
        """)
        
        # Preview do PGR expandido por padrão
        with st.expander("📄 Visualizar PGR Elaborado", expanded=True):
            # Gerar QR Code para o preview
            import socket
            import qrcode
            from io import BytesIO
            import base64
            
            hostname = socket.gethostbyname(socket.gethostname())
            dashboard_url = f"http://{hostname}:8501/?empresa={empresa_atual['empresa_id']}&view=dashboard"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(dashboard_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
            
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4;">
            <h3 style="color: #1f77b4; text-align: center;">PROGRAMA DE GERENCIAMENTO DE RISCOS - PGR</h3>
            
            <table style="width:100%; margin-top: 20px; border-collapse: collapse; border: 1px solid #333;">
                <tr style="background-color: #d0d0d0;">
                    <td style="padding: 8px; font-weight: bold; width: 30%; border: 1px solid #333; color: #000;">Empresa:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #000;">{empresa_atual['nome']}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 8px; font-weight: bold; border: 1px solid #333; color: #000;">CNPJ:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #000;">{empresa_atual['cnpj']}</td>
                </tr>
                <tr style="background-color: #d0d0d0;">
                    <td style="padding: 8px; font-weight: bold; border: 1px solid #333; color: #000;">Contrato:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #000;">{empresa_atual['contrato']}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 8px; font-weight: bold; border: 1px solid #333; color: #000;">Setor:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #000;">{empresa_atual['setor']}</td>
                </tr>
                <tr style="background-color: #d0d0d0;">
                    <td style="padding: 8px; font-weight: bold; border: 1px solid #333; color: #000;">Data de Elaboração:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #000;">{datetime.now().strftime('%d/%m/%Y')}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 8px; font-weight: bold; border: 1px solid #333; color: #000;">Validade:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #000;">{(datetime.now() + timedelta(days=730)).strftime('%d/%m/%Y')} (24 meses)</td>
                </tr>
            </table>
            
            <h4 style="color: #000; margin-top: 25px; font-weight: bold;">1. IDENTIFICAÇÃO DOS PERIGOS</h4>
            <p style="margin-bottom: 10px; color: #000;"><strong>Ruído ocupacional (Setor: Produção)</strong><br>
            - Nível médio: 85 dB(A)<br>
            - Exposição: 8 horas/dia</p>
            
            <p style="margin-bottom: 10px; color: #000;"><strong>Riscos mecânicos (Máquinas e equipamentos)</strong><br>
            - Prensas, serras, tornos<br>
            - Pontos de prensagem e corte</p>
            
            <p style="margin-bottom: 10px; color: #000;"><strong>Agentes químicos (Soldagem e pintura)</strong><br>
            - Fumos metálicos<br>
            - Solventes e tintas</p>
            
            <p style="margin-bottom: 10px; color: #000;"><strong>Ergonômicos (Levantamento de cargas)</strong><br>
            - Movimentação manual de cargas até 25kg<br>
            - Posturas inadequadas</p>
            
            <h4 style="color: #000; margin-top: 25px; font-weight: bold;">2. AVALIAÇÃO DE RISCOS</h4>
            <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
                <tr style="background-color: #1f77b4; color: white;">
                    <th style="padding: 10px; border: 1px solid #000; text-align: center; font-weight: bold;">Risco</th>
                    <th style="padding: 10px; border: 1px solid #000; text-align: center; font-weight: bold;">Probabilidade</th>
                    <th style="padding: 10px; border: 1px solid #000; text-align: center; font-weight: bold;">Severidade</th>
                    <th style="padding: 10px; border: 1px solid #000; text-align: center; font-weight: bold;">Nível</th>
                </tr>
                <tr style="background-color: #ffffff;">
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000; font-weight: bold;">Ruído</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">Alta</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">Média</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">MÉDIO</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000; font-weight: bold;">Mecânico</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">Média</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">Alta</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">ALTO</td>
                </tr>
                <tr style="background-color: #ffffff;">
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000; font-weight: bold;">Químico</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">Média</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">Média</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">MÉDIO</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000; font-weight: bold;">Ergonômico</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">Alta</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">Baixa</td>
                    <td style="padding: 10px; border: 1px solid #333; text-align: center; color: #000;">BAIXO</td>
                </tr>
            </table>
            
            <h4 style="color: #000; margin-top: 25px; font-weight: bold;">3. MEDIDAS DE CONTROLE RECOMENDADAS</h4>
            <p style="margin-bottom: 8px; color: #000;"><strong>→ Fornecimento de EPIs:</strong><br>
            • Protetor auricular tipo concha<br>
            • Luvas de segurança específicas<br>
            • Óculos de proteção<br>
            • Máscaras respiratórias</p>
            
            <p style="margin-bottom: 8px; color: #000;"><strong>→ Treinamentos obrigatórios:</strong><br>
            • NR-12 (Segurança em máquinas)<br>
            • NR-06 (Uso correto de EPIs)<br>
            • NR-17 (Ergonomia)</p>
            
            <p style="margin-bottom: 8px; color: #000;"><strong>→ Adequações técnicas:</strong><br>
            • Manutenção preventiva de equipamentos<br>
            • Enclausuramento de fontes de ruído<br>
            • Ventilação local exaustora<br>
            • Ajuste ergonômico de estações de trabalho</p>
            
            <h4 style="color: #000; margin-top: 25px; font-weight: bold;">4. CRONOGRAMA DE IMPLEMENTAÇÃO</h4>
            <p style="margin-bottom: 5px; color: #000;"><strong>Mês 1-2:</strong> Aquisição e distribuição de EPIs</p>
            <p style="margin-bottom: 5px; color: #000;"><strong>Mês 2-3:</strong> Realização de treinamentos</p>
            <p style="margin-bottom: 5px; color: #000;"><strong>Mês 3-6:</strong> Adequações de engenharia</p>
            <p style="margin-bottom: 5px; color: #000;"><strong>Contínuo:</strong> Monitoramento e avaliações periódicas</p>
            
            <hr style="margin-top: 30px; border: 1px solid #333;">
            <h4 style="color: #000; margin-top: 25px; font-weight: bold;">📱 Acesse o Dashboard do Programa:</h4>
            <div style="text-align: center; margin: 20px 0;">
            <img src="data:image/png;base64,{qr_base64}" style="width: 200px; height: 200px; border: 2px solid #333; padding: 10px; background: white;" />
            <p style="font-style: italic; color: #8b92a8; margin-top: 10px;">Escaneie o QR Code para acompanhar exames agendados e métricas de saúde ocupacional</p>
            </div>
            
            <p style="text-align: center; margin-top: 20px; color: #e0e0e0;">
            ___________________________________________<br>
            <strong>Eng. de Segurança do Trabalho SESI</strong><br>
            CREA 12345/SP
            </p>
            <p style="text-align: center; font-size: 0.9em; color: #8b92a8; font-style: italic; margin-top: 10px;">
            Este documento foi gerado automaticamente pelo sistema SESI Conecta.
            </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Botões de validação
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            pdf_data = gerar_pdf_pgr()
            st.download_button(
                label="📥 Baixar PGR (PDF)",
                data=pdf_data,
                file_name=f"PGR_{empresa_atual['nome'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        
        st.divider()
        st.subheader("✅ Validação do Documento")
        
        col_apr, col_rej = st.columns(2)
        with col_apr:
            if st.button("✅ APROVAR PGR", type="primary", use_container_width=True):
                validar_pgr()
                st.success("PGR aprovado com sucesso!")
                time.sleep(1)
                st.rerun()
        
        with col_rej:
            if st.button("❌ SOLICITAR CORREÇÕES", type="secondary", use_container_width=True):
                st.session_state['mostrar_motivo_pgr'] = True
        
        if st.session_state.get('mostrar_motivo_pgr', False):
            motivo = st.text_area("📝 Descreva as correções necessárias:", 
                                 placeholder="Ex: Incluir análise do setor de expedição...")
            if st.button("Enviar Solicitação de Correção"):
                if motivo:
                    rejeitar_pgr(motivo)
                    st.warning("Solicitação enviada! O SESI irá reelaborar o PGR.")
                    st.session_state['mostrar_motivo_pgr'] = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Por favor, descreva o motivo da rejeição.")
    
    elif status == 'PCMSO Aguardando Validação':
        st.warning("**PCMSO Elaborado - Aguardando sua aprovação**")
        st.markdown("""
        O Programa de Controle Médico de Saúde Ocupacional (PCMSO) foi elaborado.
        Por favor, revise e aprove ou solicite alterações.
        """)
        
        with st.expander("Visualizar PCMSO Elaborado", expanded=True):
            st.markdown(f"""
            ### PROGRAMA DE CONTROLE MÉDICO DE SAÚDE OCUPACIONAL - PCMSO
            
            **Empresa:** {empresa_atual['nome']}  
            **CNPJ:** {empresa_atual['cnpj']}  
            **Vigência:** {datetime.now().strftime('%d/%m/%Y')} a {(datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y')}
            
            ---
            
            #### 1. OBJETIVO
            Promoção e preservação da saúde dos trabalhadores através de exames médicos ocupacionais
            conforme NR-07, monitorando exposição aos riscos identificados no PGR.
            
            #### 2. EXAMES MÉDICOS OCUPACIONAIS
            
            | Tipo de Exame | Periodicidade | Exames Complementares |
            |---------------|---------------|----------------------|
            | Admissional | Antes da admissão | Hemograma, Audiometria, Acuidade Visual |
            | Periódico | Anual | Hemograma, Audiometria, Espirometria |
            | Retorno ao Trabalho | Após 30 dias afastado | Conforme avaliação médica |
            | Mudança de Função | Antes da mudança | Conforme novo risco |
            | Demissional | Até homologação | Audiometria, Acuidade Visual |
            
            #### 3. RISCOS MONITORADOS
            - **Ruído:** Audiometria tonal limiar anual
            - **Agentes Químicos:** Exames laboratoriais específicos
            - **Ergonômicos:** Avaliação osteomuscular
            - **Mecânicos:** Avaliação de integridade física
            
            ---
            
            #### 📱 Acesse o Dashboard do Programa
            
            """)
            
            # Gerar QR Code para o preview
            import socket
            import qrcode
            from io import BytesIO
            import base64
            
            hostname = socket.gethostbyname(socket.gethostname())
            dashboard_url = f"http://{hostname}:8501/?empresa={empresa_atual['empresa_id']}&view=dashboard"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(dashboard_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
            
            st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
            <img src="data:image/png;base64,{qr_base64}" style="width: 200px; height: 200px; border: 2px solid #333; padding: 10px; background: white;" />
            <p style="font-style: italic; color: #555; margin-top: 10px;">Escaneie o QR Code para acompanhar exames agendados e métricas de saúde ocupacional</p>
            </div>
            
            <hr>
            
            <p style="text-align: center;"><em>Médico Coordenador: Dr. Roberto Silva Santos - CRM 123456/SP</em></p>
            """)
        
        col_pdf, col_esp = st.columns([2, 1])
        with col_pdf:
            pdf_pcmso = gerar_pdf_pcmso()
            st.download_button(
                label="Baixar PCMSO (PDF)",
                data=pdf_pcmso,
                file_name=f"PCMSO_{empresa_atual['nome'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        
        st.divider()
        st.subheader("Validação do Documento")
        
        col_apr2, col_rej2 = st.columns(2)
        with col_apr2:
            if st.button("APROVAR PCMSO", type="primary", use_container_width=True):
                validar_pcmso()
                time.sleep(1)
                st.rerun()
        
        with col_rej2:
            if st.button("SOLICITAR CORREÇÕES", type="secondary", use_container_width=True):
                st.session_state['mostrar_motivo_pcmso'] = True
        
        if st.session_state.get('mostrar_motivo_pcmso', False):
            motivo_pcmso = st.text_area("Descreva as correções necessárias:", 
                                        placeholder="Ex: Incluir exame toxicológico...")
            if st.button("Enviar Solicitação"):
                if motivo_pcmso:
                    rejeitar_pcmso(motivo_pcmso)
                    st.warning("Solicitação enviada! O SESI irá reelaborar o PCMSO.")
                    st.session_state['mostrar_motivo_pcmso'] = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Por favor, descreva o motivo da rejeição.")
                
    elif status == 'Concluído':
        st.success("Processo concluído! Você já pode agendar os exames no menu Agendamento de Exames.")
        if not st.session_state['balloons_mostrados']:
            st.balloons()
            st.session_state['balloons_mostrados'] = True
        
    else:
        if status not in ['PGR Aguardando Validação', 'PCMSO Aguardando Validação']:
            st.warning(f"O processo está com o time do SESI (**{status}**). Você será notificado via WhatsApp assim que houver novidades.")
            st.image("https://media.tenor.com/On7kvXhzml4AAAAj/loading-gif.gif", width=50)
    
    # Preview de Documentos Gerados (somente se já validado)
    if st.session_state['pgr_gerado'] and status not in ['PGR Aguardando Validação']:
        st.divider()
        st.subheader("📄 Documentos Aprovados")
        
        with st.expander("📋 Visualizar PGR (Programa de Gerenciamento de Riscos)", expanded=False):
            # Gerar QR Code para o preview do PGR aprovado
            import socket
            import qrcode
            from io import BytesIO
            import base64
            
            hostname = socket.gethostbyname(socket.gethostname())
            dashboard_url_pgr = f"http://{hostname}:8501/?empresa={empresa_atual['empresa_id']}&view=dashboard"
            
            qr_pgr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr_pgr.add_data(dashboard_url_pgr)
            qr_pgr.make(fit=True)
            qr_img_pgr = qr_pgr.make_image(fill_color="black", back_color="white")
            
            qr_buffer_pgr = BytesIO()
            qr_img_pgr.save(qr_buffer_pgr, format='PNG')
            qr_base64_pgr = base64.b64encode(qr_buffer_pgr.getvalue()).decode()
            
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4;">
            <h3 style="color: #1f77b4;">PROGRAMA DE GERENCIAMENTO DE RISCOS - PGR</h3>
            <p><strong>Empresa:</strong> Indústria Metalúrgica Hackathon LTDA</p>
            <p><strong>CNPJ:</strong> 12.345.678/0001-99</p>
            <p><strong>Data de Elaboração:</strong> 28/11/2025</p>
            <p><strong>Validade:</strong> 28/11/2027 (24 meses)</p>
            <hr>
            <h4>1. IDENTIFICAÇÃO DOS PERIGOS</h4>
            <ul>
                <li>✓ Ruído ocupacional (Setor: Produção)</li>
                <li>✓ Riscos mecânicos (Máquinas e equipamentos)</li>
                <li>✓ Agentes químicos (Soldagem e pintura)</li>
                <li>✓ Ergonômicos (Levantamento de cargas)</li>
            </ul>
            <h4>2. AVALIAÇÃO DE RISCOS</h4>
            <table style="width:100%; border-collapse: collapse;">
                <tr style="background-color: #1f77b4; color: white;">
                    <th style="padding: 8px; border: 1px solid #ddd;">Risco</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Probabilidade</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Severidade</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Nível</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Ruído</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">Alta</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">Média</td>
                    <td style="padding: 8px; border: 1px solid #ddd; background-color: #ffa500; color: white;">MÉDIO</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Mecânico</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">Média</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">Alta</td>
                    <td style="padding: 8px; border: 1px solid #ddd; background-color: #ff0000; color: white;">ALTO</td>
                </tr>
            </table>
            <h4>3. MEDIDAS DE CONTROLE RECOMENDADAS</h4>
            <ul>
                <li>🔹 Fornecimento de EPIs (Protetor auricular, luvas, óculos)</li>
                <li>🔹 Treinamento em NR-12 (Segurança em máquinas)</li>
                <li>🔹 Adequação ergonômica das estações de trabalho</li>
                <li>🔹 Manutenção preventiva de equipamentos</li>
            </ul>
            <hr>
            <h4 style="color: #000; margin-top: 25px; font-weight: bold;">📱 Acesse o Dashboard do Programa:</h4>
            <div style="text-align: center; margin: 20px 0;">
            <img src="data:image/png;base64,{qr_base64_pgr}" style="width: 200px; height: 200px; border: 2px solid #333; padding: 10px; background: white;" />
            <p style="font-style: italic; color: #555; margin-top: 10px;">Escaneie o QR Code para acompanhar exames agendados e métricas de saúde ocupacional</p>
            </div>
            <p style="margin-top: 20px; font-size: 0.9em; color: #666;">Documento elaborado por: Eng. de Segurança SESI | CREA 12345/SP</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                pdf_data = gerar_pdf_pgr()
                st.download_button(
                    label="📥 Baixar PGR Completo (PDF)",
                    data=pdf_data,
                    file_name=f"PGR_{empresa_atual['nome'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    help="Clique para baixar o documento completo em PDF"
                )
            with col2:
                if st.button("📧 Enviar por Email"):
                    st.success("Email enviado para o responsável cadastrado!")
                    st.info("Enviado para: contato@metalurgicahackathon.com.br")
        
        # Mostrar PCMSO se foi gerado e validado
        if st.session_state['pcmso_gerado'] and status not in ['PCMSO Aguardando Validação']:
            with st.expander("📋 Visualizar PCMSO (Programa de Controle Médico de Saúde Ocupacional)", expanded=False):
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #2ca02c;">
                <h3 style="color: #2ca02c;">PROGRAMA DE CONTROLE MÉDICO DE SAÚDE OCUPACIONAL - PCMSO</h3>
                <p><strong>Empresa:</strong> {empresa_atual['nome']}</p>
                <p><strong>CNPJ:</strong> {empresa_atual['cnpj']}</p>
                <p><strong>Vigência:</strong> {datetime.now().strftime('%d/%m/%Y')} a {(datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y')}</p>
                <hr>
                <h4>1. OBJETIVO</h4>
                <p>Promoção e preservação da saúde dos trabalhadores através de exames médicos ocupacionais
                conforme NR-07, monitorando exposição aos riscos identificados no PGR.</p>
                <h4>2. EXAMES MÉDICOS OCUPACIONAIS</h4>
                <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
                    <tr style="background-color: #2ca02c; color: white;">
                        <th style="padding: 8px; border: 1px solid #ddd;">Tipo de Exame</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Periodicidade</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Exames Complementares</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">Admissional</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Antes da admissão</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Hemograma, Audiometria, Acuidade Visual</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">Periódico</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Anual</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Hemograma, Audiometria, Espirometria</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">Retorno ao Trabalho</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Após 30 dias afastado</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Conforme avaliação médica</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">Mudança de Função</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Antes da mudança</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Conforme novo risco</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">Demissional</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Até homologação</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">Audiometria, Acuidade Visual</td>
                    </tr>
                </table>
                <h4>3. RISCOS MONITORADOS</h4>
                <ul>
                    <li><strong>Ruído:</strong> Audiometria tonal limiar anual</li>
                    <li><strong>Agentes Químicos:</strong> Exames laboratoriais específicos</li>
                    <li><strong>Ergonômicos:</strong> Avaliação osteomuscular</li>
                    <li><strong>Mecânicos:</strong> Avaliação de integridade física</li>
                </ul>
                <hr>
                <h4 style="color: #000; margin-top: 25px; font-weight: bold;">📱 Acesse o Dashboard do Programa:</h4>
                <div style="text-align: center; margin: 20px 0;">
                </div>
                <p><em>Médico Coordenador: Dr. Roberto Silva Santos - CRM 123456/SP</em></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Gerar QR Code para o preview do PCMSO aprovado
                import socket
                import qrcode
                from io import BytesIO
                import base64
                
                hostname = socket.gethostbyname(socket.gethostname())
                dashboard_url_pcmso = f"http://{hostname}:8501/?empresa={empresa_atual['empresa_id']}&view=dashboard"
                
                qr_pcmso = qrcode.QRCode(version=1, box_size=10, border=2)
                qr_pcmso.add_data(dashboard_url_pcmso)
                qr_pcmso.make(fit=True)
                qr_img_pcmso = qr_pcmso.make_image(fill_color="black", back_color="white")
                
                qr_buffer_pcmso = BytesIO()
                qr_img_pcmso.save(qr_buffer_pcmso, format='PNG')
                qr_base64_pcmso = base64.b64encode(qr_buffer_pcmso.getvalue()).decode()
                
                st.markdown(f"""
                <div style="text-align: center; margin: 20px 0;">
                <img src="data:image/png;base64,{qr_base64_pcmso}" style="width: 200px; height: 200px; border: 2px solid #333; padding: 10px; background: white;" />
                <p style="font-style: italic; color: #555; margin-top: 10px;">Escaneie o QR Code para acompanhar exames agendados e métricas de saúde ocupacional</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_pcmso1, col_pcmso2 = st.columns(2)
                with col_pcmso1:
                    pdf_pcmso = gerar_pdf_pcmso()
                    st.download_button(
                        label="📥 Baixar PCMSO Completo (PDF)",
                        data=pdf_pcmso,
                        file_name=f"PCMSO_{empresa_atual['nome'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        help="Clique para baixar o documento completo em PDF"
                    )
                with col_pcmso2:
                    if st.button("📧 Enviar PCMSO por Email"):
                        st.success("Email enviado para o responsável cadastrado!")
                        st.info("Enviado para: contato@metalurgicahackathon.com.br")

# Aba 3: Agendamento de Exames
with aba3:
    st.subheader("Agendamento de Exames Ocupacionais")
    
    # Verificar se PCMSO foi validado
    if st.session_state['status_contrato'] not in ['PCMSO Validado', 'Concluído']:
        st.warning("O agendamento de exames estará disponível após a validação do PCMSO.")
        st.info("Status atual: " + st.session_state['status_contrato'])
    else:
        # Carregar agendamentos do banco de dados
        agendamentos_db = buscar_agendamentos(st.session_state['empresa_logada'])
        
        st.markdown("""
        Agende os exames ocupacionais dos seus colaboradores de acordo com o PCMSO validado.
        Selecione o tipo de exame e preencha os dados do colaborador.
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Novo Agendamento")
            
            tipo_exame = st.selectbox(
                "Tipo de Exame",
                ["Admissional", "Periódico", "Retorno ao Trabalho", "Mudança de Função", "Demissional"],
                help="Selecione o tipo de exame conforme PCMSO"
            )
            
            # Buscar colaboradores da planilha M1 se disponível
            if st.session_state['dados_m1'] is not None:
                colaboradores = st.session_state['dados_m1']['Nome Completo'].tolist()
                nome_colaborador = st.selectbox("Colaborador", colaboradores)
                
                # Buscar dados do colaborador selecionado
                dados_colab = st.session_state['dados_m1'][
                    st.session_state['dados_m1']['Nome Completo'] == nome_colaborador
                ].iloc[0]
                
                col_cargo, col_cpf = st.columns(2)
                with col_cargo:
                    st.text_input("Cargo", value=dados_colab['Cargo'], disabled=True)
                with col_cpf:
                    st.text_input("CPF", value=dados_colab['CPF'], disabled=True)
            else:
                nome_colaborador = st.text_input("Nome do Colaborador")
                col_cargo, col_cpf = st.columns(2)
                with col_cargo:
                    cargo_colaborador = st.text_input("Cargo")
                with col_cpf:
                    cpf_colaborador = st.text_input("CPF")
            
            # Exames complementares baseados no tipo
            exames_por_tipo = {
                "Admissional": ["Hemograma Completo", "Audiometria Tonal", "Acuidade Visual", "Glicemia"],
                "Periódico": ["Hemograma Completo", "Audiometria Tonal", "Espirometria", "Raio-X de Tórax"],
                "Retorno ao Trabalho": ["Avaliação Clínica", "Exames conforme afastamento"],
                "Mudança de Função": ["Avaliação Clínica", "Exames conforme novo risco"],
                "Demissional": ["Audiometria Tonal", "Acuidade Visual", "Avaliação Clínica"]
            }
            
            exames_selecionados = st.multiselect(
                "Exames Complementares",
                exames_por_tipo[tipo_exame],
                default=exames_por_tipo[tipo_exame],
                help="Exames recomendados pelo PCMSO para este tipo"
            )
            
            col_data, col_hora = st.columns(2)
            with col_data:
                data_exame = st.date_input(
                    "Data do Exame",
                    min_value=datetime.now(),
                    help="Selecione a data para realização dos exames"
                )
            with col_hora:
                horario_exame = st.selectbox(
                    "Horário",
                    ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", 
                     "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
                )
            
            local_exame = st.selectbox(
                "Local de Atendimento",
                ["Clínica SESI - Unidade Centro", "Clínica SESI - Unidade Industrial", 
                 "Na própria empresa (In Company)"],
                help="Escolha o local mais conveniente"
            )
            
            observacoes_exame = st.text_area(
                "Observações (opcional)",
                placeholder="Ex: Jejum de 8 horas necessário, colaborador tem dificuldade de locomoção..."
            )
            
            if st.button("Agendar Exame", type="primary", use_container_width=True):
                if nome_colaborador:
                    # Preparar dados do agendamento
                    if st.session_state['dados_m1'] is not None:
                        cargo_final = dados_colab['Cargo']
                        cpf_final = dados_colab['CPF']
                    else:
                        cargo_final = cargo_colaborador if 'cargo_colaborador' in locals() else ''
                        cpf_final = cpf_colaborador if 'cpf_colaborador' in locals() else ''
                    
                    agendamento = {
                        "colaborador": nome_colaborador,
                        "cargo": cargo_final,
                        "cpf": cpf_final,
                        "tipo": tipo_exame,
                        "data": data_exame.strftime('%Y-%m-%d'),
                        "horario": horario_exame,
                        "exames": exames_selecionados,
                        "local": local_exame,
                        "observacoes": observacoes_exame
                    }
                    
                    salvar_agendamento(st.session_state['empresa_logada'], agendamento)
                    st.success(f"Exame {tipo_exame} agendado para {nome_colaborador} em {data_exame.strftime('%d/%m/%Y')} às {horario_exame}")
                    st.rerun()
                else:
                    st.error("Por favor, preencha o nome do colaborador.")
        
        with col2:
            st.markdown("### Resumo PCMSO")
            st.info(f"""
            **Total de Colaboradores:** {empresa_atual['vidas']}
            
            **Exames Obrigatórios:**
            - Admissional
            - Periódico (anual)
            - Demissional
            
            **Clínicas Conveniadas:**
            - SESI Centro
            - SESI Industrial
            - Atendimento In Company
            """)
        
        # Lista de agendamentos
        if agendamentos_db:
            st.divider()
            st.subheader("Agendamentos Realizados")
            
            for agendamento in agendamentos_db:
                with st.expander(f"{agendamento['tipo']} - {agendamento['colaborador']} - {agendamento['data']}"):
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.markdown(f"""
                        **Colaborador:** {agendamento['colaborador']}  
                        **Tipo:** {agendamento['tipo']}  
                        **Status:** {agendamento['status']}
                        """)
                    with col_info2:
                        st.markdown(f"""
                        **Data:** {agendamento['data']}  
                        **Horário:** {agendamento['horario']}  
                        **Local:** {agendamento['local']}
                        """)
                    
                    st.markdown("**Exames a realizar:**")
                    for exame in agendamento['exames']:
                        st.markdown(f"- {exame}")
                    
                    if agendamento['observacoes']:
                        st.markdown(f"**Observações:** {agendamento['observacoes']}")
                    
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        if st.button("Cancelar", key=f"cancelar_{agendamento['id']}"):
                            cancelar_agendamento_db(agendamento['id'])
                            st.success("Agendamento cancelado!")
                            st.rerun()
                    with col_btn2:
                        if st.button("Remarcar", key=f"remarcar_{agendamento['id']}"):
                            st.info("Funcionalidade de remarcação em desenvolvimento")
                    with col_btn3:
                        if st.button("Imprimir Guia", key=f"imprimir_{agendamento['id']}"):
                            st.info("Guia de exame será enviada por email")
            
            # Resumo estatístico
            st.divider()
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Total de Agendamentos", len(agendamentos_db))
            with col_stat2:
                agendados = sum(1 for a in agendamentos_db if a['status'] == 'Agendado')
                st.metric("Confirmados", agendados)
            with col_stat3:
                tipos = {}
                for a in agendamentos_db:
                    tipos[a['tipo']] = tipos.get(a['tipo'], 0) + 1
                tipo_mais_comum = max(tipos.items(), key=lambda x: x[1])[0] if tipos else "N/A"
                st.metric("Tipo Mais Agendado", tipo_mais_comum)
        else:
            st.info("Nenhum agendamento realizado ainda. Use o formulário acima para agendar exames.")

# Aba 4: Assistente IA - Chatbot de Segurança do Trabalho
with aba4:
    st.subheader("🤖 Assistente Virtual - Segurança do Trabalho")
    st.markdown("""
    Tire suas dúvidas sobre Normas Regulamentadoras, PGR, PCMSO e segurança ocupacional.
    O assistente tem conhecimento sobre sua empresa e pode ajudar com orientações personalizadas.
    """)
    
    # Inicializar histórico do chat
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    
    # Contexto da empresa para o chatbot
    contexto_empresa = f"""
    Você é um especialista em segurança do trabalho e saúde ocupacional do SESI.
    
    Informações da Empresa:
    - Nome: {empresa_atual['nome']}
    - CNPJ: {empresa_atual['cnpj']}
    - Setor: {empresa_atual['setor']}
    - Número de funcionários: {empresa_atual['vidas']}
    - Status atual: {st.session_state['status_contrato']}
    
    Sua função é responder dúvidas sobre:
    - Normas Regulamentadoras (NR-1, NR-7, NR-9, etc)
    - Programa de Gerenciamento de Riscos (PGR)
    - Programa de Controle Médico de Saúde Ocupacional (PCMSO)
    - Exames ocupacionais obrigatórios
    - EPIs e medidas de controle
    - Procedimentos de segurança
    
    Seja objetivo, técnico e sempre cite a NR aplicável quando relevante.
    """
    
    # Usar Google Gemini (gratuito e de alta qualidade)
    import os
    
    gemini_api_key = os.environ.get('GEMINI_API_KEY', '')
    usar_gemini = False
    
    if gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-pro')
            usar_gemini = True
        except ImportError:
            st.info("📦 Para ativar o Gemini, instale: `pip install google-generativeai`")
        except Exception as e:
            st.warning(f"Erro ao configurar Gemini: {str(e)}")
    
    if not gemini_api_key and not usar_gemini:
        st.info("""
        **🤖 Assistente com IA Avançada (Opcional)**
        
        Para respostas mais inteligentes com Google Gemini:
        1. Obtenha API key gratuita em [ai.google.dev](https://ai.google.dev)
        2. Configure: `$env:GEMINI_API_KEY="sua-chave"` no PowerShell
        3. Reinicie o Streamlit
        
        **Modo atual:** Respostas baseadas em conhecimento programado (NRs atualizadas 2025)
        """)
    
    # Base de conhecimento (respostas programadas)
    respostas_demo = {
        'pcmso': f"""O PCMSO (NR-07) para {empresa_atual['nome']} deve incluir:

**Exames Obrigatórios:**
- Admissional: antes da contratação
- Periódico: anual para {empresa_atual['vidas']} colaboradores
- Retorno ao trabalho: após 30 dias de afastamento
- Mudança de função: antes da transferência
- Demissional: até a homologação

**Exames Complementares (setor {empresa_atual['setor']}):**
- Audiometria tonal limiar (risco de ruído)
- Hemograma completo
- Acuidade visual
- Espirometria (exposição a poeiras)

Médico coordenador obrigatório conforme NR-07.""",
        
        'pgr': f"""O PGR (Programa de Gerenciamento de Riscos - NR-01) substitui o PPRA desde 2022.

**Para {empresa_atual['setor']}:**
- Identificação de perigos: ruído, químicos, mecânicos, ergonômicos
- Avaliação quantitativa: probabilidade x severidade
- Medidas de controle: EPC (coletivas) antes de EPI (individuais)
- Revisão: a cada 24 meses ou quando houver mudanças

**Responsável:** Engenheiro de Segurança do Trabalho (CREA)
**Validade:** 2 anos""",
        
        'epi': f"""EPIs obrigatórios conforme NR-06:

**Entrega:**
- Gratuita ao trabalhador
- Certificado de Aprovação (CA) válido
- Treinamento de uso obrigatório
- Ficha de controle assinada

**Principais EPIs para {empresa_atual['setor']}:**
- Protetor auricular (ruído > 85 dB)
- Luvas de segurança (mecânica/química)
- Óculos de proteção
- Calçado de segurança
- Capacete (áreas de risco)

**Penalidade:** Multa de R$ 670,88 a R$ 6.708,88 por irregularidade (NR-28)""",
        
        'nr': """**Principais Normas Regulamentadoras:**

- NR-01: Gerenciamento de Riscos (PGR obrigatório)
- NR-05: CIPA (empresas com 20+ funcionários)
- NR-06: EPIs (fornecimento obrigatório)
- NR-07: PCMSO (exames médicos)
- NR-09: PGR (avaliação de riscos ambientais)
- NR-12: Segurança em Máquinas
- NR-17: Ergonomia
- NR-23: Proteção contra Incêndio
- NR-35: Trabalho em Altura

Atualização 2022: NR-01 centralizou obrigações gerais.""",
        
        'setor': f"""Riscos específicos do setor {empresa_atual['setor']}:

**Riscos Físicos:**
- Ruído de máquinas e equipamentos
- Vibração
- Calor excessivo

**Riscos Químicos:**
- Poeiras metálicas/orgânicas
- Fumos de soldagem
- Produtos de limpeza

**Riscos Mecânicos:**
- Prensas e máquinas cortantes
- Equipamentos em movimento
- Queda de materiais

**Riscos Ergonômicos:**
- Levantamento de peso
- Postura inadequada
- Movimentos repetitivos

**Medidas Prioritárias:**
1. Enclausuramento de máquinas ruidosas
2. Ventilação local exaustora
3. EPIs complementares
4. Ginástica laboral""",
        
        'multa': f"""Multas por descumprimento de NR (NR-28):

**Grau 1 (Leve):** R$ 670,88 - Falta de treinamento
**Grau 2 (Médio):** R$ 1.341,77 - Ausência de EPI
**Grau 3 (Grave):** R$ 3.354,43 - Falta de PGR/PCMSO
**Grau 4 (Gravíssimo):** R$ 6.708,86 - Risco iminente

Para {empresa_atual['vidas']} funcionários, não conformidade pode gerar multas de até R$ 50 mil/ano.

**Economia com conformidade:** Seu programa SESI já evitou aproximadamente R$ 25 mil em multas potenciais!""",
        
        'cipa': f"""CIPA (NR-05) para {empresa_atual['nome']}:

**Obrigatoriedade:** Empresas com 20+ funcionários
**Sua empresa:** {empresa_atual['vidas']} funcionários - {'CIPA obrigatória' if empresa_atual['vidas'] >= 20 else 'Designado de Segurança suficiente'}

**Composição:**
- Representantes do empregador (indicados)
- Representantes dos empregados (eleitos)
- Mandato de 1 ano

**Atribuições:**
- Mapear riscos do ambiente
- Investigar acidentes
- Promover SIPAT (Semana Interna de Prevenção)
- Acompanhar cumprimento de NRs

**Treinamento:** 20 horas obrigatórias para membros"""
    }
    
    # Interface do chat
    col_chat1, col_chat2 = st.columns([3, 1])
    
    with col_chat1:
        # Exibir histórico do chat
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state['chat_history']:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div style="background-color: #1e3a5f; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #4a90e2;">
                        <strong style="color: #4a90e2;">👤 Você:</strong><br>
                        <span style="color: #ffffff;">{msg['content']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #2d2d2d; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #00d4aa;">
                        <strong style="color: #00d4aa;">🤖 Assistente SESI:</strong><br>
                        <div style="color: #e0e0e0; line-height: 1.6;">{msg['content'].replace(chr(10), '<br>')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Input do usuário
        with st.form(key='chat_form', clear_on_submit=True):
            user_input = st.text_area(
                "Digite sua pergunta:",
                placeholder="Ex: Quais exames são obrigatórios no PCMSO?",
                height=100
            )
            submit_button = st.form_submit_button("Enviar", use_container_width=True, type="primary")
        
        if submit_button and user_input:
            # Adicionar pergunta ao histórico
            st.session_state['chat_history'].append({
                'role': 'user',
                'content': user_input
            })
            
            # Identificar palavra-chave e gerar resposta contextualizada
            user_lower = user_input.lower()
            resposta = None
            
            # Tentar usar Gemini se disponível
            if usar_gemini:
                try:
                    prompt_completo = f"""{contexto_empresa}

Pergunta do cliente: {user_input}

Responda de forma técnica, objetiva e cite as NRs aplicáveis. Máximo 300 palavras."""
                    
                    response = model.generate_content(prompt_completo)
                    resposta = response.text
                except Exception as e:
                    st.warning(f"Erro ao consultar Gemini: {str(e)}")
            
            # Sistema de IA inteligente (fallback sem API)
            if not resposta or len(resposta) < 50:
                # Palavras-chave e suas respostas
                keywords_map = {
                    'pcmso': ['pcmso', 'exame', 'médico', 'aso', 'admissional', 'periódico', 'demissional'],
                    'pgr': ['pgr', 'risco', 'perigo', 'ppra', 'avaliação', 'identificação'],
                    'epi': ['epi', 'proteção', 'equipamento', 'luva', 'capacete', 'óculos', 'protetor'],
                    'nr': ['nr ', ' nr', 'norma', 'regulamentadora', 'legislação'],
                    'cipa': ['cipa', 'comissão', 'acidente'],
                    'multa': ['multa', 'penalidade', 'fiscalização', 'autuação', 'valor'],
                    'setor': ['setor', empresa_atual['setor'].lower(), 'risco específico', 'atividade']
                }
                
                # Contar matches de palavras-chave
                scores = {}
                for key, keywords in keywords_map.items():
                    score = sum(1 for kw in keywords if kw in user_lower)
                    if score > 0:
                        scores[key] = score
                
                # Pegar a categoria com maior score
                if scores:
                    melhor_categoria = max(scores, key=scores.get)
                    resposta = respostas_demo[melhor_categoria]
                else:
                    # Resposta inteligente genérica baseada no contexto
                    if 'como' in user_lower or 'quando' in user_lower or 'onde' in user_lower:
                        resposta = f"""📋 **Processo no SESI Conecta**

Para {empresa_atual['nome']} no setor {empresa_atual['setor']}:

**1. Documentação Obrigatória:**
- PGR (Programa de Gerenciamento de Riscos) - NR-01
- PCMSO (Programa de Controle Médico) - NR-07
- Documentação de EPIs - NR-06

**2. Prazos:**
- PGR: Elaboração em até 30 dias após visita técnica
- PCMSO: Junto com PGR para coordenação de medidas
- Exames: Conforme cronograma definido

**Status atual:** {st.session_state['status_contrato']}

**Próximo passo:** {'Enviar planilha de funcionários (M1)' if st.session_state['status_contrato'] == 'Aguardando M1' else 'Acompanhar evolução no dashboard'}

Precisa de algo mais específico?"""
                    
                    elif 'valor' in user_lower or 'custo' in user_lower or 'preço' in user_lower or 'quanto' in user_lower:
                        resposta = f"""💰 **Investimento e Retorno**

**Para {empresa_atual['nome']} ({empresa_atual['vidas']} colaboradores):**

📊 **ROI Projetado:**
- Economia com prevenção de acidentes: R$ {(empresa_atual['vidas'] // 100) * 50000 * 0.75:,.2f}
- Evitar multas NR: R$ 25.000,00+
- **Total economizado/ano:** R$ {((empresa_atual['vidas'] // 100) * 50000 * 0.75) + 25000:,.2f}

✅ **Inclui:**
- Elaboração de PGR + PCMSO
- Visitas técnicas
- Coordenação médica
- Agendamento de exames
- Acompanhamento digital (SESI Conecta)

**Cada R$ 1 investido retorna R$ 4,50 em economia!**

Entre em contato com seu consultor SESI para proposta detalhada."""
                    
                    elif 'prazo' in user_lower or 'tempo' in user_lower or 'demora' in user_lower:
                        resposta = f"""⏱️ **Prazos do Processo**

**Timeline Completa para {empresa_atual['nome']}:**

📅 **Fase 1 - Levantamento (5-7 dias)**
- Envio da planilha M1
- Validação dos dados
- Agendamento de visita técnica

📅 **Fase 2 - Análise Técnica (15-20 dias)**
- Visita SESI na empresa
- Medições ambientais
- Elaboração do PGR

📅 **Fase 3 - Saúde Ocupacional (10-15 dias)**
- Elaboração do PCMSO
- Definição de exames
- Cronograma de agendamentos

📅 **Fase 4 - Implantação (contínuo)**
- Agendamento de exames
- Acompanhamento via SESI Conecta
- Renovação a cada 24 meses

**Status atual:** {st.session_state['status_contrato']}
**Tempo total estimado:** 30-45 dias até conclusão completa"""
                    
                    else:
                        # Resposta contextual inteligente
                        resposta = f"""🤖 **Assistente SESI Conecta**

Olá! Analisei sua pergunta: *"{user_input}"*

**Contexto da sua empresa:**
- {empresa_atual['nome']}
- Setor: {empresa_atual['setor']}
- Funcionários: {empresa_atual['vidas']} vidas
- Status: {st.session_state['status_contrato']}

**Posso ajudar especificamente com:**

🏥 **Saúde Ocupacional**
- PCMSO, exames admissionais, periódicos, ASO

🛡️ **Segurança do Trabalho**
- PGR, identificação de riscos, medidas de controle

⚖️ **Legislação e Compliance**
- NRs aplicáveis, CIPA, documentação obrigatória

💰 **ROI e Benefícios**
- Economia com prevenção, evitar multas

**Reformule sua pergunta** ou clique em uma sugestão ao lado →"""
            
            # Adicionar resposta ao histórico
            st.session_state['chat_history'].append({
                'role': 'assistant',
                'content': resposta
            })
            
            st.rerun()
    
    with col_chat2:
        st.markdown("### 💡 Perguntas Frequentes")
        
        perguntas_sugeridas = [
            "Quais exames do PCMSO?",
            "O que é PGR?",
            "Quanto custa o programa?",
            "Qual o prazo de entrega?",
            "Principais EPIs necessários",
            "Multas por descumprimento",
            f"Riscos no setor {empresa_atual['setor']}",
            "Como funciona o processo?",
            "Preciso de CIPA?",
            "Qual o ROI do programa?"
        ]
        
        # Dicionário de respostas pré-definidas para perguntas sugeridas
        respostas_sugeridas = {
            "Quais exames do PCMSO?": 'pcmso',
            "O que é PGR?": 'pgr',
            "Principais EPIs": 'epi',
            "Normas Regulamentadoras": 'nr',
            f"Riscos no setor {empresa_atual['setor']}": 'setor',
            "Multas por descumprimento": 'multa',
            "Preciso de CIPA?": 'cipa'
        }
        
        for pergunta in perguntas_sugeridas:
            if st.button(pergunta, key=f"sugestao_{pergunta}", use_container_width=True):
                # Adicionar pergunta
                st.session_state['chat_history'].append({
                    'role': 'user',
                    'content': pergunta
                })
                
                # Buscar resposta correspondente
                tipo_resposta = respostas_sugeridas.get(pergunta, None)
                if tipo_resposta and tipo_resposta in respostas_demo:
                    resposta = respostas_demo[tipo_resposta]
                else:
                    resposta = """Desculpe, não encontrei uma resposta específica. Posso ajudar com:
- PCMSO e exames ocupacionais
- PGR e avaliação de riscos
- EPIs e equipamentos de proteção
- Normas Regulamentadoras (NRs)
- CIPA e gestão de segurança
- Multas e fiscalização"""
                
                # Adicionar resposta ao histórico
                st.session_state['chat_history'].append({
                    'role': 'assistant',
                    'content': resposta
                })
                
                st.rerun()
        
        if st.button("🗑️ Limpar Conversa", use_container_width=True):
            st.session_state['chat_history'] = []
            st.rerun()
        
        st.markdown("---")
        st.success(f"""
        **{'🤖 Google Gemini Ativo' if usar_gemini else '✅ IA 100% Gratuita'}**
        
        {'Respostas inteligentes com IA avançada' if usar_gemini else 'Respostas baseadas em:'}
        {'' if usar_gemini else '- Base de conhecimento NRs'}
        {'' if usar_gemini else '- Contexto da sua empresa'}
        {'' if usar_gemini else '- Legislação atualizada 2025'}
        
        Total de mensagens: {len(st.session_state['chat_history'])}
        """)