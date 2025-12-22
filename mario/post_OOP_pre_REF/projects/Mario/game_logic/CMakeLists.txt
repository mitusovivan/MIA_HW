add_library(game_logic
    game.cpp
    game.hpp
)

target_include_directories(game_logic PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(game_logic PUBLIC
    console_io
    game_objects
)