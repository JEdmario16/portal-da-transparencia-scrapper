import asyncio

from playwright.async_api import ElementHandle, Page, async_playwright

from desafio_mosqti.core.elements_selectors.selector import \
    ConsultDetailsSelector
from desafio_mosqti.core.interfaces.base_crawler import BaseCrawler


class ConsultDetails(BaseCrawler):
    """
    Crawler para coletar detalhes de consultas.

    Uma consulta é uma página padronizada do portal da transparência que é reutilizado em várias operações de detalhamento.
    Ela fornecesse os dados em forma de tabela, possui filtros e paginação.

    Esta classe é capaz de extrair os dados de uma consulta e retornar os resultados em um formato padronizado. É possível extrair
    os dados de uma única página ou de todas as páginas disponíveis, dependendo do parâmetro `recursive`.

    Operações que utilizam este layout:
    - Consulta de Recursos Publicos
    - Consulta de Viagens á Serviços
    - Uso do cartão de Pagamento do Governo Federal ou da Defesa Civil
    - Consulta de imóveis funcionais cedidos
    - Contratos firmados com o Governo Federal
    - Notas fiscais emitidas

    Algumas dessas operações possui botões de detalhes mais específicos que **NÃO** são suportados por este crawler. Ao invés disso,
    apenas coletamos o link, se disponível, para que um crawler específico possa coletar os dados.

    Exemplo de uso:
        ```python
        from desafio_mosqti.core.crawlers.details.consult import ConsultDetails

        async def main():
            url = "https://portaldatransparencia.gov.br/cartoes/consulta?portador=7710354&ordenarPor=mesExtrato&direcao=desc" # exemplo com Cartão de Pagamento
            consult_details = ConsultDetails()
            data = await consult_details.fetch(url)
            print(data)

        asyncio.run(main())
        ```
    """

    BASE_URL = "https://portaldatransparencia.gov.br"

    selector = ConsultDetailsSelector()

    async def fetch(self, url: str, recursive: bool = False):
        """
        Coleta os dados de uma página de consulta do Portal da Transparência.

        Args:
            url (str): URL da página de consulta.
            recursive (bool, optional): Se True, percorre todas as páginas disponíveis. Defaults to False.

        Returns:
            list[dict]: Lista de registros coletados, cada registro representado como um dicionário.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)

            page = await browser.new_page()
            # Adiciona os headers customizados
            await page.set_extra_http_headers(self.default_headers)

            await page.goto(url)

            data = await self.collect_data(
                page, include_header=True, recursive=recursive
            )
            await browser.close()
            return data

    async def collect_data(
        self,
        page: Page,
        include_header: bool = False,
        recursive: bool = False,
        set_max_results: bool = True,
    ) -> list[dict]:
        """
        Coleta os dados da tabela de uma página de consulta iterando sobre suas linhas.
        Caso a consulta seja profunda, coleta os dados de todas as páginas disponíveis.

        Args:
            page (Page): Página atual de consulta.
            include_header (bool, optional): Se True, inclui os cabeçalhos da tabela no início dos dados. Defaults to False.
            recursive (bool, optional): Se True, coleta dados de todas as páginas disponíveis. Defaults to False.

        Returns:
            list[dict]: Dados coletados da(s) página(s).
        """

        await self.__safe_load(page)
        if set_max_results:
            await self.__set_max_results_per_page(page)

        table = await page.query_selector(self.selector.table_selector)
        if not table:
            return []

        data = []
        if include_header:
            # Coleta os cabeçalhos da tabela
            headers = await self.get_table_headers(table)
            data.append(headers)

        # Coleta os dados da tabela
        body_data = await self.get_table_data(table)
        data.extend(body_data)

        # Se a consulta for profunda, coleta os dados de todas as páginas
        if recursive:
            has_next = await self.__next_page(page)
            if not has_next:
                return data

            # Coleta os dados da próxima página

            next_page_data = await self.collect_data(
                page, include_header, recursive, set_max_results=False
            )  # set_max_results=False para não repetir a configuração de resultados por página
            data.extend(next_page_data)
        return data

    async def get_table_headers(self, table: ElementHandle) -> list[str]:
        """
        Extrai os cabeçalhos da tabela.

        Args:
            table (ElementHandle): Elemento da tabela.

        Returns:
            list[str]: Lista de nomes das colunas.
        """
        # Coleta todos os cabeçalhos da tabela
        headers = await table.query_selector_all(self.selector.table_headers)
        if not headers:
            return []

        # Coleta o texto de cada cabeçalho
        headers_text = []
        for header in headers:
            text = await header.inner_text()
            headers_text.append(text)
        return headers_text

    async def get_table_data(self, table: ElementHandle) -> list[dict]:
        """
        Extrai os dados de todas as linhas da tabela. Caso a célula possua um link, coleta o href.
        Caso contrário, coleta o texto.

        Args:
            table (ElementHandle): Elemento da tabela.

        Returns:
            list[dict]: Lista de registros, onde cada registro é uma lista de valores por célula.
        """
        # Coleta todas as linhas da tabela
        rows = await table.query_selector_all("tbody tr")
        if not rows:
            return []

        # Coleta os dados de cada linha
        data = []
        for row in rows:
            # Coleta todas as células da linha
            cells = await row.query_selector_all("td")
            if not cells:
                continue

            # Coleta o texto de cada célula
            row_data = []
            for cell in cells:

                # Verifica se a célula possui um link
                link = await cell.query_selector("a")
                if link:
                    # Se a célula possui um link, coleta o href
                    href = await link.get_attribute("href")
                    row_data.append(href)
                    continue

                # Se não possui link, coleta o texto
                text = await cell.inner_text()
                row_data.append(text)

            # Adiciona os dados da linha à lista de dados
            data.append(row_data)

        return data

    async def __safe_load(self, page: Page):
        """
        Aguarda o carregamento da tabela principal e o término dos elementos de loading.

        Args:
            page (Page): Página atual.
        """

        await page.wait_for_selector(
            self.selector.loading_selector,
            state="hidden",
            timeout=5000,
        )

        await page.wait_for_selector(
            self.selector.table_selector,
            state="attached",  # attached: o elemento está no DOM, mas não necessariamente visível
            timeout=5000,
        )

    async def __next_page(self, page: Page) -> bool:
        """
        Avança para a próxima página de resultados se disponível.

        Args:
            page (Page): Página atual.

        Returns:
            bool: True se houve navegação para próxima página, False caso contrário.
        """
        next_page = await page.locator(self.selector.next_page).element_handle()
        if not next_page:
            return False

        # checa se o botão está habilitado
        is_disabled = False
        class_name = await next_page.get_attribute("class")
        if class_name and "disabled" in class_name:
            is_disabled = True

        if is_disabled:
            return False
        await next_page.click(delay=100)
        return True

    async def __set_max_results_per_page(self, page: Page) -> None:
        """
        Define o número máximo de resultados exibidos por página para facilitar a coleta.

        Args:
            page (Page): Página atual.
        """
        MAX_RESULTS_PER_PAGE = 30
        results_per_page = await page.query_selector(self.selector.results_per_time)

        if not results_per_page:
            raise ValueError(
                "Elemento de seleção de resultados por página não encontrado."
            )

        await results_per_page.scroll_into_view_if_needed()

        if not results_per_page:
            return

        # Define a quantidade de resultados por página
        await results_per_page.select_option(str(MAX_RESULTS_PER_PAGE))


async def main():
    # url = "https://portaldatransparencia.gov.br/despesas/favorecido?faseDespesa=3&favorecido=7710354&ordenarPor=valor&direcao=desc"
    # url = "https://portaldatransparencia.gov.br/cartoes/consulta?portador=7710354&ordenarPor=mesExtrato&direcao=desc"
    url = "https://portaldatransparencia.gov.br/despesas/pagamento/280101000012015NS001415?ordenarPor=fase&direcao=desc"
    consult_details = ConsultDetails()
    data = await consult_details.fetch(url, recursive=True)
    print(data)
    print(len(data))


if __name__ == "__main__":
    asyncio.run(main())
