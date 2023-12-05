"""Backend things for the tool."""
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


if __name__ == "__main__":
    sheet = pd.read_excel("example_grades_detailed.xlsx")

    with open("assignments.toml", "rb") as f:
        assignments = tomllib.load(f)

    out_dict = parse_spreadsheet(sheet, assignments)

    df = pd.DataFrame.from_dict(out_dict)
    df.to_csv("out_test.csv", header=True)
