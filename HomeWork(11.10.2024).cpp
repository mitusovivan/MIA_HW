#include <cmath>
#include <iostream>

int random_gen(int len){
    int s, arr[len];
    for (int i = 0; i < len; i++){
        arr[i] = rand() % 10;
        std::cout << ' ' << arr[i];
        s += arr[i];
    }
    std::cout << '\n';
    return s;
}

int main()
{
    std::cout << "Первая последовательность:";
    int first_sum = random_gen(10);
    std::cout << "Среднее первой последовательности = " << first_sum / 10.0 << '\n' << "Вторая последовательность:";
    int second_sum = random_gen(10);
    std::cout << "Среднее второй последовательности = " << second_sum / 10.0 << '\n' << "Третья последовательность:";
    int fird_sum = random_gen(10);
    std::cout << "Среднее третьей последовательности = " << fird_sum / 10.0 << '\n';
    std::cin;
    return 0;
}

