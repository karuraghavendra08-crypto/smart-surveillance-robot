/*********
  ESP32-CAM Robot Controller & Live Stream
*********/
#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// Wi-Fi Credentials
const char* ssid = "project07";
const char* password = "project07";

// AI-Thinker ESP32-CAM Pin Definitions
#define PWDN_GPIO_NUM  32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM   0
#define SIOD_GPIO_NUM  26
#define SIOC_GPIO_NUM  27
#define Y9_GPIO_NUM    35
#define Y8_GPIO_NUM    34
#define Y7_GPIO_NUM    39
#define Y6_GPIO_NUM    36
#define Y5_GPIO_NUM    21
#define Y4_GPIO_NUM    19
#define Y3_GPIO_NUM    18
#define Y2_GPIO_NUM     5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM  23
#define PCLK_GPIO_NUM  22

// Motor Driver Pins (L298N / TB6612FNG)
#define M1_A 14
#define M1_B 15
#define M2_A 13
#define M2_B 12

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t camera_httpd = NULL;
httpd_handle_t stream_httpd = NULL;

// Minimalist Web Controller UI
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ESP32-CAM Robot</title>
<style>
body{font-family:sans-serif;text-align:center;background:#18181b;color:#f4f4f5;margin:0;padding:15px}
img{max-width:95%;border-radius:10px;box-shadow:0 4px 12px rgba(0,0,0,0.5)}
.btn{background:#2563eb;color:#fff;border:none;padding:14px 24px;margin:6px;font-size:18px;border-radius:8px;cursor:pointer;user-select:none;-webkit-user-select:none}
.btn:active{background:#1d4ed8}
.stop{background:#dc2626}
</style></head>
<body>
<h2>ESP32-CAM Robot</h2>
<img id="stream" src=""><br><br>
<div><button class="btn" onmousedown="cmd('forward')" ontouchstart="cmd('forward')" onmouseup="cmd('stop')" ontouchend="cmd('stop')">▲ Forward</button></div>
<div>
  <button class="btn" onmousedown="cmd('left')" ontouchstart="cmd('left')" onmouseup="cmd('stop')" ontouchend="cmd('stop')">◄ Left</button>
  <button class="btn stop" onclick="cmd('stop')">■ Stop</button>
  <button class="btn" onmousedown="cmd('right')" ontouchstart="cmd('right')" onmouseup="cmd('stop')" ontouchend="cmd('stop')">► Right</button>
</div>
<div><button class="btn" onmousedown="cmd('backward')" ontouchstart="cmd('backward')" onmouseup="cmd('stop')" ontouchend="cmd('stop')">▼ Backward</button></div>
<script>
const cmd = a => fetch('/action?go=' + a);
window.onload = () => document.getElementById('stream').src = location.origin.replace(/:\d+$/, '') + ':81/stream';
</script></body></html>)rawliteral";

// Helper to control both motors in a single line
void moveMotors(int m1a, int m1b, int m2a, int m2b) {
  digitalWrite(M1_A, m1a); digitalWrite(M1_B, m1b);
  digitalWrite(M2_A, m2a); digitalWrite(M2_B, m2b);
}

static esp_err_t index_handler(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html");
  return httpd_resp_send(req, INDEX_HTML, strlen(INDEX_HTML));
}

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  char part_buf[64];
  if (httpd_resp_set_type(req, _STREAM_CONTENT_TYPE) != ESP_OK) return ESP_FAIL;

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) return ESP_FAIL;
    size_t hlen = snprintf(part_buf, 64, _STREAM_PART, fb->len);
    if (httpd_resp_send_chunk(req, part_buf, hlen) != ESP_OK ||
        httpd_resp_send_chunk(req, (const char*)fb->buf, fb->len) != ESP_OK ||
        httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY)) != ESP_OK) {
      esp_camera_fb_return(fb);
      break;
    }
    esp_camera_fb_return(fb);
  }
  return ESP_OK;
}

static esp_err_t cmd_handler(httpd_req_t *req) {
  char query[32], val[16] = {0};
  if (httpd_req_get_url_query_str(req, query, sizeof(query)) == ESP_OK &&
      httpd_query_key_value(query, "go", val, sizeof(val)) == ESP_OK) {
    if (!strcmp(val, "forward"))       moveMotors(1, 0, 1, 0);
    else if (!strcmp(val, "backward")) moveMotors(0, 1, 0, 1);
    else if (!strcmp(val, "left"))     moveMotors(0, 1, 1, 0);
    else if (!strcmp(val, "right"))    moveMotors(1, 0, 0, 1);
    else if (!strcmp(val, "stop"))     moveMotors(0, 0, 0, 0);
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, NULL, 0);
  }
  return httpd_resp_send_404(req);
}

void startCameraServer() {
  httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
  httpd_uri_t index_uri  = { "/", HTTP_GET, index_handler, NULL };
  httpd_uri_t cmd_uri    = { "/action", HTTP_GET, cmd_handler, NULL };
  httpd_uri_t stream_uri = { "/stream", HTTP_GET, stream_handler, NULL };

  cfg.server_port = 80;
  if (httpd_start(&camera_httpd, &cfg) == ESP_OK) {
    httpd_register_uri_handler(camera_httpd, &index_uri);
    httpd_register_uri_handler(camera_httpd, &cmd_uri);
  }
  cfg.server_port = 81;
  cfg.ctrl_port = 81;
  if (httpd_start(&stream_httpd, &cfg) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
  }
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Disable brownout detector
  pinMode(M1_A, OUTPUT); pinMode(M1_B, OUTPUT);
  pinMode(M2_A, OUTPUT); pinMode(M2_B, OUTPUT);
  moveMotors(0, 0, 0, 0);

  Serial.begin(115200);

  camera_config_t cfg;
  cfg.ledc_channel = LEDC_CHANNEL_0;
  cfg.ledc_timer   = LEDC_TIMER_0;
  cfg.pin_d0 = Y2_GPIO_NUM; cfg.pin_d1 = Y3_GPIO_NUM;
  cfg.pin_d2 = Y4_GPIO_NUM; cfg.pin_d3 = Y5_GPIO_NUM;
  cfg.pin_d4 = Y6_GPIO_NUM; cfg.pin_d5 = Y7_GPIO_NUM;
  cfg.pin_d6 = Y8_GPIO_NUM; cfg.pin_d7 = Y9_GPIO_NUM;
  cfg.pin_xclk = XCLK_GPIO_NUM; cfg.pin_pclk = PCLK_GPIO_NUM;
  cfg.pin_vsync = VSYNC_GPIO_NUM; cfg.pin_href = HREF_GPIO_NUM;
  cfg.pin_sccb_sda = SIOD_GPIO_NUM; cfg.pin_sccb_scl = SIOC_GPIO_NUM;
  cfg.pin_pwdn = PWDN_GPIO_NUM; cfg.pin_reset = RESET_GPIO_NUM;
  cfg.xclk_freq_hz = 20000000;
  cfg.pixel_format = PIXFORMAT_JPEG;
  cfg.frame_size   = psramFound() ? FRAMESIZE_VGA : FRAMESIZE_QVGA;
  cfg.jpeg_quality = psramFound() ? 10 : 14;
  cfg.fb_count     = psramFound() ? 2 : 1;

  if (esp_camera_init(&cfg) != ESP_OK) {
    Serial.println("Camera init failed");
    return;
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.printf("\nStream Ready: http://%s\n", WiFi.localIP().toString().c_str());

  startCameraServer();
}

void loop() {}
