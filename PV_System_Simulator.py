import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
from datetime import date
from matplotlib.ticker import FuncFormatter, MultipleLocator
from tkinter import filedialog



def compute_surface_under_plot(time, power):
    # Function logic
    time = np.array(time)
    power = np.array(power)
    total_energy = np.trapz(power, time)  # Compute integral
    return total_energy 

class PVSystemSimulator:
    def __init__(self, latitude, longitude, beta, gamma):
        self.latitude = latitude  # Latitude (φ) in degrees
        self.longitude = longitude  # Longitude (λ) in degrees
        self.beta = beta  # Tilt angle (β) in degrees
        self.gamma = gamma  # Azimuth angle (γ) in degrees

    @staticmethod
    def day_of_year(year, month, day):
        """Calculate the day of the year using subtraction."""
        return (date(year, month, day) - date(year, 1, 1)).days + 1

    @staticmethod
    def declination_angle(day):
        """Calculate the declination angle (δ)."""
        return 23.45 * np.sin(np.radians(360 * (284 + day) / 365))

    @staticmethod
    def equation_of_time(day):
        """Calculate the equation of time (EoT)."""
        B = (360 / 365) * (day - 81)
        B_rad = np.radians(B)
        return 9.87 * np.sin(2 * B_rad) - 7.53 * np.cos(B_rad) - 1.5 * np.sin(B_rad)

    def time_correction(self, day):
        """Calculate the time correction (TC)."""
        LSTM = 15 * round(self.longitude / 15)  # Local Standard Time Meridian
        EoT = self.equation_of_time(day)
        return 4 * (self.longitude - LSTM) + EoT

    def solar_noon(self, day):
        """Calculate solar noon."""
        TC = self.time_correction(day) / 60  # Convert TC to hours
        return 12 + TC

    def sunrise_sunset(self, day):
        """Calculate sunrise and sunset times."""
        phi = self.latitude
        delta = self.declination_angle(day)
        H = np.degrees(np.arccos(-np.tan(np.radians(phi - self.beta)) * np.tan(np.radians(delta))))
        TC = self.time_correction(day) / 60  # Convert TC to hours
        t_sunrise = 12 - (H / 15) - TC
        t_sunset = 12 + (H / 15) - TC
        return t_sunrise, t_sunset

    def hour_angle(self, lst, solar_noon):
        """Calculate the hour angle (ω)."""
        return ((lst - solar_noon) / 24) * 360

    def solar_elevation_angle(self, delta, omega):
        """Calculate the solar elevation angle (α)."""
        phi = self.latitude
        alpha = np.degrees(np.arcsin(
            np.sin(np.radians(phi)) * np.sin(np.radians(delta)) +
            np.cos(np.radians(phi)) * np.cos(np.radians(delta)) * np.cos(np.radians(omega))
        ))
        return max(alpha, 0)  # Set to 0 if below the horizon

    def azimuth_of_sun(self, delta, alpha, omega):
        """Calculate the azimuth of the sun (ψ)."""
        phi = self.latitude
        numerator = np.sin(np.radians(delta)) * np.cos(np.radians(phi)) - \
                    np.cos(np.radians(delta)) * np.sin(np.radians(phi)) * np.cos(np.radians(omega))
        denominator = np.cos(np.radians(alpha))
        psi = np.degrees(np.arccos(numerator / denominator))
        return psi

    def module_irradiance(self, ion, alpha, psi):
        """Calculate the module irradiance (I_module)."""
        gamma = self.gamma
        beta = self.beta
        I_module = ion * (
            np.cos(np.radians(alpha)) * np.sin(np.radians(beta)) *
            np.cos(np.radians(gamma - psi)) +
            np.sin(np.radians(alpha)) * np.cos(np.radians(beta))
        )
        return max(I_module, 0)

    def simulate_day(self, year, month, day, mult=1.0):
        day_of_year = self.day_of_year(year, month, day)
        t_sunrise, t_sunset = self.sunrise_sunset(day_of_year)
        delta = self.declination_angle(day_of_year)
        solar_noon = self.solar_noon(day_of_year)
        margin = 1  # 60 minutes in hours

        results = {'Time': [], 'Irradiance': []}


        # Time correction
        time_corr = self.time_correction(day_of_year) / 60

        # Before sunrise
        t_before = t_sunrise - margin
        lst_before = t_before + time_corr
        omega_before = self.hour_angle(lst_before, solar_noon)
        alpha_before = self.solar_elevation_angle(delta, omega_before)
        psi_before = self.azimuth_of_sun(delta, alpha_before, omega_before)
        ion_before = 1367 * (1 + 0.033 * np.cos(2 * np.pi * day_of_year / 365))
        irr_before = self.module_irradiance(ion_before, alpha_before, psi_before) * mult
        results['Time'].append(t_before)
        results['Irradiance'].append(irr_before)

        # Sunrise
        lst_sunrise = t_sunrise + time_corr
        omega_sunrise = self.hour_angle(lst_sunrise, solar_noon)
        alpha_sunrise = self.solar_elevation_angle(delta, omega_sunrise)
        psi_sunrise = self.azimuth_of_sun(delta, alpha_sunrise, omega_sunrise)
        irr_sunrise = self.module_irradiance(ion_before, alpha_sunrise, psi_sunrise) * mult
        results['Time'].append(t_sunrise)
        results['Irradiance'].append(irr_sunrise)

        # Main daytime loop (every 15 minutes)
        time_range = np.arange(t_sunrise, t_sunset, 0.25)
        for time in time_range:
            lst = time + time_corr
            omega = self.hour_angle(lst, solar_noon)
            alpha = self.solar_elevation_angle(delta, omega)
            psi = self.azimuth_of_sun(delta, alpha, omega)
            ion = 1367 * (1 + 0.033 * np.cos(2 * np.pi * day_of_year / 365))
            I_module = self.module_irradiance(ion, alpha, psi) * mult
            results['Time'].append(time)
            results['Irradiance'].append(I_module)

        # Sunset
        lst_sunset = t_sunset + time_corr
        omega_sunset = self.hour_angle(lst_sunset, solar_noon)
        alpha_sunset = self.solar_elevation_angle(delta, omega_sunset)
        psi_sunset = self.azimuth_of_sun(delta, alpha_sunset, omega_sunset)
        irr_sunset = self.module_irradiance(ion, alpha_sunset, psi_sunset) * mult
        results['Time'].append(t_sunset)
        results['Irradiance'].append(irr_sunset)

        # After sunset
        t_after = t_sunset + margin
        lst_after = t_after + time_corr
        omega_after = self.hour_angle(lst_after, solar_noon)
        alpha_after = self.solar_elevation_angle(delta, omega_after)
        psi_after = self.azimuth_of_sun(delta, alpha_after, omega_after)
        irr_after = self.module_irradiance(ion, alpha_after, psi_after) * mult
        results['Time'].append(t_after)
        results['Irradiance'].append(irr_after)

        if 89 <= day_of_year <= 301:
            results['Time'] = [t + 1 for t in results['Time']]  # shift back so graph matches local clock time

        return pd.DataFrame(results)



class PVSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PV System Simulator")

        # Variables
        self.latitude_var = tk.DoubleVar(value=31.7187)
        self.longitude_var = tk.DoubleVar(value=34.7287)
        self.beta_var = tk.DoubleVar(value=16)
        self.gamma_var = tk.DoubleVar(value=180)
        self.date_var = tk.StringVar()
        self.year_var = tk.IntVar(value=2024)

        self.surface_area_var = tk.DoubleVar(value=1.0)  # Default 1 m²
        self.num_modules_var = tk.IntVar(value=1)        # Default 1 module

        self.create_widgets()

    def create_widgets(self):
        self.root.geometry("1000x600")
        self.root.resizable(True, True)

        container = ttk.Frame(self.root, padding="10")
        container.grid(row=0, column=0, sticky="nsew")

        left_frame = ttk.Frame(container)
        right_frame = ttk.Frame(container)

        left_frame.grid(row=0, column=0, padx=10, sticky="n")
        right_frame.grid(row=0, column=1, padx=20, sticky="n")

        # Latitude
        ttk.Label(left_frame, text="Latitude (φ):").grid(row=0, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.latitude_var).grid(row=0, column=1)

        # Longitude
        ttk.Label(left_frame, text="Longitude (λ):").grid(row=1, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.longitude_var).grid(row=1, column=1)

        # Tilt Angle (β) Single or Range
        ttk.Label(left_frame, text="Tilt Angle (β):").grid(row=2, column=0, sticky="w")
        self.beta_var = tk.DoubleVar(value=16)  # Default single value
        ttk.Entry(left_frame, textvariable=self.beta_var).grid(row=2, column=1)

        self.beta_range_toggle = tk.BooleanVar(value=False)  # Default: single value
        ttk.Checkbutton(left_frame, text="Use range", variable=self.beta_range_toggle).grid(row=2, column=2)

        # Tilt Angle Range Inputs
        ttk.Label(left_frame, text="Tilt Start (β):").grid(row=3, column=0, sticky="w")
        self.beta_start_var = tk.DoubleVar(value=10)
        ttk.Entry(left_frame, textvariable=self.beta_start_var).grid(row=3, column=1)

        ttk.Label(left_frame, text="Tilt Stop (β):").grid(row=4, column=0, sticky="w")
        self.beta_stop_var = tk.DoubleVar(value=50)
        ttk.Entry(left_frame, textvariable=self.beta_stop_var).grid(row=4, column=1)

        ttk.Label(left_frame, text="Tilt Step (β):").grid(row=5, column=0, sticky="w")
        self.beta_step_var = tk.DoubleVar(value=10)
        ttk.Entry(left_frame, textvariable=self.beta_step_var).grid(row=5, column=1)

        # Azimuth Angle (γ) Single or Range
        ttk.Label(left_frame, text="Azimuth Angle (γ):").grid(row=6, column=0, sticky="w")
        self.gamma_var = tk.DoubleVar(value=180)  # Default single value
        ttk.Entry(left_frame, textvariable=self.gamma_var).grid(row=6, column=1)

        self.gamma_range_toggle = tk.BooleanVar(value=False)  # Default: single value
        ttk.Checkbutton(left_frame, text="Use range", variable=self.gamma_range_toggle).grid(row=6, column=2)

        # Azimuth Angle Range Inputs
        ttk.Label(left_frame, text="Azimuth Start (γ):").grid(row=7, column=0, sticky="w")
        self.gamma_start_var = tk.DoubleVar(value=150)
        ttk.Entry(left_frame, textvariable=self.gamma_start_var).grid(row=7, column=1)

        ttk.Label(left_frame, text="Azimuth Stop (γ):").grid(row=8, column=0, sticky="w")
        self.gamma_stop_var = tk.DoubleVar(value=210)
        ttk.Entry(left_frame, textvariable=self.gamma_stop_var).grid(row=8, column=1)

        ttk.Label(left_frame, text="Azimuth Step (γ):").grid(row=9, column=0, sticky="w")
        self.gamma_step_var = tk.DoubleVar(value=10)
        ttk.Entry(left_frame, textvariable=self.gamma_step_var).grid(row=9, column=1)

        # Surface Area and Number of Modules
        ttk.Label(left_frame, text="Surface Area (m²):").grid(row=10, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.surface_area_var).grid(row=10, column=1)

        ttk.Label(left_frame, text="Number of Modules:").grid(row=11, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.num_modules_var).grid(row=11, column=1)

        # Power Clipping Threshold
        self.clip_threshold_var = tk.DoubleVar(value=120000000)  # Default threshold for main clipping
        ttk.Label(left_frame, text="Nominal Power (DC Limit) (W):").grid(row=12, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.clip_threshold_var).grid(row=12, column=1)

        # Alternate Clipping Threshold
        self.alt_clip_threshold_var = tk.DoubleVar(value=8500000)  # Default threshold for alternate clipping
        ttk.Label(left_frame, text="MAX Export Power (AC Limit) (W):").grid(row=13, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.alt_clip_threshold_var).grid(row=13, column=1)

        # Irradiance Multiplier
        self.irradiance_multiplier_var = tk.DoubleVar(value=30)
        ttk.Label(left_frame, text="Irradiance Losses (%):").grid(row=14, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.irradiance_multiplier_var).grid(row=14, column=1)

        # Power Multiplier
        self.power_multiplier_var = tk.DoubleVar(value=2)
        ttk.Label(left_frame, text="System Losses (%):").grid(row=15, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.power_multiplier_var).grid(row=15, column=1)

        # Efficiency Multiplier
        self.Efficiency_multiplier_var = tk.DoubleVar(value=80)
        ttk.Label(left_frame, text="Efficiency Losses (%):").grid(row=16, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.Efficiency_multiplier_var).grid(row=16, column=1)

        # Year and Date
        ttk.Label(left_frame, text="Year:").grid(row=17, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.year_var).grid(row=17, column=1)

        ttk.Label(left_frame, text="Date (e.g., 21 June):").grid(row=18, column=0, sticky="w")
        ttk.Entry(left_frame, textvariable=self.date_var).grid(row=18, column=1)

        # Simulate Button
        ttk.Button(left_frame, text="Simulate", command=self.simulate).grid(row=19, column=0, columnspan=2, pady=10)

        # Excel date input
        ttk.Label(right_frame, text="Excel Comparison Date (e.g., 21 June):").grid(row=0, column=0, sticky="w")
        self.excel_date_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.excel_date_var).grid(row=0, column=1)

        # Excel plot type selection (Irradiance vs Power)
        self.plot_type_var = tk.StringVar(value="irradiance")  # default to irradiance

        ttk.Label(right_frame, text="Excel Plot Type:").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(right_frame, text="Irradiance", variable=self.plot_type_var, value="irradiance").grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(right_frame, text="Power", variable=self.plot_type_var, value="power").grid(row=2, column=1, sticky="w")

        ttk.Button(right_frame, text="Compare Simulation with Excel", command=self.compare_with_excel).grid(row=3, column=0, columnspan=2, pady=10)

        # Total Energy from Date Range
        self.range_start_date_var = tk.StringVar(value="01/01/2024")
        self.range_end_date_var = tk.StringVar(value="03/03/2024")

        ttk.Label(right_frame, text="Start Date (dd/mm/yyyy):").grid(row=4, column=0, sticky="w")
        ttk.Entry(right_frame, textvariable=self.range_start_date_var).grid(row=4, column=1)

        ttk.Label(right_frame, text="End Date (dd/mm/yyyy):").grid(row=5, column=0, sticky="w")
        ttk.Entry(right_frame, textvariable=self.range_end_date_var).grid(row=5, column=1)

        ttk.Button(right_frame, text="Compute Energy for Date Range", command=self.compute_date_range_energy).grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(right_frame, text="Compare Simulated with Excel Energy", command=lambda: self.compute_date_range_energy(include_excel=True)).grid(row=7, column=0, columnspan=2, pady=10)

    def simulate(self):
        try:
            latitude = self.latitude_var.get()
            longitude = self.longitude_var.get()
            surface_area = self.surface_area_var.get()
            num_modules = self.num_modules_var.get()
            year = self.year_var.get()
            date_str = self.date_var.get().strip()

            # Retrieve beta and gamma values or ranges
            beta_use_range = self.beta_range_toggle.get()
            gamma_use_range = self.gamma_range_toggle.get()

            if beta_use_range:
                beta_start = self.beta_start_var.get()
                beta_stop = self.beta_stop_var.get()
                beta_step = self.beta_step_var.get()
            else:
                beta = self.beta_var.get()  # Single value

            if gamma_use_range:
                gamma_start = self.gamma_start_var.get()
                gamma_stop = self.gamma_stop_var.get()
                gamma_step = self.gamma_step_var.get()
            else:
                gamma = self.gamma_var.get()  # Single value

            # Parse the date input
            try:
                day, month_name = date_str.split(" ")
                day = int(day.strip())
                months = [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ]
                month = months.index(month_name.capitalize()) + 1
            except (ValueError, IndexError):
                raise ValueError("Invalid date format. Please use 'day month' (e.g., '14 May').")

            # Plot results for single or multiple values
            self.plot_results(
                latitude=latitude,
                longitude=longitude,
                surface_area=surface_area,
                num_modules=num_modules,
                year=year,
                month=month,
                day=day,
                beta_start=beta_start if beta_use_range else None,
                beta_stop=beta_stop if beta_use_range else None,
                beta_step=beta_step if beta_use_range else None,
                beta=beta if not beta_use_range else None,
                gamma_start=gamma_start if gamma_use_range else None,
                gamma_stop=gamma_stop if gamma_use_range else None,
                gamma_step=gamma_step if gamma_use_range else None,
                gamma=gamma if not gamma_use_range else None,
                swipe_mode="beta" if beta_use_range else "gamma" if gamma_use_range else None
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def plot_results(self, latitude, longitude, surface_area, num_modules, year, month, day, 
                 beta_start=None, beta_stop=None, beta_step=None, beta=None,
                 gamma_start=None, gamma_stop=None, gamma_step=None, gamma=None, 
                 swipe_mode=None):
        """Plot results for single or multiple combinations of tilt and azimuth angles."""
        try:
            # Initialize the plot
            fig, ax = plt.subplots(figsize=(16, 10))

            if swipe_mode == "beta" and beta_start is not None and beta_stop is not None:
                # Swipe over tilt angle (β)
                for beta in np.arange(beta_start, beta_stop + beta_step, beta_step):
                    simulator = PVSystemSimulator(latitude, longitude, beta, gamma)
                    irr_mult = 1 - self.irradiance_multiplier_var.get() / 100 if hasattr(self, 'irradiance_multiplier_var') else 1.0
                    results = simulator.simulate_day(year, month, day, mult=irr_mult)
                    power_mult = 1 - self.power_multiplier_var.get() / 100 if hasattr(self, 'power_multiplier_var') else 1.0
                    Efficiency_mult = 1 - self.Efficiency_multiplier_var.get() / 100 if hasattr(self, 'Efficiency_multiplier_var') else 1.0
                    results['Power'] = results['Irradiance'] * surface_area * num_modules * power_mult * Efficiency_mult
                    clip_threshold = self.clip_threshold_var.get()
                    results['Power'] = np.minimum(results['Power'], clip_threshold)
                    new_clip_threshold = self.alt_clip_threshold_var.get()
                    results['Power'] = np.minimum(results['Power'], new_clip_threshold)
                    ax.plot(results['Time'], results['Power'], label=f"β={beta:.1f}", linewidth=1.5)

            elif swipe_mode == "gamma" and gamma_start is not None and gamma_stop is not None:
                # Swipe over azimuth angle (γ)
                for gamma_val in np.arange(gamma_start, gamma_stop + gamma_step, gamma_step):
                    simulator = PVSystemSimulator(latitude, longitude, beta, gamma_val)
                    irr_mult = 1 - self.irradiance_multiplier_var.get() / 100 if hasattr(self, 'irradiance_multiplier_var') else 1.0
                    results = simulator.simulate_day(year, month, day, mult=irr_mult)
                    power_mult = 1 - self.power_multiplier_var.get() / 100 if hasattr(self, 'power_multiplier_var') else 1.0
                    Efficiency_mult = 1 - self.Efficiency_multiplier_var.get() / 100 if hasattr(self, 'Efficiency_multiplier_var') else 1.0
                    results['Power'] = results['Irradiance'] * surface_area * num_modules * power_mult * Efficiency_mult
                    clip_threshold = self.clip_threshold_var.get()
                    results['Power'] = np.minimum(results['Power'], clip_threshold)
                    new_clip_threshold = self.alt_clip_threshold_var.get()
                    results['Power'] = np.minimum(results['Power'], new_clip_threshold)
                    ax.plot(results['Time'], results['Power'], label=f"γ={gamma_val:.1f}", linewidth=1.5)

            else:
                # Single tilt (β) and azimuth (γ) angle
                simulator = PVSystemSimulator(latitude, longitude, beta, gamma)
                irr_mult = 1 - self.irradiance_multiplier_var.get() / 100 if hasattr(self, 'irradiance_multiplier_var') else 1.0
                results = simulator.simulate_day(year, month, day, mult=irr_mult)
                power_mult = 1 - self.power_multiplier_var.get() / 100 if hasattr(self, 'power_multiplier_var') else 1.0
                Efficiency_mult = 1 - self.Efficiency_multiplier_var.get() / 100 if hasattr(self, 'Efficiency_multiplier_var') else 1.0
                results['Power'] = results['Irradiance'] * surface_area * num_modules*Efficiency_mult*power_mult
                clip_threshold = self.clip_threshold_var.get()
                results['Power'] = np.minimum(results['Power'], clip_threshold)
                new_clip_threshold = self.alt_clip_threshold_var.get()
                results['Power'] = np.minimum(results['Power'], new_clip_threshold)
                ax.plot(results['Time'], results['Power'], label='Power Output (W)', color='blue', linewidth=1.5)

            # Dynamically set the y-axis range
            y_min = 0
            y_max = results['Power'].max()
            ax.set_ylim(y_min, y_max + y_max * 0.1)  # Add 10% padding to the top

            # Dynamically calculate y-axis tick intervals
            y_tick_interval = max(100, y_max // 10)  # Divide range into 10 intervals, minimum interval is 100 Watts
            ax.yaxis.set_major_locator(MultipleLocator(y_tick_interval))

            # Set axis labels, title, and grid
            ax.set_xlabel('Time (hours)', fontsize=14)
            ax.set_ylabel('Power Output (Watts)', fontsize=14)
            ax.set_title(f'Power Output vs Time on {day}/{month}/{year}', fontsize=16)

            # Remove scientific notation and format y-axis as plain numbers
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))

            # Add legend and grid
            ax.legend(fontsize=8, loc='upper right')
            ax.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

            # Show the plot
            plot_window = tk.Toplevel(self.root)
            plot_window.title("Power Output Plot")
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def compute_date_range_energy(self, include_excel=False):
        try:
            from datetime import datetime, timedelta

            # Read simulation inputs
            latitude = self.latitude_var.get()
            longitude = self.longitude_var.get()
            beta = self.beta_var.get()
            gamma = self.gamma_var.get()
            surface_area = self.surface_area_var.get()
            num_modules = self.num_modules_var.get()
            power_mult = 1 - self.power_multiplier_var.get() / 100
            irr_mult = 1 - self.irradiance_multiplier_var.get() / 100
            Efficiency_mult = 1 - self.Efficiency_multiplier_var.get() / 100

            # Read date range
            start_str = self.range_start_date_var.get()
            end_str = self.range_end_date_var.get()
            start_date = datetime.strptime(start_str, "%d/%m/%Y").date()
            end_date = datetime.strptime(end_str, "%d/%m/%Y").date()

            if end_date < start_date:
                raise ValueError("End date must be after or equal to start date.")

            # Simulate energy over date range
            simulator = PVSystemSimulator(latitude, longitude, beta, gamma)
            total_sim_energy = 0
            current_date = start_date
            while current_date <= end_date:
                sim_df = simulator.simulate_day(current_date.year, current_date.month, current_date.day, mult=irr_mult)
                sim_power = sim_df['Irradiance'] * surface_area * num_modules * Efficiency_mult * power_mult
                clip1 = self.clip_threshold_var.get()
                clip2 = self.alt_clip_threshold_var.get()
                sim_power = np.minimum(sim_power, clip1)
                sim_power = np.minimum(sim_power, clip2)
                total_sim_energy += compute_surface_under_plot(sim_df['Time'], sim_power)
                current_date += timedelta(days=1)

            # If Excel is NOT requested, show simulated result only
            if not include_excel:
                messagebox.showinfo("Total Energy Output",
                                    f"Simulated energy from {start_str} to {end_str}:\n"
                                    f"{total_sim_energy / 1000:.2f} kWh")
                return

            # If Excel is requested → ask for file and compute Excel total
            file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
            if not file_path:
                return

            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip().str.lower()
            df['datetime'] = pd.to_datetime(df['date'])
            df['power'] = pd.to_numeric(df['power'], errors='coerce')
            df['irradiance'] = pd.to_numeric(df['irradiance'], errors='coerce')
            df['hour'] = df['datetime'].dt.hour + df['datetime'].dt.minute / 60
            df['date_only'] = df['datetime'].dt.date

            total_excel_energy = 0
            total_sim_energy_corrected = 0
            current_date = start_date

            while current_date <= end_date:
                sim_df = simulator.simulate_day(current_date.year, current_date.month, current_date.day, mult = irr_mult)
                sim_power = sim_df['Irradiance'] * surface_area * num_modules * Efficiency_mult * power_mult
                sim_power = np.minimum(sim_power, self.clip_threshold_var.get())
                sim_power = np.minimum(sim_power, self.alt_clip_threshold_var.get())
                sim_daily_energy = compute_surface_under_plot(sim_df['Time'], sim_power)

                df_day = df[df['date_only'] == current_date].dropna(subset=['power', 'hour'])

                if not df_day.empty:
                    df_day = df_day.sort_values(by='hour')
                    excel_power = df_day['power'] * 1e3  # from kW to W
                    excel_daily_energy = compute_surface_under_plot(df_day['hour'], excel_power)

                    # Compare error
                    daily_error_percent = ((sim_daily_energy - excel_daily_energy) / excel_daily_energy) * 100

                    if abs(daily_error_percent) > 10:
                        # Correct using Excel irradiance
                        if 'irradiance' not in df_day.columns:
                            raise ValueError("Missing 'irradiance' column in Excel file!")

                        df_day = df[df['date_only'] == current_date].dropna(subset=['irradiance', 'hour'])
                        df_day = df_day.sort_values(by='hour')
                        excel_irradiance = df_day['irradiance'] 
                        corrected_power = excel_irradiance * surface_area * num_modules * Efficiency_mult * power_mult
                        corrected_power = np.minimum(corrected_power, self.clip_threshold_var.get())
                        corrected_power = np.minimum(corrected_power, self.alt_clip_threshold_var.get())

                        sim_daily_energy = compute_surface_under_plot(df_day['hour'], corrected_power)

                    # Accumulate
                    total_excel_energy += excel_daily_energy
                    total_sim_energy_corrected += sim_daily_energy

                current_date += timedelta(days=1)

            # After the loop → Show final corrected results
            percent_error = ((total_sim_energy_corrected - total_excel_energy) / total_excel_energy) * 100
            messagebox.showinfo("Corrected Simulated vs Excel Energy",
                f"Corrected simulated energy from {start_str} to {end_str}: {total_sim_energy_corrected / 1000:.2f} kWh\n"
                f"Measured Excel energy from {start_str} to {end_str}: {total_excel_energy / 1000:.2f} kWh\n"
                f"Error after correction: {percent_error:.2f}%")

        except Exception as e:
            messagebox.showerror("Error", str(e))


    def compare_with_excel(self):
        try:
            # Read GUI inputs
            latitude = self.latitude_var.get()
            longitude = self.longitude_var.get()
            beta = self.beta_var.get()
            gamma = self.gamma_var.get()
            year = self.year_var.get()
            sim_date_str = self.date_var.get().strip()
            excel_date_str = self.excel_date_var.get().strip()

            # Parse both dates (simulation + Excel)
            months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            day_sim, month_sim = sim_date_str.split(" ")
            day_excel, month_excel = excel_date_str.split(" ")
            day_sim = int(day_sim)
            day_excel = int(day_excel)
            month_sim = months.index(month_sim.capitalize()) + 1
            month_excel = months.index(month_excel.capitalize()) + 1

            from datetime import date
            date_sim = date(year, month_sim, day_sim)
            date_excel = date(year, month_excel, day_excel)

            # Simulate for selected date
            simulator = PVSystemSimulator(latitude, longitude, beta, gamma)
            sim_df = simulator.simulate_day(year, month_sim, day_sim)

            # Read Excel and filter one day
            file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
            if not file_path:
                return  # User cancelled
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip().str.lower()  # ✅ normalize headers

            df['datetime'] = pd.to_datetime(df['date'])
            df['power'] = pd.to_numeric(df['power'], errors='coerce')  # ✅ convert to numeric
            df['hour'] = df['datetime'].dt.hour + df['datetime'].dt.minute / 60
            df['date_only'] = df['datetime'].dt.date
            df_day = df[df['date_only'] == date_excel]


            if df_day.empty:
                raise ValueError(f"No data in Excel for {date_excel}")
            if 'irradiance' not in df_day.columns:
                raise ValueError("Missing 'irradiance' column in Excel file")

            # Start plotting
            fig, ax = plt.subplots(figsize=(12, 6))
            plot_type = self.plot_type_var.get()

            if plot_type == "irradiance":
                if 'irradiance' not in df_day.columns:
                    raise ValueError("Missing 'irradiance' column in Excel file")

                irr_mult = 1 - self.irradiance_multiplier_var.get() / 100 if hasattr(self, 'irradiance_multiplier_var') else 1.0
                sim_df['Irradiance'] = sim_df['Irradiance'] * irr_mult
                ax.plot(sim_df['Time'], sim_df['Irradiance'], label=f"Simulated Irradiance ({date_sim})", color='blue')
                ax.plot(df_day['hour'], df_day['irradiance'], label=f"Excel Irradiance ({date_excel})", color='orange', linestyle='--')
                ax.set_ylabel("Irradiance (W/m²)")
                ax.set_title(f"Irradiance Comparison on {date_excel}")


            elif plot_type == "power":
                if 'power' not in df_day.columns:
                    raise ValueError("Missing 'power' column in Excel file")

                power_mult = 1 - self.power_multiplier_var.get() / 100 if hasattr(self, 'power_multiplier_var') else 1.0
                irr_mult = 1 - self.irradiance_multiplier_var.get() / 100 if hasattr(self, 'irradiance_multiplier_var') else 1.0
                Efficiency_mult = 1 - self.Efficiency_multiplier_var.get() / 100 if hasattr(self, 'Efficiency_multiplier_var') else 1.0
                sim_power = sim_df['Irradiance'] * self.surface_area_var.get() * self.num_modules_var.get() * irr_mult * Efficiency_mult  * power_mult

                clip_threshold = self.clip_threshold_var.get()
                sim_power = np.minimum(sim_power, clip_threshold)
                new_clip_threshold = self.alt_clip_threshold_var.get()
                sim_power = np.minimum(sim_power, new_clip_threshold)
                excel_power = pd.to_numeric(df_day['power'], errors='coerce') * 1e3

                ax.plot(sim_df['Time'], sim_power, label=f"Simulated Power ({date_sim})", color='blue')
                ax.plot(df_day['hour'], excel_power, label=f"Excel Power ({date_excel})", color='orange', linestyle='--')
                ax.set_ylabel("Power (W)")
                ax.set_title(f"Power Comparison on {date_excel}")

                from matplotlib.ticker import FuncFormatter
                ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))  # Plain number formatting


            # Common settings
            ax.set_xlabel("Time (hours)")
            ax.legend(fontsize=7)
            ax.grid(True)

            # 🔧 Add finer axis resolution here
            from matplotlib.ticker import MultipleLocator
            ax.xaxis.set_major_locator(MultipleLocator(1))   # adjust as needed
            

            # Show in new window
            window = tk.Toplevel(self.root)
            window.title("Irradiance Comparison")
            canvas = FigureCanvasTkAgg(fig, master=window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Error", str(e))



if __name__ == "__main__":
    root = tk.Tk()
    app = PVSimulatorApp(root)
    root.mainloop()
