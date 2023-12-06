from datetime import datetime
from os.path import splitext

import click

from phys_classroom_grading.io import load_csv, load_excel, load_toml, write_csv
from phys_classroom_grading.tool import load_grades, parse_spreadsheet


@click.command()
@click.argument("physics_classroom_file")
@click.argument("canvas_file")
@click.option(
    "--assignments_file",
    default="assignments.toml",
    show_default=True,
    help="Config file assigning Physics Classroom tasks to Canvas assignments.",
)
def main(physics_classroom_file, canvas_file, assignments_file):
    """Parse output from Physics Classroom and merge into Canvas gradebook.

    PHYSICS_CLASSROOM_FILE should be the output of the "Export Detailed Progress" button
    on the Class page on Physics Classroom (an excel `.xlsx` file), and CANVAS_FILE is
    the exported `.csv` gradebook from Canvas.
    """
    # Load dataframe from physics classroom grades
    sheet = load_excel(physics_classroom_file)

    # Load assignments config file
    assignments = load_toml(assignments_file)

    # Load initial Canvas gradebook
    init_grades = load_csv(canvas_file)

    # Parse Physics Classroom grades
    pc_dict = parse_spreadsheet(sheet, assignments)

    # Merge PC grades into gradebook
    all_grades = load_grades(pc_dict, init_grades, assignments)

    # Get output filename
    out_fname = (
        splitext(canvas_file)[0]
        + f"_updated_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
    )

    # Save updated gradebook
    write_csv(all_grades, out_fname)
    click.echo(f"Updated gradebook written to {out_fname}")
