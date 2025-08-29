from __future__ import annotations

import asyncio
import random
import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from logging import Logger

    from playwright.async_api import Page


class BaseCrawler(ABC):
    """
    Base abstrata para um crawler.
    """

    def __init__(self, page: Page, logger: Logger | None = None):
        if not logger:
            from scrapper.core.loger import logger as default_logger

            logger = default_logger
        self.logger = logger
        self.page = page
        self.ctx = page.context

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

    async def captcha_check_detector(
        self,
        page: Page,
    ):
        """
        Verifica se a página contém um captcha.

        Args:
            page (Page): Página a ser verificada.

        Returns:
            bool: True se o captcha estiver presente, False caso contrário.
        """
        page_title = await page.title()
        if "Human Verification" in page_title:
            return True
        return False

    async def __aenter__(self) -> Self:
        """
        Método chamado ao entrar no contexto do gerenciador de contexto.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Método chamado ao sair do contexto do gerenciador de contexto.
        """
        ...
