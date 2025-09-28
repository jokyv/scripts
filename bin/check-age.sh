# Check when inputs were last updated
cat flake.lock |
  jaq -r '.nodes | del(.root) | map_values(.locked.lastModified) | to_entries | sort_by(.value) | .[] | "\(.key)\t\(.value)"' |
  awk -F'\t' '{
    cmd = "date -d @" $2 " +\"%Y-%m-%d\" 2>/dev/null || echo \"invalid\""
    cmd | getline date_str
    close(cmd)
    print $1 "\t" date_str
  }' |
  gum table -c 'input,updated' -w '50,50' --height=60
