from dataclasses import dataclass


@dataclass
class Selector:
    """
    Classe para armazenar os seletores de busca.

    """

    results_count_selector = (
        "xpath=/html/body/main/div/div[2]/div[2]/div[2]/div[1]/div/div/div[2]"
    )
    """
    Seletor do elemento que informa a quantidade de resultados a busca trouxe
    """

    results: str = "span#resultados"
    """Seletor do container com os intens do resultado da busca"""

    result_item: str = "div.br-item"
    """Seletor da div que contém os dados do resultado da busca"""

    result_item_link: str = "a.link-busca-nome"
    """Seletor a url do recurso encontrado na busca"""

    resullt_item_info: str = "div.col-sm-12"
    """
    Representa uma linha no card de resultados. Trata-se de uma classe do bootstrap, então
    deve ser utilziada com cuidado, preferencialmente á partir o pai.
    Por exemplo: `Selector.result_item` > div.col-sm-12
    """


@dataclass
class CPFDetailsSelector:
    received_resources: str = "[aria-controls='accordion-recebimentos-recursos']"
    """
    Seletor do container com os dados de recebimentos de recursos
    """

    inactivity: str = "[aria-controls='accordion-inatividade']"
    """
    Seletor do container com os dados de servidores e pensionistas
    """

    services_travel: str = "[aria-controls='accordion-viagens-a-servico']"

    card_payment: str = "[aria-controls='accordion-cartao-pagamento']"
    """
    Seletor do container com os dados do cartão de pagamento do governo federal ou 
    cartão da defesa civil
    """

    parliamentary_amendments: str = "[aria-controls='accordion-emendas']"
    """
    Seletor do container com os dados das emendas parlamentares
    """

    federal_employment: str = "[aria-controls='accordion-servidor']"
    """
    Seletor do container com os dados do servidor público
    """

    union_property: str = "[aria-controls='accordion-imovel-funcional']"
    """
    Seletor do container com os dados do imóvel funcional
    """

    sanctions: str = "[aria-controls='accordion-sancoes-vigentes-pf']"
    """
    Seletor do container com os dados de sanções vigentes
    """

    contracts: str = "[aria-controls='accordion-contratos-firmados']"
    """
    Seletor do container com os dados de contratos firmados
    """

    federal_invoices: str = (
        "[aria-controls='accordion-notas-fiscais-emitidas-governo-federal']"
    )
    """
    Seletor do container com os dados de notas fiscais emitidas pelo governo federal
    """

    details_button: str = "a.br-button"
    """
    Seletor do botão de detalhes.
    """

    details_container: str = "#accordion1"

    itens: str = "div.item > button"

    activate_accordion_button: str = "button.header"

    res: str = "div.box-ficha_resultados"

    detail_row_container: str = 'div[id^="accordion"]'

    detail_link: str = "div.box-ficha__resultados > a.br-button"
