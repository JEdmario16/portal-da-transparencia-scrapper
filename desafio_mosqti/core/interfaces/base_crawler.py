from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

class BaseCrawler(ABC):
    """
    Base abstrata para um crawler.
    """

    def __init__(self, page: Page):
        self.page = page
        super().__init__()

    @property
    @abstractmethod
    def BASE_URL(self) -> str:
        """
        URL base do crawler.
        """
        pass

    @property
    def default_headers(self) -> dict[str, str]:
        """
        Headers padrão para o crawler.

        O site pode bloquear requisições sem um User-Agent válido.

        Returns:
            :return: Dicionário com os headers
            :rtype: dict

        """
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
