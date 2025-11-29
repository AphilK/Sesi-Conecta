import sqlite3
from datetime import datetime

# Criar/conectar ao banco de dados
conn = sqlite3.connect('sesi_conecta.db')
cursor = conn.cursor()

# Criar tabela de empresas
cursor.execute('''
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    cnpj TEXT NOT NULL,
    contrato TEXT NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    vidas INTEGER NOT NULL,
    setor TEXT NOT NULL,
    data_cadastro TEXT NOT NULL
)
''')

# Criar tabela de histórico de processos
cursor.execute('''
CREATE TABLE IF NOT EXISTS historico_processos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id TEXT NOT NULL,
    data TEXT NOT NULL,
    evento TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (empresa_id) REFERENCES empresas (empresa_id)
)
''')

# Criar tabela de status de contratos
cursor.execute('''
CREATE TABLE IF NOT EXISTS status_contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id TEXT UNIQUE NOT NULL,
    status_atual TEXT NOT NULL,
    pgr_gerado INTEGER DEFAULT 0,
    data_atualizacao TEXT NOT NULL,
    FOREIGN KEY (empresa_id) REFERENCES empresas (empresa_id)
)
''')

# Criar tabela de agendamentos de exames
cursor.execute('''
CREATE TABLE IF NOT EXISTS agendamentos_exames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id TEXT NOT NULL,
    colaborador TEXT NOT NULL,
    cargo TEXT,
    cpf TEXT,
    tipo_exame TEXT NOT NULL,
    data_exame TEXT NOT NULL,
    horario TEXT NOT NULL,
    local TEXT NOT NULL,
    exames_complementares TEXT,
    observacoes TEXT,
    status TEXT DEFAULT 'Agendado',
    data_criacao TEXT NOT NULL,
    FOREIGN KEY (empresa_id) REFERENCES empresas (empresa_id)
)
''')

# Inserir dados das empresas
empresas_dados = [
    ('metalurgica', 'Indústria Metalúrgica Hackathon LTDA', '12.345.678/0001-99', 
     '#9823-2025', 'joao.silva', 'metal2025', 150, 'Metal-Mecânico'),
    ('textil', 'Fábrica de Tecidos Inovação S.A.', '98.765.432/0001-11',
     '#7641-2025', 'maria.santos', 'textil2025', 89, 'Têxtil'),
    ('alimentos', 'Alimentos Sabor Brasil EIRELI', '45.678.912/0001-33',
     '#5532-2025', 'carlos.lima', 'alimentos2025', 203, 'Alimentício')
]

data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

for empresa in empresas_dados:
    try:
        cursor.execute('''
        INSERT INTO empresas (empresa_id, nome, cnpj, contrato, usuario, senha, vidas, setor, data_cadastro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (*empresa, data_atual))
        
        # Inserir status inicial
        cursor.execute('''
        INSERT INTO status_contratos (empresa_id, status_atual, pgr_gerado, data_atualizacao)
        VALUES (?, 'Aguardando M1', 0, ?)
        ''', (empresa[0], data_atual))
        
        # Inserir histórico inicial
        cursor.execute('''
        INSERT INTO historico_processos (empresa_id, data, evento, status)
        VALUES (?, '28/11/2025', 'Contrato Assinado', 'ok')
        ''', (empresa[0],))
        
        print(f"✅ Empresa '{empresa[1]}' cadastrada com sucesso!")
    except sqlite3.IntegrityError:
        print(f"⚠️  Empresa '{empresa[1]}' já existe no banco de dados.")

conn.commit()
conn.close()

print("\n🎉 Banco de dados criado e populado com sucesso!")
print("📂 Arquivo: sesi_conecta.db")
