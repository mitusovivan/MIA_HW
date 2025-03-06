#pragma once

namespace MIA{
    struct MenuItem {
        const char* const title;
        const MenuItem* (*funct)(const MenuItem* current);

        const MenuItem* parent;

        const MenuItem* const *children;
        const int children_count;
    };
}