cmake_minimum_required(VERSION 3.2...3.27.5)

project(Obuchaika)

enable_testing()
add_subdirectory(lib/googletest)

add_subdirectory(merge_sort)

add_subdirectory(tests)
add_subdirectory(Obuchaika)


set(CMAKE_SUPPRESS_REGENERATION true)