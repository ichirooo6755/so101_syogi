/*
 * XIAO ESP32S3 Sense top-down camera.
 *
 * The firmware prefers the configured Wi-Fi network.  With empty credentials
 * it starts an isolated AP, so no password is committed to the repository.
 * Endpoints: /capture (one JPEG), /stream (MJPEG), /health (JSON).
 */
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "esp_camera.h"
#include "esp_timer.h"
extern WebServer server;

// The V4 electronics drawing assigns HX711 DAT=D0/GPIO1 and CLK=D1/GPIO2.
// Use the documented 3.3 V / 5 V level shifter; camera/SD pins are untouched.
static constexpr int HX_DAT = 1;
static constexpr int HX_CLK = 2;
portMUX_TYPE hx_mux = portMUX_INITIALIZER_UNLOCKED;
int32_t hx_raw = 0;
uint32_t hx_sequence = 0;
int64_t hx_time_us = 0;
char hx_boot_id[24];

void hx_task(void *) {
  for (;;) {
    if (digitalRead(HX_DAT) == LOW) {
      uint32_t bits = 0;
      // Keep every HIGH pulse below 60 us even while Wi-Fi/camera tasks run.
      // 24 data clocks + one clock select channel A, gain 128.
      portENTER_CRITICAL(&hx_mux);
      for (int i = 0; i < 24; ++i) {
        digitalWrite(HX_CLK, HIGH);
        delayMicroseconds(1);
        bits = (bits << 1) | digitalRead(HX_DAT);
        digitalWrite(HX_CLK, LOW);
        delayMicroseconds(1);
      }
      digitalWrite(HX_CLK, HIGH);
      delayMicroseconds(1);
      digitalWrite(HX_CLK, LOW);
      hx_raw = (bits & 0x800000) ? static_cast<int32_t>(bits | 0xFF000000) : static_cast<int32_t>(bits);
      hx_time_us = esp_timer_get_time();
      ++hx_sequence;
      portEXIT_CRITICAL(&hx_mux);
    }
    vTaskDelay(pdMS_TO_TICKS(2));
  }
}

void send_force() {
  int32_t raw;
  uint32_t sequence;
  int64_t acquired;
  portENTER_CRITICAL(&hx_mux);
  raw = hx_raw;
  sequence = hx_sequence;
  acquired = hx_time_us;
  portEXIT_CRITICAL(&hx_mux);
  const int64_t now = esp_timer_get_time();
  const bool ready = sequence > 0 && now - acquired < 500000;
  const bool saturated = raw <= -8388608 || raw >= 8388607;
  char body[420];
  snprintf(body, sizeof(body),
      "{\"schema\":1,\"sensor\":\"hx711-single\",\"boot_id\":\"%s\",\"sequence\":%lu,"
      "\"raw_counts\":%ld,\"device_time_us\":%lld,\"server_time_us\":%lld,"
      "\"ready\":%s,\"saturated\":%s}",
      hx_boot_id, static_cast<unsigned long>(sequence), static_cast<long>(raw),
      static_cast<long long>(acquired), static_cast<long long>(now),
      ready ? "true" : "false", saturated ? "true" : "false");
  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", body);
}

// Seeed XIAO ESP32S3 Sense camera (OV2640) pinout.
#define PWDN_GPIO_NUM -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 10
#define SIOD_GPIO_NUM 40
#define SIOC_GPIO_NUM 39
#define Y9_GPIO_NUM 48
#define Y8_GPIO_NUM 11
#define Y7_GPIO_NUM 12
#define Y6_GPIO_NUM 14
#define Y5_GPIO_NUM 16
#define Y4_GPIO_NUM 18
#define Y3_GPIO_NUM 17
#define Y2_GPIO_NUM 15
#define VSYNC_GPIO_NUM 38
#define HREF_GPIO_NUM 47
#define PCLK_GPIO_NUM 13

// The requested iPhone hotspot is the default SSID.  Override both values at
// compile time with -DSYODO_WIFI_SSID=... and -DSYODO_WIFI_PASSWORD=...;
// leaving the password empty falls back to the local AP after the timeout.
#ifndef SYODO_WIFI_SSID
#define SYODO_WIFI_SSID "iPhoneA13"
#endif
#ifndef SYODO_WIFI_PASSWORD
#define SYODO_WIFI_PASSWORD ""
#endif

static constexpr char AP_PASSWORD[] = "syodo-cam";
static constexpr char STREAM_CONTENT_TYPE[] = "multipart/x-mixed-replace;boundary=frame";
WebServer server(80);
bool camera_ready = false;
unsigned long last_frame_error_ms = 0;

void send_index() {
  server.send(
      200, "text/html; charset=utf-8",
      "<!doctype html><meta name='viewport' content='width=device-width'>"
      "<title>syodo ESP32 camera</title><h1>syodo ESP32 camera</h1>"
      "<p><a href='/capture'>capture</a></p>"
      "<img src='/stream' style='max-width:100%;height:auto'>");
}

void send_health() {
  const String ip = WiFi.getMode() == WIFI_AP ? WiFi.softAPIP().toString() : WiFi.localIP().toString();
  String body = "{\"camera\":" + String(camera_ready ? "true" : "false") +
                ",\"ip\":\"" + ip + "\"}";
  server.send(200, "application/json", body);
}

bool write_frame(WiFiClient &client) {
  camera_fb_t *frame = esp_camera_fb_get();
  if (frame == nullptr) {
    if (millis() - last_frame_error_ms > 1000) {
      Serial.println("camera frame unavailable; lower frame size or check PSRAM");
      last_frame_error_ms = millis();
    }
    return false;
  }
  client.printf("--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", frame->len);
  client.write(frame->buf, frame->len);
  client.print("\r\n");
  esp_camera_fb_return(frame);
  return true;
}

void send_capture() {
  if (!camera_ready) {
    server.send(503, "text/plain; charset=utf-8", "camera is not ready\n");
    return;
  }
  WiFiClient client = server.client();
  camera_fb_t *frame = esp_camera_fb_get();
  if (frame == nullptr) {
    server.send(503, "text/plain; charset=utf-8", "camera frame unavailable\n");
    return;
  }
  server.sendHeader("Content-Disposition", "inline; filename=syodo.jpg");
  server.setContentLength(frame->len);
  server.send(200, "image/jpeg", "");
  client.write(frame->buf, frame->len);
  esp_camera_fb_return(frame);
}

void send_stream() {
  if (!camera_ready) {
    server.send(503, "text/plain; charset=utf-8", "camera is not ready\n");
    return;
  }
  WiFiClient client = server.client();
  client.print("HTTP/1.1 200 OK\r\nContent-Type: ");
  client.print(STREAM_CONTENT_TYPE);
  client.print("\r\nCache-Control: no-cache\r\nPragma: no-cache\r\n\r\n");
  while (client.connected()) {
    if (!write_frame(client)) {
      delay(100);
      continue;
    }
    delay(120);  // about 8 fps; stable for a top-down inspection stream
    server.handleClient();
  }
}

void connect_wifi() {
  const char *ssid = SYODO_WIFI_SSID;
  const char *password = SYODO_WIFI_PASSWORD;
  if (ssid[0] != '\0') {
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    Serial.printf("Wi-Fi connecting to %s", ssid);
    const unsigned long deadline = millis() + 15000;
    while (WiFi.status() != WL_CONNECTED && millis() < deadline) {
      delay(250);
      Serial.print('.');
    }
    Serial.println();
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("HTTP camera: http://%s/\n", WiFi.localIP().toString().c_str());
      return;
    }
    Serial.println("Wi-Fi failed; starting local AP");
  }
  uint64_t mac = ESP.getEfuseMac();
  char ap_name[32];
  snprintf(ap_name, sizeof(ap_name), "syodo-cam-%04X", (unsigned)(mac & 0xFFFF));
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ap_name, AP_PASSWORD);
  Serial.printf("Camera AP: %s / %s\n", ap_name, AP_PASSWORD);
  Serial.printf("HTTP camera: http://%s/\n", WiFi.softAPIP().toString().c_str());
}

bool begin_camera() {
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
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = psramFound() ? 2 : 1;
  config.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  // Do not let the camera producer outrun a slow HTTP client.  This avoids
  // the FB-OVF condition seen in the previous firmware while preserving the
  // newest available frame for each request.
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("camera init failed");
    return false;
  }
  sensor_t *sensor = esp_camera_sensor_get();
  if (sensor != nullptr) {
    sensor->set_vflip(sensor, 1);
    sensor->set_hmirror(sensor, 0);
  }
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("syodo ESP32-S3 Sense MJPEG camera");
  pinMode(HX_DAT, INPUT);
  pinMode(HX_CLK, OUTPUT);
  digitalWrite(HX_CLK, LOW);
  snprintf(hx_boot_id, sizeof(hx_boot_id), "%08lx%08lx", static_cast<unsigned long>(esp_random()), static_cast<unsigned long>(esp_random()));
  xTaskCreate(hx_task, "hx711", 3072, nullptr, 2, nullptr);
  camera_ready = begin_camera();
  connect_wifi();
  server.on("/", HTTP_GET, send_index);
  server.on("/health", HTTP_GET, send_health);
  server.on("/force", HTTP_GET, send_force);
  server.on("/capture", HTTP_GET, send_capture);
  server.on("/stream", HTTP_GET, send_stream);
  server.begin();
  Serial.printf("camera=%s\n", camera_ready ? "ready" : "failed");
}

void loop() {
  server.handleClient();
  delay(2);
}
