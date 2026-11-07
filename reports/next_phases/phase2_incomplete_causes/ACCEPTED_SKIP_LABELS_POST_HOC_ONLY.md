# Accepted-skip correctness labels — POST-HOC ANALYSIS ONLY

**4/13** current PASS tasks accepting selected skips are incorrect-labelled.

The batch, skip and projection outputs were written before reading these labels. The fixed 13-task cohort and the label-blind document hashes are recorded in accepted_PASS_labels_POST_HOC_ONLY.json. Labels did not set a selection, parser decision, reason group or policy projection. This count is not a claim that executing skipped tests would detect those incorrect patches.
