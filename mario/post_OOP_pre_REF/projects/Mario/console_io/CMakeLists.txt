add_library(console_io
    console_renderer.cpp
    console_renderer.hpp
)

target_include_directories(console_io PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(console_io PUBLIC
    game_objects
)