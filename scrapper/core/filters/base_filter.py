from pydantic import BaseModel


class BaseFilter(BaseModel):

    def build_url_params(self) -> str:
        """
        Constrói os parâmetros da URL a partir do esquema.

        Returns:
            :return: Parâmetros da URL
            :rtype: str
        """
        params = self.model_dump(exclude_none=True, exclude_defaults=True)
        return "&".join(
            (
                f"{self.__key_parser(key)}={value.value}"
                if hasattr(value, "value")  # casos onde o valor é um Enum
                else f"{self.__key_parser(key)}={value}"
            )
            for key, value in params.items()
            if value is not None
        )

    def __key_parser(self, key: str) -> str:
        """
        As chaves armazenadas na classe de filtro usam snake_case(pythonico), mas
        os parâmetros da URL são em camelCase. Esse método transforma a chave
        pythonica em camelCase.
        Exemplo:
            - snake_case: "servidor_publico"
            - camelCase: "servidorPublico"
        """

        return "".join(
            word.capitalize() if i != 0 else word
            for i, word in enumerate(key.split("_"))
        )
