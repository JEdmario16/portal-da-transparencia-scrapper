from desafio_mosqti.core.interfaces.base_crawler import BaseCrawler


class BaseDetails(BaseCrawler):
    """
    Base abstrata para detalhes de operações do portal da transparência.
    """

    def __init__(self, page) -> None:
        super().__init__(page)

    def fetch(
        self,
        url: str,
        recursive: bool = False,
        **kwargs,
    ) -> dict:
        """
        Coleta os dados de uma página de detalhes do Portal da Transparência.

        Args:
            url (str): URL da página de detalhes.
            recursive (bool, optional): Se True, percorre todas as páginas disponíveis. Defaults to False.

        Returns:
            dict: Dicionário com os dados coletados.
        """
        raise NotImplementedError("Método fetch não implementado.")
