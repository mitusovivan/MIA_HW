#include <gtest/gtest.h>

#include "vector.hpp"

using mia::Vector;

TEST(VectorTest, DefaultConstructor) {
    Vector<int> vec;
    EXPECT_EQ(vec.get_size(), 0);
}

TEST(VectorTest, PushBack) {
    Vector<int> vec;
    vec.push_back(17);
    vec.push_back(28);
    vec.push_back(35);

    EXPECT_EQ(vec.get_size(), 3);
}

TEST(VectorTest, Insert) {
    Vector<int> vec;
    vec.push_back(17);
    vec.push_back(35);

    EXPECT_TRUE(vec.insert(1, 28));
    EXPECT_EQ(vec.get_size(), 3);

    EXPECT_TRUE(vec.insert(0, 6));
    EXPECT_EQ(vec.get_size(), 4);

    EXPECT_TRUE(vec.insert(4, 43));
    EXPECT_EQ(vec.get_size(), 5);

    EXPECT_FALSE(vec.insert(10, 100));
}

TEST(VectorTest, RemoveFirst) {
    Vector<int> vec;
    vec.push_back(17);
    vec.push_back(28);
    vec.push_back(35);
    vec.push_back(28);

    EXPECT_TRUE(vec.remove_first(28));
    EXPECT_EQ(vec.get_size(), 3);
    EXPECT_FALSE(vec.remove_first(100));
    EXPECT_EQ(vec.get_size(), 3);
}

TEST(VectorTest, HasItem) {
    Vector<int> vec;
    vec.push_back(17);
    vec.push_back(28);
    vec.push_back(35);

    EXPECT_TRUE(vec.has_item(28));
    EXPECT_FALSE(vec.has_item(100));
}

TEST(VectorTest, CapacityExpansion) {
    Vector<int> vec;
    for (int i = 0; i < 10; ++i) {
        vec.push_back(i);
    }
	const std::size_t pre_expansion_size = vec.get_size();
	vec.push_back(10);
    EXPECT_GT(vec.get_size(), pre_expansion_size);
}

TEST(VectorTest, Print) {
    Vector<int> vec;
    vec.push_back(17);
    vec.push_back(28);
    vec.push_back(35);

    testing::internal::CaptureStdout();
    vec.print();
    std::string output = testing::internal::GetCapturedStdout();
    EXPECT_EQ(output, "17, 28, 35\n");
}

int main(int argc, char **argv) {
	::testing::InitGoogleTest(&argc, argv);
	return RUN_ALL_TESTS();
}
