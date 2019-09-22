# trial-explorer
exploration tools for the [ClinicalTrials.gov](http://www.clinicaltrials.gov) database

## Downloading Raw XML Data

The following script, executed in the root directory will download and unzip the data from 
https://clinicaltrials.gov/AllPublicXML.zip into ./raw_data/ and unzip it for use.
```
bash ./scripts/wget_raw_data.sh
```

## Connecting to AACT database
- Create a login at https://aact.ctti-clinicaltrials.org/users/sign_up
- Create a file called './config/private/credentials.private.ini', following the template in 
'./config/private/credentials.template', including the above credentials

```python
import pdaactconn as pconn

ac = pconn.AACTConnection()

df = ac.query("SELECT count(*) FROM studies")

df.head()
```

|   | count  |
|---|--------|
| 0 | 316970 |


## Connecting to localhost version of AACT database
- Follow instructions on: https://aact.ctti-clinicaltrials.org/snapshots
- Create/add to a file called './config/private/credentials.private.ini', following the template in 
'./config/private/credentials.template', including localhost credentials

```python
import pdaactconn as pconn

ac = pconn.AACTConnection()
ac.set_source(ac.LOCAL)
df = ac.query("SELECT count(*) FROM studies")

df.head()
```

|   | count  |
|---|--------|
| 0 | 316970 |