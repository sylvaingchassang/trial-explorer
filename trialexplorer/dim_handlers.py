"""
map for dim name to its handler
"""
from trialexplorer.AACTStudyDimFlat import AACTStudyDimFlat

# for each implemented dimension, its handler must be specified here.
# ****key must equal table name****
DIM_HANDLE_MAP = {
    'brief_summaries': AACTStudyDimFlat
}
