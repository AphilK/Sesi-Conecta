import pandas as pd
from datetime import datetime

# Planilha 1: CAMINHO FELIZ (todas as colunas corretas)
dados_corretos = {
    'Nome Completo': [
        'João Silva Santos',
        'Maria Oliveira Costa',
        'Pedro Henrique Souza',
        'Ana Paula Ferreira',
        'Carlos Eduardo Lima'
    ],
    'CPF': [
        '123.456.789-00',
        '234.567.890-11',
        '345.678.901-22',
        '456.789.012-33',
        '567.890.123-44'
    ],
    'Cargo': [
        'Operador de Máquinas',
        'Técnica de Segurança',
        'Soldador',
        'Analista de Qualidade',
        'Supervisor de Produção'
    ],
    'Data Nascimento': [
        '15/03/1985',
        '22/07/1990',
        '10/11/1982',
        '05/09/1995',
        '30/01/1978'
    ],
    'Descrição da Atividade': [
        'Opera prensas hidráulicas e realiza controle de qualidade das peças',
        'Fiscaliza uso de EPIs e realiza treinamentos de segurança',
        'Executa soldagem MIG/MAG em estruturas metálicas',
        'Realiza inspeção dimensional e testes de materiais',
        'Coordena equipe de produção e controla processos'
    ]
}

df_correto = pd.DataFrame(dados_corretos)
df_correto.to_excel('m1_funcionarios_correto.xlsx', index=False)
print("✅ Planilha CORRETA criada: m1_funcionarios_correto.xlsx")

# Planilha 2: ERRO POKA-YOKE (faltando coluna CPF)
dados_erro = {
    'Nome Completo': [
        'Ricardo Santos',
        'Juliana Pereira',
        'Fernando Alves'
    ],
    # CPF está ausente intencionalmente!
    'Cargo': [
        'Auxiliar de Produção',
        'Operadora de Empilhadeira',
        'Mecânico Industrial'
    ],
    'Data Nascimento': [
        '20/05/1988',
        '12/12/1992',
        '08/04/1980'
    ],
    'Descrição da Atividade': [
        'Auxilia no carregamento e organização de materiais',
        'Movimenta cargas e materiais com empilhadeira',
        'Realiza manutenção preventiva e corretiva de máquinas'
    ]
}

df_erro = pd.DataFrame(dados_erro)
df_erro.to_excel('m1_funcionarios_erro.xlsx', index=False)
print("❌ Planilha COM ERRO criada: m1_funcionarios_erro.xlsx")

print("\n📋 Instruções de Teste:")
print("1. Use 'm1_funcionarios_correto.xlsx' → Deve ser aceita ✅")
print("2. Use 'm1_funcionarios_erro.xlsx' → Deve ser rejeitada pelo Poka-Yoke ❌")
print("\n✨ NOVIDADE: Agora incluindo campo 'Descrição da Atividade' obrigatório!")
