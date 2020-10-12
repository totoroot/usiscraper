# USI Scraper

Python webscraper to extract information about sport course vacancies at USI Graz (https://usionline.uni-graz.at/)

Writes to file and optionally STDOUT or InfluxDB database for visualization and alerting with Grafana

TODO clean up name shadowing, exception handling etc.
TODO python docstring documentation

## Usage

```
"writes vacancies to file"
python3 usiscraper.py

"writes vacancies to file and vacancy table to STDOUT"
python3 usiscraper.py

"writes vacancies to file and InfluxDB database"
python3 usiscraper.py
```

## Config

```
id: course number
discipline: special id for disciplines
course: description of sports course; keywords allowed
semester: full year with "S" for summer semester and "W" for winter semester
instructor: name of instructor
weekday: German shorthand weekday
after: begin of time slot in which to search for courses (quarter-hourly)
until: end of time slot in which to search for courses (quarter-hourly)
location: course location
```

### Example

```
id: 342
discipline: 1521
course: basketball fortg.
semester: 2020W
instructor: hans
weekday: mo
after: 15:15
until: 19:30
location: hallenbad
```

## InfluxDB Environment Variables

```
INFLUXDB_ADDRESS=
INFLUXDB_PORT=
INFLUXDB_USER=
INFLUXDB_PASSWORD=
INFLUXDB_DATABASE=
```

### Example

```
INFLUXDB_ADDRESS=localhost
INFLUXDB_PORT=8086
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=admin
INFLUXDB_DATABASE=usi
```

## Run regularly and write to InfluxDB

Add command to cron to run every 15 minutes.
```
crontab -e
```

*/15 * * * * <absolutePath>/usiscraper/scraper.py -i >> <absolutePath>/usiscraper/scraper.log 2>&1
