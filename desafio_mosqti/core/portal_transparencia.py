from typing import Literal, Optional, Union

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from desafio_mosqti.core.crawlers import ConsultDetails, DetailsLinks, Searcher, TabularDetails
from desafio_mosqti.core.filters import CNPJSearchFilter, CPFSearchFilter
from desafio_mosqti.core.schemas.search_result import (CnpjSearchResult,
                                                       CpfSearchResult)


from desafio_mosqti.core.elements_selectors.selector import DetailPageDetectionSelector
class PortalTransparencia:
    """
    Classe para acessar coletar dados do portal da transparência.
    """

    def __init__(self, base_url: str = "https://portaldatransparencia.gov.br", headless: bool = False):
        self.base_url = base_url
        # self.details_links = DetailsLinks()
        # self.consult = ConsultDetails()
        # self.tabular_details = TabularDetails()

        self.playwright: Optional[async_playwright] = None
        self.context: Optional[BrowserContext] = None
        self.browser: Optional[Browser] = None
        self.headless = headless

    async def bootstrap(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()

    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()
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
        **kwargs
    ) -> list[CpfSearchResult | CnpjSearchResult]:
        """
        Realiza uma busca no portal da transparência.

        Args:
            query (str): CPF ou CNPJ a ser buscado.
            mode (str): Modo de busca. Pode ser "cpf" ou "cnpj".
            _filter (Optional[Union[CPFSearchFilter, CNPJSearchFilter]]): Filtro a ser aplicado na busca.
            max_results (bool): Se True, percorre todas as páginas até 200 resultados. Defaults to False.
            extract_details (bool): Se True, coleta os detalhes de cada resultado. Defaults to False.
            **kwargs: Metodo alternativo para passar os filtros. Caso a chave não esteja presente no filtro, um erro será gerado.

        Returns:
            dict[str, Union[dict[str, str], dict[str, str]]]: Dicionário com os resultados da busca.

        Example:
            ```python
            from desafio_mosqti.core.portal_transparencia import PortalTransparencia

            portal = PortalTransparencia()
            result = await portal.search("12345678901", mode="cpf")

            ```

            Busca com filtro:
            ```python
            from desafio_mosqti.core.portal_transparencia import PortalTransparencia
            portal = PortalTransparencia()
            result = await portal.search("12345678901", mode="cpf", servidor_publico=True, portador_cpgf=True) # utilize a classe CPFSearchFilter para obter o autocomplete dos filtros
            ```

        """
        if kwargs and not _filter:
            if mode == "cpf":
                _filter = CPFSearchFilter.model_validate(kwargs)
            elif mode == "cnpj":
                _filter = CNPJSearchFilter.model_validate(kwargs)
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=self.headless)
        context = await browser.new_context()
        page = await context.new_page()
        searcher = Searcher(page)
        search_result = await searcher.search(
            query=query, mode=mode, _filter=_filter, max_results=max_results, **kwargs
        )

        # if extract_details:
        #     await self.extract_data_from_search_result(
        #     )
        await context.close()
        await browser.close()
        await playwright.stop()
        return search_result

    async def extract_data_from_search_result(
        self,
        search_results: list[CpfSearchResult | CnpjSearchResult],
    ):
        """
        Coleta os detalhes de cada resultado da busca.
        """
        data = []
        for result in search_results:
            links = await self.details_links.fetch(result.url)
            for key, value in links.items():
                # value pode se tratar de um link que leva para `desafio_mosqti.core.crawlers.details.consult` ou `desafio_mosqti.core.crawlers.tabular_details`

                pass


async def main():
    portal = PortalTransparencia(headless=False)
    # await portal.bootstrap()

    # exemplo de busca usando de forma concorrrente
    r1 = await portal.search("mario", mode="cpf", max_results=False)
    # r2 = portal.search("", mode="cnpj", max_results=True)
    # r3 = portal.search("", mode="cpf", max_results=True)

    print(r1)
    # espera todas as buscas serem concluídas
    # await asyncio.gather(r1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())