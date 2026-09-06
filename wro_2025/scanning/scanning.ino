#include <MatrixMiniR4.h>
#include <WiFiS3.h>
#include <ArduinoMqttClient.h>

// ---------- Network / MQTT (optional) ----------
// Fill these values locally before flashing. Never commit real credentials.
char ssid[] = "YOUR_WIFI_SSID";
char pass[] = "YOUR_WIFI_PASSWORD";
const char* BROKER = "YOUR_MQTT_BROKER_HOST";
const int   PORT   = 1883;
const char* TOPIC  = "dino/command";

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

// ---------- Map grid config ----------
static const int ROWS = 8;    // matches NUM_ROWS in camera script
static const int COLS = 10;   // tune to your layout
static const int CAM_W = 320;
static const int CAM_H = 240;

const float CELL_W = float(CAM_W) / COLS;
const float CELL_H = float(CAM_H) / ROWS;

int8_t   grid[ROWS][COLS];     // -1 = empty, else class_id
uint16_t strength[ROWS][COLS]; // largest area kept per cell

// ---------- Vision buffer ----------
unsigned int vbuf[128]; // generous headroom (count + 24 blobs * 4 = 97)

// ---------- Utils ----------
void resetMap() {
  for (int r = 0; r < ROWS; ++r) {
    for (int c = 0; c < COLS; ++c) {
      grid[r][c] = -1;
      strength[r][c] = 0;
    }
  }
}

void printMapToSerial() {
  Serial.println(F("[MAP]"));
  for (int r = 0; r < ROWS; ++r) {
    for (int c = 0; c < COLS; ++c) {
      Serial.print(grid[r][c]);
      if (c + 1 < COLS) Serial.print(' ');
    }
    Serial.println();
  }
}

void publishMapMQTT() {
  mqttClient.beginMessage(TOPIC);
  mqttClient.print("MAP ");
  mqttClient.print(ROWS); mqttClient.print(","); mqttClient.print(COLS); mqttClient.print(";");
  for (int r = 0; r < ROWS; ++r) {
    for (int c = 0; c < COLS; ++c) {
      mqttClient.print(grid[r][c]);
      if (!(r == ROWS - 1 && c == COLS - 1)) mqttClient.print(",");
    }
  }
  mqttClient.endMessage();
  Serial.println(F("[MQTT] MAP published."));
}

void connectWiFi() {
  Serial.print(F("WiFi"));
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) { Serial.print('.'); delay(600); }
  Serial.print(F(" OK. IP=")); Serial.println(WiFi.localIP());
}

void connectMQTT() {
  Serial.print(F("MQTT"));
  int tries = 0;
  while (!mqttClient.connect(BROKER, PORT)) {
    Serial.print(F(" .rc=")); Serial.print(mqttClient.connectError());
    if (++tries > 10) { Serial.println(F(" (fail)")); return; }
    delay(800);
  }
  mqttClient.setKeepAliveInterval(30);
  mqttClient.subscribe(TOPIC, 1);
  Serial.println(F(" OK."));
}

void handleInbound() {
  if (!mqttClient.parseMessage()) return;
  String s = mqttClient.readString(); s.trim();
  Serial.print(F("[IN ] ")); Serial.println(s);
  if (s == "start") {
    // hook if you want to gate mapping
  } else if (s == "stop") {
    // hook
  } else if (s.startsWith("INSTRUCTION ")) {
    // parse instructions here
  } else if (s == "hello") {
    mqttClient.beginMessage(TOPIC); mqttClient.print("hello from R4"); mqttClient.endMessage();
  }
}

void integrateDetectionsToMap() {
  if (vbuf[0] == 0) return; // no detections

  for (unsigned int i = 0; i < vbuf[0]; ++i) {
    unsigned int base = 1 + i * 4;
    int class_id = (int)vbuf[base + 0];
    int x        = (int)vbuf[base + 1];
    int y        = (int)vbuf[base + 2];
    unsigned int area = vbuf[base + 3];

    int col = int(x / CELL_W);
    int row = int(y / CELL_H);
    if (col < 0) col = 0; if (col >= COLS) col = COLS - 1;
    if (row < 0) row = 0; if (row >= ROWS) row = ROWS - 1;

    if (area >= strength[row][col]) {
      strength[row][col] = area;
      grid[row][col]     = (int8_t)class_id;
    }
  }
}

void setup() {
  Serial.begin(9600);        // <<< set to 9600 as requested
  while (!Serial) {}

  MiniR4.begin();
  MiniR4.Vision.Begin();
  delay(300);

  resetMap();
  connectWiFi();
  connectMQTT();

  Serial.println(F("Ready @9600: mapping SmartCam → grid."));
}

unsigned long lastPrint = 0;
unsigned long lastPublish = 0;

void loop() {
  mqttClient.poll();
  handleInbound();

  int rc = MiniR4.Vision.SmartCamReader(vbuf);
  if (rc > 0) {
    resetMap();
    integrateDetectionsToMap();
  }

  unsigned long now = millis();
  if (now - lastPrint > 1000) { printMapToSerial(); lastPrint = now; }
  if (mqttClient.connected() && (now - lastPublish > 2000)) {
    publishMapMQTT();
    lastPublish = now;
  }

  delay(1000);
  MiniR4.M4.setPower(40);
  MiniR4.M2.setPower(40);
  delay(100);
}
