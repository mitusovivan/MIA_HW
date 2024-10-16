#include <algorithm>//Подключение библиотек
#include <cmath>
#include <ctime>
#include <iostream>
#include <string>

void random_gen(int len, std::string NumberOfIterration, std::string NumberOfIterration2);//расположение функции генератора

int main()
{
    srand(time(0));//Задание ключа генерации
    random_gen(10, "Первая", "первой");//функции печати
    random_gen(10, "Вторая", "второй");
    random_gen(10, "Третья", "третьей");
    return 0;//
}

void random_gen(int len, std::string NumberOfIterration, std::string NumberOfIterration2){//функция генератора
    std::cout << NumberOfIterration << " последовательность:";//Вывод имени последовательности
    int sum = 0;//сумма чисел
    for (int i = 0; i < len; i++){//генерация чисел
        int unit = (rand() % 10);
        std::cout << ' ' << unit;
        sum += unit;
    }
    float midow_arifmetic = float(sum) / len;//рассчёт ср.арифм
    std::cout << '\n' <<"Среднее арифметическое "<< NumberOfIterration2; //вывод
    std::cout <<" последовательности = " << midow_arifmetic << '\n';
}