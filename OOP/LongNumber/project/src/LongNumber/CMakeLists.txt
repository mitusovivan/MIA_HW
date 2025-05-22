target_sources(pr_lib
	PRIVATE
		long_number.cpp
	PUBLIC
		long_number.hpp
)

target_include_directories(pr_lib PUBLIC
	"${PROJECT_SOURCE_DIR}/src/LongNumber"
)