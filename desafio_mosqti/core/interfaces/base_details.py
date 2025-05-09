import base64

from playwright.async_api import ElementHandle

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

    async def take_evidence(self, element: ElementHandle) -> str:
        """
        Tira uma captura de tela do elemento fornecido e retorna a imagem em base64.

        Args:
            element (ElementHandle): Elemento da página a ser salvo como evidência.

        Returns:
            str: Imagem em base64.
        """
        img = await element.screenshot()

        # transformar a imagem em base64
        base64_img = base64.b64encode(img).decode("utf-8")

        return base64_img
