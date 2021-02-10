cmake_minimum_required(VERSION 3.19)
project(CppMonitor)

set(CMAKE_CXX_STANDARD 17)

set(CMAKE_EXPORT_COMPILE_COMMANDS 1)

add_subdirectory(libs)

add_executable(CppMonitor main.cpp)
target_link_libraries(CppMonitor LLVM clang-cpp OGDF gvc cgraph)

add_executable(test test.cpp)
target_link_libraries(test gvc cgraph)

add_executable(testCode testCode.cpp)
