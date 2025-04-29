import asyncio

from playwright.async_api import (  # type: ignore[import-not-found] # ignore missing stub
    ElementHandle, Page, async_playwright)

from desafio_mosqti.core.elements_selectors.selector import CPFDetailsSelector
from desafio_mosqti.core.interfaces.base_crawler import BaseCrawler


class PessoaFisicaDetails(BaseCrawler):
    BASE_URL = "https://portaldatransparencia.gov.br"

    async def fetch(self, url: str):

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)

            page = await browser.new_page()
            # Adiciona os headers customizados
            await page.set_extra_http_headers(self.default_headers)

            await page.goto(url)

            # espera a página carregar
            await page.wait_for_selector(CPFDetailsSelector.details_container)
            data = await self.collect_all_details_links(page)

            return data
 
    async def collect_all_details_links(self, page: Page) -> list[str]:
        """
        Coleta todos os links de detalhes de cada CPF
        """

        container = await page.query_selector(CPFDetailsSelector.details_container)

        if not container:
            return []

        # Ativa todos os accordions
        await self.__activate_all_accordions(container)

        itens_container = await container.query_selector_all(
            CPFDetailsSelector.detail_row_container
        )

        if not itens_container:
            return []

        # Coleta todos os links de detalhes de cada accordion
        links = await self.__collect_all_links_from_accordions(container)
        if not links:
            return []

        return links

    async def __activate_all_accordions(self, container: ElementHandle) -> None:
        """
        Ativa todos os accordions no container de resultados.
        O container de resultados possui duas divs: uma item clicável e outra com os detalhes.
        A div item clicável possui o seletor ".item > button.header", um botão que ativa o accordion.
        Então, esta função ativa todos os accordions clicando no botão de cada item.

        :param container: ElementHandle do container de resultados
        :type container: ElementHandle
        :return: None

        """
        headers = await container.query_selector_all(CPFDetailsSelector.itens)

        if not headers:
            return

        for header in headers:
            await header.scroll_into_view_if_needed()
            await header.click(delay=100)

    async def __collect_all_links_from_accordions(
        self, container: ElementHandle
    ) -> dict[str, str]:
        """
        Coleta todos os links de detalhes de cada accordion
        """
        links = {}

        # a partir do container, seleciona todas divs cujo id
        # começa com "accordion"
        accordions_rows = await container.query_selector_all(
            CPFDetailsSelector.detail_row_container
        )

        if not accordions_rows:
            return links

        for accordion in accordions_rows:
            title = await accordion.get_attribute("id")
            button = await accordion.query_selector(CPFDetailsSelector.details_button)

            if not button:  # TODO: log
                continue
            link = await button.get_attribute("href")
            link = f"{self.BASE_URL}{link}"

            links[title] = link

        return links


if __name__ == "__main__":

    async def main():
        url = "https://portaldatransparencia.gov.br/busca/pessoa-fisica/5812541-abdias-barbosa-bandeira"
        crawler = PessoaFisicaDetails()
        data = await crawler.fetch(url)
        print(data)

    asyncio.run(main())
