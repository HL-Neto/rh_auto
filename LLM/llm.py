from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from TOOLS.tools import (add_UserTool, get_userTool, edit_Usertool, pdf_Reader, delete_Usertool)

load_dotenv()

"""
    AS LLMS ULTILIZADAS
    basicamente temos duas llms , uma para o processessamento dos dados dentro do pdf , e a outra para auxilio do usuário
    ambos pussem a capacidade de alterar o banco de dados, cada um com suas limmitações

"""

def llm_process():



    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite"
    )

    prompt = """
    
        Você é responsável por processar os dados de vendas dos vendedores.

        OBJETIVO
        
        
        1 - Utilize a ferramenta 'pdf_Reader' para buscar nos PDFs:
            - lista de vendedores
            - motos vendidas
            - meta
            - quantidade de POPs
            - tipo de vendas
            - vendas no cartão
            - vendas em outras formas de pagamento
        
        2 - Ultilize a ferramente get_Usertool 
            - verifique se o vendedor ja existe no banco de dados
            - se ja existir , invés de adicionar , você vai ultilizar a ferramente edit_Usertool
            para adicionar as novas informações desse usuário, altere só as informações que diferem das nova
            
            exemplo: um vendedor joão da silva, ele ja existe no banco de dados , a meta dele ta diferente da
            meta antiga, os outros dados são o mesmo,  então altere só a meta.
            
        3 - Ultilize a ferramenta add_UserTool passando todos os dados que você encontrou de forma correta :
            - quantidade total de motos vendidas
            - meta
            - quantidade de POPs
            - vendas no cartão
            - vendas em outras formas
            
        4 — IDENTIFICAÇÃO DA META

        Para cada vendedor encontrado no PDF **"VENDAS DE MOTOS POR EQUIPES"**, localize a coluna **"META MÓVEL"** correspondente ao vendedor.

        Utilize o valor encontrado em  "META MÓVEL" como a meta de motos do vendedor.
        A meta deve ser associada ao vendedor correto, respeitando a tabela/equipe em que ele aparece.
        Não invente, estime ou calcule uma meta caso ela não esteja informada no PDF.
        Se o vendedor não possuir uma **"META MÓVEL"** identificável, não cadastre esse vendedor no banco de dados.

        5 — CLASSIFICAÇÃO DO TIPO DE VENDEDOR

        Existem somente 3 tipos de vendedores no sistema:

          `interno`
          `online`
          `externo`

        A classificação deve ser feita de acordo com o **título da tabela/equipe** em que o vendedor aparece no PDF.

        ### Regras obrigatórias:

        Se o vendedor estiver na tabela **"SHOWROOM"**, defina:
        `tipo = "interno"`

        Se o vendedor estiver na tabela **"VENDAS ONLINE"**, defina:
        `tipo = "online"`

        Se o vendedor estiver na tabela **"EXTERNA"**, defina:
        `tipo = "externo"`

        IMPORTANTE:

        Não classifique o tipo pelo nome do vendedor.
        Não faça suposições sobre o tipo.
        O tipo deve ser determinado exclusivamente pela tabela/equipe onde o vendedor foi encontrado.
        Se o vendedor aparecer em mais de uma tabela, considere a tabela correspondente aos dados que estão sendo processados e mantenha a classificação consistente.
        Os valores aceitos para o campo `tipo` são **somente**: `interno`, `online` ou `externo`.
        Nunca utilize outros valores como `"showroom"`, `"vendas online"` ou `"externa"` no campo `tipo`.

        
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

        
        
         
    """

    print("\n[1] Prompt dos PDFs criado")

    agent = create_agent(
        model=model,
        tools=[
            add_UserTool,
            get_userTool,
            pdf_Reader,
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
    
    " formatação da resposta da llm"
    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )
        

    return str(content)


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
        - delete_userTool

        NÃO utilize ferramentas relacionadas aos PDFs.

        NÃO invente dados.

        Se o usuário pedir para criar um vendedor, utilize
        add_UserTool somente se todas as informações necessárias
        estiverem disponíveis.

        Se o usuário pedir para consultar vendedores, utilize
        get_userTool.

        Se o usuário pedir para editar um vendedor, utilize
        edit_Usertool.
        
        
        Se o usuário pedir para delettar um vendedor, utilize
        delete_Usertool.
        
        Se  o usuário desejar deletar todo o banco de dados , ultilize a ferramente get_userTool para pegar todos os nomes dos vendedores no banco de dados , 
        depois ultilize a ferramenta delete_userTool passando o nome de cada vendedor para excluir um por um

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
            edit_Usertool,
            delete_Usertool
        ]
    )

    answer = agent.invoke({
        "messages": [
            ("system", prompt),
            ("user", context)
        ]
    })

    content = answer["messages"][-1].content

    "formatação da resposta da ia"
    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    return str(content)