import os
import csv
from pathlib import Path

import pandas as pd

from src.scripts.analyze_newicks import analyze_newicks


def write_newick(dir_path: Path):
    # cria três pequenos newicks de exemplo que usam col_0.txt, col_1.txt, col_2.txt
    trees = [
        "(col_0.txt,col_1.txt);",
        "(col_0.txt,(col_1.txt,col_2.txt));",
        "((col_2.txt,col_3.txt),col_0.txt);",
    ]
    for i, t in enumerate(trees):
        p = dir_path / f"resample_{i:02d}.newick"
        p.write_text(t, encoding="utf-8")


def test_wide_format_mapping_from_original_csv(tmp_path: Path):
    # tmp directory for newicks and mapping
    work = tmp_path / "wide_test"
    work.mkdir()

    # write newick files
    write_newick(work)

    # Create an 'original' CSV whose headers correspond to real variable names
    original_csv = work / "original.csv"
    headers = ["spatial_id", "spatial_geo_code", "spatial_name", "other_var"]
    # write headers only (no rows needed)
    with original_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)

    # Run analyze_newicks using the original CSV as var_mapping
    res = analyze_newicks(
        str(work), metadata_csv=None, var_mapping_csv=str(original_csv)
    )

    df = res["df"]
    # At least one row should have translated variable 'spatial_id' in Clade_Variables
    found = df["Clade_Variables"].str.contains("spatial_id", na=False).any()
    assert found, (
        "Expected 'spatial_id' in Clade_Variables when using original CSV as mapping"
    )


def test_long_format_mapping(tmp_path: Path):
    work = tmp_path / "long_test"
    work.mkdir()

    # write newick files
    write_newick(work)

    # write long-format var_mapping.csv with explicit original->mapped
    vm = work / "var_mapping.csv"
    df_vm = pd.DataFrame(
        {
            "original": ["col_0.txt", "col_1.txt", "col_2.txt"],
            "mapped": ["spatial_id", "idade", "altura"],
            "category": ["Spatial", "Demografia", "Saude"],
        }
    )
    df_vm.to_csv(vm, index=False)

    res = analyze_newicks(str(work), metadata_csv=None, var_mapping_csv=str(vm))
    df = res["df"]
    import os
    import csv
    from pathlib import Path

    import pandas as pd

    from src.scripts.analyze_newicks import analyze_newicks

    def write_newick(dir_path: Path):
        # cria três pequenos newicks de exemplo que usam col_0.txt, col_1.txt, col_2.txt
        trees = [
            "(col_0.txt,col_1.txt);",
            "(col_0.txt,(col_1.txt,col_2.txt));",
            "((col_2.txt,col_3.txt),col_0.txt);",
        ]
        for i, t in enumerate(trees):
            p = dir_path / f"resample_{i:02d}.newick"
            p.write_text(t, encoding="utf-8")

    def test_wide_format_mapping_from_original_csv(tmp_path: Path):
        # tmp directory for newicks and mapping
        work = tmp_path / "wide_test"
        work.mkdir()

        # write newick files
        write_newick(work)

        # Create an 'original' CSV whose headers correspond to real variable names
        original_csv = work / "original.csv"
        headers = ["spatial_id", "spatial_geo_code", "spatial_name", "other_var"]
        # write headers only (no rows needed)
        with original_csv.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)

        # Run analyze_newicks using the original CSV as var_mapping
        res = analyze_newicks(
            str(work), metadata_csv=None, var_mapping_csv=str(original_csv)
        )

        df = res["df"]
        # At least one row should have translated variable 'spatial_id' in Clade_Variables
        found = df["Clade_Variables"].str.contains("spatial_id", na=False).any()
        assert found, (
            "Expected 'spatial_id' in Clade_Variables when using original CSV as mapping"
        )

    def test_long_format_mapping(tmp_path: Path):
        work = tmp_path / "long_test"
        work.mkdir()

        # write newick files
        write_newick(work)

        # write long-format var_mapping.csv with explicit original->mapped
        vm = work / "var_mapping.csv"
        df_vm = pd.DataFrame(
            {
                "original": ["col_0.txt", "col_1.txt", "col_2.txt"],
                "mapped": ["spatial_id", "idade", "altura"],
                "category": ["Spatial", "Demografia", "Saude"],
            }
        )
        df_vm.to_csv(vm, index=False)

        res = analyze_newicks(str(work), metadata_csv=None, var_mapping_csv=str(vm))
        df = res["df"]
        # Verify translations applied
        assert df["Clade_Variables"].str.contains("spatial_id", na=False).any()
        assert df["Clade_Variables"].str.contains("idade", na=False).any()
