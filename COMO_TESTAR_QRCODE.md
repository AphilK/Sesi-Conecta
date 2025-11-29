# 📱 Como Testar o QR Code no Hackathon

## 🎯 O Que é Esta Feature?

Cada PDF gerado (PGR e PCMSO) agora contém um **QR Code** que abre um **Dashboard Público** com:
- ✅ Métricas financeiras em tempo real (ROI, economia)
- ✅ Progresso do programa (%)
- ✅ Lista de exames agendados
- ✅ Informações da empresa

**Objetivo:** Mostrar inovação e conveniência - colaboradores/gestores podem acompanhar tudo pelo celular!

---

## 🚀 Como Demonstrar Durante o Pitch

### **Opção 1: Gerar PDF e Escanear QR Code Real**

1. **Faça login no sistema:**
   - Usuário: `metalurgica`
   - Senha: `metal123`

2. **Gere o PDF do PGR:**
   - Vá para aba "Ações Pendentes"
   - Clique em "Simular Avanço" até chegar em "PGR Aguardando Validação"
   - Clique em "📄 Baixar PGR"
   - Abra o PDF baixado

3. **Escaneie o QR Code:**
   - Use a câmera do celular
   - Aponta para o QR Code no final do PDF
   - Abre o dashboard público automaticamente! 📊

---

### **Opção 2: Simular Via URL (Sem Escanear)**

Se não tiver impressora ou celular disponível:

1. **Acesse diretamente a URL do dashboard:**
   ```
   http://localhost:8501/?empresa=metalurgica&view=dashboard
   ```

2. **Para outras empresas:**
   - TechBrasil: `?empresa=techbrasil&view=dashboard`
   - AlimentosBR: `?empresa=alimentosbr&view=dashboard`

---

## 💡 O Que os Jurados Verão

### **Dashboard Público Mostra:**

```
📊 Dashboard - MetalCorp Indústrias
Status: PGR Validado
-----------------------------------

💰 Impacto Financeiro
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ R$ 81.250   │ R$ 56.250   │ R$ 25.000   │    60%      │
│ Economia    │ Prevenção   │ Multas      │ Conformidade│
│ Total       │             │ Evitadas    │             │
└─────────────┴─────────────┴─────────────┴─────────────┘

📈 Progresso do Programa
████████████░░░░░░░░ 60% Concluído

📅 Exames Agendados
- João Silva | Admissional | 05/12/2025 | 14:00 | 🟢 Agendado
- Maria Santos | Periódico | 10/12/2025 | 09:30 | 🟢 Agendado
```

---

## 🎤 Script de Demonstração (30 segundos)

**Durante o pitch:**

> "E aqui está o diferencial: cada documento gerado tem um **QR Code inteligente**. 
> 
> _(mostra o PDF no telão)_
> 
> O colaborador ou gestor **escaneia com o celular** e abre instantaneamente um dashboard com:
> - Quanto a empresa está economizando
> - Quais exames estão agendados
> - Progresso do programa em tempo real
> 
> _(mostra o dashboard aberto no celular)_
> 
> Tudo sem login, sem app, sem complicação. **Transparência total na palma da mão!** 📱"

---

## 🏆 Por Que Isso Impressiona Jurados?

| Aspecto | Por Que é Forte |
|---------|----------------|
| **Inovação** | QR Code não é comum em sistemas de SST |
| **UX Excelente** | Zero fricção (não precisa login) |
| **Transparência** | Empresa mostra dados aos colaboradores |
| **Mobile-First** | Funciona em qualquer celular |
| **Wow Factor** | Visual impactante ao escanear |

---

## 🔧 Troubleshooting

### **QR Code não aparece no PDF?**
- Certifique-se que instalou: `pip install qrcode[pil]`
- Verifique que o app está rodando em `localhost:8501`

### **URL do QR Code não funciona?**
- O QR Code aponta para `localhost:8501`
- Funciona apenas na mesma rede
- Para demonstração em rede externa, use `ngrok` ou deploy em nuvem

### **Quer testar antes do hackathon?**
1. Gere o PDF
2. Use um leitor de QR Code online (qr-code-generator.com)
3. Copie a URL que aparece
4. Cole no navegador

---

## 📊 Métricas das 3 Empresas (para Validação)

### **MetalCorp (150 funcionários)**
- Economia Total: R$ 81.250/ano
- Status: 60% (PGR Validado)
- 2 exames agendados

### **TechBrasil (80 funcionários)**
- Economia Total: R$ 55.000/ano
- Status: Pode variar
- Login: `techbrasil` / `tech123`

### **AlimentosBR (200 funcionários)**
- Economia Total: R$ 100.000/ano
- Status: Pode variar
- Login: `alimentosbr` / `alimentos123`

---

## 🎯 Dica Final

**Durante a apresentação:**
- Tenha o PDF já aberto no telão
- Peça para um jurado escanear o QR Code com o celular dele
- Mostre a mágica acontecendo ao vivo!
- **"Vejam, em 2 segundos ele já está vendo os dados!"**

Isso cria um **momento memorável** que diferencia seu MVP! 🚀
