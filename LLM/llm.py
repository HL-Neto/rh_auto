from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from TOOLS.tools import (
    add_UserTool,
    get_userTool,
    edit_Usertool,
    pdf_Reader
)

load_dotenv()


# ============================================================
# IA PARA PROCESSAR OS PDFs
# ============================================================

def llm_process():

    print("\n==============================")
    print("INICIANDO IA DOS PDFs")
    print("==============================")

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite"
    )

    prompt = """
Você é responsável por processar os dados de vendas dos vendedores.

OBJETIVO

1 - Utilize a ferramenta 'pdf_Reader' para buscar nos PDFs:
    - lista de vendedores
    - motos vendidas
    - quantidade de POPs
    - tipo de vendas
    - vendas no cartão
    - vendas em outras formas de pagamento

2 - Calcule corretamente:
    - quantidade total de motos vendidas
    - quantidade de POPs
    - vendas no cartão
    - vendas em outras formas

IMPORTANTE:

Se um vendedor possui 10 motos vendidas e 2 foram no cartão,
obrigatoriamente as outras vendas serão 8.

Portanto:

vendas_card + vendas_other = motos

3 - Depois de extrair os dados dos PDFs, utilize a ferramenta
'add_UserTool' para cadastrar os vendedores.

4 - NÃO invente informações.

5 - Só cadastre vendedores que possuam uma meta na lista abaixo.

6 - Compare os nomes ignorando diferenças entre letras maiúsculas,
minúsculas e acentos quando necessário.

7 - Depois dos cadastros, utilize 'get_userTool' para consultar
todos os vendedores cadastrados.

VENDEDORES E METAS

ALDAIR FERREIRA DA SILVA - 35
ALISSON VELOSO DA SILVA - 10
ANA KALYNE DA MATA - 15
ANDREZA ALMEIDA DA SILVA - 55
ARYLENNE ALVES DA COSTA - 35
CARLOS EDUARDO SILVA DOS SANTOS - 7
CLEONDES GEFFERSON FARIAS FERREIRA - 8
ELIONAI ANDERSON ELEUTERIO DE AQUINO - 20
HELLITON RODRIGUES DE ALENCAR - 10
JEFERSON CALDAS FELIPE DE FREITAS - 10
JOSE ELTON DO NASCIMENTO TEODOSIO - 30
JOSE ROBERTO DA SILVA - 16
KAREN JOSSANY RODRIGUES DO CARMO - 15
LAIS MENDONÇA AMORIM - 6
LEONARDO JOSE DA SILVA - 35
LUCAS ALBINO RIBEIRO - 7
LUCAS DE SOUZA DIAS - 4
LUIZ ANDRE FELINTO DA SILVA - 6
MARCIO DIAS DE ANDRADE - 8
MARCIO RUBENS FERREIRA DA SILVA - 6
MARCOS ANTONIO DOS SANTOS - 16
NICHOLLAS DEVID DE LIMA PONTES - 6
OTHAVIO AUGUSTO LEOCADIO SOUZA - 35
RENATA COSTA DA SILVA DOS SANTOS - 5
RHUANN CARLOS MARINHO DOS SANTOS - 8
SANDRA FERNANDES DOS SANTOS - 55
THIAGO IRINEU PESSOA - 8
VINICIUS BARBOSA DA SILVA - 8
VINICIUS GABRIEL DA SILVA - 8
WILSON ARAUJO DE OLIVEIRA - 10
"""

    print("\n[1] Prompt dos PDFs criado")

    agent = create_agent(
        model=model,
        tools=[
            add_UserTool,
            get_userTool,
            pdf_Reader
        ]
    )

    answer = agent.invoke({
        "messages": [
            ("system", prompt),
            (
                "user",
                "Leia os PDFs, extraia os dados dos vendedores, "
                "cadastre somente os vendedores que possuem meta "
                "e depois consulte os vendedores cadastrados."
            )
        ]
    })

    content = answer["messages"][-1].content

    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    print("\n==============================")
    print("RESPOSTA FINAL DA IA DOS PDFs")
    print("==============================")
    print(content)

    return str(content)


# ============================================================
# IA DE COMANDOS
# ============================================================

def command_process(context: str):

    print("\n==============================")
    print("INICIANDO IA DE COMANDOS")
    print("==============================")

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite"
    )

    prompt = f"""
Você é uma IA responsável pelo gerenciamento dos vendedores
armazenados no banco de dados.

Você só pode executar comandos relacionados ao banco de dados
de vendedores.

Ações permitidas:

1. CRIAR
2. DELETAR
3. EDITAR
4. CONSULTAR

Você possui as seguintes ferramentas:

- add_UserTool
- get_userTool
- edit_Usertool

NÃO utilize ferramentas relacionadas aos PDFs.

NÃO invente dados.

Se o usuário pedir para criar um vendedor, utilize
add_UserTool somente se todas as informações necessárias
estiverem disponíveis.

Se o usuário pedir para consultar vendedores, utilize
get_userTool.

Se o usuário pedir para editar um vendedor, utilize
edit_Usertool.

Se o usuário pedir para deletar um vendedor, informe que
a exclusão não está disponível nesta IA, caso não exista
uma ferramenta de exclusão disponível.

Se o comando não tiver relação com vendedores ou com
as operações CRIAR, DELETAR, EDITAR ou CONSULTAR,
responda:

"Não posso executar essa atividade. Posso apenas realizar
operações relacionadas aos vendedores no banco de dados."

COMANDO DO USUÁRIO:

{context}
"""

    print("\n[1] Prompt criado")
    print(prompt)

    agent = create_agent(
        model=model,
        tools=[
            add_UserTool,
            get_userTool,
            edit_Usertool
        ]
    )

    answer = agent.invoke({
        "messages": [
            ("system", prompt),
            ("user", context)
        ]
    })

    content = answer["messages"][-1].content

    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    print("\n==============================")
    print("RESPOSTA FINAL DA IA")
    print("==============================")
    print(content)

    return str(content)