add_subdirectory(game_objects)
add_subdirectory(console_io)
add_subdirectory(game_logic)

add_executable(${PROJECT_NAME} main.cpp)

target_link_libraries(${PROJECT_NAME}
    game_logic
    console_io
    game_objects
)