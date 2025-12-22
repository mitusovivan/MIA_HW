#pragma once

#include "map_movable.hpp"
#include "rect.hpp"

namespace biv {
	class RectMapMovableAdapter : virtual public Rect, public MapMovable {
		public:
			RectMapMovableAdapter(const Coord& top_left, const int width, const int height);
			
			void move_map_left() noexcept override;
			void move_map_right() noexcept override;
	};
}
