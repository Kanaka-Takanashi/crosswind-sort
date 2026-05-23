"""
4 Crosswind Sort --- fast pure-Python 4-way hybrid merge sort.

A stable, O(n log n) worst-case sort that beats pure-Python quicksort
in benchmarks on random data at 10K+ elements.
"""

from ._core import crosswind_sort

__all__ = ["crosswind_sort"]
__version__ = "1.0.0"
