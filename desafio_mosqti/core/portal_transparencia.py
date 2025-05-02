from typing import Literal, Optional, Union

from playwright.async_api import async_playwright

from desafio_mosqti.core.crawlers import ConsultDetails, DetailsLinks, Searcher
from desafio_mosqti.core.filters import CNPJSearchFilter, CPFSearchFilter
from desafio_mosqti.core.schemas.search_result import CnpjSearchResult, CpfSearchResult


class PortalTransparencia:
    """
    Classe para acessar coletar dados do portal da transparência.
    """

    def __init__(self, base_url: str = "https://portaldatransparencia.gov.br"):
        self.base_url = base_url
        self.searcher = Searcher()
        self.details_links = DetailsLinks()
        self.consult = ConsultDetails()

    async def search(
        self,
        query: str,
        *,
        mode: Literal["cpf", "cnpj"] = "cpf",
        _filter: Optional[Union[CPFSearchFilter, CNPJSearchFilter]] = None,
        **kwargs
    ) -> list[CpfSearchResult | CnpjSearchResult]:
        """
        Realiza uma busca no portal da transparência.

        Args:
            query (str): CPF ou CNPJ a ser buscado.
            mode (str): Modo de busca. Pode ser "cpf" ou "cnpj".
            _filter (Optional[Union[CPFSearchFilter, CNPJSearchFilter]]): Filtro a ser aplicado na busca.
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

        result = await self.searcher.search(
            query=query, mode=mode, _filter=_filter, **kwargs
        )
        return result
