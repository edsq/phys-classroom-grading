# phys-classroom-grading

Tool for converting Physics Classroom grades into spreadsheets that can be imported as
grades for Canvas assignments.  Built for Phys 150 at Washington State University, Fall
2023.

**Please use with caution**; I have not really tested this!  Make a backup of
grades before uploading anything.


## Requirements
- Python >= 3.9


## Installation

1. Activate a python >= 3.9 environment (see [below](#creating-a-new-environment) for
   tips; I strongly recommend creating an environment just for this utility)

2. Install with `pip`:
```
python -m pip install git+https://github.com/edsq/phys-classroom-grading.git
```

3. Alternatively, you can skip dealing with environments entirely by installing with
   [pipx](https://pipx.pypa.io/stable/):
```
pipx install git+https://github.com/edsq/phys-classroom-grading.git
```

## Setup

Before using this utility, the following must all be true:

1. The names of students in the Physics Classroom Class must be exactly the same as the
   students on Canvas.  You can edit students' names on Physics Classroom if this is not
   already the case.
2. Each assignment (corresponding to multiple Physics Classroom tasks) should be on
   Canvas already with the correct number of points.
3. The config file (by default the
   [`assignments.toml`](https://github.com/edsq/phys-classroom-grading/blob/b031ddf0ea50df36e69d25defeb71f333eafd14e/src/phys_classroom_grading/assignments.toml)
   file in this repository) should correctly reflect the Physics Classroom tasks for
   each assignment, as well as the correct point value and possible bonus points for the
   assignment.  See [below](#usage) for how to specify a custom config file.  This
   config file also determines which assignments will be put into the output grades.


## Usage

This package provides the command `parse-PC-grades`, which takes two positional
arguments: a file representing the output of the "Export Detailed Progress" button on
the Class page on Physics Classroom (which should be an Excel `.xlsc` document), and a
file representing the exported Canvas gradebook (which should be a `.csv` file).

Example usage:

```
$ parse-PC-grades pc_grades_2023-12-05.xlsx canvas_grades_2023-12-05T2009.csv
Formatted grades written to physics_classroom_grades_2023_12_06-12_41_59.csv
```

You can also specify a different config file with the `--assignments-file` option.  This
would be useful if you have different assignments on Canvas than are in the default
`assignments.toml` file.  This would look like:

```
$ parse-PC-grades pc_grades_2023-12-05.xlsx canvas_grades_2023-12-05T2009.csv --assignments-file custom_assignments.toml
Formatted grades written to physics_classroom_grades_2023_12_06-12_41_59.csv
```

Finally, you can specify a different output filename (the default is
`physics_classroom_grades_<timestamp>.csv`) with the `--output` option:

```
$ parse-PC-grades pc_grades_2023-12-05.xlsx canvas_grades_2023-12-05T2009.csv --output custom-output-name.csv
Formatted grades written to custom-output-name.csv
```

See also

```
parse-PC-grades --help
```


## Creating a new environment

I strongly recommend creating a new [python
environment](https://realpython.com/python-virtual-environments-a-primer/) just for this
package.  Below are some brief instructions for how to do this with either the default
python module `venv` or `conda`.

If you want to avoid messing around with virtual environments, I would also highly
recommend just using the utility [pipx](https://pipx.pypa.io/stable/).

### With `venv`

1. Create the new environment in the local directory `.venv`
```
python -m venv .venv
```

2. Activate the environment:
```
source .venv/bin/activate
```

3. Install the utility as described [above](#installation)

4. When you're done grading, deactivate the environment:
```
deactivate
```

### With `conda`
1. Create the new python 3.11 environment (named `physics-classroom-grading`)
```
conda create --name physics-classroom-grading python=3.11
```

2. Activate the environment:
```
conda activate physics-classroom-grading
```

3. Install the utility as described [above](#installation)

4. When you're done grading, deactivate the environment:
```
conda deactivate
```

