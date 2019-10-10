"""
map for dim name to its handler
"""
from trialexplorer.AACTStudyDimFlat import AACTStudyDimFlat
from trialexplorer.AACTStudyDimResultsGroupFields import AACTStudyDimResultsGroupFields

# for each implemented dimension, its handler must be specified here.
# ****key must equal table name****
DIM_HANDLE_MAP = {
    'brief_summaries': AACTStudyDimFlat,
    'browse_interventions': AACTStudyDimFlat,
    'detailed_descriptions': AACTStudyDimFlat,
    'conditions': AACTStudyDimFlat,
    'browse_conditions': AACTStudyDimFlat,
    'id_information': AACTStudyDimFlat,
    'key_words': AACTStudyDimFlat,
    'countries': AACTStudyDimFlat,
    'calculated_values': AACTStudyDimFlat,
    'central_contacts': AACTStudyDimFlat,
    'responsible_parties': AACTStudyDimFlat,
    'overall_officials': AACTStudyDimFlat,
    'sponsors': AACTStudyDimFlat,
    'pending_results': AACTStudyDimFlat,
    'result_contacts': AACTStudyDimFlat,
    'study_references': AACTStudyDimFlat,
    'links': AACTStudyDimFlat,
    'documents': AACTStudyDimFlat,
    'ipd_information_types': AACTStudyDimFlat,
    'result_agreements': AACTStudyDimFlat,
    'provided_documents': AACTStudyDimFlat,
    'design_outcomes': AACTStudyDimFlat,
    'eligibilities': AACTStudyDimFlat,
    'designs': AACTStudyDimFlat,
    'result_groups': AACTStudyDimFlat,
    'outcomes': AACTStudyDimFlat,
    'interventions': AACTStudyDimFlat,
    'facilities': AACTStudyDimFacilitiesFields,
    'milestones': AACTStudyDimResultsGroupFields,
}
