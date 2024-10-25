#include "do_merge_sort.hpp"
#include "do_merge.hpp"

#include <cmath>

void mia::do_merge_sort(int * const arr, const int n) {
    merge_sort(arr, 0, n);
}

void mia::merge_sort(int * const arr, const int l, const int r){
    switch ((l < r) && abs(r - l) > 1)
    {
        case true: 
            int q = (l + r) / 2;
            merge_sort(arr, l, q);
            merge_sort(arr, q, r);
            mia::do_merge(arr, l, q, r);
            break;
    }
}