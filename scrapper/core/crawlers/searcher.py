import asyncio
import re
from typing import List, Literal

from playwright.async_api import (  # type: ignore[import-not-found] # ignore missing stub
    ElementHandle, Locator, Page)

from scrapper.core.elements_selectors.selector import SearcherSelector
from scrapper.core.filters import CNPJSearchFilter, CPFSearchFilter
from scrapper.core.interfaces.base_crawler import BaseCrawler
from scrapper.core.schemas.search_result import (CnpjSearchResult,
                                                       CpfSearchResult)


class Searcher(BaseCrawler):
    """
    Crawler para buscas no Portal da Transparência (Pessoa Física e Jurídica).

    Esta classe realiza consultas públicas por CPF ou CNPJ, aplicando filtros opcionais,
    e retornando os resultados estruturados como instâncias de [CpfSearchResult][scrapper.core.schemas.search_result.CpfSearchResult] ou [CnpjSearchResult][scrapper.core.schemas.search_result.CnpjSearchResult].
    O crawler é capaz de lidar com diferentes tipos de filtros, como natureza jurídica, município,

    Também é possível realizar a paginação dos resultados, limitar a quantidade de resultados, verificar
    a presença de captchas e auto retentar em caso de falhas.

    Recursos disponíveis:
    ----------------
    - Geração da URL com base no tipo de consulta e filtros.
    - Paginação de resultados (opcional, até 200 itens).
    - Extração estruturada de dados a partir da lista de resultados.
    - Compatível com modos "cpf" e "cnpj".


    Exemplo de uso:
    ```python
    from scrapper.core.crawlers.searcher import Searcher
    from scrapper.core.filters import CNPJSearchFilter
    from scrapper.core.schemas.search_result import CnpjSearchResult
    import asyncio

    async def main():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            searcher = Searcher(page=page)
            filter = CNPJSearchFilter(tipo_natureza_juridica=1)
            result = await searcher.search(
                query="12345678000195",
                mode="cnpj",
                _filter=filter,
                force_max_results=True,
                limit_results=10
            )
            print(result)
    asyncio.run(main())
    ```
    """

    BASE_URL = "https://portaldatransparencia.gov.br"

    MODES = {  # name: subdomain
        "cpf": "pessoa-fisica",
        "cnpj": "pessoa-juridica",
    }

    selector = SearcherSelector()

    async def search(
        self,
        query: str,
        *,
        mode: Literal["cpf", "cnpj"] = "cpf",
        _filter: CNPJSearchFilter | CPFSearchFilter | None = None,
        raise_for_captcha: bool = True,
        limit_results: int | None = None,
        max_retries: int = 3,
        jitter: bool = False,
    ) -> List[CpfSearchResult | CnpjSearchResult]:
        """
        Executa uma busca no Portal da Transparência, retornando os resultados estruturados.

        Args:
            query (str): Termo a ser buscado (CPF ou CNPJ).
            mode (Literal["cpf", "cnpj"]): Modo de busca (pessoa física ou jurídica).
            _filter (CNPJSearchFilter | CPFSearchFilter, optional): Filtro adicional de busca.
            raise_for_captcha (bool): Se True, levanta uma exceção se um captcha for detectado. Defaults to True.
            limit_results (int | None): Caso informado, limitará a lista de resultados de busca para os N primeiros itens.
                Defaults to None.

        Returns:
            List[CpfSearchResult | CnpjSearchResult]: Lista de resultados da busca.
        """

        url = self.build_query_url(query, mode=mode, _filter=_filter)
        try:
            await self.page.goto(url)
        except Exception as e:
            self.logger.error(
                f"Erro ao acessar a URL: {url}. Detalhes: {e}",
                extra={"url": url},
            )
            raise e

        self.logger.debug(
            f"Aguardando carregamento da página: {url}",
            extra={"url": url},
        )
        # Verifica se a página contém um captcha
        if await self.captcha_check_detector(self.page):
            self.logger.critical(
                "Operação bloqueada por captcha. Verifique manualmente o site.",
                extra={"url": url},
            )
            if raise_for_captcha:
                raise Exception("Captcha detectado na página.")
            return []

        self.logger.debug(
            f"Nenhum captcha detectado. Prosseguindo com a busca.",
            extra={"url": url},
        )
        # Aguarda o carregamento da página
        await self.safe_load(self.page)

        self.logger.debug(
            f"Página carregada com sucesso: {url}",
            extra={"url": url},
        )

        results_count_element = self.page.locator(
            selector=self.selector.results_count_selector
        )

        results_count = await self.parse_results_count(results_count_element)
        if results_count == 0:
            return []

        if limit_results:
            results_count = min(results_count, limit_results)

        page_count = self.__calculate_page_count(results_count)

        all_results = []

        self.logger.debug(
            f"Total de resultados encontrados: {results_count}. Total de páginas: {page_count}",
            extra={"url": url},
        )

        async for i, result in self.paginate_results(
            self.page, page_count, jitter=jitter, max_retries=max_retries
        ):
            self.logger.debug(
                f"Processando página {i + 1} de {page_count}",
                extra={"url": url},
            )
            all_results.extend(result)
        return all_results[:limit_results] if limit_results else all_results

    async def paginate_results(
        self, page: Page, total_pages: int, jitter: bool = False, max_retries: int = 3
    ):
        for i in range(total_pages):
            yield i, await self.parse_search_result_content(page)
            await self.__go_to_next_page(page, i + 1, total_pages)

    async def fetch(self, page: Page) -> List[CpfSearchResult | CnpjSearchResult]:
        """
        Realiza a extração de resultados da página atual já carregada.

        Args:
            page (Page): Instância da página carregada.

        Returns:
            List[CpfSearchResult | CnpjSearchResult]: Lista de resultados extraídos da página.
        """

        parsed_content: List[CpfSearchResult | CnpjSearchResult] = (
            await self.parse_search_result_content(page)
        )
        return parsed_content

    async def parse_results_count(self, he: Locator | ElementHandle) -> int:
        """
        Extrai a quantidade de resultados exibida na página.

        Args:
            he (Locator | ElementHandle): Elemento contendo o texto da contagem.

        Returns:
            int: Número total de resultados. Retorna -1 se a contagem não for identificada.
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
        Faz o parsing completo da lista de resultados exibida na página.

        Args:
            page (Page): Página da lista de busca.

        Returns:
            List[CpfSearchResult | CnpjSearchResult]: Lista de resultados convertidos.
        """
        assert "busca/lista" in page.url, "A página não é uma lista de busca"

        container = await page.query_selector(self.selector.results)
        if not container:
            return []

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
        Processa individualmente os itens da lista de busca.

        Args:
            itens (List[ElementHandle]): Elementos HTML da lista.
            mode (Literal["cpf", "cnpj"]): Modo de busca atual.

        Returns:
            List[CpfSearchResult | CnpjSearchResult]: Resultados convertidos.
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
        Faz o parse de um item individual da lista de resultados.

        Args:
            item (ElementHandle): Elemento HTML do item.
            mode (Literal["cpf", "cnpj"]): Modo de busca atual.

        Returns:
            CpfSearchResult | CnpjSearchResult: Resultado convertido.

        Raises:
            ValueError: Se o item não contiver os dados esperados.
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

        url = await url_el.get_attribute("href")
        url = f"{self.BASE_URL}{url}" if url and url.startswith("/") else url or ""

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
        _filter: CNPJSearchFilter | CPFSearchFilter | None = None,
    ) -> str:
        """
        Constrói a URL de consulta com base no termo, modo e filtros.

        Args:
            query (str): Termo de busca (CPF ou CNPJ).
            mode (Literal["cpf", "cnpj"]): Modo de busca.
            _filter (CNPJSearchFilter | CPFSearchFilter, optional): Filtro adicional.

        Returns:
            str: URL completa para a consulta.
        """
        subdomain_mode = self.__resolve_mode(mode)

        if _filter:
            self.__validate_filter(_filter, mode)

        f = _filter.build_url_params() if _filter else ""

        return f"{self.BASE_URL}/{subdomain_mode}/busca/lista?termo={query}&{f}"

    async def safe_load(self, page: Page, timeout: int = 5) -> None:
        """
        Aguarda o carregamento da página de resultados.

        Caso o tempo expire, tenta garantir se a ausência de resultados é legítima.

        Args:
            page (Page): Página da busca.
            timeout (int): Tempo máximo de espera (em segundos).

        Raises:
            ValueError: Se o elemento de resultados não for encontrado.
        """
        try:
            await page.wait_for_selector(self.selector.results, timeout=timeout * 1000)
        except Exception as _:
            # Se o timeout ocorrer, tenta extrair o elemento de contagem de resultados
            # para garantir que realmente não há resultados
            await page.wait_for_selector(
                self.selector.results_count_selector, timeout=timeout * 1000
            )
            he = await page.query_selector(self.selector.results_count_selector)
            if not he:
                raise RuntimeError("A página não pode ser carregada corretamente")

            results_count = await self.parse_results_count(he)
            if (
                results_count == -1
            ):  # neste caso, o elemento foi encontrado, mas o texto é um placeholder
                raise RuntimeError(
                    "A página não pode ser carregada corretamente. O elemento de contagem de resultados não possui texto válido."
                )

    def __resolve_mode(self, mode: str) -> str:
        """
        Retorna o subdomínio correspondente ao modo de busca.

        Args:
            mode (str): Modo ("cpf" ou "cnpj").

        Returns:
            str: Subdomínio correspondente.

        Raises:
            ValueError: Se o modo for inválido.
        """
        if mode not in self.MODES:
            raise ValueError(f"Invalid mode: {mode}")
        return self.MODES[mode]

    def __validate_filter(
        self, _filter: CNPJSearchFilter | CPFSearchFilter, mode: Literal["cnpj", "cpf"]
    ) -> None:
        """
        Valida se o filtro informado é compatível com o modo de busca.

        Args:
            _filter (CNPJSearchFilter | CPFSearchFilter): Filtro a ser validado.
            mode (Literal["cnpj", "cpf"]): Modo de busca.

        Raises:
            ValueError: Se o filtro não corresponder ao modo.
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
        Determina o modo de busca com base na URL.

        Args:
            url (str): URL acessada.

        Returns:
            Literal["cpf", "cnpj"]: Modo identificado.

        Raises:
            ValueError: Se a URL não contiver um modo reconhecido.
        """
        if "pessoa-fisica" in url:
            return "cpf"
        elif "pessoa-juridica" in url:
            return "cnpj"
        else:
            raise ValueError(f"Invalid URL: {url}")

    def __calculate_page_count(self, total_results: int) -> int:
        """
        Calcula o número de páginas com base no total de resultados.

        Args:
            total_results (int): Quantidade de resultados identificados.

        Returns:
            int: Número de páginas necessárias (máx. 200 resultados).
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
        Navega para a próxima página da lista de resultados.

        Args:
            page (Page): Página atual.
            current_page (int): Número da página atual.
            total_pages (int): Número total de páginas disponíveis.

        Raises:
            ValueError: Se o botão de próxima página não for encontrado.
        """
        if current_page < total_pages:
            next_button = await page.locator(
                "ul.pagination > li.next > a"
            ).element_handle()

            if not next_button:
                raise ValueError("Não foi possível encontrar o botão de próxima página")

            await next_button.click(delay=100)
            await page.wait_for_timeout(1000 * 10)


async def main():
    searcher = Searcher()
    result = await searcher.search("", mode="cnpj", max_results=True)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
