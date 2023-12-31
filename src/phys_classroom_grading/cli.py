from datetime import datetime
from importlib.resources import files
from os.path import splitext

import click

import phys_classroom_grading
from phys_classroom_grading.final_grades import (
    calc_grades,
    get_letter_grades,
    print_grades,
)
from phys_classroom_grading.io import load_csv, load_excel, load_toml, write_csv
from phys_classroom_grading.tool import format_grades, parse_spreadsheet


@click.command()
@click.argument("physics_classroom_file")
@click.argument("canvas_file")
@click.option(
    "-a",
    "--assignments-file",
    default=None,
    help="Custom config file assigning Physics Classroom tasks to Canvas assignments. See `assignments.toml` in this repo for an example.",
)
@click.option(
    "-o",
    "--output",
    default=None,
    help="Output filename.  Defaults to `physics_classroom_grades_<timestamp>.csv`.",
)
def main(physics_classroom_file, canvas_file, assignments_file, output):
    """Parse output from Physics Classroom and format for Canvas gradebook.

    PHYSICS_CLASSROOM_FILE should be the output of the "Export Detailed Progress" button
    on the Class page on Physics Classroom (an excel `.xlsx` file), and CANVAS_FILE is
    the exported `.csv` gradebook from Canvas.
    """
    # Load dataframe from physics classroom grades
    sheet = load_excel(physics_classroom_file)

    # Load assignments config file
    if assignments_file is None:
        assignments_file = files(phys_classroom_grading) / "assignments.toml"

    assignments = load_toml(assignments_file)

    # Load initial Canvas gradebook
    init_grades = load_csv(canvas_file)

    # Parse Physics Classroom grades
    pc_dict = parse_spreadsheet(sheet, assignments)

    # Format PC grades for gradebook
    new_grades = format_grades(pc_dict, init_grades, assignments)

    # Get output filename
    if output is None:
        output = (
            "physics_classroom_grades"
            + f"_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
        )

    # Save updated gradebook
    write_csv(new_grades, output)
    click.echo(f"Formatted grades written to {output}")


@click.command()
@click.argument("canvas_file")
@click.option(
    "-c",
    "--config-file",
    default=None,
    help="Custom config file setting grade cutoffs and units to use in final grade calculation.  Defaults to `final_grades_config.toml` in this repository.",
)
def final_grades(canvas_file, config_file=None):
    """Print final grades parsed from the gradebook.

    CANVAS_FILE should be the `csv` output of exporting the Canvas gradebook.
    """
    # Load Canvas gradebook
    gradebook = load_csv(canvas_file)

    # Load config
    if config_file is None:
        config_file = files(phys_classroom_grading) / "final_grades_config.toml"

    config = load_toml(config_file)

    # Calculate number grades
    students, grades = calc_grades(gradebook, config)

    # Get letter grades
    letters = get_letter_grades(grades, config)

    # Round grade and cast to string
    grades = [f"{grade:0.2f}" for grade in grades]

    print_grades({"Student": students, "Grade": grades, "Letter": letters})
