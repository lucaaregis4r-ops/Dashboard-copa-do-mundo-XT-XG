# Publicacao manual no GitHub

Este projeto foi preparado para ser publicado manualmente.

## Antes de subir

1. Confira se o nome e email de autoria estao corretos no `README.md`, em `app.py` e em `src/theme.py`.
2. Confira se as pastas de dados continuam fora do Git:

```text
events/
matches/
three-sixty/
```

3. Confira se os builds pesados continuam fora do Git:

```text
build/
dist/
```

4. Leia `docs/DADOS.md` e mantenha a referencia ao StatsBomb Open Data.
5. Se quiser conferir o que entraria no primeiro commit antes de publicar, rode:

```bash
git add --dry-run .
```

Esse comando nao altera nada; ele apenas mostra os arquivos que seriam adicionados.

## Comandos sugeridos

No computador com Git instalado:

```bash
git init
git add .
git status
git commit -m "Publica dashboard de analise da Copa do Mundo"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

Se o repositorio local ja existir:

```bash
git status
git add .
git commit -m "Prepara projeto para publicacao"
git push
```

## O que fica fora do repositorio

O `.gitignore` ignora:

- dados locais StatsBomb;
- executaveis e builds;
- logs;
- caches Python;
- ambientes virtuais;
- arquivos `.env` e chaves;
- PDFs/imagens exportadas.

## Como outro usuario roda

Depois de clonar:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Depois, baixar os dados StatsBomb Open Data conforme `docs/DADOS.md` e rodar:

```bash
git clone https://github.com/statsbomb/open-data.git
python tools/prepare_statsbomb_worldcup_data.py --source open-data
python -m streamlit run app.py
```

Se a pasta `open-data` estiver em outro local, troque o valor de `--source` pelo caminho correto.
