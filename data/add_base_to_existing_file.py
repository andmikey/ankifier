import click
import sys
import pandas as pd

sys.path.append("..")

from ankifier.utils import strip_stress_marks


def get_base_entry(row):
    output = "" 
    if row["Part-of-speech"] == "phrase":
        output = row["Front"]
    else:
        output = row["Front"].split(",")[0]

    return strip_stress_marks(output) 


@click.command()
@click.option("--file", type=click.Path(exists=True))
@click.option("--dest", type=click.Path())
def main(file: click.Path, dest: click.Path):
    df = pd.read_csv(file)
    df["Base"] = df.apply(get_base_entry, axis=1)

    df.to_csv(dest, index=False)


if __name__ == "__main__":
    main()
