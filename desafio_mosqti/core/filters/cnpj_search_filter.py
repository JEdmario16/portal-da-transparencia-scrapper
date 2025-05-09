from enum import Enum

from desafio_mosqti.core.filters import base_filter


class NaturezaJuridica(Enum):
    """
    Enumeração para os tipos de natureza jurídica.
    """

    TODOS = 0
    ADMINISTRACAO_PUBLICA = 1
    ENTIDADES_EMPRESARIAIS = 2
    ENTIDADES_SEM_FINS_LUCRO = 3
    ORGANIZACAO_INTERNACIONAL = 4


class GrupoObjeto(Enum):
    """
    Enumeração para os grupos de objeto.
    """

    OBRAS = 1
    SERVIÇOS = 2
    BENS_PATRIMONIAIS = 3
    MATERIAIS = 4
    OUTROS = 99


class CNPJSearchFilter(base_filter.BaseFilter):
    """
    Esquema para o filtro de CNPJ.
    """

    tipo_natureza_juridica: NaturezaJuridica = NaturezaJuridica.TODOS
    """
    Tipo de natureza jurídica da empresa.
    """
    uf_pessoa_juridica: str | None = None
    """
    UF da pessoa jurídica da empresa no formato "XX". Ex: "SP", "RJ", "MG".
    """
    municipio: str | None = None
    """
    Geocode do município da empresa, ex: "3304557" para o município do Rio de Janeiro.
    Veja: https://www.ibge.gov.br/explica/codigos-dos-municipios.php para mais detalhes.
    """

    valor_gastos_diretos_de: float | None = None
    """
    Valor mínimo dos gastos diretos.
    Nota: Existe um bug no portal em que esse filtro não irá funcionar, mas a busca irá redirecionar para uma página
    de erro 400(?). Chamando a API diretamente, o filtro funciona.
    """
    valor_gastos_diretos_ate: float | None = None
    """
    Valor máximo dos gastos diretos.
    Nota: Existe um bug no portal em que esse filtro não irá funcionar, mas a busca irá redirecionar para uma página
    de erro 400(?). Chamando a API diretamente, o filtro funciona.
    
    """
    valor_transferencia_de: float | None = None
    """
    Valor mínimo da transferência.
    Nota: Existe um bug no portal em que esse filtro não irá funcionar, mas a busca irá redirecionar para uma página
    de erro 400(?). Chamando a API diretamente, o filtro funciona.
    """
    valor_transferencia_ate: float | None = None
    """
    Valor máximo da transferência.
    Nota: Existe um bug no portal em que esse filtro não irá funcionar, mas a busca irá redirecionar para uma página
    de erro 400(?). Chamando a API diretamente, o filtro funciona.
    """
    sancao_vigente: bool | None = False
    """
    Se o CNPJ está sob sanção vigente.
    """
    emitente_nfe: bool | None = False
    """
    Se o CNPJ é emitente de NFE.
    """

    grupo_objeto: str | None = None
    """
    Código do grupo de objeto. Mais de um grupo pode ser passado, separados por vírgula.
    Ex: "1,2,3" para Obras, Serviços e Bens Patrimoniais.
    Veja a enumeração `GrupoObjeto` 
    """
