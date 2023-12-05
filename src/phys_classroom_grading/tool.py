"""Backend things for the tool."""
from warnings import warn
import tomllib
import pandas as pd


with open("assignments.toml", "rb") as f:
    assignments = tomllib.load(f)


def parse_spreadsheet(fname):
    sheet = pd.read_excel(fname)

    parsed_dict = {}
    for i, row in sheet.iterrows():
        task = row["Task"]
        student = row["Student"]

        # Strip zero width spaces and strip whitespace
        task = task.replace("\u200b", "").strip()

        for assignment, info in assignments.items():
            if task in info["tasks"]:
                break

        else:
            warn(f"Found unexpected task: {task}")
            continue

        if assignment not in parsed_dict.keys():
            parsed_dict[assignment] = {}

        if student not in parsed_dict[assignment].keys():
            parsed_dict[assignment][student] = {"points": 0, "max": 0}

        assert isinstance(row["Completed"], bool)
        if row["Completed"]:
            parsed_dict[assignment][student]["points"] += 1

        if row["Section"] != "Wizard Level":
            parsed_dict[assignment][student]["max"] += 1

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

            out_dict[assignment][student] = vals["points"]

    return out_dict


if __name__ == "__main__":
    out_dict = parse_spreadsheet("example_grades_detailed.xlsx")
    df = pd.DataFrame.from_dict(out_dict)
    df.to_csv("out_test.csv", header=True)
