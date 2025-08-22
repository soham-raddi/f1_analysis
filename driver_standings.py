import fastf1
import pandas as pd
from collections import defaultdict
from datetime import datetime

fastf1.Cache.enable_cache("./cache")
def driver_standings(year: int, debug: bool = False, include_sprint_wins_podiums: bool = False) -> pd.DataFrame:
    current_year = datetime.now().year
    if year < 1950 or year > current_year:
        raise ValueError(f"Please enter a year between 1950 and {current_year}")

    schedule = fastf1.get_event_schedule(year, include_testing=False)
    if year == current_year:
        schedule = schedule[schedule['EventDate'] < datetime.now()]

    gp_points = defaultdict(float)      # main race points
    sprint_points = defaultdict(float)  # sprint points
    wins = defaultdict(int)             # wins
    podiums = defaultdict(int)          # podiums

    # debug dictionaries
    if debug:
        gp_points_debug = defaultdict(list)
        sprint_points_debug = defaultdict(list)

    for i, ev in schedule.iterrows():
        rnd = int(ev["RoundNumber"])
        try:
            race = fastf1.get_session(year, rnd, "R")
            race.load()
            r = race.results

            for i, row in r.iterrows():
                drv = row["DriverNumber"]
                pts = float(row["Points"])
                pos = int(row["Position"])
                gp_points[drv] += pts
                if debug:
                    gp_points_debug[drv].append((rnd, pts))

                if pos == 1:
                    wins[drv] += 1
                if pos <= 3:
                    podiums[drv] += 1

        except Exception as e:
            if debug:
                print(f"Error processing GP {rnd}: {str(e)}")
            continue

    # for sprint results
    for i, ev in schedule.iterrows():
        rnd = int(ev["RoundNumber"])
        sprint = None
        try:
            sprint = fastf1.get_session(year, rnd, 'S')
            sprint.load()
        except Exception:
            try:
                sprint = fastf1.get_session(year, rnd, 'Sprint')
                sprint.load()
            except Exception:
                continue  # if there is no sprint session, skip

        if sprint is not None and sprint.results is not None:
            for i, row in sprint.results.iterrows():
                drv = row["DriverNumber"]
                pts = float(row["Points"])
                sprint_points[drv] += pts
                if debug:
                    sprint_points_debug[drv].append((rnd, pts))

                if include_sprint_wins_podiums:
                    pos = int(row["Position"])
                    if pos == 1:
                        wins[drv] += 1
                    if pos <= 3:
                        podiums[drv] += 1

    driver_names = {}
    for i, ev in schedule.iterrows():
        try:
            session = fastf1.get_session(year, int(ev["RoundNumber"]), "R")
            session.load()
            for i, row in session.results.iterrows():
                driver_names[row["DriverNumber"]] = f"{row['Abbreviation']} ({row['FullName']})"
        except Exception:
            continue

    # combine sprint and gp points
    total_points = {drv: gp_points[drv] + sprint_points[drv]
                    for drv in set(gp_points.keys()) | set(sprint_points.keys())}

    if debug:
        print("\nPoints breakdown:")
        for drv in sorted(total_points.keys()):
            print(f"\n{driver_names.get(drv, drv)}:")
            print(f"  GP points: {gp_points_debug[drv]}")
            print(f"  Sprint points: {sprint_points_debug[drv]}")
            print(f"  GP total: {gp_points[drv]}")
            print(f"  Sprint total: {sprint_points[drv]}")
            print(f"  Combined total: {total_points[drv]}")

    # final table
    df = pd.DataFrame(
        [{"Driver": driver_names.get(drv, drv),
          "Points": total_points[drv],
          "Wins": wins[drv],
          "Podiums": podiums[drv]}
         for drv in total_points]
    )
    df = df.sort_values(by=["Points", "Wins", "Podiums"], ascending=[False, False, False]).reset_index(drop=True)
    df.index += 1
    return df

# main function to run the script
if __name__ == "__main__":
    year = int(input("Enter season year (e.g., 2023): ").strip())
    table = driver_standings(year, debug=True, include_sprint_wins_podiums=False)
    print(f"\n=== Drivers' Championship {year} ===")
    print(table)