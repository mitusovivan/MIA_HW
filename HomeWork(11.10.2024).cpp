#include <algorithm>
#include <cmath>
#include <ctime>
#include <iostream>

void random_gen(int* arr, const int len);
void print_array(const int comment, const float midow, int* arr, const int size);
float midow_arithmetic(int* arr, const int len);

int main()
{
    srand(time(0));
    
    int arr_size = 10;
    int* arr = new int[arr_size];

    for (int i = 0; i < 3; i++){
        random_gen(arr, arr_size);
        print_array((i + 1), midow_arithmetic(arr, arr_size), arr, arr_size);
    }

    delete[] arr;
    return 0;
}

void random_gen(int* arr, const int len)
{
    for (int i = 0; i < len; i++){
        arr[i] = (rand() % 10);
    }
}

void print_array(const int comment, const float midow, int* arr, const int size)
{
    std::cout << "Последовательность № " << comment <<':';
    for (int i = 0; i < size; i++){
        std::cout << ' ' << arr[i];
    }
    std::cout << '\n' <<"Среднее арифметическое последовательности № " << comment; 
    std::cout  << " = " << midow << '\n';
}

float midow_arithmetic(int* arr, const int len)
{
    int sum = 0;
    for (int i = 0; i < len; i++){
        sum += arr[i];
    }
    return sum / float(len);
}