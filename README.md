# World Cup Performance Dashboard

Dashboard local em Streamlit para analisar as Copas do Mundo de 2018 e 2022 com dados do StatsBomb Open Data.

**Autor:** Lucas Regis  
**Contato:** lucas.regis4r@gmail.com  
**Fonte dos dados:** StatsBomb Open Data

O app ajuda a analisar território, sequências, criação de chances, desempenho de equipes e jogadores e a confiabilidade de cada recorte. Os métodos estatísticos complementam a leitura do jogo.

## Executar

```bash
python -m streamlit run app.py
```

No Windows, também é possível abrir o app pelos launchers:

```bat
Abrir_Dashboard.bat
Abrir_Dashboard_Console.bat
```

Os launchers usam os executáveis em `dist/` e gravam a porta em `dashboard_port.txt`. Se a porta 8501 estiver ocupada, o navegador abre a porta disponível para a nova sessão. Se um executável antigo não criar esse arquivo, o `.bat` procura uma porta Streamlit ativa entre 8501 e 8525.

Com um ambiente virtual:

```bash
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```

## Dados

O dashboard lê arquivos locais do [StatsBomb Open Data](https://github.com/statsbomb/open-data). Consulte também a [documentação](https://github.com/statsbomb/open-data/tree/master/doc).

Ao publicar ou compartilhar análises, declare a fonte como StatsBomb e use o logotipo quando aplicável. Confira os termos atuais no repositório oficial.

As pastas `events/`, `matches/` e `three-sixty/` ficam fora do Git. Depois de clonar o projeto, baixe a base oficial e prepare os dados:

```bash
git clone https://github.com/statsbomb/open-data.git
python tools/prepare_statsbomb_worldcup_data.py --source open-data
```

O script copia apenas os dados das Copas de 2018 e 2022. Consulte `docs/DADOS.md` para mais detalhes.

## Exportar relatório em PDF

Ative o modo de exportação por variável de ambiente:

```powershell
$env:DASHBOARD_EXPORT_MODE="1"
python -m streamlit run app.py
```

Ou abra `http://localhost:8501/?export=1`. Depois, use `Ctrl+P` e escolha **Salvar como PDF**.

No modo de impressão, a sidebar é reduzida, os cards usam fundo claro, os gráficos usam texto escuro e as tabelas resumidas aparecem primeiro. Os estilos de impressão controlam as quebras de página e evitam dividir os blocos principais.

## Navegação

Na sidebar, escolha o contexto da análise e depois abra uma das áreas:

- **Analisar uma seleção**
- **Comparar duas seleções**
- **Analisar uma partida**
- **Comparar jogadores**
- **Comparação visual**
- **Explorar torneio inteiro**

As abas mostram resumo do recorte, território, progressão, ameaça, caminhos de ações, jogadores, comparação, confiabilidade e metodologia. Os mapas usam zonas 3×3 para leitura visual; filtros permitem selecionar ações e jogadores. A paleta por tipo de ação é consistente entre gráficos e mapas.

A comparação visual prepara imagens em formatos 16:9, 1:1 e 4:5. Ela pode colocar duas equipes ou dois jogadores lado a lado, com cards de produção e valor da posse, gráficos de ameaça por ação, perfis de ações, mapas e tabela para PDF.

## Metodologia e limites

- xG representa a qualidade da finalização; não explica o jogo inteiro.
- Passes, conduções, dribles e recuperações não recebem xG próprio. O app calcula o valor futuro da mesma posse.
- `future_xg` usa a próxima finalização da posse, identificada por `match_id`, `period`, `possession` e `possession_team_name` quando disponíveis. Ações do time sem a bola não recebem esse xG futuro.
- `possession_id_source` indica se o identificador veio do StatsBomb ou foi reconstruído.
- O valor da posse é calculado a partir dos eventos. O método se inspira em xT, VAEP e EPV, mas não é um EPV completo porque não usa tracking data.
- A leitura visual usa zonas 3×3. O cálculo usa uma grade 12×8 em `value_state`.
- Para ações com origem e destino, `delta_valor_posse = V_xg(destino) - V_xg(origem)`. `delta_xt` é um alias exploratório desse cálculo, não uma tabela xT calibrada em uma base histórica ampla.
- `future_xg` mostra se uma ação antecede chances de finalização. O mesmo chute pode aparecer em várias ações da posse; esse valor não é xG próprio da ação.
- As comparações cruzam gols, assistências e xG com criação antes do chute, delta xT, xG futuro associado e entradas na área ou no terço final.
- Passes incompletos contam como perda de posse no cálculo do destino.
- As sequências resumem frequências do recorte filtrado. O app também calcula `delta_xt_medio` e `valor_caminho`.
- O modelo de valor ofensivo usa eventos, zonas e progressão de passes e conduções, sem tracking data.
- Recortes com poucos eventos precisam ser interpretados com cautela.

Os detalhes metodológicos ficam em `Notas Metodológicas` e em `docs/RELATORIO_METODOLOGICO.md`. As narrativas automáticas usam frases curtas e cautelosas. A aba **Confiabilidade** mostra o tamanho do recorte, os chutes, as posses, as ações relevantes e os contextos com pouca amostra.

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
