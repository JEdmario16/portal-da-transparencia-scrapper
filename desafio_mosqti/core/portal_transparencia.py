from __future__ import annotations

from typing import Literal, Optional, Union

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from desafio_mosqti.core.crawlers import (
    ConsultDetails,
    DetailsLinks,
    Searcher,
    TabularDetails,
)
from desafio_mosqti.core.elements_selectors.selector import DetailPageDetectionSelector
from desafio_mosqti.core.filters import CNPJSearchFilter, CPFSearchFilter
from desafio_mosqti.core.schemas.search_result import CnpjSearchResult, CpfSearchResult

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loguru import Logger
    from desafio_mosqti.core.interfaces.base_details import BaseDetails


class PortalTransparencia:
    """
    Classe para acessar coletar dados do portal da transparência.
    """

    # Dicionário que mapeia o tipo de página de detalhe para a classe correspondente.
    # O mapeamento é feito manualmente, através de um dicionário, para evitar abordagens por força bruta
    # (e.g.: tentar uma classe, buscar um seletor, e se falhar, tentar outra).
    # Isso é mais eficiente e reduz a chance de erros de execução.
    # O dicionário é preenchido com base no primeiro segmento do path da URL.
    #
    # Por exemplo:
    # A URL https://portaldatransparencia.gov.br/busca/pessoa-fisica/<id-pessoa><nome-pessoa>
    # é mapeada como:
    # 'busca': 'desafio_mosqti.core.crawlers.details_links.DetailsLinks'
    #
    # Veja que descartamos o trecho /pessoa-fisica/<id-pessoa><nome-pessoa>, pois não é necessário.
    # Outra possibilidade seria percebendo que o titulo da página de consultas sempre
    # tem como prefixo "Consulta", mas essa opção é mais frágil, pois pode mudar.
    DETAIL_PAGE_MAP = {
        # Dados tabulares
        "servidores": TabularDetails,  # servidor / inativo
        "beneficios": TabularDetails,  # recebimento de recursos
        "imoveis-funcionais": ConsultDetails,  # imóveis funcionais
        "despesas/favorecido": ConsultDetails,  # favorecido de recursos
        "licitacoes": TabularDetails,  # licitações
        "viagens": TabularDetails,  # Detalhes da consulta de viagens
        "despesas/pagamento": TabularDetails,  # detalhes da consulta de favorecimentos de recursos
        "contratos": TabularDetails,  # detalhes dos contratos firmados
        "notas-fiscais": TabularDetails,  # detalhes das notas fiscais emitidas
        "convenios": TabularDetails,  # detalhes dos convênios firmados
        "despesas/empenho": TabularDetails,  # detalhes dos empenhos
        "despesas/documento": TabularDetails,  # detalhes dos documentos
        "renuncias/imunidade": TabularDetails,  # detalhes das imunidades
        # Consultas
        "viagens/consulta": ConsultDetails,  # viagens a serviços
        "cartoes/consulta": ConsultDetails,  # cartão de pagamento
        "cartoes/cpgf": ConsultDetails,  # Detalhes da consulta de cartão de pagamento (Governo Federal)
        "cartoes/cpdc": ConsultDetails,  # Detalhes da consulta de cartão de pagamento (Defesa Civil)
        "emendas/consulta-por-documento": ConsultDetails,  # emendas parlamentares
        "emendas/consulta-por-favorecido": ConsultDetails,  # emendas parlamentares
        "sancoes": ConsultDetails,  # sanções vigentes
        "contratos/consulta": ConsultDetails,  # contratos firmados
        "notas-fiscais/consulta": ConsultDetails,  # notas fiscais emitidas
        "convenios/consulta": ConsultDetails,  # convênios firmados
        "renuncias/empresas-imunes-isentas": ConsultDetails,  # renúncias fiscais
    }

    def __init__(
        self,
        headless: bool = False,
        logger: Logger | None = None,
    ):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless

        if not logger:
            from desafio_mosqti.core.loger import logger
            
        self.logger = logger
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.page.close()
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

        # Limpa os atributos para evitar vazamentos de memória
        self.playwright = None
        self.browser = None
        self.context = None

    async def search(
        self,
        query: str,
        *,
        mode: Literal["cpf", "cnpj"] = "cpf",
        max_results: bool = True,
        _filter: Optional[Union[CPFSearchFilter, CNPJSearchFilter]] = None,
        extract_details: bool = False,
        deep: int = 1,
        details_max_results: bool = True,
    ):
        """
        Realiza uma busca no portal da transparência.

        Args:
            query (str): CPF ou CNPJ a ser pesquisado.
            mode (Literal["cpf", "cnpj"], optional): Modo de pesquisa. Defaults to "cpf".
            max_results (bool, optional): Se True, limita o número de resultados. Defaults to True.
            _filter (Optional[Union[CPFSearchFilter, CNPJSearchFilter]], optional): Filtro a ser aplicado. Defaults to None.

        Returns:
            list[Union[CpfSearchResult, CnpjSearchResult]]: Lista de resultados da pesquisa.
        """
        searcher = Searcher(self.page)
        search_result = await searcher.search(
            query,
            mode=mode,
            max_results=max_results,
            _filter=_filter,
        )

        if extract_details:
            sr_links = await self.__get_details_links(search_result)

            for sr_link in sr_links:
                links = sr_link.get("links", {})
                sr_data = {}
                for op_name, link in links.items():
                    # Descobre a página de detalhes com base na URL
                    detail_page_class = await self.__discover_detail_page(link)
                    if detail_page_class:
                        # Coleta os dados da página de detalhes
                        detail_page_cls = detail_page_class.__class__(page=self.page)
                        details = await detail_page_cls.fetch(
                            url=link,
                            recursive=True,
                        )
                        sr_data[op_name] = details
                # Atualiza o resultado da pesquisa com os dados coletados
                sr_link['details'] = sr_data
                # Remove o campo "links" do resultado
                sr_link.pop("links", None)
        return sr_link

    async def __get_details_links(
        self,
        search_result: list[Union[CpfSearchResult, CnpjSearchResult]],
    ) -> list:
        """
        Extrai os links de detalhes dos resultados da pesquisa.

        Args:
            search_result (Union[CpfSearchResult, CnpjSearchResult]): Resultados da pesquisa.

        Returns:
            list[DetailsLinks]: Lista de links de detalhes.
        """
        urls = []
        details_links = DetailsLinks(self.page)
        for sr in search_result:
            # Verifica se o resultado possui um link de detalhes
            if sr.url:
                links = await details_links.fetch(
                    url=sr.url,
                )
                urls.append(
                    {
                        **sr.model_dump(),
                        "links": links,
                    }
                )
        return urls

    async def __discover_detail_page(
        self,
        url: str,
    ) -> Optional[Union[TabularDetails, ConsultDetails]]:
        """
        Descobre a página de detalhes com base na URL.

        Args:
            url (str): URL da página de detalhes.

        Returns:
            Optional[Union[TabularDetails, ConsultDetails]]: Classe correspondente à página de detalhes.
        """
        # Extrai o primeiro segmento do path da URL
        path = url.split("/")[3]
        # Verifica se o path está no dicionário de mapeamento
        if path in self.DETAIL_PAGE_MAP:
            return self.DETAIL_PAGE_MAP[path](self.page)

        self.logger.warning(
            f"Não foi possível descobrir a página de detalhes para a URL: {url}"
        )
        return None


async def main():

    async with PortalTransparencia() as portal:
        # Exemplo de busca por CPF
        cpf_result = await portal.search(
            "", mode="cpf", max_results=False, extract_details=True,
            _filter=CPFSearchFilter(
                servidor_publico=True,
                beneficiario_programa_social=True,
                sancao_vigente=True,
        )
        )
        print(cpf_result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
