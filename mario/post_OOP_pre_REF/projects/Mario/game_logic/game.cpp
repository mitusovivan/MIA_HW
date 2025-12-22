#include "game.hpp"
#include <iostream>
#include <windows.h>
#include <cmath>

Game::Game() : brickCount(0), movableCount(0), currentLevel(1), score(0) {
    load_level();
}

void Game::delete_moving_object(int index) {
    if (index >= 0 && index < movableCount) {
        for (int j = index; j < movableCount - 1; ++j) {
            movingObjects[j] = movingObjects[j + 1];
        }
        movableCount--;
    }
}

void Game::load_level() {
    score = 0;
    renderer.set_console_color(1); ; 
    Sleep(50);
    brickCount = 0;
    movableCount = 0;
    mario = GameObject(39, 10, 3, 3, '@');
    

    if (currentLevel == 1) {
        brickCount = 13;
        bricks[0] = GameObject(30, 10, 5, 3, '?');
        bricks[1] = GameObject(50, 10, 5, 3, '?');
        bricks[2] = GameObject(70, 5, 5, 3, '?');
        bricks[3] = GameObject(80, 5, 5, 3, '?');

        bricks[4] = GameObject(60, 5, 10, 3, '-');
        bricks[5] = GameObject(75, 5, 5, 3, '-');
        bricks[6] = GameObject(85, 5, 10, 3, '-');

        bricks[7] = GameObject(20, 20, 40, 5, '#');
        bricks[8] = GameObject(60, 15, 40, 10, '#');
        bricks[9] = GameObject(100, 20, 20, 5, '#');
        bricks[10] = GameObject(120, 15, 10, 10, '#');
        bricks[11] = GameObject(150, 20, 40, 5, '#');
        bricks[12] = GameObject(210, 15, 10, 10, '+'); 
        
        movableCount = 2;
        movingObjects[0] = GameObject(25, 10, 3, 2, 'o');
        movingObjects[1] = GameObject(80, 10, 3, 2, 'o');
    }

    if (currentLevel == 2) {
        brickCount = 6;
        bricks[0] = GameObject(20, 20, 40, 5, '#');
        bricks[1] = GameObject(60, 15, 10, 10, '#');
        bricks[2] = GameObject(80, 20, 20, 5, '#');
        bricks[3] = GameObject(120, 15, 10, 10, '#');
        bricks[4] = GameObject(150, 20, 40, 5, '#');
        bricks[5] = GameObject(210, 15, 10, 10, '+'); 

        movableCount = 6;
        movingObjects[0] = GameObject(25, 10, 3, 2, 'o');
        movingObjects[1] = GameObject(80, 10, 3, 2, 'o');
        movingObjects[2] = GameObject(65, 10, 3, 2, 'o');
        movingObjects[3] = GameObject(120, 10, 3, 2, 'o');
        movingObjects[4] = GameObject(160, 10, 3, 2, 'o');
        movingObjects[5] = GameObject(175, 10, 3, 2, 'o');
    }
    
    if (currentLevel == 3) {
        brickCount = 4;
        bricks[0] = GameObject(20, 20, 40, 5, '#');
        bricks[1] = GameObject(80, 20, 15, 5, '#');
        bricks[2] = GameObject(120, 15, 15, 10, '#');
        bricks[3] = GameObject(160, 10, 15, 15, '+'); 

        movableCount = 6;
        movingObjects[0] = GameObject(25, 10, 3, 2, 'o');
        movingObjects[1] = GameObject(50, 10, 3, 2, 'o');
        movingObjects[2] = GameObject(80, 10, 3, 2, 'o');
        movingObjects[3] = GameObject(90, 10, 3, 2, 'o');
        movingObjects[4] = GameObject(120, 10, 3, 2, 'o');
        movingObjects[5] = GameObject(130, 10, 3, 2, 'o');
    }

    if (currentLevel == 4) {
        brickCount = 9;
        bricks[0] = GameObject(20, 20, 40, 5, '#');
        bricks[1] = GameObject(80, 20, 15, 5, '#');
        bricks[2] = GameObject(120, 15, 15, 10, '#');
        bricks[3] = GameObject(-10, 15, 20, 10, '#');
        bricks[4] = GameObject(160, 10, 15, 15, '+'); 

        bricks[5] = GameObject(30, 10, 5, 3, '?');
        bricks[6] = GameObject(0, 5, 5, 3, '-');
        bricks[7] = GameObject(-5, 5, 5, 3, '?');
        bricks[8] = GameObject(-10, 5, 5, 3, '-');


        movableCount = 6;
        movingObjects[0] = GameObject(25, 10, 3, 2, 'o');
        movingObjects[1] = GameObject(50, 10, 3, 2, 'o');
        movingObjects[2] = GameObject(80, 10, 3, 2, 'o');
        movingObjects[3] = GameObject(90, 10, 3, 2, 'o');
        movingObjects[4] = GameObject(120, 10, 3, 2, 'o');
        movingObjects[5] = GameObject(130, 10, 3, 2, 'o');
    }
}

void Game::handle_player_death() {
    renderer.set_console_color(4); 
    Sleep(500);
    score = 0;
   // currentLevel = 1; 
    load_level(); 
}

void Game::handle_mario_collisions() {
    for (int i = 0; i < movableCount; ++i) {
        if (check_collision(mario, movingObjects[i])) {
            
            if (movingObjects[i].objectType == 'o') { 
                if (mario.isFlying == true && mario.verticalSpeed > 0 &&
                    mario.y + mario.height < movingObjects[i].y + movingObjects[i].height * 0.5f) {
                    
                    score += 50;
                    delete_moving_object(i);
                    i--;
                    continue;
                } else {
                    handle_player_death();
                    return;
                }
            }
            
            if (movingObjects[i].objectType == '$') { 
                score += 100;
                delete_moving_object(i);
                i--;
                continue;
            }
        }
    }
}

void Game::move_object_horizontally(GameObject& obj) {
    obj.x += obj.horizontalSpeed;
    
    for (int i = 0; i < brickCount; ++i)
        if (check_collision(obj, bricks[i])) {
            obj.x -= obj.horizontalSpeed;
            obj.horizontalSpeed = -obj.horizontalSpeed; 
            return;
        }
    
    if (obj.objectType == 'o') { 
        GameObject temp = obj;
        
        temp.y += 1.0f; 
        
        bool foundCollisionBelow = false;
        for (int i = 0; i < brickCount; ++i) {
            if (check_collision(temp, bricks[i])) {
                foundCollisionBelow = true;
                break;
            }
        }
        
        if (!foundCollisionBelow) {
            obj.x -= obj.horizontalSpeed; 
            obj.horizontalSpeed = -obj.horizontalSpeed; 
        }
    }
}

void Game::move_object_vertically(GameObject& obj) {
    obj.isFlying = true;
    obj.verticalSpeed += 0.05f; 
    obj.y += obj.verticalSpeed;

    for (int i = 0; i < brickCount; ++i) {
        if (check_collision(obj, bricks[i])) {
            
            if (obj.verticalSpeed > 0) { 
                obj.isFlying = false;
            }


            if (bricks[i].objectType == '?' && obj.verticalSpeed < 0 && &obj == &mario) {
                bricks[i].objectType = '-'; 
                if (movableCount < MAX_MOVING_OBJECTS) {
                    movingObjects[movableCount] = GameObject(bricks[i].x, bricks[i].y - 3, 3, 2, '$');
                    movingObjects[movableCount].verticalSpeed = -0.7f; 
                    movableCount++;
                }
            }
            
            obj.y -= obj.verticalSpeed;
            obj.verticalSpeed = 0;

            if (bricks[i].objectType == '+') {
                currentLevel++;
                if (currentLevel > MAX_LEVEL) currentLevel = 1;
                renderer.set_console_color(2); 
                Sleep(500);
                load_level(); 
            }
            break;
        }
    }
}

void Game::scroll_map_horizontally(float deltaX) {
    mario.x -= deltaX;
    for (int i = 0; i < brickCount; ++i) {
        if (check_collision(mario, bricks[i])) {
            mario.x += deltaX; 
            return; 
        }
    }
    mario.x += deltaX; 

    for (int i = 0; i < brickCount; ++i) {
        bricks[i].x += deltaX;
    }
    for (int i = 0; i < movableCount; ++i) {
        movingObjects[i].x += deltaX;
    }
}


void Game::run_game_loop() {

    renderer.clear_screan();

    while (GetKeyState(VK_ESCAPE) >= 0) {
        
        renderer.clear_map();

        if ((mario.isFlying == false) && (GetKeyState(VK_SPACE) < 0)) 
            mario.verticalSpeed = -1.0f; 

        if (GetKeyState('A') < 0) 
            scroll_map_horizontally(1.0f);
        if (GetKeyState('D') < 0) 
            scroll_map_horizontally(-1.0f);

        if (mario.y > MAP_HEIGHT) 
            handle_player_death();


        move_object_vertically(mario);
        handle_mario_collisions();
        

        for (int i = 0; i < brickCount; ++i) {
            renderer.draw_object(bricks[i]);
        }
        

        for (int i = 0; i < movableCount; ++i) {
            move_object_vertically(movingObjects[i]);
            move_object_horizontally(movingObjects[i]);


            if (movingObjects[i].y > MAP_HEIGHT) {
                delete_moving_object(i);
                i--; 
                continue;
            }
            renderer.draw_object(movingObjects[i]);
        }

        renderer.draw_object(mario);
        renderer.draw_score(score, currentLevel);
        
        renderer.fast_draw_map();

        Sleep(10); 
    }
    

    renderer.set_console_color(0);
    renderer.clear_screan();     
}