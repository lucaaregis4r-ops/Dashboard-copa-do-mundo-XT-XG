from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


WORLD_CUP_SEASONS = {
    2018: {"competition_id": 43, "season_id": 3},
    2022: {"competition_id": 43, "season_id": 106},
}


def _data_root(source: Path) -> Path:
    source = source.resolve()
    if (source / "data" / "matches").exists():
        return source / "data"
    if (source / "matches").exists():
        return source
    raise FileNotFoundError(
        "Nao encontrei a pasta de dados StatsBomb. Informe a raiz do clone/ZIP "
        "do open-data ou diretamente a pasta open-data/data."
    )


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _copy_file(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True


def prepare_world_cup_data(source: Path, output: Path) -> None:
    data_root = _data_root(source)
    output = output.resolve()

    copied_events = 0
    copied_three_sixty = 0

    for year, ids in WORLD_CUP_SEASONS.items():
        competition_id = ids["competition_id"]
        season_id = ids["season_id"]
        source_matches = data_root / "matches" / str(competition_id) / f"{season_id}.json"
        target_matches = output / "matches" / f"world_cup_{year}.json"

        if not _copy_file(source_matches, target_matches):
            raise FileNotFoundError(f"Arquivo de partidas nao encontrado: {source_matches}")

        matches = _load_json(source_matches)
        match_ids = [str(match["match_id"]) for match in matches if "match_id" in match]

        for match_id in match_ids:
            event_source = data_root / "events" / f"{match_id}.json"
            event_target = output / "events" / str(year) / f"{match_id}.json"
            if _copy_file(event_source, event_target):
                copied_events += 1

            three_sixty_source = data_root / "three-sixty" / f"{match_id}.json"
            three_sixty_target = output / "three-sixty" / str(year) / f"{match_id}.json"
            if _copy_file(three_sixty_source, three_sixty_target):
                copied_three_sixty += 1

    print(f"Dados preparados em: {output}")
    print(f"Eventos copiados: {copied_events}")
    print(f"Arquivos 360 copiados: {copied_three_sixty}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepara os dados da Copa do Mundo do StatsBomb Open Data para este dashboard."
    )
    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Caminho para o clone/ZIP extraido do statsbomb/open-data ou para a pasta open-data/data.",
    )
    parser.add_argument(
        "--output",
        default=Path.cwd(),
        type=Path,
        help="Raiz deste projeto. Padrao: diretorio atual.",
    )
    args = parser.parse_args()
    prepare_world_cup_data(args.source, args.output)


if __name__ == "__main__":
    main()
