"""Configuration file for the Sphinx documentation builder."""

import tomli

project = "nova-galaxy"
copyright = "2023, ORNL"
author = "Andrew Ayres"
with open("../pyproject.toml", "rb") as toml_file:
    toml_dict = tomli.load(toml_file)
    release = toml_dict["project"]["version"]

extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode", "sphinx_rtd_theme"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
