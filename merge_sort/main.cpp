#include "do_merge_sort.hpp"
#include "io.hpp"
#include "utility.hpp"

#include <conio.h>

int main(){
    mia::set_rand();

    const int arr_len = mia::make_random(100);
    mia::print("Elements in arrange: ", arr_len);

    int arr[arr_len];
    mia::generate_arrange(arr, arr_len, 100000000);
    mia::print_arrange("Raw arrange: ", arr, arr_len);

    mia::do_merge_sort(arr, arr_len);
    mia::print_arrange("Sorted arrange: ", arr, arr_len);

    mia::print("Press any key. Code: ", 0);
    _getch();
    return 0;
}