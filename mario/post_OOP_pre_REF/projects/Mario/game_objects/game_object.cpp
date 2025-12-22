#include "game_object.hpp"

bool check_collision(const GameObject& o1, const GameObject& o2) {
    return (((o1.x + o1.width) > o2.x) && (o1.x < (o2.x + o2.width))
            && ((o1.y + o1.height) > o2.y) && (o1.y < (o2.y + o2.height)));
}