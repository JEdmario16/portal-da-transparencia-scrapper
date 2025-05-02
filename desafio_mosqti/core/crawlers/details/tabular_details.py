from desafio_mosqti.core.interfaces.base_crawler import BaseCrawler
from desafio_mosqti.core.elements_selectors.selector import TabularDetailsSelector

from playwright.async_api import async_playwright, Page, ElementHandle
import asyncio


class TabularDetails(BaseCrawler):
    """
    Coletor de dados para páginas tabulares do Portal da Transparência.

    Esta classe lida com dois elementos principais na interface:
    - `div.dados-tabelados`: seções em formato de tabela simples (semelhante a um formulário), onde uma coluna pode ter mais de uma chave.
    - `div.dados-detalhados`: seções expansíveis que contêm tabelas com dados detalhados.

    Os dados detalhados podem conter até duas estruturas:
    - dados em bloco: cada linha possui várais células, estas por sua vez com uma chave e um valor. Essa estrutura é semelhante a um formulário.
    - datatable: uma tabela com cabeçalho e várias linhas, onde cada linha representa um registro. Essa estrutura é semelhante a uma tabela de banco de dados.

    Os dados retornados tem o seguinte formato:
    ```python
    {
        "dados_tabelados": {
            "key1": "value1",
            "key2": "value2",
            ...
        },
        "dados_detalhados": {
            "section_title": {
                "block_data": {
                    "key1": "value1",
                    "key2": "value2",
                    ...
                },
                "datatable_data": [
                    ["header1", "header2", ...],
                    ["row1_col1", "row1_col2", ...],
                    ...
                ]
            },
            ...
        }
    }
    ```
    Em especial, caso datatable_data possua cabeçalhos mas não registros, o resultado será algo da forma:
    ```python
    {
        ...,
        "datatable_data": [
            ["header1", "header2", ...],
            ["Nenhum registro encontrado"]
        ]
    }

    """

    BASE_URL = "https://portaldatransparencia.gov.br"

    selector = TabularDetailsSelector()

    async def fetch(self, url: str):
        """
        Coleta os dados de uma página tabular do Portal da Transparência.

        Args:
            url (str): URL da página tabular.

        Returns:
            list[dict]: Lista de registros coletados, cada registro representado como um dicionário.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.set_extra_http_headers(self.default_headers)
            await page.goto(url)

            # Espera a página carregar
            await page.wait_for_load_state("networkidle")

            # ativa todos os detalhes
            await self.__activate_all_detailed_sections(page)

            # coleta os dados
            tabulated_data = await self.__collect_data_from_tabulated_section(page)

            dateiled_data = await self.__collect_data_from_detailed_section(page)

            await browser.close()

            data = {
                "dados_tabelados": tabulated_data,
                "dados_detalhados": dateiled_data,
            }


            # Normaliza as chaves
            data = await self.__normalize_keys(data)

            return data

    async def __activate_all_detailed_sections(self, page: Page):

        sections = await page.query_selector_all(self.selector.dados_detalhados)

        if not sections:
            return

        for section in sections:
            # verifica se a seção já está expandida
            item = await section.query_selector(self.selector.item)
            if item:
                is_active = await item.get_attribute("active") is not None
                if is_active:
                    continue

            button = await section.query_selector(
                self.selector.dados_detalhados_expand_button
            )
            if button:
                await button.click()

    async def __collect_data_from_tabulated_section(self, page: Page) -> list[dict]:
        """
        Coleta os dados de uma seção com dados tabelados.

        Args:
            section (ElementHandle): Seção tabulada a ser processada.

        Returns:
            list[dict]: Dados coletados da seção.
        """
        data = {}
        section = await page.query_selector(self.selector.dados_tabelados)
        if not section:
            return data
        rows = await section.query_selector_all(self.selector.row)
        if not rows:
            return data

        for row in rows:
            columns = await row.query_selector_all(self.selector.col)
            if not columns:
                continue
            for column in columns:
                key = await column.query_selector(self.selector.cell_key)
                value = await column.query_selector(self.selector.cell_value)
                if not key or not value:
                    continue
                key_text = await key.inner_text()
                value_text = await value.inner_text()
                data[key_text] = value_text
        return data

    async def __collect_data_from_detailed_section(
        self,
        page: Page,
    ):
        sections = await page.query_selector_all(self.selector.dados_detalhados)
        if not sections:
            return {}

        data = {}

        for section in sections:
            inner_section_data = {}
            # extrai o título da seção
            title_el = await section.query_selector(self.selector.section_title)
            if not title_el:
                continue
            title = await title_el.inner_text()
            data_block = await section.query_selector(self.selector.data_block)
            if not data_block:
                continue
            inner_section_data[f"{title}_block"] = await self.__extact_data_block(
                data_block
            )

            data_table_el = await section.query_selector(
                self.selector.data_table_container
            )
            if data_table_el:
                inner_section_data[f"{title}_block"] = await self.__extract_data_table(data_table_el)
            data[title] = inner_section_data
        return data

    async def __extact_data_block(
        self,
        datablock: ElementHandle,
    ) -> dict:
        rows = await datablock.query_selector_all(self.selector.row)
        if not rows:
            return {}
        data = {}
        for row in rows:
            columns = await row.query_selector_all(self.selector.col)
            if not columns:
                continue
            for column in columns:
                key = await column.query_selector(self.selector.cell_key)
                value = await column.query_selector(self.selector.cell_value)
                if not key or not value:
                    continue
                key_text = await key.inner_text()
                value_text = await value.inner_text()
                data[key_text] = value_text
        return data

    async def __extract_data_table(
        self,
        table_container: ElementHandle,
    ) -> list[dict]:

        data = []

        table_el = await table_container.query_selector(self.selector.data_table_table)
        if not table_el:
            return data

        # extract headers
        headers = await table_el.query_selector_all(self.selector.table_headers)
        if not headers:
            return data

        headers_text = []
        for header in headers:
            text = await header.inner_text()
            headers_text.append(text)

        data.append(headers_text)

        # extract data
        rows = await table_el.query_selector_all("tbody tr")
        if not rows:
            return data

        for row in rows:
            inner_data = []
            # Coleta todas as células da linha
            cells = await row.query_selector_all("td")
            if not cells:
                continue
            # Coleta o texto de cada célula
            for cell in cells:
                # Verifica se a célula possui um link
                link = await cell.query_selector("a")
                if link:
                    # Se a célula possui um link, coleta o href
                    href = await link.get_attribute("href")
                    href = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                    inner_data.append(href)
                    continue
                text = await cell.inner_text()
                inner_data.append(text)
            data.append(inner_data)
        return data

    async def __normalize_keys(self, data: dict) -> dict:
        """
        Normaliza as chaves do dicionário para remover espaços e caracteres especiais.

        Args:
            data (dict): Dicionário com os dados a serem normalizados.

        Returns:
            dict: Dicionário com as chaves normalizadas.
        """
        normalized_data = {}
        for key, value in data.items():
            # Remove espaços e caracteres especiais
            normalized_key = key.strip().replace(" ", "_").lower()
            if isinstance(value, dict):
                normalized_data[normalized_key] = await self.__normalize_keys(value)
            elif isinstance(value, list):
                normalized_data[normalized_key] = [
                    await self.__normalize_keys(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized_data[normalized_key] = value
        return normalized_data
    
async def main():
    url = "https://portaldatransparencia.gov.br/despesas/pagamento/280101000012015NS001415?ordenarPor=fase&direcao=desc"
    tabular_details = TabularDetails()
    data = await tabular_details.fetch(url)
    print(data)

if __name__ == "__main__":
    asyncio.run(main())
