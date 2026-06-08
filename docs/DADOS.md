# Dados

Este projeto usa arquivos locais do **StatsBomb Open Data** para as Copas do Mundo de 2018 e 2022.

Fonte oficial:

- Repositorio: https://github.com/statsbomb/open-data
- Documentacao dos eventos: https://github.com/statsbomb/open-data/tree/master/doc

Referencia recomendada no projeto:

> Data source: StatsBomb Open Data. Data available at https://github.com/statsbomb/open-data.

Observacao sobre termos de uso:

- Ao publicar, compartilhar ou distribuir analises feitas com esses dados, declare a fonte como **StatsBomb**.
- A README oficial do StatsBomb Open Data tambem solicita o uso do logo da StatsBomb quando houver publicacao, apresentacao ou distribuicao de analises baseadas nos dados.
- Verifique sempre os termos atuais no repositorio oficial antes de publicar material final.

## Estrutura esperada

O dashboard espera encontrar os dados na raiz do projeto:

```text
world_cup_data/
  matches/
    world_cup_2018.json
    world_cup_2022.json
  events/
    2018/
    2022/
  three-sixty/
    2018/
    2022/
```

Neste repositorio, essas pastas ficam no `.gitignore` para evitar subir centenas de MB ao GitHub.

## Como obter os dados

O reposititorio oficial organiza os arquivos em uma arvore propria:

```text
open-data/data/
  matches/43/3.json      # FIFA World Cup 2018
  matches/43/106.json    # FIFA World Cup 2022
  events/{match_id}.json
  three-sixty/{match_id}.json
```

Para montar a estrutura esperada por este dashboard:

1. Baixe ou clone o StatsBomb Open Data:

```bash
git clone https://github.com/statsbomb/open-data.git
```

2. Na raiz deste projeto, rode o script de preparacao:

```bash
python tools/prepare_statsbomb_worldcup_data.py --source CAMINHO/para/open-data
```

Tambem funciona apontando diretamente para `open-data/data`:

```bash
python tools/prepare_statsbomb_worldcup_data.py --source CAMINHO/para/open-data/data
```

3. Rode o dashboard:

```bash
python -m streamlit run app.py
```

Os dados copiados ficam apenas na sua maquina local e continuam ignorados pelo Git.

## Limite metodologico

Mesmo com a pasta `three-sixty`, este dashboard trata a base como majoritariamente de eventos. As metricas de valor ofensivo sao inspiradas em xT/VAEP/EPV, mas nao substituem um modelo com tracking completo dos 22 jogadores.
