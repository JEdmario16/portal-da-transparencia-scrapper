# Desafio MOST QI
Para este projeto, decidi criar uma aplicação para coletar os dados e forma completa, adicionadno algumas funcionalidades extras.
Para que isso fosse possível, precisei utilizar diversas técnicas de desenvolvimento, como separação de responsabilidades, abstração, encapsulamento e polimorfismo. 
Meu objetivo com isso foi, além de atender ao desafio, exibir também um pouco do meu conhecimento em desenvolvimento de software,
o que acredito ser precioso durante a aavaliação do desafio.

Abaixo destaco algumas das funcionalidades que foram implementadas:
- Extração de dados de CPF e CNPJ
- Extração de todos os tipos de detalhes, não se limitando aos benefícios
- Métodos para escapar de possíveis Captchas e bloqueios
- Logs de erros e informações
- Programação assíncrona
- Separação de responsabilidades
- Documentação do código

A parte II do desafio também foi implementada, utilizando o FastAPI como framework. O fato do FAST API usar um WSGI, torna a aplicação mais escalável em teoria(isso porque, mesmo com mecanismos para evitar captchas, invocar grandes quantidades de requisições seria necessário técnicas mais delicadas, como o uso de proxies, o que não foi implementado).

Para fazer com que a aplicação seja menos suscetível a alterações no site, os seletores foram escolhidos de forma bem cuidadosa, evitando o uso de seletores muito genéricos. Além disso, diversas vezes optei por trabalhar com a URL diretamente, ao invés de interagir de fato com o DOM. Como exemplo, a filtragem de resultados é feita através de parâmetros na URL, ao invés de de fato interagir com o DOM.

# Exemplos de requisições

### Requisição para buscar CPF
```bash
curl -X 'GET' \
  'https://desafio-mosqti-production.up.railway.app/busca_cpf?query=123456&extract_details=false&search_result_limit=11&store_data_in_gdrive=true&servidor_publico=true&beneficiario_programa_social=true&favorecido_recurso=true' \
  -H 'accept: application/json'
  ```

# Acessos
[URL da aplicação](https://desafio-mosqti-production.up.railway.app/docs-mkdocs)

[Repositório](https://github.com/JEdmario16/desafio-mosqti)

[Pasta no Google Drive com os dados coletados](https://drive.google.com/drive/u/0/folders/1LtnBW5gjG_yBacHyt70MtmSGLlFp9pII)
