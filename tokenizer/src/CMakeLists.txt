include(FindLibClang)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${LIBCLANG_CXXFLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -Wall -pedantic -Wextra")

include_directories(external)

add_executable(tokenize tokenize.cpp)
target_link_libraries(tokenize ${LIBCLANG_LIBRARIES})

add_executable(find_symbols find_symbols.cpp)
target_link_libraries(find_symbols ${LIBCLANG_LIBRARIES})

add_executable(extract_juliet_labels extract_juliet_labels.cpp)
target_link_libraries(extract_juliet_labels ${LIBCLANG_LIBRARIES})
