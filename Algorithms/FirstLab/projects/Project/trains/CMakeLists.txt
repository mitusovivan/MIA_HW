target_sources(Algorithm
    PRIVATE
        train.cpp;
        train.hpp;
        trains.csv;
        

)

target_include_directories(Algorithm PRIVATE
    "${PROJECT_SOURCE_DIR}/trains"
)