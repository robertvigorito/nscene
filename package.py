"""Rez package definition for nscene."""

name = "nscene"
version = "0.1.0"
description = "PySide6 Nuke scene open and save browser"

requires = [
    "python-3.12+",
    "PySide6-6.8.1+",
    "pymongo-4.15.3+",
]


def commands():
    env.PYTHONPATH.append("{root}/src")
    alias("nscene", "python -m nscene")
