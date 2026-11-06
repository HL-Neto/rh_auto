from firebase_admin import firestore


def get_desligamentos():
    db = firestore.client()
    documentos = db.collection("desligamento").stream()

    registros = []

    for doc in documentos:
        dados = doc.to_dict() or {}
        dados["id"] = doc.id

        data = dados.get("carimbo_data_hora")
        if data:
            dados["carimbo_data_hora"] = data.isoformat()

        registros.append(dados)

    return registros


def get_contratacoes():
    db = firestore.client()
    documentos = db.collection("contratacoes").stream()

    registros = []

    for doc in documentos:
        dados = doc.to_dict() or {}
        dados["id"] = doc.id

        data = dados.get("contratacao_data")
        if data:
            dados["contratacao_data"] = data.isoformat()

        registros.append(dados)

    return registros