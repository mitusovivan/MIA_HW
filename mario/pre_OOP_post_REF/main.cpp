#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cstring>
#include <iostream>
#include <windows.h>
#include <stdexcept>

const int MAP_HEIGHT = 25;
const int MAP_WIDTH = 120;
const int MAX_BRICKS = 30;
const int MAX_MOVING_OBJECTS = 30;

typedef struct GameObject {
    float x, y;
    float width, height;
    float verticalSpeed;
    bool isFlying;
    char objectType;
    float horizontalSpeed;
} GameObject;

bool check_collision(GameObject o1, GameObject o2);
void clear_map(CHAR_INFO charBuffer[]);
void delete_moving_object(GameObject movingObjects[], int& movableCount, int index);
void draw_object(CHAR_INFO charBuffer[], GameObject obj);
void draw_score(CHAR_INFO charBuffer[], int score, int currentLevel);
void fast_draw_map(CHAR_INFO charBuffer[], HANDLE hConsole);
void initialize_object(GameObject& obj, float xPos, float yPos, float oWidth, float oHeight, char inType);
bool is_position_in_map(int x, int y);
void hide_console_cursor(HANDLE hConsole);

void load_level(int& currentLevel, int maxLevel, GameObject& mario, GameObject bricks[], 
                int& brickCount, GameObject movingObjects[], int& movableCount);

void handle_player_death(
    int& score, 
    int& currentLevel, 
    int maxLevel, 
    GameObject& mario, 
    GameObject *bricks, int& brickCount,
    GameObject *movingObjects, int& movableCount
);
void handle_mario_collisions(GameObject& mario, GameObject movingObjects[], int& movableCount, int& score,
                            void (*playerDeathHandler)(int&, int&, int, GameObject&, GameObject[], int&, GameObject[], int&),
                            int& currentLevel, int maxLevel, GameObject bricks[], int& brickCount);

void move_object_horizontally(GameObject& obj, GameObject bricks[], int brickCount);

void move_object_vertically(GameObject& obj, GameObject bricks[], int& brickCount, GameObject& marioPointer, 
                            int& currentLevel, int maxLevel, GameObject movingObjects[], int& movableCount, int& score);

void scroll_map_horizontally(GameObject& mario, GameObject bricks[], int brickCount, GameObject movingObjects[], int movableCount, float deltaX);


int main() {
    CHAR_INFO charBuffer[MAP_WIDTH * MAP_HEIGHT];
    HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);

    GameObject mario;
    GameObject bricks[MAX_BRICKS];
    int brickCount;
    GameObject movingObjects[MAX_MOVING_OBJECTS];
    int movableCount;

    int currentLevel = 1;
    const int maxLevel = 3; 
    int score = 0;

    hide_console_cursor(hConsole);
    
    load_level(currentLevel, maxLevel, mario, bricks, brickCount, movingObjects, movableCount);

    while (GetKeyState(VK_ESCAPE) >= 0) {
        
        clear_map(charBuffer);

        if ((mario.isFlying == false) && (GetKeyState(VK_SPACE) < 0)) 
            mario.verticalSpeed = -1.0f; 

        if (GetKeyState('A') < 0) 
            scroll_map_horizontally(mario, bricks, brickCount, movingObjects, movableCount, 1.0f);
        if (GetKeyState('D') < 0) 
            scroll_map_horizontally(mario, bricks, brickCount, movingObjects, movableCount, -1.0f);

        if (mario.y > MAP_HEIGHT) 
            handle_player_death(score, currentLevel, maxLevel, mario, bricks, brickCount, movingObjects, movableCount);

        move_object_vertically(mario, bricks, brickCount, mario, currentLevel, maxLevel, movingObjects, movableCount, score);
        
        handle_mario_collisions(mario, movingObjects, movableCount, score, 
                                handle_player_death, currentLevel, maxLevel, bricks, brickCount);
        
        for (int i = 0; i < brickCount; ++i) {
            draw_object(charBuffer, bricks[i]);
        }
        
        for (int i = 0; i < movableCount; ++i) {
            move_object_vertically(movingObjects[i], bricks, brickCount, mario, currentLevel, maxLevel, movingObjects, movableCount, score);
            move_object_horizontally(movingObjects[i], bricks, brickCount);

            if (movingObjects[i].y > MAP_HEIGHT) {
                delete_moving_object(movingObjects, movableCount, i);
                i--; 
                continue;
            }
            draw_object(charBuffer, movingObjects[i]);
        }
        
        draw_object(charBuffer, mario);
        draw_score(charBuffer, score, currentLevel);
        
        fast_draw_map(charBuffer, hConsole);

        Sleep(10); 
    }
    
    system("color 0F");
    system("cls");
    return 0;
}

bool check_collision(GameObject o1, GameObject o2) {
    return (((o1.x + o1.width) > o2.x) && (o1.x < (o2.x + o2.width))
            && ((o1.y + o1.height) > o2.y) && (o1.y < (o2.y + o2.height)));
}

void clear_map(CHAR_INFO charBuffer[]) {
    for (int i = 0; i < MAP_WIDTH * MAP_HEIGHT; ++i) {
        charBuffer[i].Char.AsciiChar = ' ';
        charBuffer[i].Attributes = FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_RED | BACKGROUND_BLUE; 
    }
}

void delete_moving_object(GameObject movingObjects[], int& movableCount, int index) {
    if (index >= 0 && index < movableCount) {
        for (int j = index; j < movableCount - 1; ++j) {
            movingObjects[j] = movingObjects[j + 1];
        }
        movableCount--;
    }
}

void draw_object(CHAR_INFO charBuffer[], GameObject obj) {
    int ix = (int)std::round(obj.x);
    int iy = (int)std::round(obj.y);
    int iWidth = (int)std::round(obj.width);
    int iHeight = (int)std::round(obj.height);
    
    WORD color = FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_RED | BACKGROUND_BLUE; 
    
    if (obj.objectType == '@') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE;
    } else if (obj.objectType == '#') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE; 
    } else if (obj.objectType == '?') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY |  BACKGROUND_BLUE; 
    } else if (obj.objectType == '-') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | BACKGROUND_BLUE; 
    } else if (obj.objectType == 'o') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE; 
    } else if (obj.objectType == '$') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE; 
    } else if (obj.objectType == '+') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE; 
    }

    for (int y = iy; y < (iy + iHeight); y++) {
        for (int x = ix; x < (ix + iWidth); ++x) {
            if (is_position_in_map(x, y)) {
                int index = y * MAP_WIDTH + x;
                charBuffer[index].Char.AsciiChar = obj.objectType;
                charBuffer[index].Attributes = color;
            }
        }
    }
}

void draw_score(CHAR_INFO charBuffer[], int score, int currentLevel) {
    char c[50];
    std::sprintf(c, "SCORE %d | LEVEL %d", score, currentLevel);
    int len = std::strlen(c);
    
    WORD score_color = FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY | BACKGROUND_BLUE; 

    for (int i = 0; i < len; ++i) {
        int index = 1 * MAP_WIDTH + (i + 5);
        if (index < MAP_WIDTH * MAP_HEIGHT) {
            charBuffer[index].Char.AsciiChar = c[i];
            charBuffer[index].Attributes = score_color;
        }
    }
}

void fast_draw_map(CHAR_INFO charBuffer[], HANDLE hConsole) {
    COORD bufferSize = {MAP_WIDTH, MAP_HEIGHT};
    COORD characterPosition = {0, 0};
    SMALL_RECT writeRegion = {0, 0, MAP_WIDTH - 1, MAP_HEIGHT - 1};

    COORD coord = {0, 0};
    SetConsoleCursorPosition(hConsole, coord);

    WriteConsoleOutput(hConsole, charBuffer, bufferSize, characterPosition, &writeRegion);
}

void initialize_object(GameObject& obj, float xPos, float yPos, float oWidth, float oHeight, char inType) {
    obj.x = xPos;
    obj.y = yPos;
    obj.width = oWidth;
    obj.height = oHeight;
    obj.verticalSpeed = 0;
    obj.objectType = inType;
    obj.horizontalSpeed = 0.2f;
    obj.isFlying = false;
}

bool is_position_in_map(int x, int y) {
    return x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT;
}

void handle_mario_collisions(GameObject& mario, GameObject movingObjects[], int& movableCount, int& score,
                            void (*playerDeathHandler)(int&, int&, int, GameObject&, GameObject[], int&, GameObject[], int&),
                            int& currentLevel, int maxLevel, GameObject bricks[], int& brickCount) {
    
    for (int i = 0; i < movableCount; ++i) {
        if (check_collision(mario, movingObjects[i])) {
            
            if (movingObjects[i].objectType == 'o') { 
                if (mario.isFlying == true && mario.verticalSpeed > 0 &&
                    mario.y + mario.height < movingObjects[i].y + movingObjects[i].height * 0.5f) {
                    
                    score += 50;
                    delete_moving_object(movingObjects, movableCount, i);
                    i--;
                    continue;
                } else {
                    playerDeathHandler(score, currentLevel, maxLevel, mario, bricks, brickCount, movingObjects, movableCount);
                    return;
                }
            }
            
            if (movingObjects[i].objectType == '$') { 
                score += 100;
                delete_moving_object(movingObjects, movableCount, i);
                i--;
                continue;
            }
        }
    }
}

void handle_player_death(int& score, int& currentLevel, int maxLevel, GameObject& mario, 
                        GameObject bricks[], int& brickCount, GameObject movingObjects[], int& movableCount) {
    system("color 4F"); 
    Sleep(500);
    score = 0;
    load_level(currentLevel, maxLevel, mario, bricks, brickCount, movingObjects, movableCount); 
}

void hide_console_cursor(HANDLE hConsole) {
    CONSOLE_CURSOR_INFO cursorInfo;
    GetConsoleCursorInfo(hConsole, &cursorInfo);
    cursorInfo.bVisible = false;
    SetConsoleCursorInfo(hConsole, &cursorInfo);
}

void load_level(int& currentLevel, int maxLevel, GameObject& mario, GameObject bricks[], 
                int& brickCount, GameObject movingObjects[], int& movableCount) {
    
    system("color 1F"); 
    Sleep(50);
    brickCount = 0;
    movableCount = 0;
    initialize_object(mario, 39, 10, 3, 3, '@');
    
    if (currentLevel == 1) {
        brickCount = 13;

        
        initialize_object(bricks[0], 30, 10, 5, 3, '?');
        initialize_object(bricks[1], 50, 10, 5, 3, '?');
        initialize_object(bricks[2], 70, 5, 5, 3, '?');
        initialize_object(bricks[3], 80, 5, 5, 3, '?');

        initialize_object(bricks[4], 60, 5, 10, 3, '-');
        initialize_object(bricks[5], 75, 5, 5, 3, '-');
        initialize_object(bricks[6], 85, 5, 10, 3, '-');

        initialize_object(bricks[7], 20, 20, 40, 5, '#');
        initialize_object(bricks[8], 60, 15, 40, 10, '#');
        initialize_object(bricks[9], 100, 20, 20, 5, '#');
        initialize_object(bricks[10], 120, 15, 10, 10, '#');
        initialize_object(bricks[11], 150, 20, 40, 5, '#');
        initialize_object(bricks[12], 210, 15, 10, 10, '+'); 
        
        movableCount = 2;
        initialize_object(movingObjects[0], 25, 10, 3, 2, 'o');
        initialize_object(movingObjects[1], 80, 10, 3, 2, 'o');
    }

    if (currentLevel == 2) {
        brickCount = 6;
        initialize_object(bricks[0], 20, 20, 40, 5, '#');
        initialize_object(bricks[1], 60, 15, 10, 10, '#');
        initialize_object(bricks[2], 80, 20, 20, 5, '#');
        initialize_object(bricks[3], 120, 15, 10, 10, '#');
        initialize_object(bricks[4], 150, 20, 40, 5, '#');
        initialize_object(bricks[5], 210, 15, 10, 10, '+'); 

        movableCount = 6;
        initialize_object(movingObjects[0], 25, 10, 3, 2, 'o');
        initialize_object(movingObjects[1], 80, 10, 3, 2, 'o');
        initialize_object(movingObjects[2], 65, 10, 3, 2, 'o');
        initialize_object(movingObjects[3], 120, 10, 3, 2, 'o');
        initialize_object(movingObjects[4], 160, 10, 3, 2, 'o');
        initialize_object(movingObjects[5], 175, 10, 3, 2, 'o');
    }
    
    if (currentLevel == 3) {
        brickCount = 4;
        initialize_object(bricks[0], 20, 20, 40, 5, '#');
        initialize_object(bricks[1], 80, 20, 15, 5, '#');
        initialize_object(bricks[2], 120, 15, 15, 10, '#');
        initialize_object(bricks[3], 160, 10, 15, 15, '+'); 

        movableCount = 6;
        initialize_object(movingObjects[0], 25, 10, 3, 2, 'o');
        initialize_object(movingObjects[1], 50, 10, 3, 2, 'o');
        initialize_object(movingObjects[2], 80, 10, 3, 2, 'o');
        initialize_object(movingObjects[3], 90, 10, 3, 2, 'o');
        initialize_object(movingObjects[4], 120, 10, 3, 2, 'o');
        initialize_object(movingObjects[5], 130, 10, 3, 2, 'o');
    }
}

void move_object_horizontally(GameObject& obj, GameObject bricks[], int brickCount) {
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

void move_object_vertically(GameObject& obj, GameObject bricks[], int& brickCount, GameObject& marioPointer, 
                            int& currentLevel, int maxLevel, GameObject movingObjects[], int& movableCount, int& score) {
    obj.isFlying = true;
    obj.verticalSpeed += 0.05f; 
    obj.y += obj.verticalSpeed;

    for (int i = 0; i < brickCount; ++i) {
        if (check_collision(obj, bricks[i])) {
            
            if (obj.verticalSpeed > 0) { 
                obj.isFlying = false;
            }

            if (bricks[i].objectType == '?' && obj.verticalSpeed < 0 && &obj == &marioPointer) {
                bricks[i].objectType = '-'; 
                if (movableCount < MAX_MOVING_OBJECTS) {
                    initialize_object(movingObjects[movableCount], bricks[i].x, bricks[i].y - 3, 3, 2, '$');
                    movingObjects[movableCount].verticalSpeed = -0.7f; 
                    movableCount++;
                }
            }
            
            obj.y -= obj.verticalSpeed;
            obj.verticalSpeed = 0;

            if (bricks[i].objectType == '+') {
                currentLevel++;
                if (currentLevel > maxLevel) currentLevel = 1;
                system("color 2F"); 
                Sleep(500);
                load_level(currentLevel, maxLevel, marioPointer, bricks, brickCount, movingObjects, movableCount); 
            }
            break;
        }
    }
}

void scroll_map_horizontally(GameObject& mario, GameObject bricks[], int brickCount, GameObject movingObjects[], int movableCount, float deltaX) {
    
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