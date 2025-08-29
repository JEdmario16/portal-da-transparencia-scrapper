from dataclasses import dataclass
from typing import Literal


@dataclass
class SearcherSelector:
    """
    Classe para armazenar os seletores de busca.

    """

    results_count_selector: Literal[
        "xpath=/html/body/main/div/div[2]/div[2]/div[2]/div[1]/div/div/div[2]"
    ] = "xpath=/html/body/main/div/div[2]/div[2]/div[2]/div[1]/div/div/div[2]"
    """
    Seletor do elemento que informa a quantidade de resultados a busca trouxe. Como trata-se
    de um xpath, pode ser utilizado diretamente de `Page` ou de um `ElementHandle` que contém
    este elemento.
    """

    results: Literal["span#resultados"] = "span#resultados"
    """
    Seletor do container com os intens do resultado da busca.
    Pode ser utilizado para detectar se a página carregou ou extrair os dados do resultado da busca
    """

    result_item: Literal["div.br-item"] = "div.br-item"
    """Seletor da div que contém os dados do resultado da busca"""

    result_item_link: Literal["a.link-busca-nome"] = "a.link-busca-nome"
    """Seletor a url do recurso encontrado na busca"""

    resullt_item_info: Literal["div.col-sm-12"] = "div.col-sm-12"
    """
    Representa uma linha no card de resultados. Trata-se de uma classe do bootstrap, então
    deve ser utilziada com cuidado, preferencialmente á partir o pai.
    Por exemplo: `Selector.result_item` > div.col-sm-12 irá pegar todas as linhas
    do card de resultado.
    """


@dataclass
class DetailsLinksSelector:
    """
    Seletor para detalhes de CPF.
    """

    details_container: Literal["#accordion1"] = "#accordion1"
    """
    Container que contém todos os `accordions` de detalhes.
    Cada `accordion` contém detalhes de um tipo específico.
    Exemplo: `Benefícios`, `Cartões de Pagamento`, `Convênios`, etc.
    """

    details_button: str = "a.br-button"
    """
    Cada `accordion` possui um botão de detalhes, que por sua vez contém um link para uma 
    página de detalhes. Este seletor obtém esse botão.
    """

    itens: Literal["div.item > button"] = "div.item > button"
    """
    Cada `accordion` possui um botão de detalhes, e um botão de titulo.
    O botão de titulo possui o nome da seção e, ao clicar, expande ou colapsa
    o conteúdo do `accordion`.
    Este seletor obtém esse botão.
    """

    detail_row_container: Literal['div[id^="accordion"]'] = 'div[id^="accordion"]'
    """
    Assim que os accordions são expandidos, suas informações estão disponíveis
    em uma div com o id começando com "accordion".
    Exemplo: `accordion-bolsa-familia`, `accordion-cartao-pagamento`, etc.
    Esse seletor obtém essa(s) div(s).
    """

    subsection: Literal["div.br-table"] = "div.br-table"
    """
    Alguns accordions possuem subseções, com vários botões de detalhes.
    Por exemplo, a seção de 'Recebimento de Recursos' possui várias subseções,
    como 'Bolsa Família', 'Auxílio Emergencial', etc.
    Esse seletor obtém essas subseções.
    """

    subsection_title: Literal["div.responsive > strong"] = "div.responsive > strong"
    """
    Título da subseção.
    Exemplo: `Bolsa Família`, `Auxílio Emergencial`, etc.
    Esse seletor obtém o título da subseção.
    veja: `subsection` para mais detalhes.
    """

    # side case: "Recebimento de Recursos" possui dados
    # tantos de benefícios quanto de recebimentos de recursos,
    # em um layout diferente.
    beneficiary_federal_resources: Literal["div.row > div.col-xs-12"] = (
        "div.row > div.col-xs-12"
    )
    """
    Este seletor é utilizado para tratar um side-case:
    A seção "Recebimento de Recursos" possui dados tanto de benefícios
    quanto de recebimentos de recursos, em um layout diferente.
    Este seletor é utilizado para obter os dados de recebimentos de recursos.
    """

    beneficiary_federal_resources_title: Literal[
        "xpath=/html/body/main/div/div[2]/div[2]/div/div[2]/div/div/strong"
    ] = "xpath=/html/body/main/div/div[2]/div[2]/div/div[2]/div/div/strong"
    """
    Este seletor é utilizado para tratar um side-case:
    A seção "Recebimento de Recursos" possui dados tanto de benefícios
    quanto de recebimentos de recursos, em um layout diferente.
    Este seletor é utilizado para obter o título da seção de recebimentos de recursos.
    """


class ConsultDetailsSelector:
    """
    Seletor para a consulta de detalhes.
    """

    loading_selector: Literal["div#spinner"] = "div#spinner"
    """
    Seletor do elemento que indica que a página está carregando.
    """

    table_selector: Literal["table#lista"] = "table#lista"
    """
    Seletor da tabela que contém os dados do resultado da busca.
    """

    table_headers: Literal["thead th"] = "thead th"
    """
    Seletor dos cabeçalhos da tabela.
    """

    results_per_time: Literal["select.form-control"] = "select.form-control"
    """
    Seletor do elemento que permite escolher a quantidade de resultados por página.
    """

    next_page: Literal["li#lista_next"] = "li#lista_next"
    """
    Seletor do elemento que permite navegar para a próxima página de resultados.
    """


class TabularDetailsSelector:
    """
    Seletor para detalhes tabulares.
    """

    # geral
    dados_detalhados_expand_button: Literal["button.header"] = "button.header"
    item: Literal["div.item"] = "div.item"
    row: Literal["div.row"] = "div.row"
    col: Literal["div.col-xs-12"] = "div.col-xs-12"
    cell_key: Literal["strong"] = "strong"
    cell_value: Literal["span"] = "span"

    # dados tabelados
    dados_tabelados: Literal["section.dados-tabelados"] = "section.dados-tabelados"

    # dados detalhados
    dados_detalhados: Literal["section.dados-detalhados"] = "section.dados-detalhados"
    section_title: Literal["span.title"] = "span.title"
    data_block: Literal["div.bloco"] = "div.bloco"
    data_accordion: Literal["div.br-accordion"] = "div.br-accordion"

    # data table
    data_table_container: Literal["div.wrapper-table"] = "div.wrapper-table"
    data_table_title: Literal["spam"] = "spam"  # isso mesmo, 'spam' rs
    data_table_table: Literal["table.dataTable"] = "table.dataTable"
    table_headers: Literal["thead th"] = "thead th"


class DetailPageDetectionSelector:
    """
    Seletor para detectar se uma página de detalhes é `ConsultDetails` ou `TabularDetails`.
    """

    # Seletor para verificar se a página é uma página de detalhes
    filter_box: Literal["div#id-box-filtro"] = "div#id-box-filtro"
