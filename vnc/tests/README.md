# VNC Tests

## Overview

This directory contains the test suite for the VNC implementation.

## Test Categories

### Unit Tests
- **RFB Protocol Tests**: Protocol message handling and encoding
- **Network Tests**: Socket communication and error handling
- **Platform Tests**: Screen capture and input simulation
- **Security Tests**: Authentication and encryption

### Integration Tests
- **Server-Client Tests**: Full communication flow
- **Multi-client Tests**: Concurrent client handling
- **Platform Integration**: Cross-platform compatibility

### Performance Tests
- **Encoding Benchmarks**: Compression performance
- **Network Latency**: Round-trip time measurements
- **Memory Usage**: Resource consumption analysis

## Running Tests

### Prerequisites
```bash
# Install Google Test (Ubuntu/Debian)
sudo apt install libgtest-dev

# Build Google Test
cd /usr/src/gtest
sudo cmake CMakeLists.txt
sudo make
sudo cp *.a /usr/lib
```

### Build and Run
```bash
# Configure with tests enabled
cmake .. -DBUILD_TESTS=ON

# Build tests
cmake --build . --target tests

# Run all tests
ctest -V

# Run specific test
./tests/rfb_protocol_test
```

### Test Coverage
```bash
# Build with coverage
cmake .. -DCMAKE_CXX_FLAGS="--coverage"

# Run tests
ctest

# Generate coverage report
gcov *.gcno
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html
```

## Test Structure

```
tests/
├── unit/                   # Unit tests
│   ├── rfb_protocol_test.cpp
│   ├── network_test.cpp
│   └── platform_test.cpp
├── integration/           # Integration tests
│   ├── server_client_test.cpp
│   └── multi_client_test.cpp
├── performance/          # Performance tests
│   ├── encoding_benchmark.cpp
│   └── latency_test.cpp
├── data/                 # Test data files
│   ├── sample_images/
│   └── protocol_traces/
└── CMakeLists.txt        # Test build configuration
```

## Writing Tests

### Example Test
```cpp
#include <gtest/gtest.h>
#include "vnc_server.h"

class VNCServerTest : public ::testing::Test {
protected:
    void SetUp() override {
        server = std::make_unique<vnc::VNCServer>();
    }
    
    std::unique_ptr<vnc::VNCServer> server;
};

TEST_F(VNCServerTest, StartStop) {
    EXPECT_TRUE(server->start(5901));
    EXPECT_TRUE(server->isRunning());
    server->stop();
    EXPECT_FALSE(server->isRunning());
}
```

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Main branch commits
- Release builds

### CI Configuration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Install dependencies
      run: sudo apt install libx11-dev libxtst-dev libgtest-dev
    - name: Build and test
      run: |
        mkdir build && cd build
        cmake .. -DBUILD_TESTS=ON
        cmake --build .
        ctest -V
```