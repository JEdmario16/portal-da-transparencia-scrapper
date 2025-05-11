# Desafio MOST QI
Para este projeto, decidi desenvolver uma aplicação robusta para coleta de dados, indo além do escopo básico proposto e adicionando algumas funcionalidades extras. Para isso, utilizei diversas técnicas de desenvolvimento, como separação de responsabilidades, abstração, encapsulamento e polimorfismo. Meu objetivo foi, além de atender aos requisitos do desafio, demonstrar minha familiaridade com boas práticas de desenvolvimento de software — algo que acredito ser valioso durante a avaliação.

Abaixo, destaco algumas das principais funcionalidades presentes no projeto:

- Extração de dados completos de CPF e CNPJ;

- Coleta de todos os tipos de informações disponíveis, não se limitando apenas aos benefícios;

- Mecanismos para contornar captchas e bloqueios automáticos;

- Registro de logs de erro e informações;

- Programação assíncrona para melhorar o desempenho;

- Separação clara de responsabilidades entre os módulos;

- Documentação automatizada do código.

A segunda parte do desafio foi implementada utilizando o FastAPI como framework principal. O uso desse framework, que roda sobre ASGI (e não WSGI), oferece maior escalabilidade para aplicações assíncronas — o que é útil, já que múltiplas requisições podem ser feitas simultaneamente. Embora tenha implementado técnicas para minimizar o risco de bloqueio, o uso de proxies ainda seria necessário em ambientes de alta demanda, o que optei por não incluir nesta versão.

Busquei também tornar a aplicação mais resiliente a mudanças no site-alvo. Para isso, os seletores foram definidos com cuidado, evitando alvos genéricos e preferindo estratégias mais estáveis, como a manipulação direta da URL para filtrar resultados, evitando interações desnecessárias com o DOM.

## Desafios enfrentados
Ao optar por uma solução mais completa, a complexidade do projeto aumentou, o que naturalmente impactou o tempo de desenvolvimento. Inicialmente, esperava lidar com muitas variações entre os dados de CPF e CNPJ, mas após análise, percebi que ambos seguiam padrões semelhantes — o que permitiu consolidar a lógica em um único fluxo.

Um dos maiores desafios foi contornar os mecanismos de proteção do site, que frequentemente inserem captchas para bloquear automações. Isso exigiu muitos testes e tentativas até encontrar uma abordagem minimamente confiável.

Reconheço que alguns pontos ainda poderiam ser melhorados:

- A estrutura de logs está funcional, mas poderia ser mais organizada;

- O tratamento de erros pode ser refinado;

- Os schemas de dados poderiam ser mais bem definidos;

- Não foram implementados testes unitários, devido à limitação de tempo.

O tempo que levei para desenvolver foi dividido de acordo com minha disponibilidade, mas posso dizer que seria necessário
meia sprint de trabalho para concluir o projeto

O projeto está hospedado no Railway e os dados coletados são armazenados em uma pasta do Google Drive — ambas plataformas com as quais tenho familiaridade. A dockerização da aplicação foi simples, com exceção do uso do MkDocs, cuja configuração integrei diretamente ao projeto com FastAPI.

# Exemplos de requisições
> [!NOTE]
> Para testar requisições, recomendo fortemente utilizar a [documentação swagger](https://desafio-mosqti-production.up.railway.app/docs) da aplicação, que é mais amigável e intuitiva.
> Caso, por algum motivo, o site não esteja acessível, peço que entre em contato para que eu possa verificar o que ocorreu,
> já que a aplicação está rodando em um servidor com free tier e pode ter limitações de uso.

> ### Requisição para buscar CPF


```bash
curl -X 'GET' \
  'https://desafio-mosqti-production.up.railway.app/busca_cpf?query=123456&extract_details=false&search_result_limit=11&store_data_in_gdrive=true&servidor_publico=true&beneficiario_programa_social=true&favorecido_recurso=true' \
  -H 'accept: application/json'
  ```

# Acessos
[URL da aplicação](https://desafio-mosqti-production.up.railway.app/docs-mkdocs)

[Documentação da API](https://desafio-mosqti-production.up.railway.app/docs)

[Repositório](https://github.com/JEdmario16/desafio-mosqti)

[Pasta no Google Drive com os dados coletados](https://drive.google.com/drive/u/0/folders/1LtnBW5gjG_yBacHyt70MtmSGLlFp9pII)
