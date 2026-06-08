# Relatorio metodologico do dashboard

Este documento descreve a base teorica, o calculo matematico das variaveis e o funcionamento do dashboard de analise da Copa do Mundo com dados StatsBomb.

O ponto central da metodologia atual e separar tres ideias que costumam ser confundidas:

- **xG**: qualidade da finalizacao.
- **xG futuro associado**: xG de uma finalizacao posterior na mesma posse, associado a acoes anteriores.
- **Delta de valor da posse**: mudanca estimada do valor do estado da posse depois de uma acao.

Uma acao como passe, conducao, drible, recuperacao ou pressao nao recebe xG proprio. Ela pode ser associada a valor futuro se, depois dela, a mesma posse chega a uma finalizacao.

## 0. Referencias conceituais

O dashboard deve ser lido como um **modelo de valor de posse baseado em eventos, inspirado em xT/VAEP/EPV**, nao como um modelo completo de EPV com tracking.

Referencias conceituais:

- **Sarah Rudd / cadeias de Markov**: usa estados de posse e transicoes para estimar producao ofensiva esperada.
- **Expected Threat (xT), popularizado por Karun Singh**: valor de uma acao como diferenca entre valor da zona de destino e valor da zona de origem.
- **VAEP, de Decroos, Bransen, Van Haaren e Davis**: valor de uma acao como mudanca na probabilidade de marcar e/ou conceder depois da acao em relacao ao estado anterior.
- **EPV, de Fernandez e Bornn**: valor esperado da posse em cada instante, idealmente com dados espaco-temporais/tracking.

Como a base usada aqui e majoritariamente de eventos, o dashboard nao observa:

- movimento sem bola;
- linhas de passe disponiveis;
- pressao espacial completa;
- velocidade/posicionamento continuo dos 22 jogadores.

Por isso, os valores abaixo sao estimativas exploratorias baseadas em eventos.

## 1. Fonte dos dados e unidade de analise

O dashboard usa eventos StatsBomb Open Data das Copas de 2018 e 2022, carregados localmente a partir das pastas `matches/` e `events/`.

Cada linha principal do dataframe representa um evento com bola ou evento contextual do jogo. As colunas basicas vem de `src/load_data.py` e `src/preprocess.py`.

Principais identificadores:

- `match_id`: jogo.
- `year`: ano da Copa.
- `event_id`: identificador do evento.
- `index`: ordem do evento dentro da partida.
- `period`: periodo do jogo.
- `timestamp`, `minute`, `second`: tempo do evento.
- `team_name`: equipe que executou o evento.
- `player_name`: jogador.
- `action_type`: tipo de evento StatsBomb.
- `possession`: id de posse informado pela StatsBomb, quando disponivel.
- `possession_team_name`: equipe da posse.
- `event_team_in_possession`: indica se a equipe do evento e a equipe da posse.

## 2. Coordenadas, zonas e tercos do campo

StatsBomb usa um campo de 120 x 80:

- eixo `x`: 0 a 120, da defesa para o ataque.
- eixo `y`: 0 a 80, largura do campo.

### 2.1 Zona 3x3

O campo e dividido em 9 zonas:

```text
defesa esquerda | defesa centro | defesa direita
meio esquerda   | meio centro   | meio direita
ataque esquerda | ataque centro | ataque direita
```

Formalmente, para um evento com coordenadas `(x, y)`, a zona e atribuida por intervalos:

```text
defesa: 0 <= x < 40
meio:   40 <= x < 80
ataque: 80 <= x <= 120

esquerda: 0 <= y < 26.6667
centro:   26.6667 <= y < 53.3333
direita:  53.3333 <= y <= 80
```

Se `x` ou `y` estiver ausente, a zona vira `Unknown`.

### 2.2 Terco do campo

O terco e calculado apenas pelo eixo `x`:

```text
Defesa = 0 <= x < 40
Meio   = 40 <= x < 80
Ataque = 80 <= x <= 120
```

Essa variavel aparece como `field_third`.

### 2.3 Estado de valor 12x8

Para calcular mudanca de valor da posse, o app usa uma grade mais fina que a zona visual 3x3.

```text
VALUE_GRID_X_BINS = 12
VALUE_GRID_Y_BINS = 8
```

Cada celula tem aproximadamente:

```text
largura_x = 120 / 12 = 10
largura_y = 80 / 8 = 10
```

Para um evento com coordenadas `(x, y)`:

```text
x_bin = floor(clip(x, 0, 120) / 10)
y_bin = floor(clip(y, 0, 80) / 10)
```

com limite maximo:

```text
x_bin <= 11
y_bin <= 7
```

O estado calculado recebe o formato:

```text
value_state = "x{1..12}_y{1..8}"
```

Exemplo:

```text
x03_y04
```

Regra de leitura:

- `zone`: zona 3x3 para mapas e leitura visual.
- `field_third`: terco do campo.
- `value_state`: estado 12x8 usado no calculo de valor.

## 3. Tempo e estado do jogo

### 3.1 Segundos decorridos

Para cada evento:

```text
elapsed_seconds = 60 * minute + second
```

### 3.2 Duracao estimada da partida

A duracao estimada depende do periodo:

```text
periodo 1 ou 2: 90 * 60 segundos
periodo 3 ou 4: 120 * 60 segundos
periodo 5: max(minute * 60, 120 * 60)
```

### 3.3 Tempo restante

```text
seconds_remaining = max(estimated_total_seconds - elapsed_seconds, 0)
minutes_remaining = seconds_remaining / 60
```

Depois, `minutes_remaining` e agrupado em faixas:

```text
0-15 min restantes
16-30 min restantes
31-45 min restantes
46-60 min restantes
Mais de 60 min
```

### 3.4 Estado do placar

O app enriquece os eventos com placar ao vivo a partir de gols detectados. A partir disso classifica o time em:

```text
Ganhando
Empatando
Perdendo
Desconhecido
```

Conceitualmente:

```text
match_state =
  Ganhando   se team_score_live > opponent_score_live
  Empatando  se team_score_live = opponent_score_live
  Perdendo   se team_score_live < opponent_score_live
```

## 4. xG: qualidade da finalizacao

O `shot_xg` vem diretamente do campo StatsBomb:

```text
shot.statsbomb_xg
```

Ele so deve ser interpretado em finalizacoes. Para eventos que nao sao chutes, `shot_xg` e ausente ou tratado como 0 em agregacoes.

### 4.1 xG total

Para um grupo qualquer `G`:

```text
xG_total(G) = soma(shot_xg_i), para todo evento i em G
```

Na pratica, apenas finalizacoes contribuem.

### 4.2 Finalizacoes

```text
finalizacoes(G) = contagem(i em G tal que action_type_i = "Shot")
```

### 4.3 xG por finalizacao

```text
xG_por_finalizacao(G) = xG_total(G) / finalizacoes(G)
```

Se `finalizacoes(G) = 0`, o resultado fica indefinido e e exibido como vazio ou 0 conforme a tela.

### 4.4 Gols

O gol e detectado principalmente por:

```text
is_goal_event = shot_outcome == "Goal"
```

Quando disponivel, o enriquecimento tambem considera evento de gol contra a favor.

### 4.5 Assistencias

Assistencias sao detectadas por:

```text
pass_goal_assist = bool(pass.goal_assist)
```

Essa metrica depende da marcacao da StatsBomb.

## 5. Identificacao de posse e sequencia

A camada mais importante da metodologia atual fica em `src/possession_value.py`.

### 5.1 Chave de posse

Se a coluna `possession` existe e tem valores:

```text
possession_sequence_id =
  match_id + "|" + period + "|" + possession + "|" + possession_team_name
```

Se `possession` nao estiver disponivel, o app tenta reconstruir posses pela sequencia de eventos. A reconstrução considera:

```text
match_id
period
index
team_name
possession_team_name, se existir
troca de equipe
recuperacao
interceptacao
perda
passe incompleto
falta
finalizacao
evento de goleiro
fim/inicio de periodo
```

Bucket temporal fixo nao e usado como regra principal. Ele so deveria ser considerado ultimo recurso e sempre com alerta de baixa confiabilidade.

O app tambem registra a origem da chave de posse:

```text
possession_id_source =
  statsbomb, se a posse veio do dado original
  reconstruida, se a posse precisou ser reconstruida para aquele evento
```

Para evitar atribuir valor ofensivo ao time sem bola:

```text
event_team_in_possession_i =
  1 se team_name_i = possession_team_name_i
  1 se possession_team_name_i e desconhecido
  0 caso contrario
```

Eventos do time sem posse podem continuar aparecendo em volume e mapas, mas nao recebem xG futuro ofensivo da posse adversaria.

### 5.2 Ordem da sequencia

Dentro de cada posse, os eventos sao ordenados por:

```text
match_id, period, index
```

O calculo de futuro percorre cada posse de tras para frente. Isso permite saber, para cada evento, se existe uma finalizacao depois dele na mesma posse.

## 6. Valor futuro da posse

Para cada evento `i` dentro de uma posse, considere o conjunto de finalizacoes posteriores na mesma posse:

```text
S_i = {j | j ocorre depois de i, action_type_j = "Shot", mesma posse}
```

Essa associacao ofensiva so e aplicada quando:

```text
event_team_in_possession_i = 1
```

Se a acao pertence ao time sem bola dentro da posse adversaria, `future_shot`, `future_goal` e `future_xg` ofensivos ficam zerados para essa acao.

Se `S_i` nao for vazio, seja:

```text
j* = primeira finalizacao posterior a i
```

### 6.1 future_shot

Indica se existe finalizacao posterior na mesma posse:

```text
future_shot_i = 1 se S_i nao vazio
future_shot_i = 0 caso contrario
```

### 6.2 future_goal

Indica se existe gol posterior na mesma posse:

```text
future_goal_i = 1 se existe j em S_i tal que is_goal_event_j = 1
future_goal_i = 0 caso contrario
```

### 6.3 future_xg

E o xG da primeira finalizacao posterior na mesma posse:

```text
future_xg_i = shot_xg_j*, se S_i nao vazio
future_xg_i = 0, caso contrario
```

Interpretação: nao e xG proprio da acao `i`; e o xG da proxima finalizacao que aquela posse alcançou depois de `i`.

### 6.4 max_future_xg

Maior xG entre as finalizacoes posteriores:

```text
max_future_xg_i = max(shot_xg_j), para j em S_i
```

Se nao houver finalizacao posterior, vale 0.

### 6.5 sum_future_xg

Soma do xG das finalizacoes posteriores:

```text
sum_future_xg_i = soma(shot_xg_j), para j em S_i
```

Se nao houver finalizacao posterior, vale 0.

### 6.6 actions_until_shot

Numero de eventos ate a primeira finalizacao posterior:

```text
actions_until_shot_i = posicao(j*) - posicao(i)
```

Se nao houver finalizacao posterior, fica ausente.

### 6.7 shot_within_3 e shot_within_5

```text
shot_within_3_i = 1 se actions_until_shot_i <= 3
shot_within_5_i = 1 se actions_until_shot_i <= 5
```

Caso nao haja finalizacao posterior, ambos sao 0.

### 6.8 xG futuro associado / ameaca futura associada

O dashboard usa uma versao simples de xG futuro associado:

```text
future_threat_i = future_shot_i * future_xg_i
```

Como `future_xg_i` ja e 0 quando nao ha chute futuro, na pratica:

```text
future_threat_i = future_xg_i
```

Na interface, essa ideia deve ser chamada de **xG futuro associado** ou **ameaca futura associada**. Ela nao e xG proprio da acao e pode duplicar o mesmo chute quando varias acoes anteriores sao associadas a mesma finalizacao.

### 6.9 shot_within_10

```text
shot_within_10_i = 1 se actions_until_shot_i <= 10
```

Essa metrica responde se a acao aparece em uma posse que chega rapidamente a finalizacao em ate 10 eventos.

## 6B. Valores de estado e delta de valor da posse

A principal metrica para avaliar passes, conducoes e dribles passou a ser a mudanca de valor do estado da posse.

### 6B.1 Estado

O estado de calculo usa a grade 12x8:

```text
value_state_origin_i = value_state_i
state_origin_i = value_state_origin_i
```

O destino depende da acao:

```text
Passe completo:
  value_state_destination_i = value_state(pass_end_x_i, pass_end_y_i)

Passe incompleto:
  value_state_destination_i = perda_posse

Conducao:
  value_state_destination_i = value_state(carry_end_x_i, carry_end_y_i)

Drible:
  se houver proximo evento confiavel da mesma equipe na mesma posse:
    value_state_destination_i = value_state(x_proximo, y_proximo)
  senao:
    delta espacial nao calculado
```

Para compatibilidade tecnica, `state_origin` e `state_destination` apontam para os estados de valor 12x8. As colunas `visual_zone_origin` e `visual_zone_destination` preservam a leitura 3x3.

O destino de drible so e usado quando o proximo evento pertence a mesma equipe e a mesma posse.

Para finalizacoes, o valor principal continua sendo `shot_xg`; `future_xg` nao avalia o chute atual porque olha apenas eventos posteriores.

### 6B.2 Valores de estado

Para cada estado `s`, o dashboard calcula:

```text
V_shot(s) =
  P(posse ter finalizacao a partir do estado s)
  = media(future_shot_i ou is_shot_i | state_i = s)

V_goal(s) =
  P(posse ter gol a partir do estado s)
  = media(future_goal_i ou is_goal_event_i | state_i = s)

V_xg(s) =
  E[xG a partir do estado s]
  = media(shot_xg_i se a acao atual for chute, senao future_xg_i | state_i = s)

V_shot_5(s) =
  P(finalizacao em ate 5 acoes | estado atual = s)
  = media(shot_within_5_i ou is_shot_i | state_i = s)

V_shot_10(s) =
  P(finalizacao em ate 10 acoes | estado atual = s)
  = media(shot_within_10_i ou is_shot_i | state_i = s)
```

Se a amostra do estado for pequena, especialmente para `V_goal`, a leitura deve ser cautelosa.

Os valores de estado sao estimados apenas com eventos em que `event_team_in_possession = 1`. Assim, pressoes e duelos do time sem bola nao reduzem artificialmente o valor ofensivo de uma zona.

Na etapa atual, `s` e uma celula 12x8 (`value_state`), nao a zona visual 3x3. Isso melhora a granularidade do calculo sem tornar os mapas principais mais dificeis de ler.

### 6B.3 Valor da acao

Para uma acao `i` com origem `o` e destino `d`:

```text
V_shot_origem_i = V_shot(o)
V_shot_destino_i = V_shot(d)
V_xg_origem_i = V_xg(o)
V_xg_destino_i = V_xg(d)
```

Mudancas:

```text
delta_chance_finalizacao_i =
  V_shot_destino_i - V_shot_origem_i

delta_xg_futuro_i =
  V_xg_destino_i - V_xg_origem_i
```

Metrica principal atual:

```text
delta_valor_posse_i = delta_xg_futuro_i
```

Como a estrutura segue a ideia do xT de comparar destino e origem, o app tambem registra:

```text
xt_origin_i = V_xg(o)
xt_destination_i = V_xg(d)
delta_xt_i = xt_destination_i - xt_origin_i
```

Na implementacao atual:

```text
delta_xt_i = delta_valor_posse_i
```

Esse `delta_xt` e uma versao baseada nos eventos do recorte, estimada pela grade 12x8. Nao e uma tabela xT calibrada externamente em grande base historica.

Essa escolha aproxima o raciocinio do xT: valor depois da acao menos valor antes da acao. A diferenca e que, em vez de uma grade xT calibrada externamente, `V_xg` e estimado a partir dos eventos do recorte filtrado.

Para passe incompleto:

```text
value_state_destination_i = perda_posse
V_shot(perda_posse) = 0
V_xg(perda_posse) = 0
```

Assim, passes incompletos nao contam como progressao positiva apenas por terem uma coordenada final.

## 7. Progressao territorial e entradas

Para acoes com coordenada final, o dashboard usa o ponto final de passe ou conducao.

### 7.1 Coordenada final

```text
end_x_i =
  pass_end_x_i  se action_type_i = "Pass"
  carry_end_x_i se action_type_i != "Pass" e houver carry_end_x
```

Analogamente:

```text
end_y_i =
  pass_end_y_i  se action_type_i = "Pass"
  carry_end_y_i se action_type_i != "Pass" e houver carry_end_y
```

### 7.2 Progressao territorial

```text
territorial_progression_i = end_x_i - x_i
```

Se `end_x_i` ou `x_i` estiver ausente:

```text
territorial_progression_i = 0
```

Valores positivos indicam avanco para o gol adversario; negativos indicam recuo.

### 7.3 Entrada no terco final

```text
final_third_entry_i = 1 se x_i < 80 e end_x_i >= 80
```

Caso contrario, 0.

### 7.4 Entrada na area

O dashboard aproxima a area ofensiva como:

```text
x >= 102
18 <= y <= 62
```

Entao:

```text
box_entry_i = 1 se:
  evento comeca fora da area
  e termina dentro da area
```

Formalmente:

```text
starts_outside_box_i = nao (x_i >= 102 e 18 <= y_i <= 62)
ends_inside_box_i = end_x_i >= 102 e 18 <= end_y_i <= 62

box_entry_i = starts_outside_box_i e ends_inside_box_i
```

## 8. Familias de acao

As acoes sao agrupadas para evitar comparar coisas diferentes como se fossem equivalentes.

### 8.1 Criacao ofensiva

```text
Pass
Carry
Dribble
Ball Receipt*
Ball Receipt
Miscontrol
```

### 8.2 Finalizacao

```text
Shot
```

### 8.3 Recuperacao/defesa

```text
Ball Recovery
Interception
Pressure
Duel
Block
Clearance
Dispossessed
Foul Committed
```

### 8.4 Bola parada

Por acao:

```text
Foul Won
Corner
Free Kick
```

Ou por padrao de jogo:

```text
From Corner
From Free Kick
From Throw In
From Keeper
```

### 8.5 Outros/contextuais

Tudo que nao entra nas categorias anteriores.

## 9. Agregacoes de valor futuro

As agregacoes sao feitas em `summarize_sequence_value`.

Para um grupo `G` definido por equipe, jogador, acao, zona ou acao+zona:

### 9.1 Ocorrencias

```text
ocorrencias(G) = numero de eventos em G
```

### 9.2 Acoes que antecedem finalizacao

```text
acoes_que_antecedem_finalizacao(G) = soma(future_shot_i), i em G
```

### 9.3 Chance de a posse terminar em finalizacao

```text
chance_posse_terminar_em_finalizacao(G) =
  acoes_que_antecedem_finalizacao(G) / ocorrencias(G)
```

### 9.4 Posses com gol

```text
posses_com_gol(G) = soma(future_goal_i), i em G
```

### 9.5 Chance de gol futuro

```text
chance_gol_futuro(G) =
  posses_com_gol(G) / ocorrencias(G)
```

### 9.6 xG futuro associado medio

```text
xg_futuro_associado_medio(G) =
  media(future_xg_i), i em G
```

Essa media inclui zeros quando uma acao nao chega a finalizacao futura. Por isso ela combina frequencia de chegada ao chute e qualidade da chance futura.

### 9.7 Max xG futuro medio

```text
max_xg_futuro_medio(G) =
  media(max_future_xg_i), i em G
```

### 9.8 xG futuro associado acumulado

```text
xg_futuro_associado_acumulado(G) =
  soma(sum_future_xg_i), i em G
```

Esse valor pode duplicar o mesmo chute quando varias acoes anteriores pertencem a mesma posse. Por isso ele nao deve ser usado sozinho como principal ranking de qualidade ofensiva.

### 9.13 Mudanca media de valor da posse

```text
mudanca_media_chance_finalizacao(G) =
  media(delta_chance_finalizacao_i), i em G

mudanca_media_xg_futuro_esperado(G) =
  media(delta_xg_futuro_i), i em G

mudanca_media_valor_posse(G) =
  media(delta_valor_posse_i), i em G

delta_xt_medio(G) =
  media(delta_xt_i), i em G
```

Essas metricas respondem: depois dessa acao, a posse ficou em uma situacao estimada melhor ou pior?

### 9.9 Acoes ate finalizacao media

```text
acoes_ate_finalizacao_media(G) =
  media(actions_until_shot_i), i em G com chute futuro
```

Eventos sem chute futuro ficam ausentes nessa media.

### 9.10 Finalizacao em ate 3 e ate 5 acoes

```text
finalizacao_ate_3(G) = media(shot_within_3_i), i em G
finalizacao_ate_5(G) = media(shot_within_5_i), i em G
```

### 9.11 Progressao media

```text
progressao_media(G) =
  media(territorial_progression_i), i em G
```

### 9.12 Entradas no terco final e na area

```text
entradas_terco_final(G) = soma(final_third_entry_i), i em G
entradas_area(G) = soma(box_entry_i), i em G
```

Percentuais:

```text
entrada_terco_final_pct(G) = entradas_terco_final(G) / ocorrencias(G)
entrada_area_pct(G) = entradas_area(G) / ocorrencias(G)
```

## 10. Modelo territorial inspirado em xT/EPV

Ainda existe uma camada exploratoria em `src/threat.py`. Ela nao e xT calibrado nem EPV completo. E uma funcao heuristica de valor territorial.

### 10.1 Valor de uma coordenada

Para um ponto `(x, y)`:

```text
x_norm = clip(x / 120, 0, 1)
centrality = clip(1 - abs(y - 40) / 40, 0, 1)
box_bonus = 0.08 se x_norm > 0.85 e centrality > 0.45, senao 0
```

Valor territorial:

```text
pitch_value(x, y) =
  clip(0.01 + 0.24 * x_norm^2 + 0.09 * x_norm * centrality + box_bonus, 0, 0.55)
```

### 10.2 Delta de ameaca territorial

Para passe ou conducao com ponto final:

```text
threat_delta_i = pitch_value(end_x_i, end_y_i) - pitch_value(x_i, y_i)
```

Para outras acoes ou sem coordenada final:

```text
threat_delta_i = 0
```

### 10.3 Ameaca adicionada e perdida

```text
threat_added_i = max(threat_delta_i, 0)
threat_lost_i = min(threat_delta_i, 0)
```

### 10.4 Evento progressivo

```text
progressive_distance_i = end_x_i - x_i

is_progressive_event_i = 1 se:
  progressive_distance_i >= 10
  ou threat_added_i >= 0.025
```

## 11. Sequencias e caminhos de ameaca

Os modelos de transicao ficam em `src/markov.py`. Eles descrevem frequencias observadas de eventos consecutivos e, quando disponivel, agregam valor ofensivo da posse. Nao devem ser lidos como causalidade.

### 11.1 Proxima acao

Para cada evento:

```text
previous_action_i = action_type_(i-1)
next_action_i = action_type_(i+1)
```

O agrupamento e feito por partida e ordem de evento.

### 11.2 Modelo de primeira ordem

Conta transicoes:

```text
count(a, b) = numero de vezes em que current_action = a e next_action = b
```

Casos observados:

```text
observed_cases(a) = soma_b count(a, b)
```

Probabilidade:

```text
P(next_action = b | current_action = a) =
  count(a, b) / observed_cases(a)
```

### 11.3 Modelo acao + zona

```text
P(next_action = b | current_action = a, zone = z) =
  count(a, z, b) / soma_b count(a, z, b)
```

### 11.4 Modelo de segunda ordem

Considera acao anterior e acao atual:

```text
P(next_action = c | previous_action = a, current_action = b) =
  count(a, b, c) / soma_c count(a, b, c)
```

### 11.5 Metricas futuras nas transicoes

Quando os eventos ja tem valor futuro de posse, as tabelas de transicao tambem agregam:

```text
chance_finalizacao_futura =
  media(future_shot)

xg_futuro_medio =
  media(future_xg)

xg_futuro_total_medio =
  media(sum_future_xg)

delta_xt_medio =
  media(delta_xt)

delta_valor_posse_medio =
  media(delta_valor_posse)
```

Essas metricas respondem: "quando essa transicao aparece, com que frequencia a posse chega a chute e qual e o xG futuro observado?"

O dashboard tambem calcula um valor ponderado do caminho:

```text
valor_caminho =
  P(next_action | contexto) * delta_xt_medio
```

Essa metrica combina frequencia da transicao com a mudanca media de valor. Ela ajuda a separar:

- caminhos muito comuns, mas pouco progressivos;
- caminhos raros, mas com alto ganho medio;
- caminhos frequentes e com ganho positivo.

Leitura correta: `valor_caminho` mostra associacao observada no recorte, nao prova que a transicao causou o aumento de valor.

### 11.6 Delta xG da proxima linha

O codigo ainda calcula, para compatibilidade tecnica:

```text
xg_delta = next_shot_xg - current_xg
```

Mas essa metrica nao e a principal para analise ofensiva, porque xG aparece quase sempre apenas em finalizacoes. A leitura preferencial e por valor futuro da posse.

## 12. Suavizacao bayesiana

Na analise bayesiana, as probabilidades observadas podem ser suavizadas por um prior Dirichlet simetrico.

Para um contexto com `K` proximas acoes possiveis, contagem `count_k` e parametro `alpha`:

```text
posterior_probability_k =
  (count_k + alpha) / (N + alpha * K)
```

onde:

```text
N = soma_k count_k
```

Objetivo: evitar que contextos pequenos gerem probabilidades extremas ou zeros artificiais.

## 13. Validacao 2018 -> 2022

O dashboard testa transferencia de padroes:

1. Treina distribuicoes de transicao em 2018.
2. Avalia em eventos de 2022.
3. Compara contra baseline de distribuicao geral de proximas acoes.

Metricas:

### 13.1 Top-1 accuracy

```text
top1 = proporcao de eventos em que a acao real foi a acao mais provavel prevista
```

### 13.2 Top-3 accuracy

```text
top3 = proporcao de eventos em que a acao real apareceu entre as 3 mais provaveis
```

### 13.3 Log loss

Para cada evento com acao real `y` e probabilidade prevista `p(y)`:

```text
loss_i = -log(max(p(y), 1e-12))
```

Media:

```text
log_loss = media(loss_i)
```

Menor log loss indica melhor calibracao probabilistica.

## 14. Similaridade entre selecoes

O dashboard cria vetores de transicao por equipe e calcula similaridade do cosseno.

Para duas equipes com vetores `u` e `v`:

```text
cosine_similarity(u, v) =
  (u . v) / (||u|| * ||v||)
```

Valores mais proximos de 1 indicam perfis de transicao mais parecidos no recorte.

## 15. Comparacoes de equipes e jogadores

As comparacoes usam agregacoes por entidade.

Exemplos:

```text
total_actions = contagem de eventos
passes = contagem(action_type = "Pass")
shots = contagem(action_type = "Shot")
carries = contagem(action_type = "Carry")
pressures = contagem(action_type = "Pressure")
recoveries = contagem(action_type = "Ball Recovery")
xg = soma(shot_xg)
goals = soma(is_goal_event)
assists = soma(pass_goal_assist)
```

Taxas:

```text
under_pressure_rate = media(under_pressure)
attacking_zone_rate = proporcao de eventos em zonas iniciadas por "ataque"
avg_actions_per_match = total_actions / numero_de_jogos
```

Perfis recentes tambem usam:

```text
threat_added = soma(threat_added_i)
progressive_events = soma(is_progressive_event_i)
xg_per_shot = xg / shots
delta_xt_total = soma(delta_xt_i)
delta_xt_mean = media(delta_xt_i)
future_xg_associated = soma(future_xg_i)
future_shot_rate = media(future_shot_i)
final_third_entries = soma(final_third_entry_i)
box_entries = soma(box_entry_i)
```

Na interface, a comparacao de equipes e jogadores deve separar dois blocos:

```text
producao_final =
  gols, assistencias, finalizacoes, xG, xG por finalizacao

criacao_e_valor_da_posse =
  delta_xt_total,
  xG futuro associado,
  chance de chute futuro,
  entradas na area,
  entradas no terco final
```

Essa separacao evita tratar um passe ou uma conducao como se tivesse xG proprio. A leitura correta e:

```text
o jogador/equipe finalizou bem?       -> xG, gols, finalizacoes
o jogador/equipe apareceu antes das chances? -> future_xg_associated, future_shot_rate
o jogador/equipe moveu a posse para estados melhores? -> delta_xt_total, delta_xt_mean
```

## 16. Alertas de amostra

O dashboard trata amostras pequenas com cautela:

```text
ocorrencias < 30 -> alerta de amostra pequena
ocorrencias < 10 -> nao deveria ser usado como insight principal
```

Essa regra e especialmente importante em:

- acao + zona;
- jogador;
- bola parada;
- transicoes de segunda ordem;
- comparacoes em uma unica partida.

## 17. Funcionamento do dashboard

O dashboard foi reorganizado como cockpit:

```text
Usuario
  |
  v
Sidebar: Contexto da Analise
  - Modo de analise
  - Preset
  - Ano
  - Selecao principal / Selecao A-B / Partida
  - Periodo
  - Filtros avancados
  |
  v
Carregamento local
  - matches/
  - events/
  - three-sixty/ detectado, mas nao usado como tracking completo
  |
  v
Preprocessamento
  - coordenadas
  - zonas
  - tercos
  - tempo restante
  - estado do placar
  - sequencias previous/next
  |
  v
Enriquecimentos
  - valor futuro da posse
  - familias de acao
  - ameaca territorial
  - modelos de transicao
  |
  v
Cabecalho do cockpit
  - titulo do recorte
  - modo
  - preset
  - numero de eventos/jogos
  |
  v
Cards principais
  - eventos
  - finalizacoes
  - xG
  - recuperacao -> chute
  - acoes no terco final
  - entradas na area
  |
  v
Tabs de analise
  - Resumo
  - Territorio
  - Progressao
  - Perigo
  - Sequencias
  - Jogadores
  - Comparacao
  - Confiabilidade
  - Metodologia
```

## 18. Fluxo dos principais arquivos

```text
app.py
  Orquestra Streamlit, cockpit, cards e tabs.

src/load_data.py
  Le arquivos JSON locais e extrai campos StatsBomb.

src/preprocess.py
  Cria zonas, tercos, tempo restante, sequencias e filtros base.

src/filters.py
  Cria a sidebar Contexto da Analise e filtros avancados.

src/context.py
  Define modos, presets, ordem das tabs e titulo do recorte.

src/possession_value.py
  Calcula valor futuro da posse e familias de acao.

src/threat.py
  Calcula valor territorial exploratorio inspirado em xT/EPV.

src/markov.py
  Calcula transicoes, probabilidades e validacao temporal.

src/bayes.py
  Aplica suavizacao Dirichlet.

src/comparisons.py
  Agrega metricas por equipe e jogador.

src/visualizations.py
  Desenha barras, mapas de campo, mapas de zona e heatmaps.

src/labels.py
  Traduz acoes, metricas e selecoes para portugues.

src/theme.py
  Aplica estilo visual do dashboard.
```

## 19. Como interpretar corretamente

Leituras recomendadas:

- "A acao antecede finalizacoes em X% das vezes."
- "A acao aparece em posses que chegam a finalizacoes de maior xG futuro."
- "A equipe progride mais pelo corredor central/terco final."
- "A transicao e comum no recorte, mas a amostra e pequena."

Leituras a evitar:

- "Passe gera xG diretamente."
- "Drible tem xG proprio."
- "A maior probabilidade observada prova causalidade."
- "Um padrao com poucos casos define o comportamento da equipe."

## 20. Limitacoes

- Dados de evento nao mostram todos os movimentos sem bola.
- Sem tracking data, nao ha pressao espacial completa, linhas de passe disponiveis ou ocupacao dinamica.
- O valor futuro da posse associa a acao ao que acontece depois, mas nao prova que a acao causou a finalizacao.
- O modelo territorial e heuristico; nao e xT calibrado em grande base historica.
- Amostras pequenas por jogador, zona, bola parada ou partida unica podem ser instaveis.
- Quando `possession` nao estiver disponivel, a posse e reconstruida por sequencia de eventos; essa reconstrucao e menos confiavel que a posse original StatsBomb.

## 21. Resumo conceitual

O dashboard atual procura responder:

```text
1. Quem finalizou e com qual qualidade?        -> xG
2. Quem apareceu antes de chances?             -> future_shot, future_xg associado
3. Quem aumentou o valor estimado da posse?    -> delta_valor_posse
4. Onde o time progrediu?                      -> territorial_progression, entries
5. Quais padroes de acao se repetiram?         -> Markov/transicoes
6. Quanta confianca existe no padrao?          -> ocorrencias, alertas, validacao
```

A regra principal e: xG pertence ao chute; as outras acoes recebem leitura de contexto e valor futuro da posse.
