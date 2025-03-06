target_sources(merge_sort
    PRIVATE
        do_merge_sort.cpp
        io.cpp
        io.hpp
        utility.cpp 
        utility.hpp
    PUBLIC
        do_merge_sort.hpp
)

target_include_directories(merge_sort_lib PUBLIC
    "${PROJECT_SOURCE_DIR}/src"
)