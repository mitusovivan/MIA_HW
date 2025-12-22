#include <algorithm>
#include <cmath>
#include <ctime>
#include <iostream>

float colculate_midow_arithmetic(const int* const arr, const int len);
void print_array(const int comment, const int* const arr, const int size);
void random_gen(int* const arr, const int len);

int main()
{
    srand(time(0));

    for (int i = 0; i < 3; i++){
        int arr_size = 10;
        int arr[arr_size];

        random_gen(arr, arr_size);
        print_array((i + 1), arr, arr_size);
        std::cout << "Среднее арифметическое последовательности №" << (i + 1);
        std::cout << " = "<< colculate_midow_arithmetic(arr, arr_size) << std::endl;
    }

    return 0;
}

float colculate_midow_arithmetic(const int* const arr, const int len)
{
    int sum = 0;
    for (int i = 0; i < len; i++){
        sum += arr[i];
    }
    return sum / float(len);
}

void print_array(const int comment, const int* const arr, const int size)
{
    std::cout << "Последовательность №" << comment <<':';
    for (int i = 0; i < size; i++){
        std::cout << ' ' << arr[i];
    }
    std::cout << std::endl;
}

void random_gen(int* const arr, const int len)
{
    for (int i = 0; i < len; i++) {
        arr[i] = (rand() % 10);
    }
}