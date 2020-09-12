import base64
import glob
import json
import os.path
import re
from datetime import datetime
from shutil import copyfile
from tempfile import mkstemp

# Code quality metrics powered by Radon.
from radon.cli import Config
from radon.cli.harvest import MIHarvester, CCHarvester
import radon.visitors

# Needed for report PDF generation.
import cairosvg as cairo


# Default configuration file to assist with interactive project initialization.
DEFAULT_CONFIG = {
    'name': 'Unnamed project',
    'pattern': './**/*.py',
    'separate_metrics': False,
    'excludes': [],
    'mi_config': {
        'exclude': [],
        'ignore': [],
        'multi': True,
        'min': 'A',
        'max': 'F',
        'show': True
    },
    'cc_config': {
        'exclude': [],
        'ignore': [],
        'no_assert': True,
        'show_closures': True,
        'max': 'F',
        'min': 'A',
        'order': None
    }
}

# Default location of configuration file.
CONFIG_LOCATION = './.heliumrc'

# Number of maintainability index results to display.
DISPL_MI_RESULTS = 3

# Number of cyclomatic complexity results to display.
DISPL_CC_RESULTS = 8

# Either report SVG file location, or SVG base64.
REPORT_SVG = 'file:./report_template.svg'


def initialize_report_svg (path):
    """ Initializes the SVG file representing the report template at the specified file path.

    Args:
        path (str): The path to initialize the report template SVG at
    """
    if REPORT_SVG.startswith('file:'): # If template is file-based...
        template_path = REPORT_SVG.split(':')[1]
        copyfile(template_path, path) # Copy template file to destination.
    else:
        # Otherwise, we have a base64 string that needs to be written to disk as a file.
        with open(path, 'wb') as file:
            file.write(base64.b64decode(REPORT_SVG))


def svg_to_pdf (svg_path, pdf_path):
    """ Converts an SVG file to a PDF file.

    Args:
        svg_path (str): The path of the input SVG file
        pdf_path (str): The path of the output PDF file
    """
    cairo.svg2pdf(file_obj=open(svg_path, 'rb'), write_to=pdf_path)


def load_file (path):
    """ Reads a file as a string.

    Args:
        path (str): The path of the file to read
    Returns:
        str: The resulting string
    """
    buffer = ""
    with open(path) as file:
        buffer = file.read()
    return buffer


def load_json_file (path):
    """ Loads a JSON object from a file.

    Args:
        path (str): The path of the input JSON file
    Returns:
        obj: The resulting JSON object
    """
    return json.loads(load_file(path))


def replace_in_file (path, subs):
    """ Performs a set of substitutions in a text file.

    Args:
        path (str): The path of the target file
        subs (list of tuple): A list of pairs of terms and their replacements
    """
    # Compile regular expressions.
    compiled_subs = []
    for old, new in subs:
        compiled_subs.append((re.compile(old), new))
    # Perform replacement.
    buffer = []
    with open(path) as file:
        for line in file:
            processed_line = line
            for old, new in compiled_subs:
                processed_line = re.sub(old, new, processed_line)
            buffer.append(processed_line)
    with open(path, 'w') as file:
        for line in buffer:
            file.write(line)


def bracket_sub (sub, comment=False):
    """ Brackets a substitution pair.

    Args:
        sub (tuple): The substitution pair to bracket
        comment (bool): Whether or not to comment the bracketed pair
    Returns:
        tuple: The bracketed substitution pair
    """
    if comment:
        return (r'<!--\s*\{\{\s*' + sub[0] + r'\s*\}\}\s*-->', sub[1])
    else:
        return (r'\{\{\s*' + sub[0] + r'\s*\}\}', sub[1])


def fill_template (path, subs, comment=False):
    """ Fills a template file.

    Args:
        path (str): The path of the target file
        subs (list of tuple): The list of substitution pairs
        comment (bool): Whether or not to replace commented tempalating expressions
    """
    # Substitute with and without commenting.
    all_subs = [bracket_sub(sub, comment) for sub in subs]
    replace_in_file(path, all_subs)


def grade_cc (cc):
    """ Grades a cyclomatic complexity score on a scale from A-F.

    Args:
        cc (int): The cyclomatic complexity to grade
    Returns:
        str: The resulting grade
    """
    bounds = [
        (6, 'A'),
        (11, 'B'),
        (21, 'C'),
        (31, 'D'),
        (41, 'E') # Add additional bounds here.
    ]
    for bound in bounds:
        if cc < bound[0]:
            return bound[1] # Return bound corresponding to grade.
    return 'F' # Out of bounds, lowest grade.


def basename_only (path):
    """ Returns the base name of a file only, discarding the directory portion.

    Args:
        path (str): The file path to process
    Returns:
        str: The base name of the file
    """
    return os.path.basename(path)


def compute_mi_color (mi_rank):
    """ Computes an appropriate highlight color for a maintainability index based on its rank (A-C).

    Args:
        mi_rank (str): The maintainability index rank (A-C)
    Returns:
        str: The hexadecimal highlight color
    """
    return {
        'A': '#217821',
        'B': '#D45500',
        'C': '#800000'
    }[mi_rank]


def compute_cc_color (cc_rank):
    """ Computes an appropriate highlight color for a cyclomatic complexity based on its rank (A-F).

    Args:
        mi_rank (str): The cyclomatic complexity rank (A-F)
    Returns:
        str: The hexadecimal highlight color
    """
    return {
        'A': '#217821',
        'B': '#D4AA00',
        'C': '#D45500',
        'D': '#C87137',
        'E': '#A02C2C',
        'F': '#800000'
    }[cc_rank]


def hex_byte (n):
    """ Computes a minimum 2-character hexadecimal byte for an integer 0-255.

    Args:
        n (int): The integer to compute for
    Returns:
        str: The minimum 2-character hexadecimal representation of the given integer
    """
    return hex(n).replace('0x', '').zfill(2) # Strip '0x' and pad to length 2 with '0' digits.


# If configuration file doesn't exist, ask to create one.
if not os.path.exists(CONFIG_LOCATION):
    confirm = input('Warning: No .heliumrc file detected. Generate one now? [y/N] ')
    if confirm.lower() == 'y':
        proj_name = input('Project name: ') # Choose project name.
        # File selector pattern defaults to all *.py files.
        proj_pattern = input('Pattern (leave blank for all Python files): ')
        if proj_pattern == '':
            proj_pattern = './**/*.py'
        # Adjust default config structure according to input and write it out as a JSON file.
        DEFAULT_CONFIG['name'] = proj_name
        DEFAULT_CONFIG['pattern'] = proj_pattern
        with open(CONFIG_LOCATION, 'w') as file:
            file.write(json.dumps(DEFAULT_CONFIG, indent=4))
        # Confirm proceed with report.
        confirm = input('The .heliumrc file has been created. Proceed with report generation? [y/N] ')
        if confirm.lower() != 'y':
            print('Aborting...')
            exit(0)
    else:
        print('No .heliumrc file created. Aborting...')
        exit(0)

# Load config file.
config = load_json_file(CONFIG_LOCATION)

# Discover files and remove excluded.
files = glob.glob(config['pattern'], recursive=True)
for exclude in config['excludes']:
    files.remove(exclude)

# Generate report page.
temp_svg = mkstemp()[1]
initialize_report_svg(temp_svg)

# Maintainability index harvester.
mi_harvester = MIHarvester(files, Config(**config['mi_config']))

# Fill project name and report generation date.
fill_template(temp_svg, [
    ('proj_name', config['name']),
    ('report_date', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))]
)

# Structure output from maintainability index harvester as one dictionary per file.
mi_results = []
for result in mi_harvester.results:
    path, props = result
    mi_results.append({
        'path': path,
        'mi': props['mi'],
        'rank': props['rank']
    })

# Can't fill template with too few results.
if len(mi_results) < DISPL_MI_RESULTS:
    print(f"Error: Not enough maintainability results to generate report (minimum {DISPL_MI_RESULTS} required).")
    exit(1)

# Sort lowest maintainability index first.
mi_results.sort(key=lambda r: r['mi'])

# Extract lowest DISPL_MI_RESULTS maintainability indices.
lowest_mi_results = mi_results[:DISPL_MI_RESULTS]

# Fill lowest DISPL_MI_RESULTS maintainability indices.
i = 1
for result in lowest_mi_results:
    fill_template(temp_svg, [
        (f'm{i}', result['rank']),
        (f'mq{i}', str(round(result['mi'], 2))),
        (f'mf_{i}', result['path'])
    ])
    replace_in_file(temp_svg, [ # Colour circles.
        (f'#ff{hex_byte(i)}ff', compute_mi_color(result['rank'])),
    ])
    i += 1

# Cyclomatic complexity harvester for all files, or lowest MI files depending on config.
cc_targets = files if config['separate_metrics'] else [r['path'] for r in lowest_mi_results]
cc_harvester = CCHarvester(cc_targets, Config(**config['cc_config']))

# Structure output from cyclomatic complexity harvester as one dictionary per function.
cc_results = []
for result in cc_harvester.results:
    path, nodes = result
    for node in nodes:
        if type(node) == radon.visitors.Function: # We're only interested in functions.
            cc_results.append({
                'path': path,
                'name': node.name,
                'complexity': node.complexity,
                'rank': grade_cc(node.complexity) # Grades need to be done manually.
            })

# Can't fill template with too few results.
if len(cc_results) < DISPL_CC_RESULTS:
    print(f"Error: Not enough cyclomatic complexity results to generate report (minimum {DISPL_CC_RESULTS} required).")
    exit(1)

# Sort highest cyclomatic complexity first.
cc_results.sort(key=lambda r: r['complexity'], reverse=True)

# Extract highest DISPL_CC_RESULTS cyclomatic complexities.
highest_cc_results = cc_results[:DISPL_CC_RESULTS]

# Fill highest DISPL_CC_RESULTS cyclomatic complexities.
i = 1
for result in highest_cc_results:
    fill_template(temp_svg, [
        (f'cc{i}', result['rank']),
        (f'ccq{i}', str(result['complexity'])),
        (f'ccn{i}', result['name']),
        (f'ccf{i}', basename_only(result['path'])),
    ])
    replace_in_file(temp_svg, [ # Colour circles.
        (f'#ff{hex_byte(i + DISPL_MI_RESULTS)}ff', compute_cc_color(result['rank'])),
    ])
    i += 1

# Perform conversion to PDF.
svg_to_pdf(temp_svg, 'helium.pdf')
