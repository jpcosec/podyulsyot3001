#!/usr/bin/env bash

# Directory to store raw HTML files
BASE_DIR="${PHD_DATA_DIR:-$(cd "$(dirname "$0")" && pwd)/../../data/pipelined_data/tu_berlin}"
mkdir -p "$BASE_DIR"

# List of URLs (extracted from your open tabs). Add or remove as needed.
URLS=(
  "https://www.jobs.tu-berlin.de/en/job-postings/201223"
  "https://www.jobs.tu-berlin.de/en/job-postings/201399"
  "https://www.jobs.tu-berlin.de/en/job-postings/201342"
  "https://www.jobs.tu-berlin.de/en/job-postings/201084"
  "https://www.jobs.tu-berlin.de/en/job-postings/201069"
  "https://www.jobs.tu-berlin.de/en/job-postings/201553"
  "https://www.jobs.tu-berlin.de/en/job-postings/201309"
  "https://www.jobs.tu-berlin.de/en/job-postings/201596"
  "https://www.jobs.tu-berlin.de/en/job-postings?filter%5Bfulltextsearch%5D=&filter%5Bworktype_tub%5D%5B%5D"
)

# Output CSV file for the summary table
CSV="$BASE_DIR/summary.csv"
echo "URL,Brief Description,Creation Date,Facts" > "$CSV"

# Helper to extract a value from the HTML using grep/awk (very simple, may need tweaking)
extract_fact() {
  local html="$1"
  local label="$2"
  echo "$html" | grep -i "${label}" | head -n1 | sed -E "s/.*${label}[^0-9]*([0-9\.]+).*/\1/"
}

for url in "${URLS[@]}"; do
  job_id=$(printf "%s" "$url" | sed -nE 's#.*/([0-9]+)$#\1#p')
  if [[ -n "$job_id" ]]; then
    dir="$BASE_DIR/${job_id}"
    mkdir -p "$dir"
    html_file="$dir/raw.html"
  else
    safe_name=$(printf "%s" "$url" | sed -E 's#[^A-Za-z0-9._-]+#_#g')
    dir="$BASE_DIR/_source_listing"
    mkdir -p "$dir"
    html_file="$dir/${safe_name}.html"
  fi

  echo "Fetching $url ..."
  curl -L -s "$url" -o "$html_file"

  # Very naive extraction of a brief description (title tag) and creation date (if present)
  brief=$(grep -i -m1 -o "<title>[^<]*</title>" "$html_file" | sed -E 's/<\/?.*>//g' | tr ',' ';')
  creation=$(grep -i "Published" -m1 "$html_file" | sed -E 's/.*Published[^0-9]*([0-9]{2}\.[0-9]{2}\.[0-9]{4}).*/\1/')

  # Extract a few facts – this is a simple placeholder; you can extend it as needed.
  facts=""
  for label in "Number of employees" "Category" "Area of responsibility" "Start date" "Duration" "Salary" "Qualification" "Reference number"; do
    value=$(grep -i "$label" -m1 "$html_file" | sed -E "s/.*${label}[^0-9A-Za-z]*([A-Za-z0-9 ,\-]+).*/\1/")
    if [[ -n "$value" ]]; then
      facts+="${label}: ${value}; "
    fi
  done
  # Trim trailing space/semicolon
  facts=$(echo "$facts" | sed 's/; $//')

  # Append to CSV (escape commas)
  echo "\"$url\",\"$brief\",\"$creation\",\"$facts\"" >> "$CSV"
done

echo "All done. Raw HTML saved under $BASE_DIR and summary CSV at $CSV"
