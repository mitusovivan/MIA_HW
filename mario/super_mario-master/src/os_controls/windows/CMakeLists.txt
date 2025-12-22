target_sources(${PROJECT_NAME}
	PRIVATE
		os_control_settings.cpp
		user_input.cpp
)

target_include_directories(${PROJECT_NAME} PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
)
