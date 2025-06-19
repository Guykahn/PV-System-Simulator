# PV-System-Simulator

This project simulates the performance of a photovoltaic (PV) solar panel system over time based on user-defined parameters. It allows comparison with real-world irradiance or power data from an Excel file.

## Features

- Interactive GUI with Tkinter
- Simulates solar irradiance and power for a given date, location, tilt (β) and azimuth (γ) angles
- Compare simulated results with real-world PV system data imported from an Excel file.
- Computes total energy over a date range
- Generates visual output of power graphs based on the selected simulation or comparison.
- Allows customization of efficiency and system loss parameters based on user input.

## How to Use

1. Enter your PV system parameters in the GUI, including latitude, longitude, tilt angle (β), azimuth angle (γ), date, and other configuration settings.
2. Select the type of simulation or comparison you want to perform, such as power output simulation, Excel data comparison, or total energy calculation, to generate the corresponding output graphs.
3. Click the appropriate button in the GUI and the results will be shown as graphs or message popups

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Guykahn/pv-system-simulator.git
cd pv-system-simulator
```

### 2. Install dependencies
Make sure you have Python 3.x installed. Then run:

```bash
pip install -r requirements.txt
```

### 3. Run the simulator
```bash
python PV_System_Simulator.py
```

## Files Included

- `PV_System_Simulator.py` — Main Python GUI and simulation logic
- `requirements.txt` — Required Python packages
- `.gitignore` — Files and folders excluded from Git tracking
- `power_and_irradiance.xlsx` — Your Excel file with date/irradiance/power values

## Excel File Format

If using Excel comparison, your `.xlsx` file should contain:

|       date       |     irradiance    |    power   |
|------------------|-------------------|------------|
| 2024-06-21 07:00 | 480               | 1200       |
| 2024-06-21 07:15 | 610               | 1800       |

- `date`: datetime format
- `irradiance`: in **W/m²**
- `power`: in **kW**

The simulator automatically aligns the chosen date and generates graphs for comparison.


## Author

- **Guy Kahn** — [Guykahn](https://github.com/Guykahn)

