#include "make_random.hpp"

#include <ctime>
#include <random>

void mia::set_rand(){
    srand(time(0));
}

int mia::make_random(const int depth){

    return rand() % depth;
}
