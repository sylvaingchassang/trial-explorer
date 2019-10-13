"""
map for dim name to its handler
"""
from trialexplorer.AACTStudyDimFlat import AACTStudyDimFlat
from trialexplorer.AACTStudyDim2dGen import generate_2d_dim_constructor
from trialexplorer.AACTStudyDimOtcmAlysGrps import AACTStudyDimOtcmAlysGrps
from trialexplorer.AACTStudyDimOtcmCountsMeasure import AACTStudyDimOtcmCountsMeasure

# for each implemented dimension, its handler must be specified here.
# ****key must equal table name****
DIM_HANDLE_MAP = {
    'brief_summaries': AACTStudyDimFlat,
    'browse_interventions': AACTStudyDimFlat,
    'detailed_descriptions': AACTStudyDimFlat,
    'conditions': AACTStudyDimFlat,
    'browse_conditions': AACTStudyDimFlat,
    'id_information': AACTStudyDimFlat,
    'keywords': AACTStudyDimFlat,
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
    'milestones': generate_2d_dim_constructor('result_groups', 'result_group_id'),
    'drop_withdrawals': generate_2d_dim_constructor('result_groups', 'result_group_id'),
    'reported_events': generate_2d_dim_constructor('result_groups', 'result_group_id'),
    'baseline_counts': generate_2d_dim_constructor('result_groups', 'result_group_id'),
    'baseline_measurements': generate_2d_dim_constructor('result_groups', 'result_group_id'),
    'outcomes': AACTStudyDimFlat,
    'outcome_analyses': generate_2d_dim_constructor('outcomes', 'outcome_id'),
    'outcome_analysis_groups': AACTStudyDimOtcmAlysGrps,
    'outcome_counts': AACTStudyDimOtcmCountsMeasure,
    'outcome_measurements': AACTStudyDimOtcmCountsMeasure,
    'interventions': AACTStudyDimFlat,
    'intervention_other_names': generate_2d_dim_constructor('interventions', 'intervention_id'),
    'facilities': AACTStudyDimFlat,
    'facility_contacts': generate_2d_dim_constructor('facilities', 'facility_id'),
    'facility_investigators': generate_2d_dim_constructor('facilities', 'facility_id')
}
