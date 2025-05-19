add_executable(long_number_tests test_long_number.cpp)

target_link_libraries(long_number_tests 
	gtest_main 
	gmock_main
	pr_lib
)

add_test(long_number_tests long_number_tests)