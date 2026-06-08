# Como subir este dashboard no GitHub

Esta pasta ja esta limpa para publicacao: os dados StatsBomb, builds, logs, caches e executaveis ficaram de fora.

## Opcao 1: GitHub Desktop

1. Abra o GitHub Desktop.
2. Clique em `File > Add local repository`.
3. Escolha esta pasta:

```text
C:\Users\TEMP\Downloads\world_cup_dashboard_github
```

4. Publique o repositorio pelo botao `Publish repository`.

## Opcao 2: terminal com Git instalado

Na pasta `world_cup_dashboard_github`, rode:

```bash
git init
git add .
git commit -m "Publica dashboard de analise da Copa do Mundo"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

## Dados

A base nao esta incluida. Quem clonar deve baixar o StatsBomb Open Data:

```bash
git clone https://github.com/statsbomb/open-data.git
python tools/prepare_statsbomb_worldcup_data.py --source open-data
python -m streamlit run app.py
```

Mais detalhes estao em `docs/DADOS.md`.
