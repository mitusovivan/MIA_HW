#include "print.hpp"

#include <iostream>

void mia::print(const char* const comment, const int integer){
    std::cout << comment << integer << std::endl;
}
