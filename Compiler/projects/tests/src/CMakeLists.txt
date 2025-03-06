target_sources(merge_sort_lib
    PRIVATE
        merge_sort.cpp
    PUBLIC
        merge_sort.hpp
)

target_include_directories(merge_sort_lib PUBLIC
    "${PROJECT_SOURCE_DIR}/src"
)