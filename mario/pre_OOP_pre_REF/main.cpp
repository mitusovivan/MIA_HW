#include <stdio.h>
#include <stdlib.h>

#include <math.h>
#include <windows.h>

const int MAP_HEIGHT = 25;
const int MAP_WIDTH = 120;

typedef struct SObject {
    float x, y;
    float width, height;
    float vertSpeed;
    bool IsFly;
    char cType;
    float horizonSpeed;
} TObject;


char map[MAP_HEIGHT][MAP_WIDTH+1];
TObject mario;
TObject *bricks = NULL;
TObject *moving = NULL;
int movable_count;
int brick_count;
int level = 1;
int score;
int maxlvl;

void clearMap(){
    for (int i = 0; i < MAP_WIDTH; ++i)
        map[0][i] = ' ';
    map[0][MAP_WIDTH] = '\0';

    for (int j = 0; j < MAP_HEIGHT; ++j)
        sprintf(map[j], map[0]);
}

void ShowMap(){
    map[MAP_HEIGHT-1][MAP_WIDTH-1] = '\0';
    for (int j = 0; j < MAP_HEIGHT; ++j)
        printf("%s\n", map[j]);
}

void SetObjectPos(TObject *obj, float xPos, float yPos){
    obj->x = xPos;
    obj->y = yPos;
}

bool IsCollision(TObject o1, TObject o2);
void CreateLevel(int lvl);
void InitObject(TObject *obj, float xPos, float yPos, float oWidth, float oHeight, char inType);


void move_obj_vertically(TObject *obj){
    obj->IsFly = TRUE;
    obj->vertSpeed += 0.05;
    SetObjectPos(obj, obj->x, obj->y + obj->vertSpeed);


    for (int i = 0; i < brick_count; ++i){
        if (IsCollision(*obj, bricks[i])){
            if (obj[0].vertSpeed > 0){
                obj[0].IsFly = FALSE;
            }
            if (bricks[i].cType == '?' && obj[0].vertSpeed < 0 && obj == &mario){
                bricks[i].cType = '-';
                InitObject(moving+i+2, bricks[i].x, bricks[i].y - 3, 3, 2, '$');
                moving[i+2].vertSpeed = -0.7;
            }
            obj->y -= obj->vertSpeed;
            obj->vertSpeed = 0;
            if (bricks[i].cType == '+'){
                ++level;
                if (level > maxlvl) level = 1;
                system("color 2F");
                Sleep(500);
                CreateLevel(level);
            }
            break;
        }
    }
}


void InitObject(TObject *obj, float xPos, float yPos, float oWidth, float oHeight, char inType){
    SetObjectPos(obj, xPos, yPos);
    obj->width = oWidth;
    obj->height = oHeight;
    obj->vertSpeed = 0;
    obj->cType = inType;
    obj->horizonSpeed = 0.2;
}

void PlayerDead(){
    system("color 4F");
    Sleep(500);
    CreateLevel(level);
}

void DeleteMoving(int i){
    for (int j = i; j < movable_count; ++j){
        moving[j] = moving[j + 1];
    }
}

void MarioCollision(){
    for (int i = 0; i < movable_count; ++i){
        if (IsCollision(mario, moving[i])){
            if (moving[i].cType == 'o'){
                if (mario.IsFly == TRUE && mario.vertSpeed > 0 && mario.y + mario.height < moving[i].y + moving[i].height * 0.5){
                    score += 50;
                    DeleteMoving(i);
                    --i;
                    continue;
                } else {
                    PlayerDead();
                }
            }
            if (moving[i].cType == '$'){
                score += 100;
                DeleteMoving(i);
                --i;
                continue;
            }
        }
    }
}

void HorizonMoveObject(TObject *obj){
    obj[0].x += obj[0].horizonSpeed;
    for (int i = 0; i < brick_count; ++i)
        if (IsCollision(obj[0], bricks[i])){
            obj[0].x -= obj[0].horizonSpeed;
            obj[0].horizonSpeed = -obj[0].horizonSpeed;
            return;
        }
    
    if (obj[0].cType == 'o'){        
        TObject tmp = *obj;
        move_obj_vertically(&tmp);
        if (tmp.IsFly == TRUE){
            obj[0].x -= obj[0].horizonSpeed;
            obj[0].horizonSpeed = -obj[0].horizonSpeed;
        }
    }

}

bool IsPosInMap(int x, int y){
    return x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT;
}

void PutObjectOnMap(TObject obj){
    int ix = (int)round(obj.x);
    int iy = (int)round(obj.y);
    int iWidth = (int)round(obj.width);
    int iHeight = (int)round(obj.height);


    for (int i = ix; i < (ix + iWidth); ++i)
        for (int j = iy; j < (iy + iHeight); j++)
            if (IsPosInMap(i, j))
                map[j][i] = obj.cType;
}


void setCur(int x, int y){
    COORD coord;
    coord.X = x;
    coord.Y = y;
    SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), coord);
}

void HorizonMoveMap(float dx){

    mario.x -= dx;
    for (int i = 0; i < brick_count; ++i){
        if (IsCollision(mario, bricks[i])){
            mario.x += dx;
            return;
        }
    }
    mario.x += dx;

    for (int i = 0; i < brick_count; ++i){
        bricks[i].x += dx;
    }
    for (int i = 0; i < movable_count; ++i){
        moving[i].x += dx;
    }
}

bool IsCollision(TObject o1, TObject o2){
    return (((o1.x + o1.width) > o2.x) && (o1.x < (o2.x + o2.width))
            && ((o1.y + o1.height) > o2.y) && (o1.y < (o2.y + o2.height)));
}

void PutScoreOnMap(){
    char c[30];
    sprintf(c, "Score %d", score);
    int len = strlen(c);
    for (int i = 0; i < len; ++i){
        map[1][i+5] = c[i];
    }
}

void CreateLevel(int lvl){

    system("color 9F");
    brick_count = 0;
    movable_count = 0;
    delete bricks;
    delete moving;
    InitObject(&mario, 39, 10, 3, 3, '@');
    score = 0;

        if (lvl == 1){
        brick_count = 13;
        bricks = new TObject[brick_count];

        InitObject(bricks+0, 30, 10, 5, 3, '?');
        InitObject(bricks+1, 50, 10, 5, 3, '?');
        InitObject(bricks+2, 70, 5, 5, 3, '?');
        InitObject(bricks+3, 80, 5, 5, 3, '?');

        InitObject(bricks+4, 60, 5, 10, 3, '-');
        InitObject(bricks+5, 75, 5, 5, 3, '-');
        InitObject(bricks+6, 85, 5, 10, 3, '-');

        InitObject(bricks+7, 20, 20, 40, 5, '#');
        InitObject(bricks+8, 60, 15, 40, 10, '#');
        InitObject(bricks+9, 100, 20, 20, 5, '#');
        InitObject(bricks+10, 120, 15, 10, 10, '#');
        InitObject(bricks+11, 150, 20, 40, 5, '#');
        InitObject(bricks+12, 210, 15, 10, 10, '+');

        movable_count = 6;
        moving = new TObject[movable_count];

        InitObject(moving+0, 25, 10, 3, 2, 'o');
        InitObject(moving+1, 80, 10, 3, 2, 'o');
        
    }

    if (lvl == 2){
        brick_count = 6;
        bricks = new TObject[brick_count];       
        InitObject(bricks+0, 20, 20, 40, 5, '#');
        InitObject(bricks+1, 60, 15, 10, 10, '#');
        InitObject(bricks+2, 80, 20, 20, 5, '#');
        InitObject(bricks+3, 120, 15, 10, 10, '#');
        InitObject(bricks+4, 150, 20, 40, 5, '#');
        InitObject(bricks+5, 210, 15, 10, 10, '+');

        movable_count = 6;
        moving = new TObject[movable_count];     
        InitObject(moving+0, 25, 10, 3, 2, 'o');
        InitObject(moving+1, 80, 10, 3, 2, 'o');
        InitObject(moving+2, 65, 10, 3, 2, 'o');
        InitObject(moving+3, 120, 10, 3, 2, 'o');
        InitObject(moving+4, 160, 10, 3, 2, 'o');
        InitObject(moving+5, 175, 10, 3, 2, 'o');
    }
    if (lvl == 3){
        brick_count = 4;
        bricks = new TObject[brick_count];   
        InitObject(bricks+0, 20, 20, 40, 5, '#');
        InitObject(bricks+1, 80, 20, 15, 5, '#');
        InitObject(bricks+2, 120, 15, 15, 10, '#');
        InitObject(bricks+3, 160, 10, 15, 15, '+');

        movable_count = 6;
        moving = new TObject[movable_count];     
        InitObject(moving+0, 25, 10, 3, 2, 'o');
        InitObject(moving+1, 50, 10, 3, 2, 'o');
        InitObject(moving+2, 80, 10, 3, 2, 'o');
        InitObject(moving+3, 90, 10, 3, 2, 'o');
        InitObject(moving+4, 120, 10, 3, 2, 'o');
        InitObject(moving+5, 130, 10, 3, 2, 'o');
    }
    maxlvl = 3;
}

int main(){
    CreateLevel(level);

    while (GetKeyState(VK_ESCAPE) >= 0){
        clearMap();


        if ((mario.IsFly == FALSE) && (GetKeyState(VK_SPACE) < 0)) mario.vertSpeed = -1;
        if (GetKeyState('A') < 0) HorizonMoveMap(1);
        if (GetKeyState('D') < 0) HorizonMoveMap(-1);

        if (mario.y > MAP_HEIGHT) PlayerDead();

        move_obj_vertically(&mario);
        MarioCollision();
        for (int i = 0; i < brick_count; ++i){
            PutObjectOnMap(bricks[i]);
        }
        for (int i = 0; i < movable_count; ++i){
            move_obj_vertically(moving + i);
            HorizonMoveObject(moving + i);
            if (moving[i].y > MAP_HEIGHT){
                DeleteMoving(i);
                --i;
                continue;
            }
            PutObjectOnMap(moving[i]);
        }
        PutObjectOnMap(mario);
        PutScoreOnMap();
        setCur(0,0);
        ShowMap();

        Sleep(10);
    }

    return 0;
}