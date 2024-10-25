#include "generate_arrange.hpp"
#include "make_random.hpp"

void mia::generate_arrange(int * const arr, const int n, const int depth){
    for(int i = 0; i < n; i++) arr[i] = mia::make_random(depth);
}
