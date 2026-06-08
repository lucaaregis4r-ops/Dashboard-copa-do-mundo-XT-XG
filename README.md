# World Cup Performance Dashboard

Dashboard local em `Streamlit` para analisar Copas do Mundo de 2018 e 2022 com dados StatsBomb Open Data.

**Marca/autoria:** Lucas Regis  
**Contato:** lucaaregis4r@gmail.com  
**Fonte dos dados:** StatsBomb Open Data

O objetivo do app e apoiar analise de desempenho com perguntas de futebol: territorio, sequencias, perigo ofensivo, comparacao entre equipes/jogadores e confiabilidade do recorte. A interface prioriza leitura de jogo; os metodos estatisticos ficam como apoio.

## Como Rodar

```bash
python -m streamlit run app.py
```

No Windows, tambem e possivel abrir pelos launchers:

```bat
Abrir_Dashboard.bat
Abrir_Dashboard_Console.bat
```

Esses launchers usam os executaveis em `dist/` e gravam a porta real em `dashboard_port.txt`. Assim, se `8501` ja estiver ocupada por uma sessao antiga, o navegador abre a porta correta do dashboard novo. Se o executavel antigo nao criar esse arquivo, o `.bat` espera alguns segundos e procura uma porta Streamlit ativa entre `8501` e `8525`.

Se estiver usando ambiente virtual:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```

## Dados

O dashboard usa dados locais do **StatsBomb Open Data**.

Fonte oficial:

- https://github.com/statsbomb/open-data
- Documentacao: https://github.com/statsbomb/open-data/tree/master/doc

Referencia recomendada:

```text
Data source: StatsBomb Open Data. Data available at https://github.com/statsbomb/open-data.
```

Observacao: o repositorio oficial do StatsBomb Open Data pede que analises publicadas, compartilhadas ou distribuidas declarem a fonte como StatsBomb e usem o logo da StatsBomb quando aplicavel. Confira os termos atuais no repositorio oficial antes de publicar.

As pastas locais de dados ficam fora do Git por padrao:

```text
events/
matches/
three-sixty/
```

Isso evita subir centenas de MB ao GitHub. Para rodar o projeto apos clonar, baixe os dados no repositorio oficial e prepare a estrutura local com:

```bash
git clone https://github.com/statsbomb/open-data.git
python tools/prepare_statsbomb_worldcup_data.py --source open-data
```

O script copia apenas as Copas de 2018 e 2022 para o formato esperado pelo dashboard. Mais detalhes em `docs/DADOS.md`.

## Modo Relatorio/PDF

O dashboard tem um modo visual para exportacao manual em PDF pelo navegador.

Opcoes:

```powershell
$env:DASHBOARD_EXPORT_MODE="1"
python -m streamlit run app.py
```

Ou use a URL com parametro:

```text
http://localhost:8501/?export=1
```

No modo PDF, a sidebar e reduzida/ocultada por CSS de impressao, os cards usam fundo claro, os graficos usam texto escuro e as tabelas resumidas sao priorizadas. Para exportar, abra a pagina no navegador e use `Ctrl+P` / `Salvar como PDF`.

Melhorias visuais recentes:

- Tema claro com fundo `#F7F8FA`, cards brancos, bordas suaves e sombra leve.
- Cards responsivos com titulo, valor e contexto, evitando truncamento de valores comparativos.
- Comparacao de jogadores com cards lado a lado, nomes completos, xG, Delta xT, xG futuro associado, gols, assistencias e entradas.
- Graficos de comparacao e mix de acoes em barras horizontais, com fonte maior e legenda mais legivel.
- Mapas de acoes com legenda `Eventos`, tamanho consistente e resumo abaixo de cada mapa.
- Mapas de acoes com legenda externa por tipo de acao, sem HTML bruto no relatorio.
- Tabela resumida para relatorio/PDF e tabela completa mantida em expander para uso interativo.
- CSS `@media print` com quebras de pagina mais controladas e `break-inside: avoid` nos blocos principais.
- Paleta semantica fixa por tipo de acao: finalizacao, passe, conducao, drible, recepcao, pressao e recuperacao mantem a mesma cor em graficos e mapas.
- Graficos de mix mostram primeiro familias de acao e depois o detalhe por acao.
- Mapas de jogadores permitem filtrar finalizacoes, passes, conducoes, dribles e pressoes/recuperacoes.

## Estrutura

```text
world_cup_data/
  app.py
  context.md
  README.md
  docs/
    DADOS.md
    PUBLICACAO_GITHUB.md
  src/
    filters.py
    context.py
    narrative.py
    labels.py
    load_data.py
    preprocess.py
    markov.py
    bayes.py
    possession_value.py
    comparisons.py
    visualizations.py
    theme.py
    runner.py
  tools/
    prepare_statsbomb_worldcup_data.py
```

Pastas esperadas localmente, mas ignoradas no Git:

```text
matches/
events/
three-sixty/
```

## Paginas

O app agora usa uma estrutura de cockpit: primeiro o usuario define o **Contexto da Analise** na sidebar, depois navega por tabs de pergunta no painel principal.

Modos disponiveis:

- **Analisar uma selecao**
- **Comparar duas selecoes**
- **Analisar uma partida**
- **Comparar jogadores**
- **Comparacao visual**
- **Explorar torneio inteiro**

Tabs principais:

- **Resumo**: leitura geral do recorte, volume, selecoes, acoes e explorador estatistico.
- **Territorio**: eventos no campo, zonas e tercos.
- **Progressao**: avancos territoriais, tercos e mapas.
- **Ameaca**: xG como qualidade de finalizacao e valor futuro da posse para acoes antes do chute.
- **Caminhos**: caminhos de ameaca com proxima acao, zona, chance de finalizar, xG futuro e `delta_xt`.
- **Jogadores**: comparacoes e participacao individual.
- **Comparacao**: equipes ou jogadores lado a lado conforme o modo.
- **Confiabilidade**: amostra, estabilidade entre anos, similaridade e robustez.
- **Metodologia**: limites de xG, valor da posse, sequencias e dados de evento.

## Comparacao visual

O modo `Comparacao visual` monta uma tela mais limpa para screenshot/postagem.

- Comparacao de dois jogadores ou duas selecoes.
- Formatos de referencia: `16:9`, `1:1` e `4:5`.
- Cards curtos de producao e valor da posse.
- Graficos separados de `Producao final` e `Valor da posse`.
- Distribuicao de ameaca por tipo de acao em barras horizontais.
- Perfil de acoes com resumo por familia e mix detalhado.
- Mapas de acoes lado a lado, com resumo abaixo de cada mapa.
- Tabela resumida voltada para PDF.

## Metodologia

- O app usa somente arquivos locais; nao baixa dados externos.
- xG e tratado como qualidade de finalizacao, nao como explicacao completa do jogo.
- Passes, conducoes, dribles, recuperacoes e outras acoes nao recebem xG proprio; elas sao avaliadas pelo valor futuro da mesma posse.
- `future_xg` e calculado pela proxima finalizacao posterior na mesma posse; quando possivel, a posse usa `match_id`, `period`, `possession` e `possession_team_name`.
- Eventos do time sem bola dentro da posse adversaria nao recebem xG futuro ofensivo dessa posse.
- O app registra a origem da posse em `possession_id_source`: `statsbomb` ou `reconstruida`.
- O app usa um **modelo de valor de posse baseado em eventos**. Ele se inspira em xT/VAEP/EPV, mas nao e EPV completo porque nao usa tracking data.
- Para leitura visual, o campo usa zonas 3x3; para calculo de valor, o app usa uma grade refinada 12x8 em `value_state`.
- Para acoes com origem e destino, o valor principal e `delta_valor_posse = V_xg(destino) - V_xg(origem)`, com origem/destino na grade 12x8, em linha com a ideia do xT de comparar valor antes/depois da acao.
- `delta_xt` e um alias exploratorio desse mesmo delta de valor na grade 12x8; nao e uma tabela xT externa calibrada em base historica ampla.
- `future_xg` e chamado de xG futuro associado: ajuda a saber se a acao aparece antes de chances, mas pode duplicar o mesmo chute em varias acoes da posse e nao deve ser lido como xG proprio da acao.
- Comparacoes de equipes e jogadores cruzam producao final (`gols`, `assistencias`, `xG`) com criacao anterior ao chute (`delta_xt_total`, `xG futuro associado`, entradas na area e entradas no terco final).
- Passes incompletos sao tratados como perda de posse no calculo de destino, evitando progressao positiva artificial.
- Sequencias descrevem frequencias observadas no recorte filtrado; internamente usam cadeias de transicao simples e tambem agregam `delta_xt_medio` e `valor_caminho`.
- A camada de valor ofensivo usa eventos, zonas e progressao de passes/conducoes, com limitacoes por nao usar tracking data.
- Contextos com poucos eventos devem ser interpretados com cautela.

## Interface

- A interface principal evita textos longos no corpo do dashboard.
- Explicacoes teoricas ficam concentradas em `Notas Metodologicas` e em `docs/RELATORIO_METODOLOGICO.md`.
- Comparacoes separam producao final e valor da posse para nao misturar escalas demais no mesmo grafico.
- Narrativas automaticas usam frases curtas e cautelosas.
- A aba `Confiabilidade` mostra volume do recorte, chutes, posses, acoes relevantes e contextos com baixa amostra.


