from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from TOOLS.tools import add_UserTool, get_userTool , edit_Usertool

load_dotenv()

def llm(context):

    print("\n==============================")
    print("INICIANDO LLM")
    print("==============================")

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite"
    )

    prompt = f""" ultilize a ferramenta edit_Usertool para colocar as metas nos respectivos usuários
VENDEDORES	META DE MOTOS
ALDAIR FERREIRA DA SILVA	35
ALISSON VELOSO DA SILVA	10
ANA KALYNE DA MATA	15
ANDREZA ALMEIDA DA SILVA	55
ARYLENNE ALVES DA COSTA	35
CARLOS EDUARDO SILVA DOS SANTOS	7
CLEONDES GEFFERSON FARIAS FERREIRA	8
ELIONAI ANDERSON ELEUTERIO DE AQUINO	20
HELLITON RODRIGUES DE ALENCAR	10
JEFERSON CALDAS FELIPE DE FREITAS	10
JOSE ELTON DO NASCIMENTO TEODOSIO	30
JOSE ROBERTO DA SILVA	16
KAREN JOSSANY RODRIGUES DO CARMO	15
LAIS MENDONÇA AMORIM	6
LEONARDO JOSE DA SILVA	35
LUCAS ALBINO RIBEIRO	7
LUCAS DE SOUZA DIAS	4
LUIZ ANDRE FELINTO DA SILVA	6
MARCIO DIAS DE ANDRADE	8
MARCIO RUBENS FERREIRA DA SILVA	6
MARCOS ANTONIO DOS SANTOS	16
NICHOLLAS DEVID DE LIMA PONTES	6
OTHAVIO AUGUSTO LEOCADIO SOUZA	35
RENATA COSTA DA SILVA DOS SANTOS	5
RHUANN CARLOS MARINHO DOS SANTOS	8
SANDRA FERNANDES DOS SANTOS	55
THIAGO IRINEU PESSOA	8
VINICIUS BARBOSA DA SILVA	8
VINICIUS GABRIEL DA SILVA	8
WILSON ARAUJO DE OLIVEIRA	10

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
            ("user", "Processe os dados dos PDFs e atualize o banco de dados.")
        ]
    })

    text = answer["messages"][-1].content

    print("\n==============================")
    print("RESPOSTA FINAL DA IA")
    print("==============================")
    print(text)

    return text