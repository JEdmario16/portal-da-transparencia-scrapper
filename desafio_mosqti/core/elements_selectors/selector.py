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

    next_page_selector: str = "div#paginacao > li.next > a"


@dataclass
class CPFDetailsSelector:

    details_button: str = "a.br-button"
    """
    Seletor do botão de detalhes.
    """

    details_container: str = "#accordion1"

    itens: str = "div.item > button"

    detail_row_container: str = 'div[id^="accordion"]'

    subsection: str = "div.br-table"

    subsection_title: str = "div.responsive > strong"


class ConsultDetailsSelector:
    """
    Seletor para a consulta de detalhes.
    """

    loading_selector = "div#spinner"
    table_selector = "table#lista"
    table_headers = "thead th"

    results_per_time = "select.form-control"

    next_page = "li#lista_next"


class TabularDetailsSelector:
    """
    Seletor para detalhes tabulares.
    """

    # geral
    dados_detalhados_expand_button = "button.header"
    item = "div.item"
    row = "div.row"
    col = "div.col-xs-12"
    cell_key = "strong"
    cell_value = "span"

    # dados tabelados
    dados_tabelados = "section.dados-tabelados"

    # dados detalhados
    dados_detalhados = "section.dados-detalhados"
    section_title = "span.title"
    data_block = "div.bloco"

    # data table
    data_table_container = "div.wrapper-table"
    data_table_title = "spam"  # isso mesmo, 'spam' rs
    data_table_table = "table.dataTable"
    table_headers = "thead th"
