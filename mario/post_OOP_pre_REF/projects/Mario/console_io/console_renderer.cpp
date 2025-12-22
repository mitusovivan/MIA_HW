#include "console_renderer.hpp"
#include <cmath>
#include <cstring>
#include <iostream>

ConsoleRenderer::ConsoleRenderer() {
    hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
    hide_console_cursor();
}

bool ConsoleRenderer::is_position_in_map(int x, int y) const {
    return x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT;
}

WORD ConsoleRenderer::get_object_color(char objectType) const {
    WORD color = FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_RED | BACKGROUND_BLUE; 
    
    if (objectType == '@') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE;
    } else if (objectType == '#') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE; 
    } else if (objectType == '?') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY |  BACKGROUND_BLUE; 
    } else if (objectType == '-') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | BACKGROUND_BLUE; 
    } else if (objectType == 'o') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE; 
    } else if (objectType == '$') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE; 
    } else if (objectType == '+') { 
        color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY | BACKGROUND_BLUE; 
    }
    return color;
}

void ConsoleRenderer::clear_screan(){
    system("cls");
}


void ConsoleRenderer::clear_map() {
    for (int i = 0; i < MAP_WIDTH * MAP_HEIGHT; ++i) {
        charBuffer[i].Char.AsciiChar = ' ';
        charBuffer[i].Attributes = FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_RED | BACKGROUND_BLUE; 
    }
}

void ConsoleRenderer::draw_object(const GameObject& obj) {
    int ix = (int)std::round(obj.x);
    int iy = (int)std::round(obj.y);
    int iWidth = (int)std::round(obj.width);
    int iHeight = (int)std::round(obj.height);
    
    WORD color = get_object_color(obj.objectType);

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

void ConsoleRenderer::draw_score(int score, int currentLevel) {
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

void ConsoleRenderer::fast_draw_map() {
    COORD bufferSize = {MAP_WIDTH, MAP_HEIGHT};
    COORD characterPosition = {0, 0};
    SMALL_RECT writeRegion = {0, 0, MAP_WIDTH - 1, MAP_HEIGHT - 1};

    COORD coord = {0, 0};
    SetConsoleCursorPosition(hConsole, coord);

    WriteConsoleOutput(hConsole, charBuffer, bufferSize, characterPosition, &writeRegion);
}

void ConsoleRenderer::hide_console_cursor() {
    CONSOLE_CURSOR_INFO cursorInfo;
    GetConsoleCursorInfo(hConsole, &cursorInfo);
    cursorInfo.bVisible = false;
    SetConsoleCursorInfo(hConsole, &cursorInfo);
}

void ConsoleRenderer::set_console_color(int colorCode) {
    char command[10];
    sprintf(command, "color %XF", colorCode);
    system(command);
}