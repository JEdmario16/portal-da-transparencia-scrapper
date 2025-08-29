import asyncio

from playwright.async_api import (  # type: ignore[import-not-found] # ignore missing stub
    ElementHandle, Page, async_playwright)

from scrapper.core.elements_selectors.selector import \
    DetailsLinksSelector
from scrapper.core.interfaces.base_crawler import BaseCrawler


class DetailsLinks(BaseCrawler):
    """
    Classe base para coletar links de detalhes de um CPF ou CNPJ.
    os links de detalhes referem-se as telas em portaldatransparencia.gov.br/busca/(pessoa-fisica|pessoa-juridica)/...
    Esta tela possui várias seções, contendo informações rápidas sobre um tipo de informação e um botão "detalhes" que leva a uma tela com mais informações.
    Esse crawler coleta estes links, e ignora as informações rápidas.
    Algumas seções, como "Recebimento de Recursos", podem ter várias subseções(por exemplo: "Bolsa Família", "Auxílio Brasil", etc),
    e cada uma delas possui um botão "detalhes" que leva a uma tela com mais informações.

    Alguns exemplos de seções são:
    - "Recebimento de Recursos"
    - "Contratos"
    - "Inatividade"
    - "Processos Administrativos"
    ... etc

    Esta classe pode ser combinada com `scrapper.core.crawlers.searcher` para coletar esses links de resultados de busca, e com
    `scrapper.core.crawlers.details.consult` ou `scrapper.core.crawlers.tabular_details` (dependendo do layout da tela)
    para coletar os detalhes de cada link.

    """

    BASE_URL = "https://portaldatransparencia.gov.br"

    selector = DetailsLinksSelector()

    async def fetch(self, url: str):

        await self.page.goto(url)

        # espera a página carregar
        await self.page.wait_for_selector(self.selector.details_container)
        data = await self.collect_all_details_links(self.page)

        return data

    async def collect_all_details_links(self, page: Page) -> dict[str, str]:
        """
        Coleta todos os links de detalhes de cada CPF
        """

        container = await page.query_selector(self.selector.details_container)

        if not container:
            return {}

        # Ativa todos os accordions
        await self.__activate_all_accordions(container)

        itens_container = await container.query_selector_all(
            self.selector.detail_row_container
        )

        if not itens_container:
            return {}

        # Coleta todos os links de detalhes de cada accordion
        links = await self.__collect_all_links_from_accordions(container)
        if not links:
            return {}
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
        headers = await container.query_selector_all(self.selector.itens)

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
        links: dict[str, str] = {}
        # a partir do container, seleciona todas divs cujo id
        # começa com "accordion"
        accordions_rows = await container.query_selector_all(
            self.selector.detail_row_container
        )

        if not accordions_rows:
            return links

        for accordion in accordions_rows:
            title = await accordion.get_attribute("id") or "Sem titulo"
            title = title.strip()

            if await self.__accordion_has_subsecton(accordion):
                # Se o accordion possui subseções, coleta os links de cada subseção
                links.update(await self.__collect_all_links_from_subsections(accordion))

                # extrarow apenas ocorre em subseções
                if await self.__accordion_has_extra_row(accordion):
                    # Se o accordion possui uma linha extra, coleta os links de cada linha extra
                    links.update(
                        await self.__collect_links_from_extra_row(
                            page=self.page, accordion=accordion
                        )
                    )
                continue

            buttons = await accordion.query_selector_all(self.selector.details_button)

            if not buttons:  # TODO: log
                continue

            for i, button in enumerate(buttons):
                # Se o accordion não possui subseções, coleta os links de cada botão
                link = await button.get_attribute("href")
                link = f"{self.BASE_URL}{link}"

                if not link:
                    continue

                # Adiciona o link ao dicionário com o título do accordion como chave
                links[f"{title}_{i}"] = link

        return links

    async def __accordion_has_subsecton(self, accordion: ElementHandle) -> bool:
        """
        Verifica se o accordion possui uma subseção. Usado especialmente para a seção de "Recebimento de Recursos",
        que pode conter váras subseções com cada benefício(exemplo: "Bolsa Família", "Auxílio Brasil", etc).
        """

        subsections = await accordion.query_selector_all(self.selector.subsection)

        if not subsections:
            return False

        return True

    async def __accordion_has_extra_row(self, accordion: ElementHandle) -> bool:
        """
        Verifica se o accordion possui uma linha extra. Usado especialmente para a seção de "Recebimento de Recursos",
        que pode conter váras subseções com cada benefício(exemplo: "Bolsa Família", "Auxílio Brasil", etc).
        """

        extra_row = await accordion.query_selector(
            self.selector.beneficiary_federal_resources
        )
        if not extra_row:
            return False
        return True

    async def __collect_all_links_from_subsections(
        self, accordion: ElementHandle
    ) -> dict[str, str]:
        """
        Coleta todos os links de detalhes de cada accordion
        """

        links: dict[str, str] = {}

        # a partir do container, seleciona todas divs cujo id
        # começa com "accordion"
        subsections = await accordion.query_selector_all(self.selector.subsection)

        if not subsections:
            return links

        for i, subsection in enumerate(subsections):

            buttons = await subsection.query_selector_all(self.selector.details_button)

            if not buttons:
                continue

            for i, button in enumerate(buttons):
                title_el = await subsection.query_selector(
                    self.selector.subsection_title
                )

                if not title_el:
                    # fallback caso o título não seja encontrado
                    accordion_title = (
                        await accordion.get_attribute("id") or "Sem titulo"
                    )
                    title = f"{accordion_title}_{i}"
                else:
                    title = await title_el.inner_text()
                    title = title.strip()

                link = await button.get_attribute("href")
                link = f"{self.BASE_URL}{link}"
                links[title] = link

        return links

    async def __collect_links_from_extra_row(
        self, accordion: ElementHandle, page: Page
    ) -> dict[str, str]:
        """
        Coleta o link da linha extra do accordion.
        A linha extra é usada especialmente para a seção de "Recebimento de Recursos",
        que pode conter váras subseções com cada benefício(exemplo: "Bolsa Família", "Auxílio Brasil", etc).
        A linha extra possui um botão "detalhes" que leva a uma tela com mais informações.
        O objeto `Page` é necessário, pois o caminho do titulo do botão é obtido via xpath.

        """

        container = await accordion.query_selector(
            self.selector.beneficiary_federal_resources
        )

        if not container:
            return {}

        title = await page.query_selector(
            self.selector.beneficiary_federal_resources_title
        )

        if not title:
            title = "Sem titulo"
        else:
            title = await title.inner_text()
            title = title.strip()

        btn = await container.query_selector(self.selector.details_button)
        if not btn:
            return {}
        link = await btn.get_attribute("href")
        if not link:
            return {}
        link = f"{self.BASE_URL}{link}"
        return {title: link}


if __name__ == "__main__":

    async def main():
        # url = "https://portaldatransparencia.gov.br/busca/pessoa-fisica/7419128-cleber-moreira-de-oliveira?paginacaoSimples=true&tamanhoPagina=&offset=&direcaoOrdenacao=asc&colunasSelecionadas=linkDetalhamento&id=7419128"
        # url = "https://portaldatransparencia.gov.br/busca/pessoa-juridica/ESTRANG0022309-cto-events-limited?paginacaoSimples=true&tamanhoPagina=&offset=&direcaoOrdenacao=asc&colunasSelecionadas=linkDetalhamento%2Corgao%2CunidadeGestora%2CnumeroLicitacao%2CdataAbertura&id=23340505"
        # url = "https://portaldatransparencia.gov.br/busca/pessoa-fisica/4414745-abadio-jose-vital"
        # url = "https://portaldatransparencia.gov.br/busca/pessoa-fisica/411913-acir-pimenta-madeira-filho"
        # url = "https://portaldatransparencia.gov.br/busca/pessoa-fisica/284652885-a-guida-sulidade-silva"
        # url = "https://portaldatransparencia.gov.br/busca/pessoa-fisica/14410537-aalin-juvene-picanco-dos-santos"
        # url = "https://portaldatransparencia.gov.br/busca/pessoa-fisica/9319343-abdalio-pereira-damasceno-cruz?paginacaoSimples=true&tamanhoPagina=&offset=&direcaoOrdenacao=asc&colunasSelecionadas=linkDetalhamento%2Corgao%2CunidadeGestora%2CnumeroLicitacao&id=9319343"
        url = "https://portaldatransparencia.gov.br/busca/pessoa-juridica/09036777000180-centro-de-educacao-profissionalizacao-cidadania-e-empreendedorismo"
        crawler = DetailsLinks(page=None)
        data = await crawler.fetch(url)
        print(data)

    asyncio.run(main())
