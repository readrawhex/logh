# logh

*silly hour tracker so I don't forget later*

---

# usage

Just running the script will give you a status for your most
recent project hours / clock ins. Options describe other features.

```bash
$ python3 logh.py -h
usage: logh.py [-h] [-i] [-o] [-e EXPORT] [-d] [--start-time START_TIME] [--end-time END_TIME] [project] [description ...]

log working hours

positional arguments:
  project               project being worked on
  description           description of tasks completed

options:
  -h, --help            show this help message and exit
  -i, --clock-in        mark current time as clock start
  -o, --clock-out       mark current time as clock end
  -e EXPORT, --export EXPORT
                        export timesheet data to file
  -d, --delete-clock-in
                        delete the most recent clock-in / hours
  --start-time START_TIME
                        specify a specific starting time
  --end-time END_TIME   specify a speicific ending time
```
