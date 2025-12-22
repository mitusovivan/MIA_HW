#pragma once

namespace biv {
	namespace os {
		enum class UserInput {
			EXIT,
			MAP_LEFT,
			MAP_RIGHT,
			MARIO_JUMP,
			NO_INPUT
		};
	
		UserInput get_user_input();
	}
}
