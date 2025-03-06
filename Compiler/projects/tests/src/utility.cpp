#include "utility.hpp"

#include <ctime>
#include <random>

void mia::generate_arrange(int * const arr, const int n, const int depth){
    for(int i = 0; i < n; i++) arr[i] = mia::make_random(depth);
}

void mia::set_rand(){
    srand(time(0));
}

int mia::make_random(const int depth){

    return rand() % depth;
}
