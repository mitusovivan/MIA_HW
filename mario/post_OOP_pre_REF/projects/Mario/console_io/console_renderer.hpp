#pragma once

#include <windows.h>
#include <cstdio>
#include "game_object.hpp"

const int MAP_HEIGHT = 25;
const int MAP_WIDTH = 120;

class ConsoleRenderer {
private:
    HANDLE hConsole;
    CHAR_INFO charBuffer[MAP_WIDTH * MAP_HEIGHT];

    bool is_position_in_map(int x, int y) const;
    WORD get_object_color(char objectType) const;
    
public:
    ConsoleRenderer();
    ~ConsoleRenderer() = default;

    void clear_screan();
    void clear_map();
    void draw_object(const GameObject& obj);
    void draw_score(int score, int currentLevel);
    void fast_draw_map();
    void hide_console_cursor();
    void set_console_color(int colorCode);
};

