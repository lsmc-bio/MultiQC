"""Offline, independently loaded sections with the native MultiQC renderer."""

import os

from multiqc.templates.default import template_functions

template_dir = os.path.dirname(__file__)
template_parent = "default"
base_fn = "base.html"
template_dark_mode = True
