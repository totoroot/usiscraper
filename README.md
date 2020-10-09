# USI Scraper

Python webscraper to extract information about open slots for sport courses at USI Graz

TODO extract relevant data and send to influxdb to realize visualization and alerting in grafana

## Config

id: course number
discipline: special id for disciplines
course: description of sports course; keywords allowed
semester: full year with "S" for summer semester and "W" for winter semester
instructor: name of instructor
weekday: German shorthand weekday
after: begin of time slot in which to search for courses (quarter-hourly)
until: end of time slot in which to search for courses (quarter-hourly)
location: course location

### Example

id: 342
discipline: 1521
course: basketball fortg.
semester: 2020W
instructor: hans
weekday: mo
after: 15:15
until: 19:30
location: hallenbad

## InfluxDB Environment Variables

INFLUXDB_ADDRESS=
INFLUXDB_PORT=
INFLUXDB_USER=
INFLUXDB_PASSWORD=
INFLUXDB_DATABASE=
