#include "io.hpp"

#include <iostream>

void mia::print(const char* const comment, const int integer){
    std::cout << comment << integer << std::endl;
}

void mia::print_arrange(const char* const comment, const int* const arr,  const int length){
    std::cout << comment;
    for(int i = 0; i < length; i++) std::cout << arr[i] << ' ';
    std::cout << std::endl;
}
