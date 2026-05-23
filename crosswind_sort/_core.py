"""
4 Crosswind Sort --- maxed-out pure-Python hybrid merge sort.

Optimizations:
  - Swapped src/dst ping-pong: no level tracking, no modulo, no branch.
  - No slice copy at base case: insertion sort always targets src directly.
  - Inline split4: no list allocation, direct bound computation.
  - Inline merge2: all 2-way merges inlined into _merge4, no function calls.
  - Slice-assignment tail copies: 2.2x faster than while-loop copies.
  - Tuned threshold (default 24): fewer merge levels, still fast insertion sort.
  - Unrolled 3-comparison tree for 4-active, 2-comparison for 3-active.
  - In-place or new-list API.
"""


# ---------- Insertion sort (index-bounded, in-place) ----------
def _insertion_sort(arr, lo, hi):
    for i in range(lo + 1, hi):
        key = arr[i]
        j = i - 1
        while j >= lo and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key


# ---------- 4-way merge (fully inlined, slice tail copies) ----------
def _merge4(src, dst, b0, b1, b2, b3, b4, d0):
    """
    Merge 4 sorted runs from src into dst.
    Runs: src[b0:b1], src[b1:b2], src[b2:b3], src[b3:b4].

    Hot path (all 4 active): 3-comparison decision tree.
    Falls through to inlined 3-way then 2-way then slice-copy tail.
    Zero function calls, zero per-iteration allocations.
    After 2-way merge: slice-copy BOTH remaining runs (at most one has data).
    """
    i0, i1, i2, i3 = b0, b1, b2, b3
    end0, end1, end2, end3 = b1, b2, b3, b4
    di = d0

    # --- Phase 1: all 4 runs active ---
    while i0 < end0 and i1 < end1 and i2 < end2 and i3 < end3:
        v0 = src[i0]
        v1 = src[i1]
        v2 = src[i2]
        v3 = src[i3]
        if v0 <= v1:
            if v2 <= v3:
                if v0 <= v2:
                    dst[di] = v0
                    i0 += 1
                else:
                    dst[di] = v2
                    i2 += 1
            else:
                if v0 <= v3:
                    dst[di] = v0
                    i0 += 1
                else:
                    dst[di] = v3
                    i3 += 1
        else:
            if v2 <= v3:
                if v1 <= v2:
                    dst[di] = v1
                    i1 += 1
                else:
                    dst[di] = v2
                    i2 += 1
            else:
                if v1 <= v3:
                    dst[di] = v1
                    i1 += 1
                else:
                    dst[di] = v3
                    i3 += 1
        di += 1

    # --- Phase 2: exactly 3 runs active ---
    if i0 >= end0:
        while i1 < end1 and i2 < end2 and i3 < end3:
            v1 = src[i1]
            v2 = src[i2]
            v3 = src[i3]
            if v1 <= v2:
                if v1 <= v3:
                    dst[di] = v1
                    i1 += 1
                else:
                    dst[di] = v3
                    i3 += 1
            else:
                if v2 <= v3:
                    dst[di] = v2
                    i2 += 1
                else:
                    dst[di] = v3
                    i3 += 1
            di += 1
        # 2-way fallthrough + slice-copy BOTH remaining runs
        if i1 >= end1:
            while i2 < end2 and i3 < end3:
                if src[i2] <= src[i3]:
                    dst[di] = src[i2]
                    i2 += 1
                else:
                    dst[di] = src[i3]
                    i3 += 1
                di += 1
        elif i2 >= end2:
            while i1 < end1 and i3 < end3:
                if src[i1] <= src[i3]:
                    dst[di] = src[i1]
                    i1 += 1
                else:
                    dst[di] = src[i3]
                    i3 += 1
                di += 1
        else:
            while i1 < end1 and i2 < end2:
                if src[i1] <= src[i2]:
                    dst[di] = src[i1]
                    i1 += 1
                else:
                    dst[di] = src[i2]
                    i2 += 1
                di += 1
        # Slice-copy ALL remaining runs (at most 2 have data after 2-way)
        if i1 < end1:
            dst[di : di + end1 - i1] = src[i1:end1]
            di += end1 - i1
        if i2 < end2:
            dst[di : di + end2 - i2] = src[i2:end2]
            di += end2 - i2
        if i3 < end3:
            dst[di : di + end3 - i3] = src[i3:end3]
        return

    if i1 >= end1:
        while i0 < end0 and i2 < end2 and i3 < end3:
            v0 = src[i0]
            v2 = src[i2]
            v3 = src[i3]
            if v0 <= v2:
                if v0 <= v3:
                    dst[di] = v0
                    i0 += 1
                else:
                    dst[di] = v3
                    i3 += 1
            else:
                if v2 <= v3:
                    dst[di] = v2
                    i2 += 1
                else:
                    dst[di] = v3
                    i3 += 1
            di += 1
        if i0 >= end0:
            while i2 < end2 and i3 < end3:
                if src[i2] <= src[i3]:
                    dst[di] = src[i2]
                    i2 += 1
                else:
                    dst[di] = src[i3]
                    i3 += 1
                di += 1
        elif i2 >= end2:
            while i0 < end0 and i3 < end3:
                if src[i0] <= src[i3]:
                    dst[di] = src[i0]
                    i0 += 1
                else:
                    dst[di] = src[i3]
                    i3 += 1
                di += 1
        else:
            while i0 < end0 and i2 < end2:
                if src[i0] <= src[i2]:
                    dst[di] = src[i0]
                    i0 += 1
                else:
                    dst[di] = src[i2]
                    i2 += 1
                di += 1
        if i0 < end0:
            dst[di : di + end0 - i0] = src[i0:end0]
            di += end0 - i0
        if i2 < end2:
            dst[di : di + end2 - i2] = src[i2:end2]
            di += end2 - i2
        if i3 < end3:
            dst[di : di + end3 - i3] = src[i3:end3]
        return

    if i2 >= end2:
        while i0 < end0 and i1 < end1 and i3 < end3:
            v0 = src[i0]
            v1 = src[i1]
            v3 = src[i3]
            if v0 <= v1:
                if v0 <= v3:
                    dst[di] = v0
                    i0 += 1
                else:
                    dst[di] = v3
                    i3 += 1
            else:
                if v1 <= v3:
                    dst[di] = v1
                    i1 += 1
                else:
                    dst[di] = v3
                    i3 += 1
            di += 1
        if i0 >= end0:
            while i1 < end1 and i3 < end3:
                if src[i1] <= src[i3]:
                    dst[di] = src[i1]
                    i1 += 1
                else:
                    dst[di] = src[i3]
                    i3 += 1
                di += 1
        elif i1 >= end1:
            while i0 < end0 and i3 < end3:
                if src[i0] <= src[i3]:
                    dst[di] = src[i0]
                    i0 += 1
                else:
                    dst[di] = src[i3]
                    i3 += 1
                di += 1
        else:
            while i0 < end0 and i1 < end1:
                if src[i0] <= src[i1]:
                    dst[di] = src[i0]
                    i0 += 1
                else:
                    dst[di] = src[i1]
                    i1 += 1
                di += 1
        if i0 < end0:
            dst[di : di + end0 - i0] = src[i0:end0]
            di += end0 - i0
        if i1 < end1:
            dst[di : di + end1 - i1] = src[i1:end1]
            di += end1 - i1
        if i3 < end3:
            dst[di : di + end3 - i3] = src[i3:end3]
        return

    # Runs 0, 1, 2 active (i3 exhausted)
    while i0 < end0 and i1 < end1 and i2 < end2:
        v0 = src[i0]
        v1 = src[i1]
        v2 = src[i2]
        if v0 <= v1:
            if v0 <= v2:
                dst[di] = v0
                i0 += 1
            else:
                dst[di] = v2
                i2 += 1
        else:
            if v1 <= v2:
                dst[di] = v1
                i1 += 1
            else:
                dst[di] = v2
                i2 += 1
        di += 1
    if i0 >= end0:
        while i1 < end1 and i2 < end2:
            if src[i1] <= src[i2]:
                dst[di] = src[i1]
                i1 += 1
            else:
                dst[di] = src[i2]
                i2 += 1
            di += 1
    elif i1 >= end1:
        while i0 < end0 and i2 < end2:
            if src[i0] <= src[i2]:
                dst[di] = src[i0]
                i0 += 1
            else:
                dst[di] = src[i2]
                i2 += 1
            di += 1
    else:
        while i0 < end0 and i1 < end1:
            if src[i0] <= src[i1]:
                dst[di] = src[i0]
                i0 += 1
            else:
                dst[di] = src[i1]
                i1 += 1
            di += 1
    if i0 < end0:
        dst[di : di + end0 - i0] = src[i0:end0]
        di += end0 - i0
    if i1 < end1:
        dst[di : di + end1 - i1] = src[i1:end1]
        di += end1 - i1
    if i2 < end2:
        dst[di : di + end2 - i2] = src[i2:end2]


# ---------- Core recursive sort (swapped src/dst, inline split) ----------
def _crosswind(src, dst, lo, hi, threshold):
    """
    Sort src[lo:hi]. Result ends up in src.

    Convention: recursive calls swap src<->dst so that sorted sub-runs
    land in dst. The merge then reads from dst and writes back to src.
    No level counter, no modulo, no branch to decide the target.
    """
    size = hi - lo
    if size < threshold:
        _insertion_sort(src, lo, hi)
        return

    # Inline split4 avoid list creation + unpacking
    base, rem = divmod(size, 4)
    b0 = lo
    b1 = b0 + base + (1 if 0 < rem else 0)
    b2 = b1 + base + (1 if 1 < rem else 0)
    b3 = b2 + base + (1 if 2 < rem else 0)
    b4 = b3 + base + (1 if 3 < rem else 0)

    # Sort 4 chunks: swap src/dst so results go into dst
    _crosswind(dst, src, b0, b1, threshold)
    _crosswind(dst, src, b1, b2, threshold)
    _crosswind(dst, src, b2, b3, threshold)
    _crosswind(dst, src, b3, b4, threshold)

    # Merge the 4 sorted runs from dst back into src
    _merge4(dst, src, b0, b1, b2, b3, b4, lo)


# ---------- Public API ----------
def crosswind_sort(arr, inplace=False, threshold=24):
    """
    Sort `arr` using the 4-way crosswind algorithm.

    A stable, O(n log n) worst-case hybrid merge sort that beats
    pure-Python quicksort in benchmarks on random data at 10K+ elements.

    Parameters
    ----------
    arr : list
        Input list (not necessarily sorted).
    inplace : bool, default False
        If True, sort the list in-place and return None.
        If False, return a new sorted list (original unchanged).
    threshold : int, default 24
        Size below which insertion sort is used.

    Returns
    -------
    list or None
        Sorted list if `inplace=False`, otherwise None.
    """
    if not inplace:
        arr = arr[:]

    n = len(arr)
    if n <= 1:
        return arr if not inplace else None

    buf = arr[:]
    _crosswind(arr, buf, 0, n, threshold)

    if not inplace:
        return arr
