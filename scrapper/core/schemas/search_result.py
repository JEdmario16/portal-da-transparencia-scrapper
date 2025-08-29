from typing import Any, Literal

from pydantic import BaseModel


class CpfSearchResult(BaseModel):
    """
    Esquema para representar o resultado da busca de CPF, retornado por scrapper.core.crawlers.searcher.Searcher
    """

    nome: str
    """
    Nome do beneficiário.
    """

    url: str
    """
    URL do resultado da busca.
    """

    cpf: str
    """
    6 digítos centrais do CPF. Ex: ***.123.456-**
    """

    beneficio_tipo: str
    """
    Tipo de benefício.
    """

    details: dict[str, Any] | None = None
    """
    Detalhes adicionais sobre o beneficiário, se disponíveis.
    """

    details_links: dict[str, str] | None = None
    """
    Links para detalhes adicionais, se disponíveis.
    """


class CnpjSearchResult(BaseModel):
    """
    Esquema para o resultado da busca de CNPJ.
    """

    nome: str
    """
    Nome da empresa.
    """

    url: str
    """
    URL do resultado da busca.
    """

    cnpj: str
    """
    CNPJ da empresa, formatado como 00.000.000/0000-00.
    """
    grupo_natureza_jud: str
    """
    Grupo de natureza jurídica da empresa.
    """
    muni_uf: str
    """
    Município e UF da empresa, formatado como "Município/UF".
    """

    details: dict[str, Any] | None = None
    """
    Detalhes adicionais sobre a empresa, se disponíveis.
    """

    details_links: dict[str, str] | None = None
    """
    Links para detalhes adicionais, se disponíveis.
    """
