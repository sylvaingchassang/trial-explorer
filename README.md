# trial-explorer
exploration tools for the [ClinicalTrials.gov](http://www.clinicaltrials.gov) database

## Downloading Raw XML Data

The following script, executed in the root directory will download and unzip the data from 
https://clinicaltrials.gov/AllPublicXML.zip into ./raw_data/ and unzip it for use.
```
bash ./scripts/wget_raw_data.sh
```

## Usage
#### Initialization
```python
import pdaactconn as pc
from trialexplorer import AACTStudySet

# optional:
from tqdm import tqdm_notebook as tqdm  # if notebook
# import tqdm # if commandline

# default using local connection
ss = AACTStudySet.AACTStudySet()

# use remote connection to aact host
conn = pc.AACTConnection(source=pc.AACTConnection.REMOTE)
ss = AACTStudySet.AACTStudySet(conn=conn)

# enable progress bars:
ss = AACTStudySet.AACTStudySet(tqdm_handler=tqdm)
```

#### Loading studies
```python
from trialexplorer import AACTStudySet

ss = AACTStudySet.AACTStudySet()
ss.load_studies() 
ss.studies.shape
```
315291 studies loaded!
```
>> Output:
(315291, 63)
```

#### Constraints
- Before loading any data, we can set constraints on the main studies table.
- Initial constraints are added in SQL notation
- Constraints are automatically added as AND constraint
- OR conditions can be added in a single line: add_constraint("A OR B")
- List of available columns to filter on is in the .list_columns() method

```python
from trialexplorer import AACTStudySet

ss = AACTStudySet.AACTStudySet()
ss.add_constraint("start_date >= '2018-06-30'")
ss.add_constraint("start_date <= '2018-12-31'")
ss.load_studies()
```
12790 studies loaded!

```python
from trialexplorer import AACTStudySet

ss = AACTStudySet.AACTStudySet()
ss.list_columns()
```
['nct_id',
 'nlm_download_date_description',
 'study_first_submitted_date',
 'results_first_submitted_date',
 'disposition_first_submitted_date',
 'last_update_submitted_date',
 'study_first_submitted_qc_date',
 'study_first_posted_date',
 ...
 ]

#### Loading dimensions
```python
# can first see which dimensions are available
from trialexplorer import AACTStudySet

ss = AACTStudySet.AACTStudySet()
ss.avail_dims.list
```
['brief_summaries',
 'browse_interventions',
 'detailed_descriptions',
 'conditions',
 'browse_conditions',
 'id_information',
 'key_words',
 'countries',
 'calculated_values',
 ...
 ]
 
 ```python
# loading dimesions and filling data
from trialexplorer import AACTStudySet

ss = AACTStudySet.AACTStudySet()
tested_dims = ['result_groups',
               'outcomes', 
               'outcome_counts',
               'outcome_measurements']
ss.add_constraint("start_date >= '2018-12-31'")
ss.load_studies()
ss.add_dimensions(tested_dims)
ss.refresh_dim_data()
```
```
>> Output:
Syncing the temp table temp_cur_studies in 26 chunks x 500 records each

Creating index on the temp table
 - Loading dimension result_groups
 -- Loading raw data
 -- Sorting index
 - Loading dimension outcomes
 -- Loading raw data
 -- Sorting index
 - Loading dimension outcome_counts
 -- Loading raw data
 -- Sorting index
 - Loading dimension outcome_measurements
 -- Loading raw data
 -- Sorting index
```

```python 
for dim_name, cur_dim in ss.dimensions.items():
    print("**", dim_name)
    print(cur_dim.data.head(2))
```

```
>> Output:
** result_groups

                    id ctgov_group_code result_type               title  \
nct_id                                                                   
NCT02610972  14105968               B3    Baseline               Total   
NCT02610972  14105969               B2    Baseline  CLINICALLY HEALTHY   

                                                   description  
nct_id                                                          
NCT02610972                      Total of all reporting groups  
NCT02610972  Women with a delivery of a healthy normal baby...  


** outcomes

                  id         outcome_type  \
nct_id                                      
NCT02610972  4265972              Primary   
NCT03196349  3947130  Other Pre-specified   

                                                         title  \
nct_id                                                           
NCT02610972  Prevalence of Urine Congophilia Using Congo Re...   
NCT03196349                                     Major Bleeding   


** outcome_counts

                                              id ctgov_group_code    scope  \
nct_id      result_group_id outcome_id                                       
NCT02610972 14105973        4265972     10055373               O2  Measure   
            14105974        4265972     10055374               O1  Measure   

                                               units  count  
nct_id      result_group_id outcome_id                       
NCT02610972 14105973        4265972     Participants     50  
            14105974        4265972     Participants    100  


** outcome_measurements

                                              id ctgov_group_code  \
nct_id      result_group_id outcome_id                              
NCT02610972 14105973        4265972     31894991               O2   
            14105974        4265972     31894992               O1   

                                       classification category  \
nct_id      result_group_id outcome_id                           
NCT02610972 14105973        4265972                              
            14105974        4265972                           
```
 
#### Dropping studies
Dropping studies will remove those studies from memory in both .studies and dimensions
```python
from trialexplorer import AACTStudySet

ss = AACTStudySet.AACTStudySet()
tested_dims = ['result_groups',
               'outcomes', 
               'outcome_counts',
               'outcome_measurements']
ss.add_constraint("start_date >= '2018-12-31'")
ss.load_studies()


# dropping first 100 studies
ss.drop_studies(ss.studies[:100].index)
```

```
>> Output:
started with 12790 studies
ended with 12690 studies
Dropping records from the result_groups dimension
Dropping records from the outcomes dimension
Dropping records from the outcome_counts dimension
Dropping records from the outcome_measurements dimension
```