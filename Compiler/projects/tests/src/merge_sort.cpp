#include "merge_sort.hpp"

#include <cmath>
#include <limits>
#include <vector>

void mia::do_merge(int * const arr, const int l, const int q, const int r){
    float left[q - l + 1], right[r - q + 1];
    
    for (int i = 0; i < (q - l); i++) left[i] = arr[l + i];
    for (int i = 0; i < (r - q); i++) right[i] = arr[q + i];

    right[r - q] = std::numeric_limits<float>::infinity(), left[q - l] = std::numeric_limits<float>::infinity();
    
    int a = 0, b = 0; 

    for (int i = 0; i < (r - l); i++){
        switch (right[b] < left[a])
        {
        case true:
            arr[l + i] = right[b];
            b++;
            break;
        default:
            arr[l + i] = left[a];
            a++;
            break;
        }
    } 
}

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
            do_merge(arr, l, q, r);
            break;
    }
}