#include "io.hpp"

#include <iostream>

int mia::input(const char* const message){
    std::cout << message;
    int input;
    std::cin >> input;
    return input;
}

void mia::print(const char* const comment, const int integer){
    std::cout << comment << integer << std::endl;
}

void mia::print(const char* const comment, const int* const arr,  const int length){
    std::cout << comment;
    for(int i = 0; i < length; i++) std::cout << arr[i] << ' ';
    std::cout << std::endl;
}

