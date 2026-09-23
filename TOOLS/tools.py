from langchain_core.tools import tool
from MODULLES.module import get_user, add_user
              

@tool
def calc(meta:int , vendas: int, vendas_card: int, vendas_other: int) -> int:
    
    """Calcula o bônus do vendedor quando a quantidade de vendas ultrapassa a meta."""
    if vendas >= meta :
        
        vendas_card_bonus = vendas_card * 15
        vendas_other_bonus = vendas_other * 30
        
        total = vendas_other_bonus + vendas_card_bonus 
        
        
        return total
    
    return 0


@tool 
def get_userTool():

    """ Busca todos os vendedores dentro do banco de dados """
    
    return get_user("all")

@tool 
def add_UserTool(nome:str , meta:int , motos:int, pops:int, vendas_card:int , vendas_other:int):
    """Adiciona um novo vendedor ao banco de dados."""
    
    return add_user(nome, meta, motos, pops, vendas_card, vendas_other)
        
