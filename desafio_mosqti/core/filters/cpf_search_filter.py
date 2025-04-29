from desafio_mosqti.core.filters import base_filter


class CPFSearchFilter(base_filter.BaseFilter):
    """
    Esquema para o filtro de CPF.
    """

    servidor_publico: bool = False
    """
    Se o CPF é de um servidor público.
    """
    beneficiario_programa_social: bool = False
    """
    Se o CPF é de um beneficiário de programa social.
    """
    portador_cpgf: bool = False
    """
    Se o CPF é de um portador do CPGF.
    """
    portador_cpdc: bool = False
    """
    Se o CPF é de um portador do CPDC.
    """
    sancao_vigente: bool = False
    """
    Se o CPF está sob sanção vigente.
    """
    ocupante_imovel_funcional: bool = False
    """
    Se o CPF ocupa imóvel funcional.
    """
    possui_contrato: bool = False
    """
    Se o CPF possui contrato.
    """
    favorecido_recurso: bool = False
    """
    Se o CPF é favorecido de recurso público.
    """
    emitente_nfe: bool = False
    """
    Se o CPF é emitente de NFE.
    """
