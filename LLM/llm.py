from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from TOOLS.tools import add_UserTool, get_userTool

load_dotenv()


def llm(context):

    print("\n==============================")
    print("INICIANDO LLM")
    print("==============================")

    print("\n[1] Contexto recebido:")
    print(context)

    print("\n[2] Criando modelo Gemini...")

    model = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite"
    )

    print("[OK] Modelo criado")

    prompt = f"""
Você é responsável por processar relatórios de vendas de uma concessionária.

Sua tarefa é ler os dados dos relatórios fornecidos e cadastrar os vendedores
corretamente no banco de dados utilizando a ferramenta add_UserTool.

REGRAS:

1. Extraia exclusivamente os dados presentes nos relatórios.

2. Para cada os 5 primeiros vendedores, identifique:
   - Nome do vendedor
   - Quantidade de motos vendidas
   - Quantidade de POPs
   - Quantidade de pagamentos realizados no cartão
   - Quantidade de pagamentos realizados em outras formas

depois ignore o resto , sua missão foi concluida

3. Não invente nenhum dado.

4. Não altere os nomes dos vendedores.

5. Não crie vendedores que não estejam nos relatórios.

6. Não faça estimativas.

7. Caso algum dado não esteja presente ou não possa ser identificado,
   não invente um valor.

8. Utilize a ferramenta add_UserTool para cadastrar os dados no banco.

9. Antes de cadastrar, organize corretamente os dados de cada vendedor.

10. Processe todos os vendedores encontrados nos relatórios.

11. O documento possui várias páginas.
    Processe o documento de forma sequencial.


DADOS DOS RELATÓRIOS:

{context}
"""

    print("\n[3] Prompt criado")
    print("------------------------------")
    print(prompt)
    print("------------------------------")

    print("\n[4] Criando agente...")

    agent = create_agent(
        model=model,
        tools=[
            add_UserTool,
            get_userTool
        ]
    )

    print("[OK] Agente criado")

    print("\n[5] Enviando dados para a IA...")

    answer = agent.invoke({
        "messages": [
            ("system", prompt),
            ("user", context)
        ]
    })

    print("[OK] IA respondeu")

    print("\n[6] Resposta completa do agente:")
    print(answer)

    print("\n[7] Extraindo resposta final...")

    text = answer["messages"][-1].content

    print("\n==============================")
    print("RESPOSTA FINAL DA IA")
    print("==============================")

    print(text)

    print("\n==============================")
    print("LLM FINALIZADA")
    print("==============================")

    return text