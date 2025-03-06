#include "do_merge_sort.hpp"
#include "io.hpp"
#include "utility.hpp"

int main(){
    while (true){
        int n = mia::input("Введите тип операции: 1 - кодирование, 2 - декодирование: ")
        if (n == 1) mia::print(code())
        if (n == 2) mia::print(decode())
    }
}