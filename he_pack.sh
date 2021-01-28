#!/bin/bash

# Helium packing script.
# Author: Saul Johnson <saul.a.johnson@gmail.com>
# Packing script for the Helium report generator. Bundles report template as base64 inside script.

# Activate virtual environment.
. venv/bin/activate

# Input and output filenames.
HELIUM_SCRIPT="./helium.py"
HELIUM_PACKED_OUT="./helium_packed.py"

# Get line number of REPORT_SVG variable.
LINE_NO=$(awk '/REPORT_SVG/{ print NR; exit }' ${HELIUM_SCRIPT})

# Get file prefix and suffix, excluding variable line.
PREFIX="$(head -n $(( ${LINE_NO} - 1 )) ${HELIUM_SCRIPT})"
SUFFIX="$(tail -n +$(( ${LINE_NO} + 1 )) ${HELIUM_SCRIPT})"

# Reconstruct file around base64 value.
echo "${PREFIX}" > ${HELIUM_PACKED_OUT}
echo "REPORT_SVG = \"\"\"$(base64 ${HELIUM_SCRIPT})\"\"\"" >> ${HELIUM_PACKED_OUT}
echo "${SUFFIX}" >> ${HELIUM_PACKED_OUT}

# Deactivate virtual environment.
deactivate
