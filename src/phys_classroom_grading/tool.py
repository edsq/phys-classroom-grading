"""Backend things for the tool."""
from datetime import datetime
from itertools import zip_longest
from warnings import warn
import tomllib
import pandas as pd


def sanitize_str(in_str, lower=False):
    """Get rid of extra crap that comes with strings in the PhysicsClassroom output."""
    out_str = in_str.replace("\u200b", "").strip()
    if lower:
        out_str = out_str.lower()

    return out_str


def parse_spreadsheet(sheet, assignments):
    """Parse a dataframe representing PhysicsClassroom "Detailed Progress".

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
        task = sanitize_str(row["Task"])
        student = sanitize_str(row["Student"])

        for assignment, info in assignments.items():
            if task in info["tasks"]:
                break

        else:
            warn(f"Found unexpected task: {task}")
            continue

        if assignment not in parsed_dict.keys():
            parsed_dict[assignment] = {}

        if student not in parsed_dict[assignment].keys():
            parsed_dict[assignment][student] = {
                "points": 0,
                "max": 0,
                "bonus": 0,
                "tasks": [],
            }

        assert isinstance(row["Completed"], bool)
        if row["Completed"]:
            parsed_dict[assignment][student]["points"] += 1

        task_section = sanitize_str(row["Section"], lower=True)
        if task_section == "wizard level" or task_section == "wizard":
            parsed_dict[assignment][student]["bonus"] += 1

        else:
            parsed_dict[assignment][student]["max"] += 1

        # Get tasks that go into this assignment (useful for debugging purposes)
        parsed_dict[assignment][student]["tasks"].append(f"{task}: {row['Section']}")

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
    """Merge parsed concept builder grades into the overall Canvas grades spreasheet."""
    canvas_students = list(all_grades["Student"][1:])

    if ignore_test_student and canvas_students[-1] == "Student, Test":
        canvas_students = canvas_students[:-1]

    for assignment, info in assignments.items():
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
        canvas_points = all_grades[col_name][0]
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
        all_grades.loc[1 : len(canvas_students), col_name] = cb_grades

    return all_grades


if __name__ == "__main__":
    sheet = pd.read_excel("example_grades_detailed.xlsx")

    with open("assignments.toml", "rb") as f:
        assignments = tomllib.load(f)

    out_dict = parse_spreadsheet(sheet, assignments)

    df = pd.DataFrame.from_dict(out_dict)
    df.to_csv("out_test.csv", header=True)

    canvas_grades_fname = "all_grades"
    init_grades = pd.read_csv(canvas_grades_fname + ".csv")
    all_grades = load_grades(out_dict, init_grades, assignments)
    all_grades.to_csv(
        canvas_grades_fname
        + f"_updated_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.csv",
        header=True,
    )
