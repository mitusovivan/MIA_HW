#include "user_input.hpp"

#include <windows.h>

using biv::os::UserInput;

UserInput biv::os::get_user_input() {
	if (GetKeyState('A') < 0) {
		return UserInput::MAP_RIGHT;
	} else if (GetKeyState('D') < 0) {
		return UserInput::MAP_LEFT;
	} else if (GetKeyState(VK_SPACE) < 0) {
		return UserInput::MARIO_JUMP;
	} else if (GetKeyState(VK_ESCAPE) < 0) {
		return UserInput::EXIT;
	} else {
		return UserInput::NO_INPUT;
	}
}
