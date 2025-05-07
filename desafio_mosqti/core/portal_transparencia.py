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

import random
import re
from urllib.parse import urlparse

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loguru import Logger
    from desafio_mosqti.core.interfaces.base_details import BaseDetails

class PortalTransparencia:
    """
    Classe principal para orquestrar a coleta de dados do Portal da Transparência.

    Esta classe integra os componentes de busca (Searcher), extração de links de detalhes (DetailsLinks),
    e coleta dos dados detalhados (TabularDetails, ConsultDetails). Permite a coleta de dados em lote
    com randomização de contexto (user-agent, timezone, etc) para evitar bloqueios e fingerprinting.
    """
    # Mapeamento estático de caminhos de URL para a classe de detalhamento correspondente.
    DETAIL_PAGE_MAP = {
        # Dados tabulares
        "servidores": TabularDetails,  # servidor / inativo
        "beneficios": TabularDetails,  # recebimento de recursos
        "imoveis-funcionais": ConsultDetails,  # imóveis funcionais
        "despesas": ConsultDetails,  # favorecido de recursos
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

    # Parâmetros de randomização do contexto do navegador
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Linux; U; Linux i684 ; en-US) AppleWebKit/600.41 (KHTML, like Gecko) Chrome/47.0.1935.258 Safari/603",
        "Mozilla/5.0 (Linux; Linux x86_64; en-US) Gecko/20100101 Firefox/57.7",
        "Mozilla/5.0 (Linux; U; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/54.0.2192.241 Safari/600"
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    ]

    VIEWPORTS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1280, "height": 720},
    ]

    TIMEZONES = [
        "America/Sao_Paulo",
        "America/New_York",
        "Europe/London",
    ]

    LOCALES = [
        "pt-BR",
        "en-US",
        "es-ES",
    ]


    def __init__(self, headless: bool = False, logger: Logger | None = None):
        """
        Inicializa o orquestrador do portal.

        Args:
            headless (bool): Define se o navegador será executado em modo invisível.
            logger (Logger, opcional): Logger customizado. Se não for fornecido, usa o logger padrão.
        """
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless

        if not logger:
            from desafio_mosqti.core.loger import logger

        self.logger = logger

    async def __aenter__(self):
        """
        Inicializa o Playwright, navegador e prepara os contextos.
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            ignore_default_args=["--enable-automation"],
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        self.contexts = []
        self.pages = []
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Fecha todas as páginas, contextos e o navegador ao encerrar o uso com 'async with'.
        """
        await self.browser.close()
        await self.playwright.stop()

        for page in self.pages:
            try:
                await page.close()
            except Exception as e:
                pass
            finally:
                self.pages.remove(page)

        for context in self.contexts:
            try:
                await context.close()
            except Exception as e:
                pass
            finally:
                self.contexts.remove(context)

        # Limpa os atributos para evitar vazamentos de memória
        self.playwright = None
        self.browser = None
        self.contexts = []
        self.pages = []
    async def __randomize_context(self, browser: Browser) -> BrowserContext:
        """
        Cria um novo contexto de navegador com fingerprint aleatório para evitar bloqueios.

        Args:
            browser (Browser): Instância do navegador.
        Returns:
            BrowserContext: Novo contexto do navegador.
        """

        ctx_data = {
            "user_agent": random.choice(self.USER_AGENTS),
            "viewport": random.choice(self.VIEWPORTS),
            "timezone_id": random.choice(self.TIMEZONES),
            "locale": random.choice(self.LOCALES),
            "device_scale_factor": random.uniform(1, 2),
            "color_scheme": random.choice(["light", "dark"]),
            "has_touch": random.choice([True, False]),
        }
        # Cria um novo contexto com os dados aleatórios
        return await browser.new_context(
            **ctx_data,
        )

    async def __new_page(self) -> Page:
        """
        Cria uma nova página em um contexto randomizado.

        Returns:
            Page: A nova página criada.
        """
        # Cria um novo contexto com um user agent aleatório
        context = await self.__randomize_context(self.browser)
        self.contexts.append(context)
        # Cria uma nova página no contexto
        page = await context.new_page()
        self.pages.append(page)
        return page

    async def search(
        self,
        query: str,
        *,
        mode: Literal["cpf", "cnpj"] = "cpf",
        max_results: bool = True,
        _filter: Optional[Union[CPFSearchFilter, CNPJSearchFilter]] = None,
        extract_details: bool = False,
        search_result_limit: int | None = None,
    ):
        """
        Executa uma busca no portal da transparência por CPF ou CNPJ.

        Pode incluir extração dos links de detalhes e posterior raspagem dos detalhes.

        Args:
            query (str): CPF ou CNPJ a ser pesquisado.
            mode (Literal["cpf", "cnpj"], optional): Modo de pesquisa. Defaults to "cpf".
            max_results (bool, optional): Se True, limita o número de resultados por página para o máximo permitido. Defaults to True.
            _filter (Optional[Union[CPFSearchFilter, CNPJSearchFilter]], optional): Filtro a ser aplicado. Defaults to None.
            extract_details (bool, optional): Se True, extrai os detalhes dos resultados. Defaults to False.

        Returns:
            list[Union[CpfSearchResult, CnpjSearchResult]]: Lista de resultados da pesquisa.
        """
        page = await self.__new_page()

        async with Searcher(page=page, logger=self.logger) as searcher:
            search_results = await searcher.search(
                query,
                mode=mode,
                max_results=max_results,
                _filter=_filter,
            )

            if search_result_limit:
                search_results = search_results[:search_result_limit]
                

        self.logger.debug(
            f"Search result retuned successfully", extra={"count": len(search_results)}
        )

        if len(search_results) > 10 and extract_details:
            self.logger.warning(
                "Mais de 10 resultados encontrados. Extraindo detalhes pode levar um tempo considerável e pode causar bloqueios." \
                "Experimente usar filtros para reduzir o número de resultados, ou limitar os resultados de busca.",
            )

        if extract_details:
            search_results_links = await self.__get_details_links(search_results)
            for result in search_results_links:
                self.logger.debug(
                    f"Fetching details for {result.get("nome")}",
                    extra={"url": result.get("url")},
                )

                details, err_count = await self.__extract_all_details_from_search_result_links(
                    result["links"],
                )
                self.logger.debug(
                    f"Details fetched successfully",
                    extra={
                        "count": len(details),
                        "errors": err_count,
                    },
                )
                result["details"] = details
                result["details_links"] = result.pop("links", None)

                await asyncio.sleep(random.uniform(0.5, 2))
            return search_results_links
        return search_results

    async def __extract_all_details_from_search_result_links(
        self,
        search_result_links: dict,
    ) -> tuple[dict, int]:
        details = {}
        errors = 0
        for op_name, link in search_result_links.items():
            detail = await self.__extract_detail(
                url=link,
                page=self.page,
            )
            if detail:
                details[op_name] = detail

            if 'error' in detail:
                errors += 1
        return details, errors

    async def __extract_detail(
        self,
        url: str,
        *,
        page: Page | None = None,
        retries: int = 10,
    ):
        for attempt in range(retries):
            try:
                page = page or await self.__new_page()
                detail_page_class = await self.__discover_detail_page(url)
                if detail_page_class:
                    async with detail_page_class(page=page) as detail_page_cls:
                        should_raise_for_captcha = attempt > retries # do not raise when last attempt
                        return  await detail_page_cls.fetch(
                            url=url,
                            recursive=True,
                            raise_for_captcha= should_raise_for_captcha,
                        )
            except Exception as e:
                self.logger.warning(
                    f"Falaha ao extrair detalhes (tentativa {attempt + 1} de {retries}): {e}",
                )
                attempt += 1
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    async def __get_details_links(
        self,
        search_result: list[Union[CpfSearchResult, CnpjSearchResult]],
        *,
        page: Page | None = None,
    ) -> list:
        """
        Extrai os links de detalhes dos resultados da pesquisa.

        Args:
            search_result (Union[CpfSearchResult, CnpjSearchResult]): Resultados da pesquisa.

        Returns:
            list[DetailsLinks]: Lista de links de detalhes.
        """
        page = page or await self.__new_page()
        urls = []
        details_links = DetailsLinks(page)
        for sr in search_result:
            self.logger.debug(
                f"Fetching details links for {sr.nome}", extra={"url": sr.url}
            )
            # Verifica se o resultado possui um link de detalhes
            if sr.url:
                links = await details_links.fetch(
                    url=sr.url,
                )
                self.logger.debug(
                    f"Details links fetched successfully",
                    extra={"count": len(links), "keys": list(links.keys())},
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
        parts = urlparse(url).path.split("/")[1:-1]
        path = "/".join(parts)
        # Verifica se o path está no dicionário de mapeamento
        if path in self.DETAIL_PAGE_MAP:
            return self.DETAIL_PAGE_MAP[path]

        if (
            len(parts) > 1
        ):  # tenta verificar se o primeiro segmento do path está no dicionário de mapeamento
            if parts[0] in self.DETAIL_PAGE_MAP:
                return self.DETAIL_PAGE_MAP[parts[0]]

        if f"{parts[0]}/consulta" in self.DETAIL_PAGE_MAP:
            return self.DETAIL_PAGE_MAP[f"{parts[0]}/consulta"]
        
        self.logger.warning(
            f"Não foi possível descobrir a página de detalhes: {path} não está mapeado",
            extra={"url": url},
        )
        return None


async def main():

    async with PortalTransparencia(headless=True) as portal:
        # Exemplo de busca por CPF
        cpf_result = await portal.search(
            "",
            mode="cpf",
            max_results=False,
            extract_details=True,
            _filter=CPFSearchFilter(
                servidor_publico=True,
                beneficiario_programa_social=True,
                sancao_vigente=True,
            ),
        )
        print(cpf_result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
