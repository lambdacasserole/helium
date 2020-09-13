# Helium
A fast and focused report-generation tool for lifting the quality of Python codebases.

![Logo](he_logo.svg)

## Overview
Helium is a report generation tool designed to focus on the parts of your code with the lowest maintainability indices
and highest cyclomatic complexities. It's a well-known fact that metrics like these can be a bit of a blunt instrument
when it comes to measuring code quality, but they can provide useful insight into which areas of your code could do
with more documentation, or a bit of a refactor.

Helium computes quantitative metrics from your code using the [Radon](https://github.com/rubik/radon) library and
renders a single-page report from these by filling an SVG template and converting this to a PDF.

## Installation
The script does not require installation. Just download it and run it like so:

```bash
python3 helium.py
```

It is advised that you do this from the root of your project, as a `.heliumrc` file will be generated containing
configuration options for your project including a list of files to ignore and configuration options for the
[Radon harvesters](https://radon.readthedocs.io/en/latest/api.html#module-radon.cli.harvest) that do the actual code
metric computation.

### Configuration
Parameters currently supported in the `.heliumrc` file include:

| Name               | Type    | Description                                                                                                                                                                                                           |
|--------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`             | `str`   | The name of the project (will be included in the report).                                                                                                                                                             |
| `pattern`          | `str`   | The pattern to match files to include in the report.                                                                                                                                                                  |
| `separate_metrics` | `bool`  | If true, maintainability indices and cyclomatic complexities will be computed and listed separately. If false, cyclomatic complexities will be computed only for those files with the lowest maintainability indices. |
| `excludes`         | `[str]` | Files to exclude. Must be individual relative filepaths starting with `./`.                                                                                                                                           |
| `mi_config`        | `obj`   | A Radon maintainability index harvester configuration object (see Radon docs).                                                                                                                                        |
| `cc_config`        | `obj`   | A Radon cyclomatic complexity harvester configuration object (see Radon docs).                                                                                                                                        |

## Templates
The templating that Helium uses is very simple, and you can see exactly how it's done by taking a look at the
`report_template.svg` file included in the repo using a free editor like [Inkscape](https://inkscape.org/). Values
that will be filled by Helium by default include:

+ `m1... m3` - The 3 lowest (worst) maintainability index grades (A-C) computed by Radon for your codebase (per file).
+ `mq1... mq3` - The 3 lowest (worst) maintainability indices (numeric) computed by Radon for your codebase (per file).
+ `mf_1... mf_3` - The names of the 3 files with the lowest (worst) maintainability indices computed by Radon for your
  codebase (per file).
+ `cc1... cc8` - The 8 highest (worst) cyclomatic complexity grades (A-F) computed by Radon for your codebase (per
  function).
+ `ccq1... ccq8` - The 8 highest (worst) cyclomatic complexities (numeric) computed by Radon for your codebase (per
  function).
+ `ccn1... ccn8` - The names of the 8 functions with the highest (worst) cyclomatic complexities computed by Radon for
  your codebase (per function).
+ `ccf1... ccf8` - The names of the 8 files containing the functions with the highest (worst) cyclomatic complexities
  computed by Radon for your codebase (per function).

You can add more maintainability indices and cyclomatic complexities to the template, but for them to be filled you'll
need to adjust the `DISPL_MI_RESULTS` and `DISPL_CC_RESULTS` constants in `helium.py`.

Template highlight colours are filled by searching for shades of magenta (`#ff00ff`) with the middle byte incremented
for each colour region. For example, the highlight colour corresponding to maintainability index 1 is `#ff01ff`, for
maintainability index 2 `#ff02ff` and so on. Cyclomatic complexity highlight colours start where maintainability index
highlight colours leave off. Very hacky, but works in a pinch.

## Packing
It's possible to pack the file `report_template.svg` into the `helium.py` script in order to create one portable script
file for report generation. This can be useful if you want the `helium.py` file to stand alone without any dependency
on other files in the same directory. To do this, make any adjustments you like to `report_template.svg` and run:

```bash
bash he_pack.sh
```

You'll end up with a file called `helium_packed.py` which contains the `report_template.svg` file as a base64 string
ready to write back to disk as-needed.

## Acknowledgements

+ The Radon library is awesome for extracting quantitative code metrics from Python codebases, and what's more its
  [hosted right here on GitHub](https://github.com/rubik/radon).
* The font used in the logo is [Monofur](https://www.dafont.com/monofur.font) by Tobias Benjamin Köhler.
