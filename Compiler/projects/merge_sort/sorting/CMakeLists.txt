target_sources(merge_sort
    PRIVATE
        do_merge_sort.cpp
        do_merge_sort.hpp
        io.cpp
        io.hpp
        utility.cpp 
        utility.hpp
)

target_include_directories(merge_sort PRIVATE
    "${PROJECT_SOURCE_DIR}/sorting"
)