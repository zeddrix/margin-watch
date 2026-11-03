# Running margin-watch every morning at 6:30 AM (Melbourne)

The run is one command. It writes the run JSON, the Excel report and the email draft into `output/`, and appends to a log in `output/logs/`. Nothing is sent: the mailer is a dry run.

In this prototype the source is the sample file, so the as-of date comes from the file. With a real `SimproSource` the as-of date would be the morning of the run.

## macOS / Linux (cron)

`crontab -e`, then add (replace the path):

```cron
CRON_TZ=Australia/Melbourne
30 6 * * 1-5  cd /path/to/margin-watch && mkdir -p output/logs && /usr/local/bin/uv run --project agent margin-watch run >> output/logs/margin-watch-$(date +\%F).log 2>&1
```

- `CRON_TZ` makes 6:30 AM mean Melbourne time all year, daylight saving included (cronie and most Linux crons; on macOS cron, set the Mac's time zone to Melbourne instead).
- `1-5` is weekdays; use `*` for every day.
- `%` must be escaped as `\%` inside crontab.
- Use the full path to `uv` (`which uv`), because cron runs with a minimal `PATH`.
- `MARGIN_WATCH_AI` and `ANTHROPIC_API_KEY` can live in `agent/.env`; the CLI loads it.

To refresh the dashboard after the run, add `&& cd dashboard && npm run sync-runs && npm run build` and serve `dashboard/build/` with any static web server.

## Windows (Task Scheduler)

Set the PC's time zone to "(UTC+10:00) Canberra, Melbourne, Sydney" so 6:30 AM follows daylight saving. Save the XML below as `margin-watch.xml`, edit the two paths, then import it:

```powershell
schtasks /Create /TN "Margin Watch" /XML margin-watch.xml
```

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>margin-watch: 6:30 AM margin check (dry run, sample data)</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-11-05T06:30:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek><Monday /><Tuesday /><Wednesday /><Thursday /><Friday /></DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT15M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>cmd.exe</Command>
      <Arguments>/c "if not exist output\logs mkdir output\logs &amp;&amp; uv run --project agent margin-watch run &gt;&gt; output\logs\margin-watch.log 2&gt;&amp;1"</Arguments>
      <WorkingDirectory>C:\path\to\margin-watch</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
```

`StartWhenAvailable` runs a missed 6:30 job as soon as the PC wakes.

## Checking it ran

- `output/logs/` holds one log per day (cron) or one appended log (Windows). A successful run prints the counts and the five files it wrote.
- Exit codes: `0` ok, `2` the input file is invalid (the log says which job and field), `1` unexpected error.
- `output/runs/index.json` lists every run, newest first.
