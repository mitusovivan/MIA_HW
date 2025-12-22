#pragma once

struct GameObject {
    float x, y;
    float width, height;
    float verticalSpeed;
    bool isFlying;
    char objectType;
    float horizontalSpeed;

    GameObject() : x(0), y(0), width(0), height(0), verticalSpeed(0), isFlying(false), objectType(' '), horizontalSpeed(0.2f) {}

    GameObject(float xPos, float yPos, float oWidth, float oHeight, char inType) {
        x = xPos;
        y = yPos;
        width = oWidth;
        height = oHeight;
        verticalSpeed = 0;
        objectType = inType;
        horizontalSpeed = 0.2f;
        isFlying = false;
    }
};

bool check_collision(const GameObject& o1, const GameObject& o2);

