# ESP32-CAM Wi-Fi Robot Controller & Live Stream

A concise and lightweight IoT robot controller with real-time video streaming built for the **AI-Thinker ESP32-CAM** module and an **L298N / TB6612FNG** motor driver.

---

## 📋 Features

- **Real-Time Video Stream**: MJPEG stream running on dedicated port `81`.
- **Integrated Web Interface**: Responsive touch/mouse controller hosted on port `80`.
- **Motor Control**: Forward, Backward, Left, Right, and Instant Stop actions via HTTP GET requests.
- **Optimized Footprint**: Code reduced from ~440 lines down to ~135 lines by eliminating dead board definitions, streamlining motor logic, and using modern JavaScript `fetch()` calls.

---

## 🔌 Hardware Pin Configuration (AI-Thinker ESP32-CAM)

### Motor Driver Connections
| ESP32-CAM GPIO | Motor Driver Pin | Function |
| :--- | :--- | :--- |
| **GPIO 14** | IN1 (Motor 1) | Motor 1 Terminal A |
| **GPIO 15** | IN2 (Motor 1) | Motor 1 Terminal B |
| **GPIO 13** | IN3 (Motor 2) | Motor 2 Terminal A |
| **GPIO 12** | IN4 (Motor 2) | Motor 2 Terminal B |

> **Note**: Power the motors and ESP32-CAM using a stable 5V power source (at least 2A) to prevent camera reset or Wi-Fi disconnection caused by voltage brownouts.

---

## 🧠 Code Architecture & Explanation

The application consists of 5 modular components:

1. **Brownout & Motor Initialization (`setup`)**:
   - `WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0)` prevents spontaneous reboots caused by current spikes during Wi-Fi and camera boot.
   - Configures motor GPIOs as outputs and defaults all pins to LOW (stopped).

2. **Camera Configuration (`camera_config_t`)**:
   - Sets up AI-Thinker OV2640 pin maps, clock speed (20MHz), and frame format (`PIXFORMAT_JPEG`).
   - Dynamically selects VGA resolution if PSRAM is detected, or QVGA for standard boards to ensure smooth frame rates.

3. **Compact Motor Helper (`moveMotors`)**:
   - Condenses motor direction switching into a single function call:
     ```cpp
     moveMotors(m1a, m1b, m2a, m2b);
     ```
   - Replaces 30+ redundant `digitalWrite` calls.

4. **Dual HTTP Server (`startCameraServer`)**:
   - **Port 80 (`camera_httpd`)**:
     - `/` (`index_handler`): Serves the embedded HTML/CSS/JS control dashboard.
     - `/action?go=<direction>` (`cmd_handler`): Receives robot motion commands and drives the motors.
   - **Port 81 (`stream_httpd`)**:
     - `/stream` (`stream_handler`): Continuously captures frames with `esp_camera_fb_get()` and streams multipart JPEG chunks.

5. **Modernized Web Dashboard (`INDEX_HTML`)**:
   - Touch and mouse enabled (`onmousedown`, `onmouseup`, `ontouchstart`, `ontouchend`).
   - Uses asynchronous `fetch('/action?go=' + cmd)` without reloading the page.

---

## 🚀 How to Flash & Run

1. Open `esp32_cam_robot.ino` in the **Arduino IDE**.
2. Install the **ESP32** board package (`Tools` > `Board` > `Boards Manager` > Search `esp32` by Espressif).
3. Select **AI Thinker ESP32-CAM** under `Tools` > `Board`.
4. Update your Wi-Fi credentials in the code:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
5. Connect **GPIO 0 to GND** on the ESP32-CAM to enter flashing mode, press the reset button, and click **Upload**.
6. Once uploaded, disconnect GPIO 0 from GND, press reset, and open the Serial Monitor (115200 baud) to view the assigned IP address.
7. Open `http://<ESP32_IP>` in any web browser to control the robot.

---

## 📤 Step-by-Step Guide: Push This Project to GitHub Manually

Follow these exact steps in your terminal (Command Prompt, PowerShell, or Git Bash) to push this repository to GitHub:

### Step 1: Create a New Repository on GitHub
1. Go to [github.com/new](https://github.com/new).
2. Enter a **Repository name** (e.g., `esp32-cam-robot`).
3. Set visibility to **Public** or **Private**.
4. **Important**: Leave `Add a README file`, `.gitignore`, and `License` **unchecked** (an empty repository).
5. Click **Create repository**.
6. Copy the repository URL (e.g., `https://github.com/<YOUR_USERNAME>/esp32-cam-robot.git`).

---

### Step 2: Configure Git User Info (if first time on your PC)
Open your terminal in this project folder and run:
```bash
git config --global user.name "Your GitHub Username"
git config --global user.email "your-email@example.com"
```

---

### Step 3: Initialize Git & Add Files
Run the following commands in order inside the project directory:

```bash
# 1. Initialize local git repository
git init

# 2. Set the default branch to main
git branch -M main

# 3. Add all project files to staging
git add .

# 4. Create your initial commit
git commit -m "Initial commit: ESP32-CAM robot concise code and documentation"
```

---

### Step 4: Link Local Repository to GitHub
Replace `<REPO_URL>` with your copied GitHub repository URL:

```bash
git remote add origin https://github.com/karuraghavendra08-crypto/smart-surveillance-robot.git
```

---

### Step 5: Push the Code to GitHub
```bash
git push -u origin main
```
> If prompted for authentication:
> - Sign in with your browser or enter your GitHub Personal Access Token (PAT).

---

### Step 6: Verify
Refresh your GitHub repository page in your browser. All your files (`.py`, `esp32_cam_robot.ino`, and `README.md`) and documentation will now be live on GitHub!
