import asyncio
import re
from typing import List, Literal

from playwright.async_api import (  # type: ignore[import-not-found] # ignore missing stub
    ElementHandle,
    Locator,
    Page,
    async_playwright,
)

from desafio_mosqti.core.elements_selectors.selector import Selector
from desafio_mosqti.core.filters import CNPJSearchFilter, CPFSearchFilter
from desafio_mosqti.core.interfaces.base_crawler import BaseCrawler
from desafio_mosqti.core.schemas.search_result import CnpjSearchResult, CpfSearchResult


class Searcher(BaseCrawler):

    BASE_URL = "https://portaldatransparencia.gov.br"

    MODES = {  # name: subdomain
        "cpf": "pessoa-fisica",
        "cnpj": "pessoa-juridica",
    }

    selector = Selector()

    async def search(
        self,
        query: str,
        *,
        mode: Literal["cpf", "cnpj"] = "cpf",
        _filter: CNPJSearchFilter | CPFSearchFilter | None = None,
        max_results: bool = False,
    ) -> List[CpfSearchResult | CnpjSearchResult]:
        """
        Faz a busca no Portal da Transparência.

        Params:
            :param query: O termo de busca (CPF ou CNPJ)
            :param mode: Modo de busca (cpf ou cnpj)
            :param _filter: Filtros adicionais para a busca (opcional)
            :param max_results: Se True, retorna o número máximo de resultados possíveis (até 200). Caso contrário, retorna apenas os primeiros 10 resultados.

        Returns:
            :return: Resultado da busca
            :rtype: dict
        """
        url = self.build_query_url(query, mode=mode, _filter=_filter)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)

            page = await browser.new_page()

            # Adiciona os headers customizados
            await page.set_extra_http_headers(self.default_headers)

            await page.goto(url)

            # Aguarda o carregamento da página
            await self.safe_load(page)

            results_count_element = page.locator(
                selector=self.selector.results_count_selector
            )

            results_count = await self.parse_results_count(results_count_element)
            if results_count == 0:
                return []

            page_count = (
                self.__calculate_page_count(results_count) if max_results else 1
            )

            results = []

            for i in range(1, page_count + 1):
                results.extend(await self.fetch(page))
                await self.__go_to_next_page(page, i, page_count)
                if i == page_count:
                    break

        return results

    async def fetch(self, page: Page) -> List[CpfSearchResult | CnpjSearchResult]:
        """
        Faz a busca no Portal da Transparência.

        Params:
            :param url: URL de busca

        Returns:
            :return: Resultado da busca
            :rtype: dict
        """

        results_count_element = page.locator(
            selector=self.selector.results_count_selector
        )

        # Aguarda o carregamento da página
        await self.safe_load(page)

        results_count = await self.parse_results_count(results_count_element)
        if results_count == 0:
            return []

        parsed_content: List[CpfSearchResult | CnpjSearchResult] = (
            await self.parse_search_result_content(page)
        )
        return parsed_content

    async def parse_results_count(self, he: Locator | ElementHandle) -> int:
        """
        Faz o parse do elemento que contém a quantidade de resultados.
        Params:
            :param he: Locator do elemento que contém a quantidade de resultados
        Returns:
            :return: Quantidade de resultados. Caso não seja possível extrair uma quantidade válida,
            retorna -1.
            :rtype: int
        """

        text = await he.inner_text()
        match = re.search("(\d{1,3}(?:\.\d{3})*)", text)
        if match:
            # Remove os pontos e converte para inteiro
            count = int(match.group(1).replace(".", "").replace(",", ""))
            return count
        else:
            return -1

    async def parse_search_result_content(
        self, page: Page
    ) -> List[CpfSearchResult | CnpjSearchResult]:
        """
        Faz o parse do conteúdo da página.

        Params:
            :param page: Página a ser parseada

        Returns:
            :return: Resultado do parse
            :rtype: list
        """

        assert "busca/lista" in page.url, "A página não é uma lista de busca"

        container = await page.query_selector(self.selector.results)
        if not container:
            raise ValueError(
                "Não foi possível encontrar o container de resultados", page.url
            )

        itens = await container.query_selector_all(self.selector.result_item)
        if not itens:
            raise ValueError("Não foram encontrados itens na lista de busca", page.url)

        mode = self.__get_mode_from_url(page.url)
        parsed_itens: List[CpfSearchResult | CnpjSearchResult] = (
            await self.parse_search_result_itens(itens, mode)
        )
        return parsed_itens

    async def parse_search_result_itens(
        self, itens: List[ElementHandle], mode: Literal["cpf", "cnpj"]
    ) -> List[CpfSearchResult | CnpjSearchResult]:
        """
        Faz o parse dos itens da lista de busca.

        Params:
            :param itens: Lista de itens a serem parseados

        Returns:
            :return: Resultado do parse
            :rtype: list
        """
        parsed_itens = []
        for item in itens:
            parsed_item: CpfSearchResult | CnpjSearchResult = (
                await self.__parse_search_result_item(item, mode)
            )
            parsed_itens.append(parsed_item)
        return parsed_itens

    async def __parse_search_result_item(
        self, item: ElementHandle, mode: Literal["cpf", "cnpj"]
    ) -> CpfSearchResult | CnpjSearchResult:
        """
        Faz o parse de um item de CPF.

        Params:
            :param item: Item a ser parseado

        Returns:
            :return: Resultado do parse
            :rtype: CpfSearchResult
        """
        data_card = await item.query_selector_all(self.selector.resullt_item_info)
        if not data_card:
            raise ValueError("Não foi possível encontrar os dados do item")

        # Alguns resultados possuem strings vazias no resultado
        # então extraímos campo por campo ao invés de usar inner_text no elemento pai
        # além disso, o texto extraído é na forma de "Campo: Valor", então
        # extraímos apenas o valor e removemos os espaços em branco antes e depois
        data = [await d.inner_text() for d in data_card]
        data = [d.strip().split(": ")[-1] for d in data]
        url_el = await item.query_selector(self.selector.result_item_link)

        if not url_el:
            raise ValueError("Não foi possível encontrar o link do item")

        url = await url_el.get_attribute("href") or ""

        if mode == "cnpj":
            nome = data[0]
            cnpj = data[1]
            grupo_natureza_jud = data[2]
            muni_uf = data[3]
            return CnpjSearchResult(
                url=url,
                cnpj=cnpj,
                grupo_natureza_jud=grupo_natureza_jud,
                muni_uf=muni_uf,
                nome=nome,
            )

        elif mode == "cpf":
            nome = data[0]
            cpf = data[1]
            beneficio_tipo = data[2]
            return CpfSearchResult(
                url=url,
                nome=nome,
                cpf=cpf,
                beneficio_tipo=beneficio_tipo,
            )
        raise ValueError(f"Invalid mode: {mode}")

    def build_query_url(
        self,
        query: str,
        *,
        mode: Literal["cpf", "cnpj"] = "cpf",
        page: int = 1,
        size: int = 10,
        _filter: CNPJSearchFilter | CPFSearchFilter | None = None,
    ):
        """
        Constrói a URL de busca no Portal da Transparência. Este método não faz a busca em si, apenas gera a URL.

        Params:
            :param query: O termo de busca (CPF ou CNPJ)
            :param mode: Modo de busca (cpf ou cnpj)
            :param _filter: Filtros adicionais para a busca (opcional)

        Returns:
            :return: URL de busca construída
            :rtype: str

        """
        subdomain_mode = self.__resolve_mode(mode)

        if _filter:
            self.__validate_filter(_filter, mode)

        f = _filter.build_url_params() if _filter else ""

        return f"{self.BASE_URL}/{subdomain_mode}/busca/lista?termo={query}&{f}"

    async def safe_load(self, page: Page, timeout: int = 5) -> None:
        """
        Espera a página carregar até que o elemento de resultados esteja visível.
        Caso alcance o timeout, extraí o elemento com a quantidade de resultados para garantir
        que realmente não há resultados.

        Isso é necessário pois o elemento que contém a quantidade de resultados é pré-carregado
        antes mesmo da resposta da busca ser recebida.
        Isso pode causar problemas em alguns casos, como quando a busca não retorna resultados.

        Params:
            :param page: Página a ser carregada
            :param timeout: Tempo máximo de espera (em segundos)
        """

        try:
            await page.wait_for_selector(self.selector.results, timeout=timeout * 1000)
        except Exception as _:
            # Se o timeout ocorrer, tenta extrair o elemento de contagem de resultados
            # para garantir que realmente não há resultados
            he = await page.query_selector(self.selector.results_count_selector)

            if not he:
                raise ValueError("Não foi possível encontrar o elemento de resultados")

            results_count = await self.parse_results_count(he)
            if (
                results_count == -1
            ):  # neste caso, o elemento foi encontrado, mas o texto é um placeholder
                await self.safe_load(page, timeout=timeout)
            else:
                print("A busca não retornou resultados")

    def __resolve_mode(self, mode: str) -> str:
        """
        Interpreta o modo de busca (cpf ou cnpj) e retorna o subdomínio correto.

        Params:
            :param mode: Modo de busca (cpf ou cnpj)

        Returns:
            :return: Subdomínio correto para a busca
            :rtype: str

        Raises:
            :raises ValueError: Se o modo não for válido

        """
        if mode not in self.MODES:
            raise ValueError(f"Invalid mode: {mode}")
        return self.MODES[mode]

    def __validate_filter(
        self, _filter: CNPJSearchFilter | CPFSearchFilter, mode: Literal["cnpj", "cpf"]
    ) -> None:
        """
        Valida os filtros de busca.

        Params:
            :param filter: Filtro a ser validado
            :param mode: Modo de busca (cpf ou cnpj)

        Raises:
            :raises ValueError: Se o filtro não for válido
        """
        if mode == "cnpj":
            if not isinstance(_filter, CNPJSearchFilter):
                raise ValueError("Invalid filter for CNPJ search")
        elif mode == "cpf":
            if not isinstance(_filter, CPFSearchFilter):
                raise ValueError("Invalid filter for CPF search")
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def __get_mode_from_url(self, url: str) -> Literal["cpf", "cnpj"]:
        """
        Interpreta o modo de busca a partir da URL.

        Params:
            :param url: URL a ser interpretada

        Returns:
            :return: Modo de busca (cpf ou cnpj)
            :rtype: str

        Raises:
            :raises ValueError: Se o modo não for válido
        """
        if "pessoa-fisica" in url:
            return "cpf"
        elif "pessoa-juridica" in url:
            return "cnpj"
        else:
            raise ValueError(f"Invalid URL: {url}")

    def __calculate_page_count(self, total_results: int) -> int:
        """
        Calcula a quantidade de páginas com base no total de resultados.

        Params:
            :param total_results: Total de resultados encontrados

        Returns:
            :return: Quantidade de páginas necessárias
            :rtype: int
        """
        total_results = min(
            total_results, 200
        )  # Limita o total de resultados a 200 por limite do portal
        RESULTS_PER_PAGE = 10
        return (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE

    async def __go_to_next_page(
        self, page: Page, current_page: int, total_pages: int
    ) -> None:
        """
        Navega para a próxima página de resultados.

        Params:
            :param page: Página atual
            :param current_page: Página atual
            :param total_pages: Total de páginas disponíveis
        """
        if current_page < total_pages:
            next_button = await page.query_selector("ul.pagination > li.next > a")

            if next_button:
                print("achou a div de paginação")
            if not next_button:
                raise ValueError("Não foi possível encontrar o botão de próxima página")

            await next_button.click()
            await page.wait_for_timeout(1000)


async def main():
    searcher = Searcher()
    result = await searcher.search("", mode="cnpj", max_results=True)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
