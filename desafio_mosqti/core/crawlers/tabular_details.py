import asyncio
from typing import Any

from playwright.async_api import ElementHandle, Page, async_playwright

from desafio_mosqti.core.elements_selectors.selector import TabularDetailsSelector
from desafio_mosqti.core.interfaces.base_details import BaseDetails


class TabularDetails(BaseDetails):
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

    async def fetch(self, url: str, raise_for_captcha: bool = True, **kwargs) -> dict[str, Any]:
        """
        Coleta todos os dados de uma página tabular do Portal da Transparência.

        Realiza a ativação das seções expansíveis, extrai os dados da seção principal
        ("dados tabelados") e das seções detalhadas (que podem conter blocos ou tabelas),
        e normaliza as chaves para um formato padronizado.

        Args:
            url (str): URL da página tabular.
            raise_for_captcha (bool, optional): Se True, levanta uma exceção se um captcha for detectado. Defaults to True.

        Returns:
            dict: Dicionário contendo os dados extraídos da página, com as chaves normalizadas.
        """
        await self.page.goto(url)

        # Espera a página carregar
        await self.page.wait_for_load_state("networkidle")

        # Verifica se a página contém um captcha
        if await self.captcha_check_detector(self.page):
            self.logger.critical(
                "Captcha detectado. A página não pode ser processada.",
                extra={"url": url},
            )
            if raise_for_captcha:
                raise Exception("Captcha detectado na página.")
            
            return {
                "error": "Registros foram encontrados, mas a página não pode ser processada.",
                "url": url,
                "identifier": "captcha_detected",
            }

        # ativa todos os detalhes
        await self.__activate_all_detailed_sections(self.page)

        # coleta os dados
        tabulated_data = await self.__collect_data_from_tabulated_section(self.page)

        dateiled_data = await self.__collect_data_from_detailed_section(self.page)

        data = {
            "dados_tabelados": tabulated_data,
            "dados_detalhados": dateiled_data,
        }

        # Normaliza as chaves
        data = await self.__normalize_keys(data)

        return data

    async def __activate_all_detailed_sections(self, page: Page):
        """
        Ativa todas as seções expansíveis de dados detalhados na página.

        Algumas seções requerem interação para revelar seu conteúdo. Essa função simula
        o clique em cada botão de expansão, caso a seção ainda não esteja ativa.

        Args:
            page (Page): Instância da página carregada.
        """

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

    async def __collect_data_from_tabulated_section(self, page: Page) -> dict:
        """
        Extrai os dados da seção principal "dados tabelados".

        Esta seção contém informações em formato de formulário, com chave e valor,
        possivelmente com múltiplas colunas por linha.

        Args:
            page (Page): Página onde os dados serão extraídos.

        Returns:
            dict: Dicionário com pares chave-valor extraídos da seção principal.
        """
        data = {}
        section = await page.query_selector(self.selector.dados_tabelados)
        if not section:
            return data
        rows = await section.query_selector_all(self.selector.row)
        if not rows:
            return data

        for row in rows:
            data.update(await self.__extract_key_value_pairs(row))
        return data

    async def __collect_data_from_detailed_section(self, page: Page) -> dict:
        """
        Coleta os dados de todas as seções de "dados detalhados" da página.

        Cada seção pode conter:
        - Um bloco de dados em formato chave-valor.
        - Uma tabela com cabeçalho e múltiplas linhas (datatable).

        O conteúdo é organizado por título de seção.

        Args:
            page (Page): Página a ser processada.

        Returns:
            dict: Dicionário contendo os dados extraídos por seção.
        """
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

            # Aqui existem dois seletores, pois os dados podem estar em div.bloco
            # ou div.br-accordion
            data_block = (
                await section.query_selector(self.selector.data_block) or None
            ) or (await section.query_selector(self.selector.data_accordion) or None)
            if not data_block:
                continue

            inner_section_data[f"block_{title}"] = await self.__extact_data_block(
                data_block
            )

            data_table_el = await section.query_selector(
                self.selector.data_table_container
            )
            if data_table_el:
                inner_section_data[f"datatable_{title}"] = (
                    await self.__extract_data_table(data_table_el)
                )
            data[title] = inner_section_data

        return data

    async def __extact_data_block(self, datablock: ElementHandle) -> dict:
        """
        Extrai os dados de um bloco do tipo formulário (chave-valor).

        Usado em seções de dados detalhados que possuem múltiplas colunas com pares chave-valor.

        Args:
            datablock (ElementHandle): Elemento contendo os dados do bloco.

        Returns:
            dict: Dicionário com os pares extraídos.
        """
        rows = await datablock.query_selector_all(self.selector.row)
        if not rows:
            return {}
        data = {}
        for row in rows:
            data.update(await self.__extract_key_value_pairs(row))
        return data

    async def __extract_key_value_pairs(
        self,
        container: ElementHandle,
    ) -> dict[str, str]:
        """
        Extrai pares chave-valor de um container com colunas estruturadas.

        Este método é utilizado para processar blocos do tipo formulário, onde cada coluna
        contém uma célula com a chave (label) e uma célula com o valor correspondente.

        Args:
            container (ElementHandle): Elemento HTML contendo as colunas a serem extraídas.

        Returns:
            dict[str, str]: Dicionário com os pares extraídos do container.
        """
        data = {}
        columns = await container.query_selector_all(self.selector.col)
        if not columns:
            return data

        for column in columns:
            key = await column.query_selector(self.selector.cell_key)
            value = await column.query_selector(self.selector.cell_value)
            if not key or not value:
                continue
            key_text = await key.inner_text()
            value_text = await value.inner_text()
            data[key_text] = value_text
        return data

    async def __extract_data_table(self, table_container: ElementHandle) -> list:
        """
        Extrai os dados de uma tabela tabular com cabeçalho e múltiplas linhas.

        Cada linha representa um registro. O cabeçalho é incluído como a primeira linha da lista.

        Args:
            table_container (ElementHandle): Elemento que contém a tabela a ser processada.

        Returns:
            list: Lista de listas, onde a primeira linha contém os cabeçalhos, seguida pelos registros.
                Caso a tabela não contenha registros, retorna uma lista com o cabeçalho e uma mensagem
                padrão: ["Nenhum registro encontrado"].
        """

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

    async def __normalize_keys(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Normaliza as chaves de um dicionário recursivamente.

        Remove espaços, converte para minúsculo e substitui espaços por underscore.
        Aplica-se a chaves internas em dicionários aninhados ou listas de dicionários.

        Args:
            data (dict): Dicionário com as chaves originais.

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
                    (
                        await self.__normalize_keys(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                normalized_data[normalized_key] = value
        return normalized_data


async def main():
    # url = "https://portaldatransparencia.gov.br/despesas/pagamento/280101000012015NS001415?ordenarPor=fase&direcao=desc"
    url = "https://portaldatransparencia.gov.br/notas-fiscais/25231008761132000148558929001316531207162194?ordenarPor=dataEvento&direcao=asc"
    tabular_details = TabularDetails(page=None)
    data = await tabular_details.fetch(url)
    print(data)


if __name__ == "__main__":
    asyncio.run(main())
