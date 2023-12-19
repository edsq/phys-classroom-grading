"""Tool for calculating final overall grades."""
import math
import statistics
from warnings import warn


def print_grades(columns):
    """Print nicely formatted grades."""

    # Get column widths and header to print
    widths = []
    titles = []
    seps = []
    for col_name in columns.keys():
        width = max([len(item) for item in columns[col_name] + [col_name]])
        widths.append(width)

        titles.append(f"{col_name:>{width}}")
        seps.append("-" * width)

    # Print header
    print(" ".join(titles))
    print(" ".join(seps))

    # Print rows
    for row in zip(*columns.values()):
        print(" ".join([f"{item:>{width}}" for item, width in zip(row, widths)]))


def get_letter_grades(grades, config_dict):
    """Get letter grades corresponding to each grade in `grades`."""
    grade_minimums = config_dict["grade_minimums"]

    letters = []
    for grade in grades:
        for possible_grade in grade_minimums:
            if grade >= possible_grade["min"]:
                letters.append(possible_grade["letter"])
                break

        else:
            raise ValueError(f"Grade {grade} not covered in config")

    return letters


def calc_grades(canvas_grades, config_dict, max_100=True, skip_test_student=True):
    """Calculate and print final grades.

    Parameters
    ----------
    canvas_grades : DataFrame
        DataFrame representing the Canvas gradebook csv sheet.
    config_dict : dict
        Dictionary with the key `"units"` defined; the value should be a list of strings
        where each string is the title of a column in the gradebook.  The output grade
        will be the average of the grade in each of these columns, with unit grades over
        100 rounded down to 100 if `max_100` is `True`.
    max_100 : bool, optional
        If True, unit grades over 100 will be set to 100 when calculating the final
        grade.
    skip_test_student : bool, optional
        Skip a student named 'Student, Test'.

    Returns
    -------
    students : list
        The students each grade was calculated for.
    grades : list
        The grades, in the same order as the `students` list.
    """
    # Get starting index - students are listed after a "Points Possible" row
    students_col = list(canvas_grades["Student"])
    i0 = students_col.index("    Points Possible") + 1

    # Re-collect students, just in case the order changes somehow
    students = []
    grades = []
    for i, row in canvas_grades.iterrows():
        if i < i0:
            continue

        if skip_test_student and row["Student"] == "Student, Test":
            continue

        students.append(row["Student"])

        unit_grades = []
        for unit_name in config_dict["units"]:
            unit_grade = float(row[unit_name + " Final Score"])

            # Check that the 'final' and 'current' versions are the same
            # The current grade might show NaN for non-entered grades
            unit_grade_current = float(row[unit_name + " Current Score"])
            if unit_grade == 0 and math.isnan(unit_grade_current):
                warn(
                    f"'Current Score' empty for unit {unit_name}, student {students[-1]}"
                )

            elif unit_grade != unit_grade_current:
                raise ValueError(
                    f"'Current Score' different from 'Final Score' for unit {unit_name}, student {students[-1]}"
                )

            if max_100:
                unit_grade = min([100, unit_grade])

            unit_grades.append(unit_grade)

        grades.append(statistics.mean(unit_grades))

    return students, grades
