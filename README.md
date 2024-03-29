Para executar esse código é necessário ter o Python instalado. Versões mais recentes que a 3.10.9 devem funcionar com certeza

Uma vez com o Python instalado é necessário instalar as bibliotecas necessárias. Para isso, execute o seguinte comando dentro da pasta com esses arquivos:

`python -m pip install -r requirements.txt`

Após o término da instalação é possível executar o codigo da seguinte forma:

 - Crie uma pasta dentro da pasta `raw_files` e coloque dentro dela os arquivos pdf que você deseja processar
 - Supondo que a pasta que você criou se chama `exemplo`, o comando a ser executado é o seguinte: `python main.py exemplo`
   - Caso o nome da sua pasta contenha espaços será necessário colocar o nome dela entre aspas duplas
   - Ex: `python main.py "nome da minha pasta"`
 - O arquivo de saída estará na pasta `processed_files` dentro de uma pasta de mesmo nome que a sua, acrescida do horário de execução
 - Por padrão o código usa a biblioteca `ID_LIBRARY_TMS.xlsx` que está na pasta `templates`
   - Caso deseje utilizar outra biblioteca basta incluir o arquivo na pasta `templates` e executar o código com um parâmetro adicional:
   - `python main.py "nome da minha pasta" --lib nome_do_arquivo.xlsx`
