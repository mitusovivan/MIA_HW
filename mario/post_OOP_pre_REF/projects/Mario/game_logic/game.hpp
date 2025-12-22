#pragma once

#include "game_object.hpp"
#include "console_renderer.hpp"

const int MAX_BRICKS = 300;
const int MAX_MOVING_OBJECTS = 300;
const int MAX_LEVEL = 4; 

class Game {
private:
    GameObject mario;
    GameObject bricks[MAX_BRICKS];
    int brickCount;
    GameObject movingObjects[MAX_MOVING_OBJECTS];
    int movableCount;

    int currentLevel;
    int score;
    
    ConsoleRenderer renderer;

    void load_level();
    void delete_moving_object(int index);
    void handle_player_death();
    void handle_mario_collisions();
    void move_object_horizontally(GameObject& obj);
    void move_object_vertically(GameObject& obj);
    void scroll_map_horizontally(float deltaX);

public:
    Game();
    void run_game_loop();
};
