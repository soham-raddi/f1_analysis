import fastf1
import fastf1.plotting as f1plot
from fastf1.core import DataNotLoadedError
fastf1.Cache.enable_cache('./f1_analysis/cache') 

def main():
    year = int(input("Enter year (e.g., 2021): "))
    gp_name = input("Enter Grand Prix name (e.g., Bahrain): ").strip()
    session_type = input("Enter session type (FP1, FP2, FP3, Q, R): ").strip().upper()

    print(f"\nLoading {year} {gp_name} GP - {session_type}...\n")
    session = fastf1.get_session(year, gp_name, session_type)

    # Load session data
    try:
        session.load()
    except Exception as e:
        print(f"Failed to load session data: {e}")
        return

    # Print results summary
    if session.results is not None:
        print("Session Results:")
        print(session.results[['Abbreviation', 'Position', 'Points', 'Status']])
    else:
        print("No results data available.")
    
if __name__ == "__main__":
    main()
