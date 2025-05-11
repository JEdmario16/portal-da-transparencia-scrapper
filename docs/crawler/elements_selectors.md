# Elements Selectors
As classes de seletores de elementos são simples dataclasses que definem os seletores como atributos. Desta forma, é possível referenciar aos seletores de forma mais legível e sem deixá-las hardcoded no código. Para facilitar o desenvolvimento, os atributos de classe são tipados como `Literal`, o que permite utilizar o editor para autocompletar os seletores disponíveis.
Além disso, pelo fato de serem dataclasses em um arquivo separado, é possível utilizar docstrings para documentar os seletores, o que facilita a manutenção e compreensão do código.

::: desafio_mosqti.core.elements_selectors.selector.SearcherSelector

::: desafio_mosqti.core.elements_selectors.selector.DetailsLinksSelector

::: desafio_mosqti.core.elements_selectors.selector.ConsultDetailsSelector

::: desafio_mosqti.core.elements_selectors.selector.TabularDetailsSelector