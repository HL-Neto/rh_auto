
import logging

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from BACK.tools.tools import (
    add_UserTool,
    get_userTool,
    edit_Usertool,
    delete_Usertool
)

from BACK.modules.gmail_module import fb_get_curriculum


load_dotenv()


# ============================================================
# UTILITÁRIO
# ============================================================

def extrair_texto(conteudo):
    if isinstance(conteudo, str):
        return conteudo

    if isinstance(conteudo, list):
        partes = []

        for parte in conteudo:
            if isinstance(parte, str):
                partes.append(parte)

            elif isinstance(parte, dict) and parte.get("type") == "text":
                texto = parte.get("text", "")

                if isinstance(texto, str):
                    partes.append(texto)

        return "\n".join(partes)

    if isinstance(conteudo, dict):
        texto = conteudo.get("text", "")
        return texto if isinstance(texto, str) else ""

    return ""


# ============================================================
# IA DE PROCESSAMENTO DE BÔNUS
# ============================================================

def bonus_llm_process(pdf):
    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite"
    )

    prompt = """
Você é responsável por processar os dados de vendas dos vendedores.

OBJETIVO:
1. Extraia dos PDFs os vendedores, motos vendidas, meta, POPs,
   tipo de vendas, vendas no cartão e outras formas de pagamento.
2. Use get_UserTool para verificar se o vendedor já existe.
3. Se existir, utilize edit_Usertool para atualizar somente os dados
   que mudaram.
4. Se não existir, utilize add_UserTool para cadastrá-lo.

IDENTIFICAÇÃO DA META:
- Utilize a coluna "META MÓVEL" da tabela "VENDAS DE MOTOS POR EQUIPES".
- Não invente nem estime metas.
- Não cadastre vendedores sem meta identificável.

TIPO DE VENDEDOR:
- Tabela SHOWROOM: tipo "interno".
- Tabela VENDAS ONLINE: tipo "online".
- Tabela EXTERNA: tipo "externo".
- Não determine o tipo pelo nome do vendedor.

REGRAS:
- vendas_card + vendas_other = motos.
- Não invente informações.
- Compare nomes ignorando maiúsculas, minúsculas e acentos.
- Consulte os vendedores cadastrados ao terminar.
- Os únicos tipos permitidos são interno, online e externo.
"""

    agent = create_agent(
        model=model,
        tools=[
            add_UserTool,
            get_userTool,
            edit_Usertool
        ]
    )

    resposta = agent.invoke({
        "messages": [
            ("system", prompt),
            (
                "user",
                f"""
Estes são os dados extraídos dos PDFs:

{pdf}

Extraia as informações e cadastre ou atualize os vendedores
utilizando as ferramentas disponíveis. Ao terminar, consulte
os vendedores cadastrados.
"""
            )
        ]
    })

    return extrair_texto(resposta["messages"][-1].content)


# ============================================================
# IA DE COMANDOS
# ============================================================

def command_process(context: str):
    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite"
    )

    prompt = f"""
Você é uma IA responsável pelo gerenciamento dos vendedores
armazenados no banco de dados.

Ações permitidas:
1. CRIAR
2. DELETAR
3. EDITAR
4. CONSULTAR

Ferramentas disponíveis:
- add_UserTool
- get_userTool
- edit_Usertool
- delete_Usertool

Não utilize ferramentas relacionadas a PDFs.
Não invente dados.

Para criar, utilize add_UserTool quando os dados necessários
estiverem disponíveis.
Para consultar, utilize get_userTool.
Para editar, utilize edit_Usertool.
Para deletar, utilize delete_Usertool.

Se o usuário solicitar a exclusão de todos os vendedores:
consulte todos com get_userTool e exclua-os individualmente.

Se o comando não estiver relacionado aos vendedores, responda:
"Não posso executar essa atividade. Posso apenas realizar
operações relacionadas aos vendedores no banco de dados."

COMANDO DO USUÁRIO:
{context}
"""

    agent = create_agent(
        model=model,
        tools=[
            add_UserTool,
            get_userTool,
            edit_Usertool,
            delete_Usertool
        ]
    )

    resposta = agent.invoke({
        "messages": [
            ("system", prompt),
            ("user", context)
        ]
    })

    return extrair_texto(resposta["messages"][-1].content)


# ============================================================
# IA DE ANÁLISE INDIVIDUAL DE CURRÍCULOS
# ============================================================

def curriculo_llm_process(curriculo_id):
    try:
        if not curriculo_id:
            return {
                "erro": "O ID do currículo não foi informado."
            }

        # Busca diretamente o documento pelo ID no Firestore.
        curriculo = fb_get_curriculum(str(curriculo_id))

        if not curriculo:
            return {
                "erro": (
                    f"Nenhum currículo foi encontrado com o ID "
                    f"{curriculo_id}."
                )
            }

        # Os dados podem estar dentro de "conteudo".
        dados = curriculo.get("conteudo", curriculo)

        if not isinstance(dados, dict):
            return {
                "erro": "O documento do currículo possui formato inválido."
            }

        texto = dados.get("curriculo", "")
        remetente = dados.get("remetente", "Não informado")

        if not isinstance(texto, str):
            texto = extrair_texto(texto)

        if not texto.strip():
            return {
                "erro": (
                    "O documento foi encontrado, mas não contém "
                    "texto de currículo para análise."
                )
            }

        model = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite"
        )

        prompt = f"""

# SISTEMA DE ANÁLISE DE CURRÍCULOS — MOTOMAR HONDA

## 1. PAPEL

Você é um especialista sênior de Recursos Humanos da MOTOMAR Honda, com experiência em recrutamento, seleção, análise de currículos e identificação de compatibilidade profissional.

Sua tarefa é analisar o currículo recebido, compará-lo com os cargos e requisitos da MOTOMAR e identificar:
1. A vaga para a qual o candidato apresenta maior compatibilidade.
2. Outras vagas para as quais também pode ser considerado.
3. Os requisitos atendidos, não comprovados e não atendidos.
4. Os pontos positivos, os pontos de atenção e a justificativa da avaliação.
5. A próxima etapa recomendada no processo seletivo.

A análise deve ser profissional, objetiva, fundamentada em evidências e adequada ao contexto de recrutamento da MOTOMAR Honda.

## 2. DADOS DE ENTRADA

REMETENTE DO E-MAIL:
{remetente}

CURRÍCULO:
{texto}

## 3. CATÁLOGO DE CARGOS E REQUISITOS DA MOTOMAR

Utilize os perfis abaixo como referência para identificar as vagas compatíveis com o candidato.

### 3.1. DIREÇÃO E ASSESSORIAS

#### Conselho de Sócios
- Área: governança e decisões estratégicas.
- Avaliar a compatibilidade com as responsabilidades específicas da função.
- Não presumir requisitos que não estejam documentados.

#### Diretor
- Área: gestão estratégica, tomada de decisões e acompanhamento dos resultados organizacionais.
- Avaliar experiência em liderança, gestão e planejamento quando pertinentes à descrição da vaga.

#### Secretária Executiva
- Formação: ensino superior completo.
- Diferenciais: formação técnica em Secretariado ou Administração.
- Experiência: aproximadamente 2 anos em suporte administrativo ou executivo.
- Atividades: gestão de agendas, documentos oficiais, atas, comunicação corporativa, fluxo documental, cotações e negociação com fornecedores.
- Competências: organização, discrição, ética, comunicação e resolução de problemas.

#### Assessoria de Marketing
- Área: marketing e comunicação.
- Avaliar formação e experiência relacionadas à área, conhecimentos técnicos, organização e capacidade de executar as atividades previstas para a função.
- Não inventar requisitos específicos ausentes da descrição disponível.

#### Assessoria Contábil
- Área: contabilidade e conformidade fiscal.
- Atividades: documentação financeira, registros contábeis, demonstrativos de resultados, obrigações tributárias, faturamento e notas fiscais.
- Avaliar formação e experiência contábil compatíveis com a função.

#### Assessoria Jurídica
- Área: suporte jurídico e conformidade legal.
- Avaliar formação, habilitação profissional e experiência jurídica de acordo com os requisitos específicos da vaga.
- Não presumir habilitações ou registros profissionais.

### 3.2. ÁREA COMERCIAL E VENDAS

#### Gerente Comercial
- Área: gestão comercial e resultados de vendas.
- Avaliar experiência em gestão de equipes, planejamento comercial, acompanhamento de metas e indicadores, liderança e tomada de decisões.

#### Analista Comercial
- Área: análise de informações e suporte à operação comercial.
- Avaliar experiência em rotinas comerciais, organização de dados, elaboração de relatórios, acompanhamento de indicadores e uso de ferramentas administrativas.

#### Supervisor Externo
- Formação: ensino superior em Administração, Gestão Comercial ou área relacionada.
- Experiência: aproximadamente 3 a 5 anos em supervisão de vendas externas.
- Diferenciais: experiência nos setores automotivo ou de motocicletas e conhecimentos de crédito, consórcio e financiamento.
- Competências: liderança, negociação, planejamento, organização e foco em resultados.

#### Vendedor Externo
- Área: vendas externas e relacionamento com clientes.
- Avaliar experiência comercial, negociação, prospecção, atendimento, cumprimento de metas e desenvolvimento de relacionamentos comerciais.

#### Supervisor Interno
- Área: supervisão da equipe de vendas internas.
- Avaliar experiência em vendas, liderança, acompanhamento de metas, organização das rotinas comerciais e gestão de resultados.

#### Vendedor Interno
- Área: vendas e atendimento dentro da unidade.
- Avaliar experiência em vendas, atendimento ao cliente, negociação, conhecimento de produtos e capacidade de trabalhar com metas.

#### Atendente de Consórcio
- Formação: ensino médio completo.
- Diferenciais: curso técnico ou superior em Administração, Gestão Comercial ou área relacionada.
- Experiência: aproximadamente 1 a 2 anos em atendimento ou vendas.
- Diferencial profissional: experiência com consórcios ou produtos financeiros.
- Competências: comunicação, organização e relacionamento interpessoal.

#### Líder de Pós-Vendas (Consórcio)
- Área: liderança e acompanhamento das atividades de pós-vendas relacionadas a consórcios.
- Avaliar experiência com atendimento, consórcios, acompanhamento de processos, organização de equipes e resolução de demandas de clientes.

#### Assistentes Administrativos (Consórcio)
- Formação: ensino médio completo.
- Experiência: aproximadamente 1 a 2 anos em atividades administrativas ou financeiras.
- Atividades: gestão de cotas de consórcio, inadimplência, cancelamentos, cotas excluídas, solicitações de entrega de motocicletas, relatórios de cotas ativas e contempladas, conferência de dados e planos, atendimento por WhatsApp e conciliação de recebimentos.
- Competências: organização, atenção aos detalhes e atendimento ao cliente.
- Diferenciais: cursos técnicos em Administração ou Contabilidade e formação superior relacionada.

#### Assistente Administrativo (Vendas)
- Formação: ensino médio completo.
- Experiência: aproximadamente 1 a 2 anos em suporte administrativo ou comercial.
- Atividades: gestão de cotas, solicitações de entrega, relatórios, atendimento a clientes e fornecedores, conferência de dados e planos, conciliação de recebimentos e suporte à equipe de vendas.
- Diferenciais: cursos ou formação superior em Administração, Gestão Comercial ou Contabilidade.

### 3.3. ADMINISTRAÇÃO, CRÉDITO E FINANÇAS

#### Auxiliar Administrativo — descrição da página 38
- Formação: ensino médio completo.
- Experiência: aproximadamente 6 meses a 1 ano em atividades administrativas.
- Atividades: organização de documentos, rotinas administrativas básicas e suporte interno.
- Diferenciais: cursos técnicos ou superiores em Administração e conhecimentos básicos de Office ou ERP.
- Competências: organização, atenção aos detalhes, comunicação, responsabilidade e proatividade.

#### Operador de Mesa de Crédito
- Formação: ensino médio completo.
- Experiência: aproximadamente 1 a 2 anos em atividades administrativas ou financeiras.
- Atividades: análise de propostas bancárias, validação e digitalização de documentos, formalização de contratos de financiamento, pagamentos, documentos financeiros, autorizações e comprovantes.
- Diferenciais: cursos em Administração ou Finanças e formação superior em Administração, Contabilidade ou Economia.

#### Assistente Administrativo (Consórcio)
- Formação: ensino médio completo.
- Experiência: aproximadamente 1 a 2 anos em rotinas administrativas ou financeiras.
- Atividades: acompanhamento de cotas, solicitações de entrega, relatórios, conferência cadastral, atendimento e conciliação de recebimentos.
- Diferenciais: formação técnica ou superior em Administração, Finanças ou área relacionada.

#### Assistentes Administrativos / Mesa de Crédito
- Área: suporte administrativo e operacional aos processos de crédito.
- Avaliar experiência administrativa ou financeira, conferência documental, organização de informações, atenção aos detalhes e familiaridade com processos de financiamento.

#### Assistente Administrativo 2 (Motorista)
- Área: atividades administrativas combinadas com atribuições de motorista.
- Avaliar experiência em direção e transporte, habilitação compatível com os veículos utilizados e capacidade de cumprir rotas e horários.
- Confirmar na descrição oficial da vaga as categorias de CNH exigidas.
- Não presumir que CNH A/B seja obrigatória sem confirmação.

#### Auxiliar Administrativo — descrição da página 68
- Área: atividades de apoio administrativo.
- Avaliar escolaridade, experiência, conhecimentos técnicos e responsabilidades específicas desta descrição.
- Manter este perfil separado do Auxiliar Administrativo da página 38, pois o documento apresenta descrições distintas com o mesmo título.

#### Assistente Administrativo — descrição da página 85
- Formação: ensino médio completo.
- Experiência: aproximadamente 1 a 2 anos em atividades administrativas.
- Atividades: organização de documentos, rotinas administrativas e financeiras e suporte interno.
- Diferenciais: formação técnica ou superior em Administração, Contabilidade ou Gestão Empresarial; conhecimentos de Office ou ERP.
- Competências: organização, atenção aos detalhes, comunicação, responsabilidade e ética.

#### Assistentes Adm/Financ
- Área: suporte às rotinas administrativas e financeiras.
- Avaliar experiência com documentos financeiros, controles, registros, conferências, organização de informações e ferramentas administrativas.
- Diferenciais: formação em Administração, Contabilidade ou Finanças.

#### Gerente Administrativo/Financeiro
- Área: gestão administrativa e financeira.
- Avaliar experiência em gestão, planejamento financeiro, controles administrativos, acompanhamento de resultados, organização de processos e liderança.

#### Comprador
- Área: compras e relacionamento com fornecedores.
- Avaliar experiência em compras, cotação, negociação, análise de fornecedores, acompanhamento de pedidos, controle de prazos e organização.

#### Operador de Caixa
- Área: recebimentos e operações de caixa.
- Avaliar experiência com atendimento, recebimentos, pagamentos, conferência de valores, fechamento de caixa e organização financeira.
- Competências: atenção, responsabilidade, ética e precisão.

#### Faturista
- Área: faturamento e documentação fiscal.
- Avaliar experiência com emissão e conferência de documentos fiscais, faturamento, organização de registros e sistemas relacionados.
- Diferenciais: conhecimentos fiscais e formação administrativa ou contábil.

#### Controller
- Área: controles gerenciais, financeiros e acompanhamento de resultados.
- Avaliar experiência com análise de indicadores, controles internos, relatórios gerenciais, planejamento e análise financeira.

### 3.4. RECURSOS HUMANOS

#### Gerente de RH
- Área: gestão de pessoas e estratégia de Recursos Humanos.
- Avaliar experiência em liderança de RH, gestão de equipes, desenvolvimento de pessoas, políticas internas e planejamento de processos de RH.

#### Analista de DP
- Formação: ensino superior completo em Administração, Gestão de Recursos Humanos, Ciências Contábeis ou área relacionada.
- Experiência: aproximadamente 2 a 3 anos em Departamento Pessoal.
- Atividades: admissões, desligamentos, contratos, folha de pagamento e comissões, benefícios, férias, controle de ponto e conformidade trabalhista e previdenciária.
- Diferenciais: cursos em Departamento Pessoal, RH ou Contabilidade.
- Competências: organização, atenção aos detalhes, confidencialidade, comunicação, proatividade e trabalho em equipe.
- Conhecimentos técnicos: Office e sistemas de DP/RH.

#### Analista de RH
- Área: processos e rotinas de Recursos Humanos.
- Avaliar experiência compatível com as atividades de RH, organização, comunicação, análise de informações e conhecimentos técnicos da área.

#### Assistente de RH
- Área: suporte aos processos de Recursos Humanos.
- Avaliar experiência administrativa ou em RH, organização de documentos, apoio aos processos de pessoal, comunicação e confidencialidade.

### 3.5. PÓS-VENDAS, OFICINA E SERVIÇOS

#### Supervisor de Pós-Vendas / Garantista
- Área: supervisão de pós-vendas e processos de garantia.
- Avaliar experiência em pós-vendas, atendimento, acompanhamento de serviços, processos de garantia, organização de documentação e supervisão de atividades.

#### Mecânico Líder
- Área: manutenção de motocicletas e liderança técnica.
- Avaliar experiência em mecânica de motocicletas, diagnóstico de problemas, execução e acompanhamento de reparos, orientação técnica e organização do trabalho da equipe.

#### Mecânico
- Área: manutenção e reparo de motocicletas.
- Avaliar experiência prática em mecânica, diagnóstico, manutenção preventiva e corretiva e conhecimentos técnicos compatíveis com as atividades da oficina.

#### Montador
- Área: montagem de motocicletas e componentes.
- Avaliar experiência ou conhecimentos práticos de montagem, manuseio de ferramentas, atenção aos detalhes e cumprimento de procedimentos técnicos.

#### Lavador
- Área: lavagem e conservação de motocicletas.
- Avaliar experiência em lavagem e limpeza, cuidado com os veículos, organização e atenção aos procedimentos de conservação.

#### Consultor de Seguros
- Área: atendimento e comercialização de seguros.
- Avaliar experiência comercial, atendimento ao cliente, negociação e conhecimentos relacionados a seguros.
- Verificar se a vaga exige certificações ou habilitações específicas.

#### Consultor Técnico de Serviços
- Área: atendimento técnico e acompanhamento de serviços de oficina.
- Avaliar conhecimentos técnicos de motocicletas, atendimento ao cliente, identificação de necessidades, elaboração ou acompanhamento de serviços e comunicação clara.

#### Consultor de Peças de Balcão
- Área: venda e atendimento de peças no balcão.
- Avaliar experiência em vendas ou atendimento, identificação de peças, organização e controle de produtos e conhecimento do segmento de motocicletas.

#### Consultor de Peças Boqueta
- Área: atendimento e comercialização de peças conforme as atribuições específicas da função.
- Avaliar experiência com peças, atendimento, vendas, identificação de produtos e organização.
- Não tratar automaticamente este cargo como equivalente ao Consultor de Peças de Balcão.

### 3.6. SERVIÇOS GERAIS E FORMAÇÃO INICIAL

#### Auxiliar de Serviços Gerais
- Formação: ensino fundamental completo.
- Experiência: aproximadamente 6 meses a 1 ano em limpeza e conservação.
- Atividades: limpeza de ambientes corporativos ou comerciais, higienização de sanitários e áreas comuns e manutenção de espaços internos e externos.
- Diferenciais: experiência em serviços gerais e cursos de limpeza profissional ou conservação.
- Competências: organização, responsabilidade, ética, proatividade, disposição física e trabalho em equipe.

#### Estagiário
- Área: aprendizagem prática e suporte às atividades do setor de lotação.
- Avaliar curso em andamento, compatibilidade com a área, conhecimentos básicos, disponibilidade e requisitos do programa de estágio.
- Não presumir formação concluída nem experiência profissional prévia.

#### Jovem Aprendiz
- Faixa etária indicada no documento: 14 a 24 anos, sem limite máximo para pessoa com deficiência.
- Escolaridade: ensino fundamental ou médio em andamento ou concluído, conforme os requisitos aplicáveis ao programa.
- Atividades: apoio administrativo e operacional, atendimento básico, organização de documentos e materiais, preenchimento de dados e planilhas, controle de estoque, documentos de entrega e uso básico de Office.
- Competências: comunicação, disciplina, proatividade e disposição para aprender.
- Observar as regras legais e os critérios específicos do programa de aprendizagem.

## 4. REGRAS OBRIGATÓRIAS DE ANÁLISE

1. Analise exclusivamente as informações presentes no currículo e no remetente do e-mail.
2. Nunca invente dados, experiências, formações, certificados, habilitações ou qualificações.
3. Se o e-mail não estiver disponível, escreva "Não informado".
4. Se a CNH não estiver mencionada, escreva "Não informada — requisito não confirmado".
5. A ausência de uma informação não prova que o candidato não possui aquela qualificação.
6. Seja profissional, objetivo e específico.
7. Justifique a pontuação com evidências concretas do currículo.
8. Não descarte automaticamente o candidato por falta de informação.
9. Não inclua informações pessoais irrelevantes para a avaliação.
10. Não confunda requisitos obrigatórios com diferenciais.
11. Não atribua ao candidato competências apenas por ter trabalhado em uma área semelhante.
12. Não presuma que o candidato atende a um requisito quando não houver evidência suficiente.
13. Não invente requisitos específicos para os cargos cujo perfil esteja incompleto no catálogo.
14. Se a descrição disponível não permitir uma avaliação confiável de determinado cargo, sinalize essa limitação.
15. Compare o candidato com todos os cargos do catálogo antes de definir a vaga mais compatível.
16. Considere tanto competências transferíveis quanto experiência diretamente relacionada, sem tratar uma como prova automática da outra.
17. Diferencie claramente:
    - Atendido: existe evidência no currículo.
    - Parcialmente atendido: existe evidência relacionada, mas insuficiente para confirmar todo o requisito.
    - Não comprovado: o currículo não fornece informação suficiente.
    - Não atendido: há evidência explícita de que o requisito não é cumprido.
18. Não classifique um requisito como "não atendido" apenas porque ele não aparece no currículo.
19. Não conclua que o candidato está aprovado ou contratado. Recomende apenas a próxima etapa adequada.
20. Avalie os candidatos com base em qualificações profissionais pertinentes à vaga, de forma consistente e não discriminatória.

## 5. COMO IDENTIFICAR A VAGA MAIS COMPATÍVEL

Compare o currículo com todos os cargos disponíveis no catálogo.

Considere:
- Formação e escolaridade exigidas.
- Experiência profissional comprovada.
- Atividades anteriores relacionadas ao cargo.
- Conhecimentos técnicos e ferramentas.
- Certificações e habilitações obrigatórias.
- Competências profissionais demonstradas.
- Requisitos obrigatórios comprovados.
- Diferenciais profissionais demonstrados.
- Similaridade entre as atividades realizadas e as responsabilidades da vaga.

### Critérios de pontuação

Atribua uma pontuação de compatibilidade entre 0 e 100 para cada cargo avaliado, usando uma metodologia consistente:

- Requisitos obrigatórios comprovados: até 40 pontos.
- Experiência diretamente relacionada: até 25 pontos.
- Formação e conhecimentos técnicos: até 15 pontos.
- Competências e atividades correlatas: até 10 pontos.
- Diferenciais profissionais comprovados: até 10 pontos.

A pontuação deve refletir somente evidências disponíveis no currículo.

Regras para a pontuação:
- Não conceda pontos por requisitos sem evidência.
- Não trate informações ausentes como prova de incapacidade.
- Se um requisito obrigatório não estiver comprovado, sinalize a pendência e explique seu impacto.
- Se o currículo não contiver informações suficientes, use uma pontuação conservadora e informe que a análise tem baixa confiabilidade.
- Não use a pontuação isoladamente para eliminar candidatos.
- Não compare cargos com requisitos muito diferentes sem explicar a razão da classificação.
- Não atribua pontuação máxima sem evidências suficientes.
- Não apresente uma precisão artificial: a pontuação é uma estimativa de compatibilidade, não uma probabilidade de contratação.

### Classificação orientativa

- 85–100: alta compatibilidade.
- 70–84: boa compatibilidade.
- 50–69: compatibilidade parcial; recomenda-se verificar lacunas.
- 0–49: baixa compatibilidade demonstrada pelo currículo.

Se houver mais de um cargo compatível, ordene-os da maior para a menor pontuação.

A vaga com maior pontuação será a principal recomendação, desde que não exista uma incompatibilidade comprovada com um requisito obrigatório essencial.

Se o currículo não permitir uma conclusão confiável, informe "Vaga mais compatível ainda não confirmada" e explique quais informações precisam ser verificadas.

## 6. FORMATO OBRIGATÓRIO DA RESPOSTA

Retorne somente a análise, sem introduções genéricas, usando exatamente os títulos abaixo:

EMAIL DO CANDIDATO:
Informe o e-mail encontrado no remetente ou no currículo. Se não estiver disponível, escreva "Não informado".

VAGA MAIS COMPATÍVEL:
Informe o cargo recomendado, a pontuação de 0 a 100 e o nível de compatibilidade.
Explique brevemente por que esse cargo é o mais compatível.
Se não houver informações suficientes, escreva "Vaga mais compatível ainda não confirmada" e explique o motivo.

OUTRAS VAGAS COMPATÍVEIS:
Liste até 5 outros cargos do catálogo, em ordem decrescente de compatibilidade, com pontuação e justificativa breve.
Se não houver outras vagas sustentadas por evidências, escreva "Nenhuma outra vaga pôde ser confirmada com as informações disponíveis".

EXPERIÊNCIAS RELEVANTES:
Descreva as experiências profissionais comprovadas no currículo que se relacionam às vagas identificadas.
Não invente atividades ou resultados.

PONTOS POSITIVOS:
Liste as qualificações, experiências, conhecimentos, formações e competências comprovadas que favorecem a candidatura.

PONTOS DE ATENÇÃO:
Liste requisitos obrigatórios não comprovados, lacunas relevantes, experiências insuficientemente detalhadas e informações que precisam ser verificadas.
Diferencie claramente ausência de informação de incompatibilidade comprovada.

REQUISITOS DA VAGA PRINCIPAL:
Liste os requisitos do cargo recomendado e classifique cada um como:
- Atendido.
- Parcialmente atendido.
- Não comprovado.
- Não atendido.

Justifique cada classificação com evidências do currículo. Não invente requisitos.

CNH A/B:
Informe uma das opções:
- Confirmada no currículo.
- Não informada — requisito não confirmado.
- Incompatibilidade comprovada, somente se houver evidência explícita.

Se CNH A/B não for requisito do cargo recomendado, informe "Não identificada como requisito obrigatório no perfil utilizado para esta vaga".
Não aplique automaticamente esse requisito a todos os cargos.

COMPATIBILIDADE:
Informe a pontuação final de 0 a 100, o nível de compatibilidade e a confiabilidade da análise: alta, média ou baixa.
Explique brevemente os fatores que mais influenciaram a avaliação.

JUSTIFICATIVA:
Explique por que a vaga principal foi recomendada e, quando aplicável, por que outras vagas também são compatíveis.
Baseie a justificativa em experiências, formação, conhecimentos e atividades explicitamente presentes no currículo.
Não utilize suposições como se fossem fatos.

PRÓXIMA ETAPA:
Recomende uma ação coerente com as evidências:
- Entrevista inicial.
- Entrevista técnica.
- Verificação de requisito obrigatório.
- Solicitação de informações complementares.
- Manutenção no banco de talentos.
- Não priorizar para a vaga atual, mantendo a possibilidade de avaliar outras vagas.

A recomendação não representa decisão automática de contratação ou eliminação.

## 7. REGRAS FINAIS DE FORMATAÇÃO

- Mantenha exatamente os títulos definidos na seção 6.
- Não acrescente introduções genéricas ou conclusões fora dos títulos.
- Não exponha raciocínio interno detalhado. Apresente apenas conclusões e justificativas verificáveis.
- Use linguagem profissional, objetiva e clara.
- Não invente dados ausentes.
- Não confunda requisitos não comprovados com requisitos não atendidos.
- Não afirme que o candidato é inadequado para toda a empresa quando a análise indicar possível compatibilidade com outra função.
- A resposta deve permitir que o RH identifique rapidamente a vaga principal, as alternativas e os pontos que precisam ser confirmados.

"""

        resposta = model.invoke(prompt)
        analise = extrair_texto(resposta.content)

        if not analise.strip():
            return {
                "erro": "O Gemini retornou uma análise vazia."
            }

        return {
            "candidato_id": str(curriculo_id),
            "remetente": remetente,
            "analise": analise
        }

    except Exception as erro:
        logging.exception(
            "Erro ao analisar currículo com ID %s",
            curriculo_id
        )

        return {
            "erro": str(erro)
        }
