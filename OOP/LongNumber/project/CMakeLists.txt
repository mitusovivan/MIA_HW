cmake_minimum_required(VERSION 3.2...3.27.5)
project(project)

enable_testing()
add_subdirectory(lib/googletest)

add_library(pr_lib "")

add_subdirectory(src)
add_subdirectory(test)

set(CMAKE_SUPPRESS_REGENERATION true)