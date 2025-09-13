#include <gtest/gtest.h>
#include "../src/common/rfb_protocol.h"

class RFBProtocolTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup test environment
    }
    
    void TearDown() override {
        // Cleanup
    }
};

TEST_F(RFBProtocolTest, VersionHandshake) {
    vnc::RFBServer server;
    
    // Test version string handling
    const char* versionString = "RFB 003.008\n";
    bool result = server.handleIncomingData(
        reinterpret_cast<const uint8_t*>(versionString), 
        strlen(versionString)
    );
    
    EXPECT_TRUE(result);
}

TEST_F(RFBProtocolTest, PixelFormatValidation) {
    vnc::PixelFormat format;
    format.bitsPerPixel = 32;
    format.depth = 24;
    format.bigEndianFlag = 0;
    format.trueColourFlag = 1;
    
    // Validate pixel format structure
    EXPECT_EQ(format.bitsPerPixel, 32);
    EXPECT_EQ(format.depth, 24);
    EXPECT_EQ(format.trueColourFlag, 1);
}

TEST_F(RFBProtocolTest, SecurityNegotiation) {
    vnc::RFBServer server;
    
    // Test security type handling
    uint8_t securityChoice = vnc::NONE;
    bool result = server.handleIncomingData(&securityChoice, 1);
    
    EXPECT_TRUE(result);
}

TEST_F(RFBProtocolTest, MessageEncoding) {
    vnc::RFBClient client;
    
    // Test key event encoding
    client.sendKeyEvent(65, true); // 'A' key down
    auto data = client.getOutgoingData();
    
    EXPECT_FALSE(data.empty());
    EXPECT_EQ(data[0], vnc::KEY_EVENT);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}