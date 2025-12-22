add_library(game_objects
    game_object.cpp 
)


target_include_directories(game_objects PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)