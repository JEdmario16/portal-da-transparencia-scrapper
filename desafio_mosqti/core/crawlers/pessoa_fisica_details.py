import asyncio

from playwright.async_api import (  # type: ignore[import-not-found] # ignore missing stub
    ElementHandle,
    Page,
    async_playwright,
)

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

            if await self.__accordion_has_subsecton(accordion):
                # Se o accordion possui subseções, coleta os links de cada subseção
                links.update(await self.__collect_all_links_from_subsections(accordion))
                continue

            button = await accordion.query_selector(CPFDetailsSelector.details_button)

            if not button:  # TODO: log
                continue
            link = await button.get_attribute("href")
            link = f"{self.BASE_URL}{link}"

            links[title] = link

        return links

    async def __accordion_has_subsecton(self, accordion: ElementHandle) -> bool:
        """
        Verifica se o accordion possui uma subseção. Usado especialmente para a seção de "Recebimento de Recursos",
        que pode conter váras subseções com cada benefício(exemplo: "Bolsa Família", "Auxílio Brasil", etc).
        """

        subsections = await accordion.query_selector_all(CPFDetailsSelector.subsection)

        if not subsections:
            return False

        return True

    async def __collect_all_links_from_subsections(
        self, accordion: ElementHandle
    ) -> dict[str, str]:
        """
        Coleta todos os links de detalhes de cada accordion
        """

        links = {}

        # a partir do container, seleciona todas divs cujo id
        # começa com "accordion"
        subsections = await accordion.query_selector_all(CPFDetailsSelector.subsection)

        if not subsections:
            return links

        for i, subsection in enumerate(subsections):

            buttons = await subsection.query_selector_all(
                CPFDetailsSelector.details_button
            )

            if not buttons:
                continue

            for i, button in enumerate(buttons):
                title = await subsection.query_selector(
                    CPFDetailsSelector.subsection_title
                )

                if not title:
                    # fallback caso o título não seja encontrado
                    accordion_title = await accordion.get_attribute("id")
                    title = f"{accordion_title}_{i}"
                else:
                    title = await title.inner_text()
                    title = title.strip()

                link = await button.get_attribute("href")
                link = f"{self.BASE_URL}{link}"
                links[title] = link

        return links


if __name__ == "__main__":

    async def main():
        url = "https://portaldatransparencia.gov.br/busca/pessoa-fisica/7419128-cleber-moreira-de-oliveira?paginacaoSimples=true&tamanhoPagina=&offset=&direcaoOrdenacao=asc&colunasSelecionadas=linkDetalhamento&id=7419128"
        crawler = PessoaFisicaDetails()
        data = await crawler.fetch(url)
        print(data)

    asyncio.run(main())
