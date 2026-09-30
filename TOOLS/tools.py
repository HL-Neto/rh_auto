from langchain_core.tools import tool
from MODULLES.module import get_user, add_user, edit_user , calc
              

@tool
def calc_UserTool(meta:int , vendas: int, vendas_card: int, vendas_other: int) -> int:
    
    """Calcula o bônus do vendedor quando a quantidade de vendas ultrapassa a meta."""
    return calc(vendas , meta,  vendas_card, vendas_other)


@tool 
def get_userTool():

    """ Busca todos os vendedores dentro do banco de dados """
    
    return get_user("all")

@tool 
def add_UserTool(nome:str , meta:int , motos:int, pops:int, vendas_card:int , vendas_other:int):
    """Adiciona um novo vendedor ao banco de dados."""
    
    return add_user(nome, meta, motos, pops, vendas_card, vendas_other)

@tool 
def edit_Usertool(nome:str , meta:int , motos:int, pops:int, vendas_card:int , vendas_other:int):
    """ Edita um usário dentro do banco de dados"""
    return edit_user(nome, meta, motos, pops, vendas_card, vendas_other)
