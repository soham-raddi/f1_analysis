import fastf1
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import logging

# Disable FastF1 logging to reduce output
logging.getLogger('fastf1').setLevel(logging.ERROR)
fastf1.Cache.enable_cache("cache")

# Unicode superscript mapping for sprint positions
SUPER = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

# FIA Grand Prix abbreviations
FIA_ABBR = {
    "Australian Grand Prix": "AUS", "Azerbaijan Grand Prix": "AZE", 
    "Bahrain Grand Prix": "BHR", "Saudi Arabian Grand Prix": "SAU",
    "Miami Grand Prix": "MIA", "Monaco Grand Prix": "MON",
    "Spanish Grand Prix": "ESP", "Canadian Grand Prix": "CAN",
    "Austrian Grand Prix": "AUT", "British Grand Prix": "GBR",
    "Hungarian Grand Prix": "HUN", "Belgian Grand Prix": "BEL",
    "Dutch Grand Prix": "NED", "Italian Grand Prix": "ITA",
    "Singapore Grand Prix": "SGP", "Japanese Grand Prix": "JPN",
    "Qatar Grand Prix": "QAT", "United States Grand Prix": "USA",
    "Mexico City Grand Prix": "MEX", "São Paulo Grand Prix": "SAP",
    "Las Vegas Grand Prix": "LVG", "Abu Dhabi Grand Prix": "ABU",
}

def safe_int(value, default=999):
    try:
        if pd.isna(value):
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def get_sprint_data(year, round_number):
    sprint_positions = {}
    sprint_points = {}
    
    try:
        sprint = fastf1.get_session(year, round_number, "S")
        sprint.load(laps=False, telemetry=False, weather=False, messages=False)
        if year < 2022:
            # 2021: Only top 3 score points (3-2-1)
            sprint_points_table = {1: 3, 2: 2, 3: 1}
            max_positions = 3
        else:
            # 2022+: Top 8 score points (8-7-6-5-4-3-2-1)
            sprint_points_table = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
            max_positions = 8
        
        for _, row in sprint.results.iterrows():
            position = safe_int(row.Position)
            if position <= max_positions:
                sprint_positions[row.DriverNumber] = position
                sprint_points[row.DriverNumber] = sprint_points_table.get(position, 0)
                
    except Exception as e:
        print(f"No sprint data available for round {round_number}")
        
    return sprint_positions, sprint_points

def format_race_result(position, status, sprint_position=None, year=2023):
    status_lower = str(status).lower()
    
    # Define colors
    podium_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#EECC6D"} 
    points_color = "#CCFFCC"  # point-scoring positions (4th-10th)
    other_color = "#E5CCFF"   # non-point positions (11th and beyond)
    
    # dnf/dns/wd/dsq handling
    if any(keyword in status_lower for keyword in ["dnf", "retired", "not classified"]):
        return ("DNF", "#FF9999", "black")
    elif "did not start" in status_lower:
        return ("DNS", "white", "black")
    elif "withdrew" in status_lower:
        return ("WD", "#CCCCCC", "black")
    elif any(keyword in status_lower for keyword in ["dsq", "disqualified", "excluded"]):
        return ("DSQ", "black", "white")
    else:
        display_text = str(position) if position != 999 else "-"
        
        # Add sprint position as superscript if available
        if sprint_position and sprint_position <= 8:
            display_text += str(sprint_position).translate(SUPER)
        
        # Choose background color based on position
        if position in podium_colors:
            background_color = podium_colors[position]
        elif position <= 10:
            background_color = points_color
        else:
            background_color = other_color
            
        return (display_text, background_color, "black")

def driver_standings(year=2023):
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except ValueError as e:
        print(f"Error loading schedule for year {year}: {e}")
        print("Please use a valid F1 season year (e.g., 2018-2024)")
        return None
    driver_points = defaultdict(float)
    driver_results = defaultdict(dict)
    race_abbreviations = []

    print(f"Loading F1 {year} season data...")

    for race_index, race in schedule.iterrows():
        race_name = race["EventName"]
        gp_abbr = FIA_ABBR.get(race_name, race_name[:3].upper())
        round_number = race["RoundNumber"]
        race_abbreviations.append(gp_abbr)

        try:
            session = fastf1.get_session(year, round_number, "R")
            session.load(laps=False, telemetry=False, weather=False, messages=False)
        except Exception:
            continue

        sprint_positions, sprint_points = get_sprint_data(year, round_number)

        for _, row in session.results.iterrows():
            driver_abbr = row.Abbreviation
            if not driver_abbr:  
                continue
                
            position = safe_int(row.Position)
            status = row.Status if pd.notna(row.Status) else "Unknown"
            race_points = float(row.Points) if pd.notna(row.Points) else 0.0

            driver_number = row.DriverNumber
            sprint_pts = sprint_points.get(driver_number, 0)
            sprint_pos = sprint_positions.get(driver_number, None)
            
            cell_data = format_race_result(position, status, sprint_pos)

            driver_points[driver_abbr] += race_points + sprint_pts
            driver_results[driver_abbr][gp_abbr] = cell_data

    all_drivers = list(driver_results.keys())

    data_dict = {}
    for driver in all_drivers:
        data_dict[driver] = {}
        for race_abbr in race_abbreviations:
            if race_abbr in driver_results[driver]:
                data_dict[driver][race_abbr] = driver_results[driver][race_abbr]
            else:
                data_dict[driver][race_abbr] = ("-", "white", "black")
    
    df = pd.DataFrame.from_dict(data_dict, orient="index")
    df = df.reindex(columns=race_abbreviations) 
    
    df["Total"] = [driver_points[driver] for driver in df.index]
    
    df = df.sort_values("Total", ascending=False)
    df.index.name = "Driver"
    
    print("Data loaded successfully")
    return df

def plot_standings(df):
    if df is None or df.empty:
        print("No data to plot")
        return
        
    fig, ax = plt.subplots(figsize=(max(12, len(df.columns) * 0.6), len(df) * 0.4))
    ax.axis("off")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.02)

    cell_colors = []
    cell_text = []
    cell_text_colors = []
    
    for driver_name, row in df.iterrows():
        row_colors = ["#F0F0F0"]
        row_text = [str(driver_name)]
        row_text_colors = ["black"]
        
        for column in df.columns:
            value = row[column]
            
            if isinstance(value, tuple) and len(value) == 3:
                text, bg_color, text_color = value
                row_text.append(str(text))
                row_colors.append(bg_color)
                row_text_colors.append(text_color)
            else:
                row_text.append(str(value))
                row_colors.append("white")
                row_text_colors.append("black")
        
        cell_colors.append(row_colors)
        cell_text.append(row_text)
        cell_text_colors.append(row_text_colors)

    table = ax.table(
        cellText=cell_text,
        cellColours=cell_colors,
        colLabels=["Driver"] + list(df.columns),
        loc="center",
        cellLoc="center"
    )

    # Apply text colors to each cell
    for (row_idx, col_idx), cell in table.get_celld().items():
        if row_idx > 0: 
            try:
                text_color = cell_text_colors[row_idx - 1][col_idx]
                cell.get_text().set_color(text_color)
            except (IndexError, TypeError):
                pass

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.2)
    
    for col_idx in range(len(df.columns) + 1):
        header_cell = table[(0, col_idx)]
        header_cell.set_facecolor("#4472C4")
        header_cell.get_text().set_color("white")
        header_cell.get_text().set_weight("bold")

    plt.title(f"F1 {year} Driver Championship Standings", fontsize=14, fontweight="bold", pad=10)
    plt.tight_layout(pad=0.5)
    plt.show()

def print_summary(df, year):
    if df is None or df.empty:
        return
        
    print(f"\n=== F1 {year} Driver Championship Summary ===")
    print(f"Champion: {df.index[0]} ({df.iloc[0]['Total']} points)")
    print(f"Runner-up: {df.index[1]} ({df.iloc[1]['Total']} points)")
    print(f"Third place: {df.index[2]} ({df.iloc[2]['Total']} points)")
    print(f"\nTotal drivers: {len(df)}")
    print(f"Total races: {len(df.columns) - 1}") 

if __name__ == "__main__":
    try:
        year = int(input("Enter F1 season year (e.g., 2021, 2022, 2023, 2024): "))
    except ValueError:
        print("Invalid input. Using default year 2023.")
        year = 2023
    
    print(f"Generating F1 {year} Driver Standings...")
    df = driver_standings(year)
    
    if df is not None:
        print_summary(df, year)
        plot_standings(df)
    else:
        print("Failed to generate standings. Please check the year and try again.")