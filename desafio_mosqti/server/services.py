import datetime
import json
import os
import tempfile
from typing import Literal, Optional

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gspread import Worksheet

# Constantes
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

SEARCH_RESULT_CPF_SHEET_NAME = "Buscas CPF"
SEARCH_RESULT_CNPJ_SHEET_NAME = "Buscas CNPJ"
DETAILS_SHEET_NAME = "Detalhes"
CREDS_PATH = "desafio_mosqti/server/creds.json"
GOOGLE_DRIVE_FOLDER_ID = "1EnLW2luuWHni9JHIsIFNvZ9rk-L31ren"

# Autenticação global gspread
creds = service_account.Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
client = gspread.authorize(creds)


def authenticate_google_drive():
    """
    Autentica e retorna credenciais para uso com a API do Google Drive.
    """
    return service_account.Credentials.from_service_account_file(
        CREDS_PATH, scopes=SCOPES
    )


def get_sheet_by_mode(mode: Literal["cpf", "cnpj"]) -> Worksheet:
    sheet_name = (
        SEARCH_RESULT_CPF_SHEET_NAME if mode == "cpf" else SEARCH_RESULT_CNPJ_SHEET_NAME
    )
    return client.open(sheet_name).sheet1


def add_search_result_register(
    *,
    identifier: str,
    data: dict,
    query: str,
    mode: Literal["cpf", "cnpj"],
    detail_register_id: Optional[str] = None,
) -> list:
    """
    Adiciona ou atualiza um registro de resultado de busca em uma planilha Google Sheets.

    Args:
        identifier (str): CPF ou CNPJ do registro.
        data (dict): Dados a serem registrados.
        query (str): Termo de busca original.
        mode (Literal["cpf", "cnpj"]): Modo de busca.
        detail_register_id (Optional[str]): ID do arquivo no Google Drive (detalhes).

    Returns:
        list: Linha adicionada ou atualizada na planilha.
    """
    sheet = get_sheet_by_mode(mode)
    existing_records = sheet.findall(identifier, in_column=1)
    row_index = None
    created_at = None

    if existing_records:
        row_index = existing_records[0].row
        created_at = sheet.cell(row_index, 3).value

    detail_url = (
        f"https://drive.google.com/file/d/{detail_register_id}/view"
        if detail_register_id
        else None
    )

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [
        identifier,
        query,
        now,  # atualizado em
        created_at if created_at else now,
        detail_url,
    ]

    if mode == "cpf":
        row.extend(
            [
                data.get("nome", ""),
                data.get("cpf", ""),
                data.get("beneficio_tipo", ""),
                data.get("url", ""),
            ]
        )
    else:
        row.extend(
            [
                data.get("nome", ""),
                data.get("cnpj", ""),
                data.get("grupo_natureza_jud", ""),
                data.get("url", ""),
            ]
        )

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    if row_index:
        sheet.update(f"A{row_index}:{alphabet[len(row) - 1]}{row_index}", [row])
    else:
        sheet.append_row(row)

    print(f"Registro adicionado/atualizado: {row}")
    return row


def upload_details_to_google_drive(
    data: dict, identifier: str, mode: Literal["cpf", "cnpj"]
) -> str:
    """
    Envia os detalhes coletados como arquivo JSON para o Google Drive.

    Args:
        data (dict): Conteúdo do JSON a ser enviado.
        identifier (str): CPF ou CNPJ.
        mode (Literal["cpf", "cnpj"]): Modo da operação.

    Returns:
        str: ID do arquivo no Google Drive.
    """
    creds = authenticate_google_drive()
    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": f"{identifier}_{mode}_details.json",
        "mimeType": "application/json",
        "parents": [GOOGLE_DRIVE_FOLDER_ID],
    }

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".json", mode="w", encoding="utf-8"
    ) as temp_file:
        json.dump(data, temp_file, ensure_ascii=False, indent=4)
        temp_file_path = temp_file.name

    media = MediaFileUpload(temp_file_path, mimetype="application/json")
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    file_id = file.get("id")

    print(f"Arquivo enviado: {file_id}")
    os.remove(temp_file_path)
    return file_id
