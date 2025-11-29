# Professional IoT Digital Twin Dashboard for Predictive Maintenance

## Project Overview
Create a modern, real-time industrial dashboard for a **Grundfos CR Pump Digital Twin** system that combines IoT sensor monitoring with AI-powered diagnostics. This is a predictive maintenance platform that helps maintenance engineers diagnose pump failures before catastrophic breakdown occurs.

---

## Core Concept
The system simulates a physical industrial pump in real-time, monitors 5 key sensors (amperage, voltage, vibration, pressure, temperature), detects anomalies automatically, and uses Google Gemini AI with RAG (Retrieval-Augmented Generation) to provide expert diagnostic recommendations based on the manufacturer's troubleshooting manual.

**Think of it as:** A digital twin of a real pump + An AI maintenance engineer working 24/7

---

## Dashboard Layout Structure

### Main Layout (Single Page Application)
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "🏭 Digital Twin - Grundfos CR Pump Monitor"                       │
│  [Status Badge: NORMAL/FAULT] | [Last Update: 14:32:18] | [Uptime: 2h 15m] │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┬────────────────────────────────────────┐
│  LEFT PANEL (65% width)             │  RIGHT PANEL (35% width)               │
│  ════════════════════════            │  ════════════════════════              │
│                                      │                                        │
│  🎛️ REAL-TIME SENSOR DASHBOARD      │  🤖 AI DIAGNOSTIC ASSISTANT            │
│                                      │                                        │
│  [Section 1: Metrics Grid]          │  [Auto-Diagnosis Panel]                │
│  [Section 2: Live Chart]            │  Shows when fault detected             │
│  [Section 3: Fault Controls]        │                                        │
│                                      │  [Chat Interface]                      │
│                                      │  Manual questions                      │
│                                      │                                        │
└─────────────────────────────────────┴────────────────────────────────────────┘
```

---

## LEFT PANEL: IoT Dashboard Components

### Section 1: Real-Time Metrics Grid (Top Third)
Display 5 sensor cards in a responsive grid layout:

#### Card Design Template:
- **Card Style:** Glass morphism effect with subtle gradient background
- **Status Indicator:** Color-coded left border (Green=Normal, Yellow=Warning, Red=Critical)
- **Layout per card:**
  ```
  ┌────────────────────────────┐
  │ [Icon] SENSOR NAME         │ ← Header with icon (⚡ 🔌 📊 🌡️ 💨)
  │                            │
  │    [LARGE VALUE]           │ ← Primary reading (48px bold)
  │    [Unit Label]            │ ← Small gray text (A, V, mm/s, bar, °C)
  │                            │
  │ [Mini Sparkline Chart]     │ ← Last 30 seconds trend
  │ ▂▃▅▇▆▄▃▂ (last 30s)       │
  │                            │
  │ Threshold: < 11.5 A ✓      │ ← Status text with checkmark/alert
  └────────────────────────────┘
  ```

**5 Sensor Cards:**

1. **Three-Phase Amperage (Composite Card)**
   - Icon: ⚡
   - Display: 
     - Phase A: 10.2 A (small pill badge, green)
     - Phase B: 10.1 A (small pill badge, green)
     - Phase C: 13.5 A (small pill badge, RED - imbalanced)
   - Below values: "Imbalance: 19.5%" (large warning text if >5%)
   - Threshold: Normal <5% imbalance

2. **Supply Voltage**
   - Icon: 🔌
   - Large Value: "228.5 V"
   - Status: "Normal Range (207-253V)" (green) or "⚠️ LOW VOLTAGE" (red if <207V)
   - Sparkline: Voltage trend

3. **Vibration**
   - Icon: 📊
   - Large Value: "8.24 mm/s"
   - Status: "⚠️ CRITICAL" (red background pulsing animation if >5)
   - Visual: Add a subtle shake animation to the card if vibration >5
   - Sparkline: Vibration spikes

4. **Discharge Pressure**
   - Icon: 💨
   - Large Value: "4.95 bar"
   - Status: "Normal" or "⚠️ Fluctuating" (if varying >10%)
   - Sparkline: Pressure trend

5. **Motor Temperature**
   - Icon: 🌡️
   - Large Value: "67.2 °C"
   - Status: "Normal (<80°C)" or "🔥 OVERHEATING" (if >80°C)
   - Visual: Color gradient from blue (cool) to red (hot) background

**Design Requirements:**
- Cards should have smooth hover effects (slight elevation)
- Use CSS animations for warning states (subtle pulse on critical values)
- Responsive grid: 3 cards on large screens, 2 on tablets, 1 on mobile

---

### Section 2: Live Time-Series Chart (Middle Third)

**Chart Title:** "⚡ Three-Phase Current Monitoring (Last 60 Seconds)"

**Chart Type:** Multi-line time-series chart (use Recharts or similar library)

**Specifications:**
- X-axis: Time (last 60 seconds, auto-scrolling)
- Y-axis: Current (Amperes)
- 3 Lines:
  - Phase A: Blue solid line
  - Phase B: Green solid line  
  - Phase C: Red solid line
- Features:
  - Animated smooth transitions as new data points arrive
  - Horizontal reference line at 10A (rated current) - dashed gray
  - Shaded region above 11.5A labeled "Overload Zone" (light red fill)
  - Legend with color-coded labels (top right)
  - Tooltip on hover showing exact value + timestamp
  - Auto-scrolling (new data pushes old data left)

**Visual State Changes:**
- When imbalance detected (>5%), the chart container gets a yellow warning border
- When overload detected, add a red pulsing border

**Additional Info Below Chart:**
```
📈 Current Status:  Average: 10.3A  |  Peak: 13.5A  |  Imbalance: 19.5% ⚠️
```

---

### Section 3: Fault Simulation Controls (Bottom Third)

**Section Title:** "🧪 Fault Injection Controls (Development Mode)"

**Layout:** Button grid with 2 rows

**Row 1: Fault Triggers (6 buttons in a grid)**
```
┌──────────────┬──────────────┬──────────────┐
│ ⚡ WINDING   │ 🔌 SUPPLY    │ 💧 CAVITATION│
│   DEFECT     │   FAULT      │              │
│              │              │              │
│ Click to     │ Click to     │ Click to     │
│ simulate     │ simulate     │ simulate     │
└──────────────┴──────────────┴──────────────┘

┌──────────────┬──────────────┬──────────────┐
│ ⚙️ BEARING   │ 🔥 OVERLOAD  │ ✅ RESET     │
│   WEAR       │              │   TO NORMAL  │
│              │              │              │
│ Click to     │ Click to     │ Clear all    │
│ simulate     │ simulate     │ faults       │
└──────────────┴──────────────┴──────────────┘
```

**Button Design:**
- Each button: Large, rounded corners, icon + text
- Default state: Light gray with hover effect
- Active state (fault injected): Corresponding button has red background with white text
- Reset button: Green background
- Add ripple effect on click

**Active Fault Indicator:**
Below buttons, display a banner if a fault is active:
```
┌─────────────────────────────────────────────────────────┐
│ 🚨 ACTIVE FAULT: Winding Defect                         │
│ Duration: 00:02:15  |  [Stop Simulation] button         │
└─────────────────────────────────────────────────────────┘
```

---

## RIGHT PANEL: AI Assistant

### Panel Design
- Sticky position (stays visible when scrolling)
- Two tabs at top: "🤖 Auto-Diagnosis" | "💬 Chat"

---

### Tab 1: Auto-Diagnosis Panel

**Purpose:** Automatically displays AI analysis when a fault is detected

**Initial State (No Fault):**
```
┌────────────────────────────────────────┐
│                                        │
│     ✅ SYSTEM OPERATING NORMALLY      │
│                                        │
│     All sensors within parameters     │
│                                        │
│  [Graphic: Green checkmark animation] │
│                                        │
└────────────────────────────────────────┘
```

**Active Fault State:**
```
┌────────────────────────────────────────┐
│ 🚨 FAULT DETECTED: Cavitation          │
│ ⏱️ Detected at: 14:32:18               │
├────────────────────────────────────────┤
│                                        │
│ [Loading spinner] Analyzing...         │
│ Querying AI diagnostic system...       │
│                                        │
├────────────────────────────────────────┤
│ 🤖 AI DIAGNOSIS                        │
│ ────────────────────────────────────   │
│                                        │
│ PRIMARY DIAGNOSIS:                     │
│ Cavitation confirmed by high           │
│ vibration (8.24 mm/s)                 │
│                                        │
│ ROOT CAUSE:                            │
│ Insufficient Net Positive Suction      │
│ Head (NPSHA). Low liquid level or      │
│ air ingress on suction side.          │
│                                        │
│ IMMEDIATE ACTIONS:                     │
│ 1. ⚠️ SHUTDOWN PUMP IMMEDIATELY       │
│ 2. 🔍 Inspect suction line             │
│ 3. 📏 Measure NPSHA with gauge         │
│                                        │
│ VERIFICATION STEPS:                    │
│ • Check supply tank level              │
│ • Look for air bubbles in line         │
│ • Verify suction pressure              │
│                                        │
├────────────────────────────────────────┤
│ 📚 Manual References:                  │
│ • Page 5 (Cavitation diagnosis)        │
│ • Page 10 (NPSH calculations)          │
│                                        │
│ [View Full Report] button              │
└────────────────────────────────────────┘
```

**Design Notes:**
- Use card-style containers with clear section dividers
- Color-code action items: Red for urgent, Yellow for important, Green for verification
- Add copy-to-clipboard button for the full diagnosis
- Smooth fade-in animation when diagnosis appears

---

### Tab 2: Chat Interface

**Purpose:** Allow users to ask maintenance questions manually

**Layout:**
```
┌────────────────────────────────────────┐
│ 💬 Ask the AI Maintenance Expert      │
├────────────────────────────────────────┤
│                                        │
│ [Chat Message History]                 │
│                                        │
│ User: What tools do I need?            │
│ ├─ AI: To inspect the impeller...     │
│                                        │
│ User: How to measure voltage?          │
│ ├─ AI: Use a multimeter...            │
│                                        │
│                                        │
│ [Scroll to bottom]                     │
│                                        │
├────────────────────────────────────────┤
│ [Text Input Box]                       │
│ Type your question...                  │
│                [Send] button           │
└────────────────────────────────────────┘
```

**Chat Bubble Design:**
- User messages: Right-aligned, blue background
- AI messages: Left-aligned, gray background with robot avatar
- Timestamp below each message
- Loading indicator (three dots animation) while AI responds
- Show "✓ Read" indicator on AI responses

**Quick Action Buttons (Above Input):**
Suggested questions as clickable chips:
```
[What causes cavitation?] [Impeller inspection steps]
[Bearing replacement tools] [Voltage testing procedure]
```

---

## Design System Specifications

### Color Palette
```
Primary Colors:
- Background: #0F172A (dark slate)
- Card Background: #1E293B with rgba(255,255,255,0.05) overlay (glass effect)
- Text Primary: #F1F5F9 (light slate)
- Text Secondary: #94A3B8 (slate gray)

Status Colors:
- Normal: #10B981 (emerald green)
- Warning: #F59E0B (amber)
- Critical: #EF4444 (red)
- Info: #3B82F6 (blue)

Accent Colors:
- Primary Action: #6366F1 (indigo)
- Hover: #818CF8 (lighter indigo)
```

### Typography
```
Font Family: 'Inter' or 'SF Pro Display'

Headings:
- Dashboard Title: 32px, Bold
- Section Titles: 24px, Semibold
- Card Titles: 18px, Medium

Body Text:
- Sensor Values: 48px, Bold (large display)
- Labels: 14px, Regular
- Status Text: 12px, Medium
```

### Animations & Transitions
```
- Card hover: transform: translateY(-4px) + shadow increase (200ms ease)
- Alert pulse: scale(1.02) + opacity 0.8 → 1.0 (1s infinite)
- Chart updates: smooth transitions (300ms)
- Panel collapse/expand: height transition (400ms ease-in-out)
- Loading spinners: smooth rotation
```

---

## Technical Requirements for V0

### Component Architecture
```
App
├── Header (Status bar + Title)
├── MainLayout
│   ├── LeftPanel (Dashboard)
│   │   ├── MetricsGrid
│   │   │   ├── AmperageCard
│   │   │   ├── VoltageCard
│   │   │   ├── VibrationCard
│   │   │   ├── PressureCard
│   │   │   └── TemperatureCard
│   │   ├── LiveChart (Recharts Line Chart)
│   │   └── FaultControls
│   └── RightPanel (AI Assistant)
│       ├── AutoDiagnosisTab
│       └── ChatTab
```

### State Management Needs
```
Global State:
- sensorData (object with all current readings)
- faultState (enum: NORMAL, WINDING_DEFECT, etc.)
- faultDuration (seconds)
- chartHistory (array of last 60 data points)
- aiDiagnosis (string, AI response)
- chatMessages (array of message objects)
- isLoading (boolean for AI requests)
```

### Responsive Breakpoints
```
Desktop (>1280px): Full side-by-side layout
Tablet (768px - 1280px): Stacked panels, collapsible right panel
Mobile (<768px): Single column, tabs for dashboard/AI switch
```

---

## Data Flow Explanation

### Real-Time Updates (Simulated Backend)
The dashboard should simulate receiving data every 1 second:

1. **Normal Operation Loop:**
   - Every 1 second, update sensor values with small random variations
   - Update chart with new data point
   - Check thresholds (if vibration >5mm/s, trigger alert)

2. **Fault Detection Trigger:**
   - When user clicks "Winding Defect" button:
     - Update faultState to "WINDING_DEFECT"
     - Start modifying sensor values to show symptoms:
       - Phase C current jumps to 13.5A
       - Temperature increases gradually
       - Phase imbalance > 5%
   - After 2 seconds, trigger auto-diagnosis panel
   - Show loading spinner for 1.5 seconds (simulating AI processing)
   - Display formatted diagnosis text

3. **Chat Interaction:**
   - User types question → Show in chat bubble
   - Display typing indicator (3 dots)
   - After 1.5s delay (simulate AI thinking), show response
   - Response should be relevant to the current fault state

---

## Key Interactive Features

### 1. Auto-Scrolling Chart
- Chart X-axis shows last 60 seconds
- New data points arrive from the right
- Old data scrolls off to the left
- Smooth animation (no jumpy updates)

### 2. Alert System
- When critical threshold crossed:
  - Play subtle notification sound (optional)
  - Card border turns red with pulse animation
  - Browser notification (if permission granted)
  - Show toast message at top: "⚠️ CAVITATION DETECTED - Review AI Diagnosis"

### 3. Collapsible Panels
- On smaller screens, AI panel can collapse to a floating button
- Click to expand as modal overlay
- Mobile: Swipe gesture to switch between dashboard/chat

### 4. Data Export
- Add button to download current sensor snapshot as JSON
- Export chart as PNG image
- Export AI diagnosis as PDF report (future enhancement)

---

## Accessibility Requirements

- **Keyboard Navigation:** All buttons and inputs accessible via Tab key
- **Screen Reader Support:** 
  - ARIA labels on all sensor cards
  - Status announcements for fault changes
  - Chat messages readable by screen readers
- **Color Contrast:** Ensure WCAG AA compliance (4.5:1 minimum)
- **Motion Preferences:** Respect prefers-reduced-motion for animations

---

## Example Use Case Scenario

**Scenario: Maintenance Engineer Monitoring Pump**

1. **Dashboard loads** → Shows all green (normal operation)
2. **Engineer suspects bearing issue** → Clicks "Bearing Wear" button
3. **System responds:**
   - Vibration card starts showing 4.2 mm/s (yellow warning)
   - Temperature slowly rises to 72°C
   - Chart shows gradual vibration increase
4. **After 3 seconds:**
   - Auto-diagnosis panel updates with red banner
   - AI displays: "Bearing Wear Detected - Progressive vibration increase indicates bearing degradation"
5. **Engineer asks follow-up:**
   - Types in chat: "What tools do I need to inspect the bearing?"
   - AI responds with detailed tool list and procedure steps
6. **Engineer takes action:**
   - Clicks "Reset to Normal" to clear simulation
   - Dashboard returns to green status

---

## Polish & Professional Touches

### Loading States
- Skeleton screens for initial load (pulsing gray placeholders)
- Smooth fade-in when data arrives
- "Connecting to pump..." message if simulating connection delay

### Empty States
- If chart has no data: Show "Waiting for sensor data..." with animation
- If no faults detected: Show encouraging message "System healthy ✓"

### Microinteractions
- Button click: Subtle ripple effect
- Card hover: Slight lift with shadow
- Success actions: Green checkmark animation
- Error states: Shake animation

### Performance
- Optimize chart re-renders (only update when new data arrives)
- Lazy load chat messages (if history grows large)
- Debounce sensor updates if needed (though 1Hz is manageable)

---

## Final Notes for V0

**This is an industrial IoT dashboard, not a consumer app** - prioritize:
- ✅ Data clarity over fancy graphics
- ✅ Fast response times (critical for maintenance)
- ✅ Clear visual hierarchy (engineers need to scan quickly)
- ✅ Professional, trustworthy design (lives depend on accurate diagnostics)

**Inspiration:**
- Tesla vehicle diagnostics dashboard
- AWS CloudWatch metrics
- Grafana dashboards
- Industrial SCADA systems

**Must avoid:**
- Overly playful animations
- Distracting gradients
- Too much empty space
- Cluttered layouts

The goal is a dashboard that a maintenance engineer would trust to make $100,000 decisions about shutting down production equipment.
