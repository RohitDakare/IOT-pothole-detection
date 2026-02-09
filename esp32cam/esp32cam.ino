#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// --- WiFi Configuration ---
String ssid = "";
String password = "";
const char* serverUrl = "http://195.35.23.26/api/upload_image";

// --- Pin Definitions (AI-THINKER ESP32-CAM) ---
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setup() {
  Serial.begin(115200);
  
  // Wait for WiFi credentials
  while (ssid == "" || password == "") {
    if (Serial.available()) {
      String command = Serial.readStringUntil('\n');
      if (command.startsWith("ssid:")) {
        ssid = command.substring(5);
      } else if (command.startsWith("pass:")) {
        password = command.substring(5);
      }
    }
    delay(100);
  }

  // WiFi Setup
  WiFi.begin(ssid.c_str(), password.c_str());
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  // Camera Config
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if(psramFound()){
    config.frame_size = FRAMESIZE_UXGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x", err);
  }
}

void captureAndUpload() {
  camera_fb_t * fb = esp_camera_fb_get();
  if(!fb) {
    Serial.println("UPLOAD_FAILED");
    return;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "image/jpeg");
    int code = http.POST(fb->buf, fb->len);
    if(code > 0) {
      Serial.printf("UPLOAD_SUCCESS:%d\n", code);
    } else {
      Serial.println("UPLOAD_FAILED");
    }
    http.end();
  } else {
    Serial.println("UPLOAD_FAILED");
  }
  esp_camera_fb_return(fb);
}

void loop() {
  // Listen for Serial Command from Raspberry Pi (USB connection)
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'c' || cmd == 'C') {
        Serial.println("Taking Picture...");
        captureAndUpload();
    }
  }
  delay(50);
}
