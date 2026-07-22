// Hardware Pin Definitions
#define ZC_PIN 2    // Zero-Cross Input (Must be D2 on Nano)
#define GATE_PIN 3  // Dimmer Firing Output
#define KNOB_PIN A0 // Potentiometer Wiper

// Global Timing & Hardware Variables
volatile bool zeroCrossed = false;
int dimmingDelay = 7000;
unsigned long lastPrintTime = 0; // Tracks time for our offline Serial timer

// EMA Filter Variables
float smoothedKnob = 0.0;
float alpha = 0.2; // Smoothing factor (0.0 to 1.0 scale. Lower is smoother)

void setup() {
  Serial.begin(9600);

  pinMode(ZC_PIN, INPUT_PULLUP);
  pinMode(GATE_PIN, OUTPUT);
  digitalWrite(GATE_PIN, LOW);

  attachInterrupt(digitalPinToInterrupt(ZC_PIN), onZeroCross, RISING);

  // Prime the filter with the actual starting position of the knob
  smoothedKnob = analogRead(KNOB_PIN);

  Serial.println("System Booted. Offline Knob Testing Active.");
}

// Interrupt Service Routine (Only triggers when AC is connected)
void onZeroCross() { zeroCrossed = true; }

void loop() {
  // ==========================================
  // 1. LOW-VOLTAGE LOGIC (Runs continuously)
  // ==========================================

  // Read the raw physical knob
  int rawKnob = analogRead(KNOB_PIN);

  // Apply Exponential Moving Average (EMA) Filter
  smoothedKnob = (alpha * rawKnob) + ((1.0 - alpha) * smoothedKnob);

  // Map the smoothed value to a 0 to 100 percent power scale
  int powerPercent = map((int)smoothedKnob, 0, 1023, 0, 100);
  powerPercent = constrain(powerPercent, 0, 100);

  // 100% Power = 0us delay, 0% Power = 7500us delay
  dimmingDelay = map(powerPercent, 0, 100, 7500, 0);

  // ==========================================
  // 2. OFFLINE TESTING OUTPUT (Runs every 50ms)
  // ==========================================

  // Check if 50 milliseconds have passed since the last print
  if (millis() - lastPrintTime >= 50) {
    // Formatted specifically for the Arduino IDE Serial Plotter
    Serial.print("Raw_Knob:");
    Serial.print(rawKnob);
    Serial.print(",");
    Serial.print("Smoothed_Knob:");
    Serial.print((int)smoothedKnob);
    Serial.print(",");
    Serial.print("Target_Power_%:");
    Serial.println(powerPercent);

    lastPrintTime = millis(); // Reset the timer
  }

  // ==========================================
  // 3. HIGH-VOLTAGE LOGIC (Runs only on AC sync)
  // ==========================================

  if (zeroCrossed) {
    // Fire the TRIAC if power target is >= 1
    if (powerPercent >= 1) {
      delayMicroseconds(dimmingDelay);
      digitalWrite(GATE_PIN, HIGH);
      delayMicroseconds(10);
      digitalWrite(GATE_PIN, LOW);
    }

    zeroCrossed = false; // Reset the flag for the next AC cycle
  }
}
