import argparse
import sys
from src.render.render_cv import render_cv
from src.render.render_letter import render_letter

def main():
    parser = argparse.ArgumentParser(description="Deterministic Document Rendering Pipeline")
    parser.add_argument("--action", required=True, choices=["cv", "letter"], help="Which document to render")
    parser.add_argument("--source", required=True, help="Job portal source folder (e.g. 'tuberlin', 'stepstone')")
    parser.add_argument("--job-id", required=True, help="The target job ID")
    parser.add_argument("--language", default="english", choices=["english", "german", "spanish"], help="Target language (only applies to CV currently)")
    
    args = parser.parse_args()

    try:
        if args.action == "cv":
            render_cv(args.source, args.job_id, args.language)
        elif args.action == "letter":
            render_letter(args.source, args.job_id)
    except FileNotFoundError as e:
        print(f"[Error] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[Fatal Error] Pipeline rendering failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
