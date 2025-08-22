import fastf1
import pandas as pd
from collections import defaultdict

# Use a local cache (create the folder first if needed)
fastf1.Cache.enable_cache("./cache")

def driver_standings(year: int) -> pd.DataFrame:
    
    schedule = fastf1.get_event_schedule(year, include_testing=False)

    points = defaultdict(float)
    wins = defaultdict(int)
    podiums = defaultdict(int)

    for _, ev in schedule.iterrows():
        rnd = int(ev["RoundNumber"])
        fmt = ev["EventFormat"]  # 'conventional' or 'sprint'

        # ---- Race (points + wins + podiums) ----
        try:
            race = fastf1.get_session(year, rnd, "R")
            race.load()
            r = race.results

            for _, row in r.iterrows():
                drv = row["Abbreviation"]
                pts = float(row["Points"])
                pos = int(row["Position"])
                points[drv] += pts
                if pos == 1:
                    wins[drv] += 1
                if pos <= 3:
                    podiums[drv] += 1
        except Exception:
            # Canceled rounds or unavailable data are skipped
            continue

        # ---- Sprint (points only; no wins/podiums) ----
        if fmt == "sprint":
            try:
                spr = fastf1.get_session(year, rnd, "S")
                spr.load()
                s = spr.results
                for _, row in s.iterrows():
                    drv = row["Abbreviation"]
                    pts = float(row["Points"])
                    points[drv] += pts
            except Exception:
                pass

    df = pd.DataFrame(
        [{"Driver": d, "Points": points[d], "Wins": wins[d], "Podiums": podiums[d]} for d in points]
    )
    df = df.sort_values(by=["Points", "Wins", "Podiums"], ascending=[False, False, False]).reset_index(drop=True)
    df.index += 1
    return df

if __name__ == "__main__":
    year = int(input("Enter season year (e.g., 2023): ").strip())
    table = driver_standings(year)
    print(f"\n=== Drivers’ Championship {year} ===")
    print(table)