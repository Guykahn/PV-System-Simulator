# PV-System-Simulator

This project simulates the performance of a photovoltaic (PV) solar panel system over time based on user-defined parameters. It allows comparison with real-world irradiance or power data from an Excel file.

## Features

- Interactive GUI with Tkinter
- Simulates solar irradiance and power for a given date/location
- Supports both single values and ranges for tilt (β) and azimuth (γ) angles
- Compares simulated data with measured Excel data
- Computes total energy over a date range
- Visualizes irradiance and power curves
- Includes clipping thresholds, loss factors, and energy integration

## How to Use

1. Insert in the GUI the parameters of your PV system (latitude, longitude, tilt, azimuth, date, etc.)
2. Choose the relevant comparison or simulation type you want output graphs for (e.g., simulate power, compare with Excel data, or calculate total energy)
3. Click the appropriate button in the GUI and the results will be shown as graphs or message popups

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/pv-system-simulator.git
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
- `irradiance_data.xlsx` — Your Excel file with date/irradiance/power values

## Excel File Format

If using Excel comparison, your `.xlsx` file should contain:

| date (datetime) | irradiance (W/m²) | power (kW) |
|-----------------|-------------------|------------|
| 2024-06-21 07:00 | 480               | 1.2        |
| 2024-06-21 07:15 | 610               | 1.8        |

- `date`: datetime format
- `irradiance`: in **W/m²**
- `power`: in **kW**

The simulator automatically aligns the chosen date and generates graphs for comparison.


## Author

- **Guy Kahn** — [yourname](https://github.com/yourusername)

## License

This project is open-source and available under the [MIT License](LICENSE).
