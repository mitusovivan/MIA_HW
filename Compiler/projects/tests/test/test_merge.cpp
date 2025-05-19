//#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include "merge_sort.hpp"

#include <algorithm>
#include <random>

TEST(ArraysEqual, AnyElementsCount){
    srand(time(0));
    for (int i = 0; i < 100; i++){
    const int arr_len = rand() % 10000;
    int actual[arr_len];
    for(int i = 0; i < arr_len; i++) actual[i] = rand() % 10000;
    mia::do_merge_sort(actual, arr_len);
    int expected[arr_len];

    for (int i = 0; i < arr_len; i++) expected[i] = actual[i];

    std::sort(expected, expected + arr_len);
    //expected[0] = -1;

    //ASSERT_EQ(n, m) << "Разные";

    for (int i = 0; i < arr_len; i++){
        ASSERT_EQ(expected[i], actual[i])
        << "Ожидаемые и отсортированые различны"
        <<   i;     
    }
 }
}

int main(int argc, char **argv){
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}