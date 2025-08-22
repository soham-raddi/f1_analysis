import fastf1
import pandas as pd
from collections import defaultdict
from datetime import datetime

fastf1.Cache.enable_cache("./cache")

def constructor_standings(year: int, debug: bool = False, include_sprint_wins_podiums: bool = False) -> pd.DataFrame:
    current_year = datetime.now().year
    if year < 1950 or year > current_year:
        raise ValueError(f"Please enter a year between 1950 and {current_year}")

    schedule = fastf1.get_event_schedule(year, include_testing=False)

    if year == current_year:
        schedule = schedule[schedule['EventDate'] < datetime.now()]

    gp_points = defaultdict(float)       # main race points
    sprint_points = defaultdict(float)   # Sprint points
    team_wins = defaultdict(int)         # wins
    team_podiums = defaultdict(int)      # podiums

    # Debug dictionaries
    gp_points_debug = defaultdict(list)
    sprint_points_debug = defaultdict(list)

    # main race results
    for i, ev in schedule.iterrows():
        rnd = int(ev["RoundNumber"])
        try:
            race = fastf1.get_session(year, rnd, "R")
            race.load()
            r = race.results

            for i, row in r.iterrows():
                team = row["TeamName"]
                pts = float(row["Points"])
                pos = int(row["Position"])
                gp_points[team] += pts
                gp_points_debug[team].append((rnd, pts))

                if pos == 1:
                    team_wins[team] += 1
                if pos <= 3:
                    team_podiums[team] += 1

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
                team = row["TeamName"]
                pts = float(row["Points"])
                sprint_points[team] += pts
                sprint_points_debug[team].append((rnd, pts))

                if include_sprint_wins_podiums:
                    pos = int(row["Position"])
                    if pos == 1:
                        team_wins[team] += 1
                    if pos <= 3:
                        team_podiums[team] += 1

    # combining main race and sprint race points
    total_points = {team: gp_points[team] + sprint_points[team]
                    for team in set(gp_points.keys()) | set(sprint_points.keys())}

    df = pd.DataFrame(
        [{"Team": t, "Points": total_points[t], "Wins": team_wins[t], "Podiums": team_podiums[t]}
         for t in total_points]
    )
    df = df.sort_values(by=["Points", "Wins", "Podiums"], ascending=[False, False, False]).reset_index(drop=True)
    df.index += 1
    return df

# main function to run the script
if __name__ == "__main__":
    year = int(input("Enter season year (e.g., 2023): ").strip())
    table = constructor_standings(year, debug=True, include_sprint_wins_podiums=False)
    print(f"\n=== Constructors' Championship {year} ===")
    print(table)