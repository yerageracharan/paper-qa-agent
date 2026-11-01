from paperqa.verification import find_missing_question_anchor


def test_missing_technical_acronym_is_detected():
    paper = "The SGA method reports average macro-F1 on English datasets."
    assert find_missing_question_anchor(
        "What accuracy does SGA reach on the MNLI dataset?", paper
    ) == "missing_acronym:MNLI"


def test_acronym_present_in_paper_is_allowed():
    paper = "The SGA model is evaluated on MNLI and FoodReviews."
    assert find_missing_question_anchor(
        "What accuracy does SGA reach on the MNLI dataset?", paper
    ) is None


def test_human_evaluation_question_requires_study_evidence():
    paper = "The paper reports macro-F1 and accuracy for five datasets."
    assert find_missing_question_anchor(
        "Did the authors run a human evaluation?", paper
    ) == "missing_human_evaluation_evidence"


def test_participant_evidence_satisfies_human_study_anchor():
    paper = "The authors interviewed 20 participants after the experiment."
    assert find_missing_question_anchor(
        "Did the authors run a human evaluation?", paper
    ) is None


def test_usability_study_evidence_satisfies_human_evaluation_anchor():
    paper = "We conducted a usability study with ten volunteers."
    assert find_missing_question_anchor(
        "Did the authors run a human evaluation?", paper
    ) is None


def test_ordinary_paraphrase_question_is_not_blocked():
    paper = (
        "With only 100 labeled examples, SGA reaches 68.2 macro-F1 "
        "versus 63.5 for standard adapters."
    )
    assert find_missing_question_anchor(
        "How much does the method help when very little labeled data is available?",
        paper,
    ) is None


def test_missing_camel_case_technical_name_is_detected():
    paper = "The paper discusses low-rank matrices and adapter tuning."
    assert find_missing_question_anchor(
        "What macro-F1 does LoRA achieve on FoodReviews?", paper
    ) == "missing_acronym:LoRA"


def test_camel_case_dataset_name_present_in_paper_is_allowed():
    paper = "The experiments use FoodReviews and ForumToxicity."
    assert find_missing_question_anchor(
        "Which results are reported for FoodReviews?", paper
    ) is None
