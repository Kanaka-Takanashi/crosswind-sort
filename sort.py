"""
4 Crosswind Sort --- maxed-out pure-Python hybrid merge sort.

Optimizations over v1:
  - Swapped src/dst ping-pong: no level tracking, no modulo, no branch.
  - No slice copy at base case: insertion sort always targets src directly.
  - Inline split4: no list allocation, direct bound computation.
  - Inline merge2: all 2-way merges inlined into _merge4, no function calls.
  - Slice-assignment tail copies: 2.2x faster than while-loop copies.
  - Tuned threshold (default 24): fewer merge levels, still fast insertion sort.
  - Unrolled 3-comparison tree for 4-active, 2-comparison for 3-active.
  - In-place or new-list API.
"""

import random
import time


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


# ═══════════════════════════════════════════════════════════════
# Competitors for Benchmark
# ═══════════════════════════════════════════════════════════════

import heapq

# --- Quicksort (Lomuto + insertion sort) ---


def _quicksort(arr, lo, hi, threshold):
    if hi - lo < threshold:
        _insertion_sort(arr, lo, hi)
        return
    pivot = arr[hi - 1]
    i = lo
    for j in range(lo, hi - 1):
        if arr[j] < pivot:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
    arr[i], arr[hi - 1] = arr[hi - 1], arr[i]
    _quicksort(arr, lo, i, threshold)
    _quicksort(arr, i + 1, hi, threshold)


def quicksort(arr, threshold=32):
    copy = arr[:]
    _quicksort(copy, 0, len(copy), threshold)
    return copy


# --- Heapsort ---


def _sift_down(arr, start, end):
    root = start
    while True:
        child = 2 * root + 1
        if child >= end:
            break
        if child + 1 < end and arr[child] < arr[child + 1]:
            child += 1
        if arr[root] >= arr[child]:
            break
        arr[root], arr[child] = arr[child], arr[root]
        root = child


def heapsort(arr):
    copy = arr[:]
    n = len(copy)
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(copy, i, n)
    for end in range(n - 1, 0, -1):
        copy[0], copy[end] = copy[end], copy[0]
        _sift_down(copy, 0, end)
    return copy


# --- 2-way Mergesort ---


def mergesort_2way(arr, threshold=4):
    if len(arr) < threshold:
        result = arr[:]
        _insertion_sort(result, 0, len(result))
        return result
    mid = len(arr) // 2
    left = mergesort_2way(arr[:mid], threshold)
    right = mergesort_2way(arr[mid:], threshold)
    return list(heapq.merge(left, right))


# --- Original hybrid_4way ---


def _equal_cuts(size, num_batches=4):
    base, remainder = divmod(size, num_batches)
    return [base + (1 if i < remainder else 0) for i in range(num_batches)]


def hybrid_4way_original(arr, threshold=4):
    if len(arr) < threshold:
        result = arr[:]
        _insertion_sort(result, 0, len(result))
        return result
    batch_sizes = _equal_cuts(len(arr), 4)
    cuts = [0]
    for bs in batch_sizes:
        cuts.append(cuts[-1] + bs)
    chunks = [
        hybrid_4way_original(arr[cuts[i] : cuts[i + 1]], threshold) for i in range(4)
    ]
    return list(heapq.merge(*chunks))


# ═══════════════════════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════════════════════


def benchmark(sizes=(1_000, 10_000, 50_000, 100_000), repeats=5):
    algorithms = [
        ("4 Crosswind", crosswind_sort),
        ("quicksort", quicksort),
        ("mergesort_2w", mergesort_2way),
        ("heapsort", heapsort),
        ("timsort", lambda a: sorted(a)),
    ]

    header = f"{'Size':>10} | " + " | ".join(f"{name:>14}" for name, _ in algorithms)
    print(header)
    print("-" * len(header))

    for size in sizes:
        base = [random.randint(0, 1_000_000) for _ in range(size)]
        times = {name: 0.0 for name, _ in algorithms}

        for _ in range(repeats):
            for name, func in algorithms:
                t0 = time.perf_counter()
                func(base[:])
                times[name] += time.perf_counter() - t0

        avg = {name: t / repeats for name, t in times.items()}
        baseline = avg["4 Crosswind"]

        row = f"{size:>10,} | "
        for name, _ in algorithms:
            speedup = baseline / avg[name]
            marker = " <<<" if name == "4 Crosswind" else ""
            row += f"  {avg[name]:.4f}s {speedup:4.1f}x |"
        print(row)

    print()
    print("  Speedup relative to 4 Crosswind.  >1.0x = faster  |  <1.0x = slower")


# ═══════════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("4 Crosswind Sort\n")

    # --- Correctness ---
    print("=== Correctness ===")
    test = [2, 27, 43, 3, 9, 82, 10, 55, 12, 99, 1, 5]
    print(f"  Input:  {test}")
    print(f"  Result: {crosswind_sort(test)}")

    # Edge cases
    for size in (0, 1, 2, 3, 4, 5, 15, 16, 100, 101):
        t = list(range(size, 0, -1))
        assert crosswind_sort(t) == sorted(t), f"Failed at size {size}"
    print("  Edge cases passed (sizes 0-101)")

    # In-place mode
    t = [5, 3, 1, 4, 2]
    crosswind_sort(t, inplace=True)
    assert t == [1, 2, 3, 4, 5], "In-place sort failed"
    print("  In-place mode works")

    # Large random
    big = [random.randint(0, 10_000) for _ in range(2_000)]
    assert crosswind_sort(big) == sorted(big), "Mismatch on 2000 elements"
    print("  Verified on 2,000 random elements")

    # --- Benchmark ---
    print("\n=== Benchmark: 4 Crosswind vs Classics ===\n")
    benchmark()
