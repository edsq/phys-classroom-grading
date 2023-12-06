"""Backend things for the tool."""
from datetime import datetime
from itertools import zip_longest
from warnings import warn

import pandas as pd


def sanitize_str(in_str, lower=False):
    """Get rid of extra crap that comes with strings in the PhysicsClassroom output."""
    out_str = in_str.replace("\u200b", "").strip()
    if lower:
        out_str = out_str.lower()

    return out_str


def parse_spreadsheet(sheet, assignments):
    """Parse a dataframe representing PhysicsClassroom "Detailed Progress".

    We step through the PhysicsClassroom spreadsheet row by row.  Each row corresponds
    to a single sub-part/difficulty level (or "Section", on the spreadsheet) of a
    Concept Builder.  A student earns 1 point if the "Completed" column reads "True", 0
    otherwise.  We then accumulate points per assignment by looking up which assignment
    each concept builder belongs to, and check that the assignment has the right number
    of maximum regular points and bonus points.

    Parameters
    ----------
    sheet : DataFrame
        A Pandas dataframe representing the "Detailed Progress" xlsx file from the
        PhysicsClassroom class page.
    assignments : dict
        The assignments to accumulate tasks into.  Each key should be the name of an
        assignment on Canvas, and each value should itself be a dictionary.  These
        sub-dictionaries should have the following key/values: "points", the point value
        of the assignment on Canvas (float); "bonus", the number of bonus points over
        the assigned point value a student can get (float); and "tasks", the (exact!)
        names on PhysicsClassroom of the Concept Builders that belong to this assignment
        (list of str).

    Returns
    -------
    dict
        The accumulated points for each assignment by student.  The keys of this
        dictionary are the Canvas assignment names (defined in the `assignments`
        parameter), and the values are dictionaries of the form
        `{student name: points earned}`.
    """
    parsed_dict = {}
    for i, row in sheet.iterrows():
        # Need to strip zero length spaces and leading/trailing whitespace
        task = sanitize_str(row["Task"])
        student = sanitize_str(row["Student"])

        # Get the assignment corresponding to this task (concept builder)
        for assignment, info in assignments.items():
            if task in info["tasks"]:
                break

        else:
            # We only get here if the for loop didn't break - hence we did not find the
            # task in the assignments dictionary keys.
            warn(f"Found unexpected task: {task}")
            continue

        # Add assignment to parsed_dict if it isn't already there
        if assignment not in parsed_dict.keys():
            parsed_dict[assignment] = {}

        # Add per-student dictionary to assignment if it isn't already there
        if student not in parsed_dict[assignment].keys():
            parsed_dict[assignment][student] = {
                "points": 0,
                "max": 0,
                "bonus": 0,
                "tasks": [],
            }

        # Student gets a point for each completed section
        assert isinstance(row["Completed"], bool)
        if row["Completed"]:
            parsed_dict[assignment][student]["points"] += 1

        # Also add up how many regular and bonus points this assignment is worth
        task_section = sanitize_str(row["Section"], lower=True)
        if task_section == "wizard level" or task_section == "wizard":
            parsed_dict[assignment][student]["bonus"] += 1

        else:
            parsed_dict[assignment][student]["max"] += 1

        # Get tasks that go into this assignment (useful for debugging purposes)
        parsed_dict[assignment][student]["tasks"].append(f"{task}: {row['Section']}")

    # Now having parsed the spreadsheet, get dictionary with just earned points, and run
    # some checks against expected point values
    out_dict = {}
    for assignment in assignments.keys():
        out_dict[assignment] = {}
        for student, vals in parsed_dict[assignment].items():
            expected_max_pts = assignments[assignment]["points"]
            found_max_pts = vals["max"]
            if expected_max_pts != found_max_pts:
                raise ValueError(
                    f"Got {found_max_pts} instead of {expected_max_pts} max points for assignment '{assignment}', student '{student}'"
                )

            expected_bonus = assignments[assignment]["bonus"]
            found_bonus = vals["bonus"]
            if expected_bonus != found_bonus:
                raise ValueError(
                    f"Got {found_bonus} instead of {expected_bonus} bonus points for assignment '{assignment}', student '{student}'"
                )

            out_dict[assignment][student] = vals["points"]

    return out_dict


def load_grades(concept_builders, all_grades, assignments, ignore_test_student=True):
    """Merge parsed concept builder grades into the overall Canvas grades spreasheet.

    Parameters
    ----------
    concept_builders : dict
        Output of `parse_spreadsheet`, represents the grades for each assignment totaled
        off of PhysicsClassroom.
    all_grades : DataFrame
        An exported gradebook spreadsheet from Canvas, loaded into a Pandas DataFrame.
    assignments : dict
        The assignments we are going to populate in the gradebook.  Each key should be
        the name of an assignment on Canvas, and each value should itself be a
        dictionary.  Only one key is used in these sub-dictionaries: "points", the value
        of the assignment in Canvas (float).
    ignore_test_student : bool, optional
        Whether to ignore a student on the last row of the gradebook named "Student,
        Test".  This should probably always be `True` unless there is a student in your
        class who is actually named "Test Student" and comes last in alphabetical order.

    Returns
    -------
    DataFrame
        The gradebook spreadsheet with the appropriate assignments filled in.
    """
    # Get starting index - students are listed after a "Points Possible" row
    canvas_students = list(all_grades["Student"])
    i0 = canvas_students.index("    Points Possible") + 1
    canvas_students = canvas_students[i0:]

    # Test Student seems to always come at the end of the roster; ignore them
    if ignore_test_student and canvas_students[-1] == "Student, Test":
        canvas_students = canvas_students[:-1]

    # Iterate through assignments
    for assignment, info in assignments.items():
        # Check that we have the same students for this assignment as listed in Canvas
        physics_classroom_students = sorted(list(concept_builders[assignment].keys()))
        if not canvas_students == physics_classroom_students:
            # Prepare output to make differences obvious
            max_name_len = max(
                [
                    len(name)
                    for name in physics_classroom_students + ["Physics Classroom"]
                ]
            )
            zipped_names = zip_longest(
                physics_classroom_students, canvas_students, fillvalue=""
            )

            error_str = f"{'Physics Classroom':>{max_name_len}}  Canvas"
            error_str += f"\n{'-----------------':>{max_name_len}}  ------"
            for pc_name, canvas_name in zipped_names:
                error_str += f"\n{pc_name:>{max_name_len}}  {canvas_name}"

            raise ValueError(
                f"Inconsistent students for assignment '{assignment}': \n{error_str}"
            )

        # Get Concept Builder grades; should be in same order as students/rows
        cb_grades = [
            concept_builders[assignment][student]
            for student in physics_classroom_students
        ]

        # Canvas appends a number to each assignment, so we need some effort to get the
        # correct column name
        col_matches = [col for col in all_grades.columns if col.startswith(assignment)]
        if len(col_matches) > 1:
            raise ValueError(
                f"Multiple columns ({col_matches}) match assignment '{assignment}'"
            )

        else:
            col_name = col_matches[0]

        # Check that point value in assignments is same as on Canvas
        canvas_points = all_grades[col_name][i0 - 1]
        expected_points = info["points"]
        if canvas_points != expected_points:
            raise ValueError(
                f"Canvas spreadsheet shows '{assignment}' worth {canvas_points}, expected {expected_points}"
            )

        # Set grades to corresponding students.  Need to use `loc` here to avoid
        # ambiguity with view vs. copy, see:
        # https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
        # Also note that the slice here is inclusive of the endpoint, unlike the rest of
        # python.
        all_grades.loc[i0 : len(canvas_students) + i0 - 1, col_name] = cb_grades

    return all_grades


if __name__ == "__main__":
    from os.path import splitext

    from phys_classroom_grading.io import load_csv, load_excel, load_toml, write_csv

    physics_classroom_grades_fname = "example_grades_detailed.xlsx"
    sheet = load_excel(physics_classroom_grades_fname)

    assignments_fname = "assignments.toml"
    assignments = load_toml(assignments_fname)

    canvas_grades_fname = "all_grades.csv"
    init_grades = load_csv(canvas_grades_fname)

    out_dict = parse_spreadsheet(sheet, assignments)

    df = pd.DataFrame.from_dict(out_dict)
    df.to_csv("out_test.csv", header=True)

    all_grades = load_grades(out_dict, init_grades, assignments)
    out_fname = (
        splitext(canvas_grades_fname)[0]
        + f"_updated_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv"
    )
    write_csv(all_grades, out_fname)
