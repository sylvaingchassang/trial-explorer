# Connection Utility 

A small stand-alone package that handles connections between pandas and the aact postgres database

Handles connections to
- aact-db.ctti-clinicaltrials.org
- localhost

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