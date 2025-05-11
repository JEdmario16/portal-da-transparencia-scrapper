from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse as Response 
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

from desafio_mosqti.core.filters import CNPJSearchFilter, CPFSearchFilter
from desafio_mosqti.core.filters.cnpj_search_filter import NaturezaJuridica
from desafio_mosqti.core.loger import logger as default_logger
from desafio_mosqti.core.portal_transparencia import PortalTransparencia
from desafio_mosqti.server.services import (add_search_result_register,
                                            upload_details_to_google_drive)

app = FastAPI()

app.mount("/docs-mkdocs", StaticFiles(directory="site", html=True), name="docs-mkdocs")
# app.mount("/", StaticFiles(directory="site", html=True), name="docs-mkdocs")

def store_records(
    records: list[dict],
    query: str,
    mode: str,
    extract_details: bool = False,
) -> None:
    """
    Armazena os registros de busca no Google Drive.

    Args:
        records (list[dict]): Lista de registros a serem armazenados.
        query (str): Consulta realizada.
        mode (str): Modo de busca, pode ser "cpf" ou "cnpj".
        extract_details (bool): Se `True`, extrai detalhes adicionais dos registros.

    """

    for r in records:
        if isinstance(r, BaseModel):
            r = r.dict()
        identifier = f"{r[mode]}_{r['nome']}"
        if extract_details:
            detail_register_id = upload_details_to_google_drive(
                data=r,
                identifier=identifier,
                mode=mode,
            )
        else:
            detail_register_id = None
        add_search_result_register(
            identifier=identifier,
            data=r,
            query=query,
            mode=mode,
            detail_register_id=detail_register_id,
        )


@app.get("/busca_cpf")
async def busca_cpf(
    query: str = Query(str),
    extract_details: Optional[bool] = False,
    search_result_limit: int = 10,
    store_data_in_gdrive: Optional[bool] = False,
    # filtros
    servidor_publico: Optional[bool] = False,
    beneficiario_programa_social: Optional[bool] = None,
    portador_cpgf: Optional[bool] = None,
    portador_cpdc: Optional[bool] = None,
    sancao_vigente: Optional[bool] = None,
    ocupante_imovel_funcional: Optional[bool] = None,
    possui_contrato: Optional[bool] = None,
    favorecido_recurso: Optional[bool] = None,
    emitente_nfe: Optional[bool] = None,
):
    """
    Busca informações no Portal da Transparência com base em CPF ou CNPJ informado.

    ### Parâmetros:
    - **query** (`str`, obrigatório): CPF, Nome ou NIS a ser pesquisado.
    - **search_result_limit** (`int`): Número máximo de resultados a serem retornados. Caso informado, a busca irá retornar os 'n' primeiros resultados. AVISO: Caso o número informado seja maior que o número de resultados disponíveis em uma página, os resultados serão limitados à página atual, a menos que a paginação seja forçada. Padrão: `10`.
    - **extract_details** (`bool`, opcional): Se `True`, extrai detalhes adicionais dos resultados. Padrão: `False`.
    - **search_result_limit** (`int`): Número máximo de resultados a serem retornados. Padrão: `10`.
    - **servidor_publico** (`bool`, opcional): Filtra por servidor público. Padrão: `None`.
    - **beneficiario_programa_social** (`bool`, opcional): Filtra por beneficiários de programas sociais. Padrão: `None`.
    - **portador_cpgf** (`bool`, opcional): Filtra por portadores do CPGF. Padrão: `None`.
    - **portador_cpdc** (`bool`, opcional): Filtra por portadores do CPDC. Padrão: `None`.
    - **sancao_vigente** (`bool`, opcional): Filtra por pessoas com sanções vigentes. Padrão: `None`.
    - **ocupante_imovel_funcional** (`bool`, opcional): Filtra por ocupantes de imóvel funcional. Padrão: `None`.
    - **possui_contrato** (`bool`, opcional): Filtra por pessoas com contratos com o governo. Padrão: `None`.
    - **favorecido_recurso** (`bool`, opcional): Filtra por favorecidos com recursos públicos. Padrão: `None`.
    - **emitente_nfe** (`bool`, opcional): Filtra por emitentes de Nota Fiscal Eletrônica. Padrão: `None`.

    ### Retorno:
    - `dict`: Um dicionário com os resultados encontrados no Portal da Transparência.

    ### Exemplo de uso:
    ```bash
    curl -X GET "http://localhost:8000/busca?query=12345678901&max_results=true&extract_details=false"
    ```
    """

    async with PortalTransparencia(headless=True) as portal:

        _filter = CPFSearchFilter(
            servidor_publico=servidor_publico,
            beneficiario_programa_social=beneficiario_programa_social,
            portador_cpgf=portador_cpgf,
            portador_cpdc=portador_cpdc,
            sancao_vigente=sancao_vigente,
            ocupante_imovel_funcional=ocupante_imovel_funcional,
            possui_contrato=possui_contrato,
            favorecido_recurso=favorecido_recurso,
            emitente_nfe=emitente_nfe,
        )
        if query == "''" or query == '""':
            query = ""

        try:
            result = await portal.search(
                query,
                mode="cpf",
                extract_details=extract_details,
                search_result_limit=search_result_limit,
                _filter=_filter,
            )
            result = [
                r.model_dump() if isinstance(r, BaseModel) else r
            for r in result
            ]
        except Exception as e:
            default_logger.error(f"Erro ao buscar CPF: {e}")
            default_logger.exception(e)
            return Response(
                content={
                    "error": "Não foi possível obter os resultados da busca devido a um erro interno. Tente novamente mais tarde.",
                    "details": str(e)
                },
                media_type="application/json",
                status_code=500,
            )

        if store_data_in_gdrive:
            # Adiciona os resultados ao banco de dados
            try:
                store_records(
                    records=result,
                    query=query,
                    mode="cpf",
                    extract_details=extract_details,
                )
            except Exception as e:
                default_logger.error(f"Erro ao adicionar registros ao banco de dados: {e}")
                default_logger.exception(e)
                return Response(
                    content={
                        "data": result,
                        "warning": f"Os dados foram obtidos, mas não foi possível armazená-los no banco de dados. {str(e)}"
                    },
                    media_type="application/json",
                    status_code=200,
                )
        return Response(
            content={"data": result},
            media_type="application/json",
            status_code=200,
        )


@app.get("/busca_cnpj")
async def busca_cnpj(
    query: str = Query(str),
    extract_details: Optional[bool] = False,
    search_result_limit: int = 10,
    # filtros
    tipo_natureza_juridica: Optional[int] = None,
    uf_pessoa_juridica: Optional[str] = None,
    municipio: Optional[str] = None,
    valor_gastos_diretos_de: Optional[float] = None,
    valor_gastos_diretos_ate: Optional[float] = None,
    valor_transferencia_de: Optional[float] = None,
    valor_transferencia_ate: Optional[float] = None,
    sancao_vigente: Optional[bool] = None,
    emitente_nfe: Optional[bool] = None,
):
    """
    Busca informações no Portal da Transparência com base em CPF ou CNPJ informado.

    ### Parâmetros:
    - **query** (`str`, obrigatório): CPF, Nome ou NIS a ser pesquisado.
    - **search_result_limit** (`int`): Número máximo de resultados a serem retornados. Caso informado, a busca irá retornar os 'n' primeiros resultados. AVISO: Caso o número informado seja maior que o número de resultados disponíveis em uma página, os resultados serão limitados à página atual, a menos que a paginação seja forçada. Padrão: `10`.
    - **extract_details** (`bool`, opcional): Se `True`, extrai detalhes adicionais dos resultados. Padrão: `False`.
    - **tipo_natureza_juridica** (`int`, opcional): Tipo de natureza jurídica da empresa. Padrão: `None`.
    - **uf_pessoa_juridica** (`str`, opcional): UF da pessoa jurídica da empresa no formato "XX". Ex: "SP", "RJ", "MG". Padrão: `None`.
    - **municipio** (`str`, opcional): Geocode do município da empresa, ex: "3304557" para o município do Rio de Janeiro. Veja: https://www.ibge.gov.br/explica/codigos-dos-municipios.php para mais detalhes. Padrão: `None`.
    - **valor_gastos_diretos_de** (`float`, opcional): Valor mínimo dos gastos diretos. Padrão: `None`.
    - **valor_gastos_diretos_ate** (`float`, opcional): Valor máximo dos gastos diretos. Padrão: `None`.
    - **valor_transferencia_de** (`float`, opcional): Valor mínimo da transferência. Padrão: `None`.
    - **valor_transferencia_ate** (`float`, opcional): Valor máximo da transferência. Padrão: `None`.
    - **sancao_vigente** (`bool`, opcional): Se o CNPJ está sob sanção vigente. Padrão: `None`.
    - **emitente_nfe** (`bool`, opcional): Se o CNPJ é emitente de NFE. Padrão: `None`.

    ### Retorno:
    - `dict`: Um dicionário com os resultados encontrados no Portal da Transparência.

    ### Exemplo de uso:
    ```bash
    curl -X GET "http://localhost:8000/busca_cnpj?query=12345678000195&max_results=true&extract_details=false"
    ```
    """

    async with PortalTransparencia(headless=True) as portal:

        _filter = CNPJSearchFilter(
            tipo_natureza_juridica=(
                tipo_natureza_juridica
                if tipo_natureza_juridica
                else NaturezaJuridica.TODOS
            ),
            uf_pessoa_juridica=uf_pessoa_juridica,
            municipio=municipio,
            valor_gastos_diretos_de=valor_gastos_diretos_de,
            valor_gastos_diretos_ate=valor_gastos_diretos_ate,
            valor_transferencia_de=valor_transferencia_de,
            valor_transferencia_ate=valor_transferencia_ate,
            sancao_vigente=sancao_vigente,
            emitente_nfe=emitente_nfe,
        )
        if query == "''" or query == '""':
            query = ""

        try:
            result = await portal.search(
                query,
                mode="cnpj",
                extract_details=extract_details,
                search_result_limit=search_result_limit,
                _filter=_filter,
            )
        except Exception as e:
            default_logger.error(f"Erro ao buscar CNPJ: {e}")
            default_logger.exception(e)
            return Response(
                content={
                    "error": "Não foi possível obter os resultados da busca devido a um erro interno. Tente novamente mais tarde."
                },
                media_type="application/json",
                status_code=500,
            )

        # Adiciona os resultados ao banco de dados
        try:
            store_records(
                records=result,
                query=query,
                mode="cnpj",
                extract_details=extract_details,
            )
        except Exception as e:
            default_logger.error(f"Erro ao adicionar registros ao banco de dados: {e}")
            default_logger.exception(e)
            return Response(
                content={
                    "data": result,
                    "warning": "Os dados foram obtidos, mas não foi possível armazená-los no banco de dados."
                },
                media_type="application/json",
                status_code=200,
            )

        return Response(
            content={"data": result},
            media_type="application/json",
            status_code=200,
        )
