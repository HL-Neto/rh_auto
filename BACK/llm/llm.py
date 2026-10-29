
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
Você é um profissional de Recursos Humanos da MOTOMAR Honda.
Analise este currículo para a vaga de Assistente da Administração.

REQUISITOS DA VAGA:
- CNH A/B: requisito obrigatório.
- Experiência com entregas: diferencial.
- Transporte de motocicletas entre unidades.
- Cumprimento de rotas e cronogramas.
- Carregamento e descarregamento de veículos.

REMETENTE DO E-MAIL:
{remetente}

CURRÍCULO:
{texto}

REGRAS OBRIGATÓRIAS:
1. Analise exclusivamente as informações presentes no currículo.
2. Nunca invente dados, experiências ou qualificações.
3. Se o e-mail não estiver disponível, escreva "Não informado".
4. Se a CNH não estiver mencionada, escreva
   "Não informada — requisito não confirmado".
5. A ausência de informação não prova que o candidato não possui
   aquela qualificação.
6. Seja profissional, objetivo e específico.
7. Justifique a pontuação com evidências do currículo.
8. Não descarte automaticamente o candidato por falta de informação.
9. Não inclua informações pessoais irrelevantes para a avaliação.
10. Retorne somente a análise, sem introduções genéricas.

FORMATO OBRIGATÓRIO:

EMAIL DO CANDIDATO:
Informe o e-mail encontrado ou "Não informado".

EXPERIÊNCIAS RELEVANTES:
Liste experiências relacionadas à vaga.

PONTOS POSITIVOS:
Liste qualificações, experiências e habilidades comprovadas.

PONTOS DE ATENÇÃO:
Liste requisitos que precisam ser confirmados e lacunas relevantes.
Não trate informações ausentes como prova de incapacidade.

CNH A/B:
Informe se está confirmada, não foi mencionada ou há outra
informação explícita.

COMPATIBILIDADE:
Informe uma pontuação de 0 a 100, seguida de "/100".

JUSTIFICATIVA:
Explique brevemente a pontuação com base nos requisitos.

PRÓXIMA ETAPA:
Sugira o que o recrutador deve confirmar durante o contato
ou a entrevista.

Mantenha exatamente esses títulos.
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
