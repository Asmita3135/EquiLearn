"""
Member 3 Comprehensive Test Suite
All record() calls use flat single-line format to avoid multi-line parsing issues.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import re
from text_preprocessing import preprocess_text
from text_analysis import analyze_text, count_syllables, correct_ocr_token
from accessibility_rules import get_accessibility_representation, UserProfile
from input_integration import UnifiedInput, IntegrationResult, TimestampedSegment
from dyslexia_pipeline import run_dyslexia_pipeline, DyslexiaPipelineResult
from llm_processing import LLMProcessor
from main_pipeline import run_member3_pipeline
from text_analysis import TextAnalysisResult

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARNING"
NT   = "NOT TESTED (no real LLM)"

results = []

def record(tid, name, inp, expected, actual, status, note=""):
    results.append((tid, name, status, note))
    label = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARNING": "[WARN]",
             "NOT TESTED (no real LLM)": "[N/T ]"}[status]
    print(label + " " + tid + " " + name)
    if status != PASS:
        print("     Expected : " + str(expected))
        print("     Actual   : " + str(actual))
        if note:
            print("     Note     : " + str(note))

# ── Mock LLMs ──────────────────────────────────────────────────────────────
def mock_simplify(prompt):
    if "REFINEMENT" in prompt or "further simplify" in prompt:
        return "Plants make food. Sunlight helps. This is photosynthesis."
    if "Summarize" in prompt:
        return "Plants use sunlight to make glucose."
    return "Plants use sunlight to make food. This is called photosynthesis."

def exc_provider(prompt):
    raise ConnectionError("Simulated timeout")

def mock_empty(prompt):
    return ""

def garbage_provider(prompt):
    return "!!@@##$$%%" * 20

std_proc     = LLMProcessor(provider_func=mock_simplify,   model_config="Mock-Simple")
exc_proc     = LLMProcessor(provider_func=exc_provider,    model_config="Mock-Exception")
emp_proc     = LLMProcessor(provider_func=mock_empty,      model_config="Mock-Empty")
garbage_proc = LLMProcessor(provider_func=garbage_provider, model_config="Garbage")

SIMPLE_TEXT = "Cats are nice. They like to play."
NORMAL_TEXT = ("Photosynthesis is the process by which plants use sunlight, water, and carbon "
               "dioxide to produce oxygen and energy in the form of glucose. This vital process "
               "supports nearly all life on Earth.")
COMPLEX_TEXT = ("Photosynthesis is a fundamental biochemical process in which chlorophyll-bearing "
                "organisms convert radiant electromagnetic energy into chemical potential energy "
                "via the light-dependent and light-independent Calvin cycle reactions, sequestering "
                "carbon dioxide and producing adenosine triphosphate and nicotinamide adenine "
                "dinucleotide phosphate as intermediate metabolites.")
LONG_SENT = ("The rapid proliferation of antibiotic-resistant bacterial strains, exacerbated "
             "by the indiscriminate and widespread overuse of broad-spectrum antimicrobial agents "
             "in both clinical and agricultural settings, poses an unprecedented, multifaceted "
             "threat to global public health infrastructure and necessitates an urgent, "
             "coordinated, and internationally cooperative policy response.")
FACT_TEXT = ("Isaac Newton formulated the three laws of motion in 1687. "
             "Water boils at 100 degrees C at sea level. "
             "The speed of light is approximately 299792 km/s. "
             "DNA is a double-helix molecule discovered by Watson and Crick in 1953.")

print("=" * 70)
print("  MEMBER 3 COMPREHENSIVE TEST SUITE")
print("=" * 70)

# ── TEST 1: COMPLEXITY ────────────────────────────────────────────────────
print("\n-- TEST 1: COMPLEXITY --")

r1a = analyze_text(SIMPLE_TEXT)
record("T1-A", "Simple text: Low complexity", SIMPLE_TEXT[:40], "Low in complexity", r1a.complexity_indicator, PASS if "Low" in r1a.complexity_indicator else FAIL)

r1b = analyze_text(NORMAL_TEXT)
ok1b = r1b.complexity_indicator in ("Medium (High School Level)", "High (College/Professional Level)")
record("T1-B", "Normal text: Medium/High complexity", NORMAL_TEXT[:40], "Medium or High", r1b.complexity_indicator, PASS if ok1b else FAIL)

r1c = analyze_text(COMPLEX_TEXT)
record("T1-C", "Complex text: High + long sentences", COMPLEX_TEXT[:40], "High, long>=1", "grade=" + str(r1c.flesch_kincaid_grade) + " long=" + str(len(r1c.long_sentences)), PASS if "High" in r1c.complexity_indicator and len(r1c.long_sentences) >= 1 else FAIL)

r1d = analyze_text(LONG_SENT)
record("T1-D", "Long sentence: detected", LONG_SENT[:40], "long_sentences>=1", "long_sentences=" + str(len(r1d.long_sentences)), PASS if len(r1d.long_sentences) >= 1 else FAIL)

r1e = analyze_text(COMPLEX_TEXT)
expected_diff = {"biochemical","photosynthesis","electromagnetic","chlorophyll","adenosine","triphosphate","nicotinamide","dinucleotide","phosphate"}
found1e = expected_diff & r1e.difficult_words
record("T1-E", "Complex vocab: difficult words flagged", ">=5 of technical set", "difficult words check", "found=" + str(len(found1e)) + " " + str(found1e), PASS if len(found1e) >= 5 else FAIL)

r1f_s = analyze_text(SIMPLE_TEXT)
r1f_c = analyze_text(COMPLEX_TEXT)
record("T1-F", "Grade monotonicity: complex > simple", "grade(complex)>grade(simple)", "monotonicity", "complex=" + str(r1f_c.flesch_kincaid_grade) + " simple=" + str(r1f_s.flesch_kincaid_grade), PASS if r1f_c.flesch_kincaid_grade > r1f_s.flesch_kincaid_grade else FAIL)
record("T1-G", "Flesch Ease: simple > complex", "ease(simple)>ease(complex)", "flesch ease", "simple=" + str(r1f_s.flesch_reading_ease) + " complex=" + str(r1f_c.flesch_reading_ease), PASS if r1f_s.flesch_reading_ease > r1f_c.flesch_reading_ease else FAIL)

# ── TEST 2: SUMMARY ──────────────────────────────────────────────────────
print("\n-- TEST 2: SUMMARY --")

res2 = run_dyslexia_pipeline(FACT_TEXT, std_proc)
record("T2-A", "Summary: generated (not None)", FACT_TEXT[:40], "summary not None/empty", repr(res2.summary), PASS if res2.summary else FAIL)
record("T2-B", "Summary: shorter than original", "len(summary)<len(original)", "length check", "orig=" + str(len(FACT_TEXT)) + " summ=" + str(len(res2.summary or "")), WARN if (res2.summary and len(res2.summary) >= len(FACT_TEXT)) else PASS, "Mock LLM may not shrink; real LLM needed")
record("T2-C", "Summary: original text separately preserved", "original preserved", "original preserved", "preserved=" + str(FACT_TEXT.strip() in res2.original_text), PASS if FACT_TEXT.strip() in res2.original_text else FAIL)
record("T2-D", "Fact preservation: numbers/names in summary", "Real LLM preserves facts", "No real LLM", "Cannot verify without real LLM", NT, "Requires real LLM")

# ── TEST 3: SIMPLIFICATION ───────────────────────────────────────────────
print("\n-- TEST 3: SIMPLIFICATION --")

res3 = run_dyslexia_pipeline(COMPLEX_TEXT, std_proc)
record("T3-A", "Simplification: text generated", COMPLEX_TEXT[:40], "simplified not None/empty", repr((res3.simplified_text or "")[:40]), PASS if res3.simplified_text else FAIL)
record("T3-B", "Simplification: original text unchanged", "original preserved", "original unchanged", "match=" + str(res3.original_text.strip() == COMPLEX_TEXT.strip()), PASS if res3.original_text.strip() == COMPLEX_TEXT.strip() else FAIL)
record("T3-C", "Simplification: meaning preservation", "Real LLM validates meaning", "No real LLM", "Cannot evaluate", NT, "Requires real LLM")
record("T3-D", "Simplification: no hallucinations", "Real LLM validates facts", "No real LLM", "Cannot evaluate", NT, "Requires real LLM")

# ── TEST 4: READABILITY ──────────────────────────────────────────────────
print("\n-- TEST 4: READABILITY --")

r4a = analyze_text("The cat sat.")
expected_ease = round(206.835 - 1.015 * (3 / 1) - 84.6 * (3 / 3), 2)
record("T4-A", "Flesch Ease spot-check", "expected~=" + str(expected_ease), "formula check", str(r4a.flesch_reading_ease), PASS if abs(r4a.flesch_reading_ease - expected_ease) < 5 else WARN, "Minor variation from syllable heuristic acceptable")

r4b = analyze_text(SIMPLE_TEXT)
record("T4-B", "Simple text: grade < 8", "grade < 8", "grade check", str(r4b.flesch_kincaid_grade), PASS if r4b.flesch_kincaid_grade < 8 else FAIL)

r4c = analyze_text(COMPLEX_TEXT)
record("T4-C", "Complex text: grade >= 12", "grade >= 12", "grade check", str(r4c.flesch_kincaid_grade), PASS if r4c.flesch_kincaid_grade >= 12 else FAIL)

r4d_before = analyze_text(COMPLEX_TEXT)
r4d_after  = analyze_text("Plants use sunlight to make food. This is called photosynthesis.")
record("T4-D", "Readability improves after simplification", "grade_after < grade_before", "improvement check", "before=" + str(r4d_before.flesch_kincaid_grade) + " after=" + str(r4d_after.flesch_kincaid_grade), PASS if r4d_after.flesch_kincaid_grade < r4d_before.flesch_kincaid_grade else FAIL)

# ── TEST 5: ITERATIVE REFINEMENT ─────────────────────────────────────────
print("\n-- TEST 5: ITERATIVE REFINEMENT --")

res5a = run_dyslexia_pipeline(SIMPLE_TEXT, std_proc)
record("T5-A", "Simple text: 0 refinements", "refinement_count=0", "refinement count", "refinement_count=" + str(res5a.refinement_count), PASS if res5a.refinement_count == 0 else WARN, "Depends on mock output grade")

res5b = run_dyslexia_pipeline(COMPLEX_TEXT, std_proc)
record("T5-B", "Complex text: refinement_required is bool", "bool", "type check", "refinement_required=" + str(res5b.refinement_required), PASS if isinstance(res5b.refinement_required, bool) else FAIL)

class AlwaysComplexMock:
    def generate(self, p):
        return ("The extraordinarily complex biochemical mechanism of photosynthesis involves "
                "the continuous phosphorylation of adenosine diphosphate by specialized "
                "transmembrane protein complexes embedded within the thylakoid membrane.")

always_proc = LLMProcessor(provider_func=AlwaysComplexMock().generate, model_config="AlwaysComplex")
res5c = run_dyslexia_pipeline(COMPLEX_TEXT, always_proc)
record("T5-C", "Max 2 iterations respected, no infinite loop", "refinement_count <= 2", "limit check", "refinement_count=" + str(res5c.refinement_count), PASS if res5c.refinement_count <= 2 else FAIL)

res5d = run_dyslexia_pipeline(COMPLEX_TEXT, exc_proc)
record("T5-D", "LLM exception: graceful error field set", "error set", "exception handling", "error='" + str(res5d.error) + "'", PASS if res5d.error and "LLM Generation Error" in res5d.error else FAIL)

# ── TEST 6: KEY TERMS ────────────────────────────────────────────────────
print("\n-- TEST 6: KEY TERMS --")

r6a = analyze_text("Mitochondria generate ATP. Mitochondria are the powerhouse of the cell. ATP fuels cellular respiration.")
record("T6-A", "Key terms: technical terms extracted", "mitochondria+atp in key_terms", "term check", str(r6a.key_terms), PASS if "mitochondria" in r6a.key_terms and "atp" in r6a.key_terms else FAIL)

stop_words = {"the","of","are","is","in","a","an","and","to"}
leaked = stop_words & set(r6a.key_terms)
record("T6-B", "Key terms: stop words excluded", "no stop words", "stop word check", "leaked=" + str(leaked), PASS if not leaked else FAIL)

record("T6-C", "Key terms: no duplicates", "unique list", "duplicate check", str(r6a.key_terms), PASS if len(r6a.key_terms) == len(set(r6a.key_terms)) else FAIL)

r6d = analyze_text("COVID-19 and DNA are studied in molecular biology labs.")
record("T6-D", "Key terms: abbreviations (dna)", "dna in key_terms", "abbreviation check", str(r6d.key_terms), PASS if "dna" in r6d.key_terms else WARN, "Depends on frequency threshold")

try:
    r6e = analyze_text("Biology")
    record("T6-E", "Key terms: single word no crash", "no exception", "crash check", "key_terms=" + str(r6e.key_terms), PASS)
except Exception as e:
    record("T6-E", "Key terms: single word no crash", "no exception", "crash check", str(e), FAIL)

r6f = analyze_text(COMPLEX_TEXT * 10)
record("T6-F", "Key terms: long text returns <=10 terms", "len<=10", "count check", "len=" + str(len(r6f.key_terms)), PASS if len(r6f.key_terms) <= 10 else FAIL)

# ── TEST 7: ACCESSIBILITY RULES ─────────────────────────────────────────
print("\n-- TEST 7: ACCESSIBILITY RULES --")

r7_orig  = analyze_text(NORMAL_TEXT)
r7_final = analyze_text("Plants use sunlight to make food. This is photosynthesis.")

mp = DyslexiaPipelineResult(
    original_text=NORMAL_TEXT,
    original_analysis=r7_orig,
    summary="Photosynthesis converts sunlight to glucose, sustaining life.",
    simplified_text="Plants use sunlight to make food. This is photosynthesis.",
    final_analysis=r7_final,
    difficult_terms=["photosynthesis","glucose"],
    refinement_count=1, refinement_required=True, error=None
)
segs = [TimestampedSegment(0.0, 3.0, "Photosynthesis..."), TimestampedSegment(3.0, 6.0, "...glucose")]
mi = IntegrationResult(
    unified_text="[Visual Description: A leaf absorbing sunlight.]\n\n" + NORMAL_TEXT,
    pipeline_result=mp, timestamps=segs
)

blind = get_accessibility_representation(UserProfile.BLIND,      mi)
deaf  = get_accessibility_representation(UserProfile.DEAF,       mi)
lv    = get_accessibility_representation(UserProfile.LOW_VISION, mi)
dys   = get_accessibility_representation(UserProfile.DYSLEXIA,  mi)

record("T7-A", "BLIND: primary_text=original", "NORMAL_TEXT", "primary_text check", blind.primary_text[:40], PASS if blind.primary_text == NORMAL_TEXT else FAIL)
record("T7-B", "BLIND: tts includes image description", "Image Description in tts", "tts check", str("Image Description" in (blind.tts_ready_text or "")), PASS if "Image Description" in (blind.tts_ready_text or "") else FAIL)
record("T7-C", "BLIND: summary available", "summary not None", "summary check", repr(blind.summary), PASS if blind.summary else FAIL)
record("T7-D", "DEAF: primary_text=original", "NORMAL_TEXT", "primary_text check", deaf.primary_text[:40], PASS if deaf.primary_text == NORMAL_TEXT else FAIL)
record("T7-E", "DEAF: timestamps preserved (2 segs)", "2 segments", "segment check", str(len(deaf.transcript_segments or [])) + " segments", PASS if deaf.transcript_segments and len(deaf.transcript_segments) == 2 else FAIL)
record("T7-F", "DEAF: has_synchronized_captions=True", "True", "caption metadata", str(deaf.metadata.get("has_synchronized_captions")), PASS if deaf.metadata.get("has_synchronized_captions") else FAIL)
record("T7-G", "LOW VISION: primary_text=original", "NORMAL_TEXT", "primary_text check", lv.primary_text[:40], PASS if lv.primary_text == NORMAL_TEXT else FAIL)
record("T7-H", "LOW VISION: tts_ready_text available", "tts not empty", "tts check", repr((lv.tts_ready_text or "")[:30]), PASS if lv.tts_ready_text else FAIL)
record("T7-I", "DYSLEXIA: primary_text=simplified", "simplified_text", "primary_text check", dys.primary_text[:40], PASS if dys.primary_text == mp.simplified_text else FAIL)
record("T7-J", "DYSLEXIA: tts=simplified", "simplified_text", "tts check", (dys.tts_ready_text or "")[:40], PASS if dys.tts_ready_text == mp.simplified_text else FAIL)
record("T7-K", "DYSLEXIA: difficult_terms in metadata", "list present", "metadata check", str(dys.metadata.get("difficult_terms_to_highlight")), PASS if dys.metadata.get("difficult_terms_to_highlight") else FAIL)
record("T7-L", "DYSLEXIA: readability grade in metadata", "float present", "grade metadata", str(dys.metadata.get("final_readability_grade")), PASS if dys.metadata.get("final_readability_grade") is not None else FAIL)
record("T7-M", "Profiles differ: BLIND != DYSLEXIA primary_text", "different", "separation check", "same" if blind.primary_text == dys.primary_text else "different", PASS if blind.primary_text != dys.primary_text else FAIL)

# ── TEST 8: NLP/LLM EVALUATION ─────────────────────────────────────────
print("\n-- TEST 8: NLP/LLM EVALUATION --")
record("T8-A", "Factual accuracy",      "Real LLM", "N/A", "No real LLM", NT)
record("T8-B", "Hallucination",         "Real LLM", "N/A", "No real LLM", NT)
record("T8-C", "Meaning preservation",  "Real LLM", "N/A", "No real LLM", NT)
record("T8-D", "Summary quality",       "Real LLM", "N/A", "No real LLM", NT)
record("T8-E", "Simplification quality","Real LLM", "N/A", "No real LLM", NT)

# ── ROBUSTNESS ───────────────────────────────────────────────────────────
print("\n-- ROBUSTNESS TESTS --")

rob_cases = [
    ("R01", "Empty input",            ""),
    ("R02", "Whitespace-only",        "     "),
    ("R03", "One sentence",           "The mitochondria is the powerhouse of the cell."),
    ("R04", "Numbers only",           "1234 5678 91011"),
    ("R05", "Symbols/Unicode",        "alpha beta gamma C water"),
    ("R06", "Repeated text",          (NORMAL_TEXT + " ") * 5),
    ("R07", "Already simple text",    "Cats play. Dogs run."),
    ("R08", "Extremely complex text", COMPLEX_TEXT * 3),
]
for rid, rname, rtext in rob_cases:
    try:
        run_member3_pipeline(UnifiedInput(text=rtext), std_proc)
        record(rid, "Robustness: " + rname, rtext[:20], "no crash", "completed", PASS)
    except Exception as e:
        record(rid, "Robustness: " + rname, rtext[:20], "no crash", str(e)[:80], FAIL)

try:
    res_emp = run_dyslexia_pipeline(NORMAL_TEXT, emp_proc)
    record("R09", "Empty LLM response: graceful", "no crash", "empty response", repr((res_emp.simplified_text or "")[:30]), PASS if res_emp is not None else FAIL)
except Exception as e:
    record("R09", "Empty LLM response: graceful", "no crash", "empty response", str(e)[:80], FAIL)

try:
    res_ex = run_dyslexia_pipeline(NORMAL_TEXT, exc_proc)
    record("R10", "LLM exception: graceful", "error set", "exception", "error='" + str(res_ex.error) + "'", PASS if res_ex.error else FAIL)
except Exception as e:
    record("R10", "LLM exception: graceful", "no crash", "exception", str(e)[:80], FAIL)

rr1 = analyze_text(NORMAL_TEXT)
rr2 = analyze_text(NORMAL_TEXT)
record("R11", "Repeated analysis: deterministic", "same grade", "determinism", str(rr1.flesch_kincaid_grade) + " vs " + str(rr2.flesch_kincaid_grade), PASS if rr1.flesch_kincaid_grade == rr2.flesch_kincaid_grade else FAIL)

try:
    run_dyslexia_pipeline(NORMAL_TEXT, garbage_proc)
    record("R12", "Malformed LLM output: no crash", "no exception", "garbage output", "completed", PASS)
except Exception as e:
    record("R12", "Malformed LLM output: no crash", "no exception", "garbage output", str(e)[:80], FAIL)

# ── FINAL REPORT ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
passed = sum(1 for r in results if r[2] == PASS)
failed = sum(1 for r in results if r[2] == FAIL)
warned = sum(1 for r in results if r[2] == WARN)
nt_ct  = sum(1 for r in results if r[2] == NT)
total  = len(results)

print("Total tests          : " + str(total))
print("Passed               : " + str(passed))
print("Failed               : " + str(failed))
print("Warnings             : " + str(warned))
print("LLM tests run        : 0  (mock only)")
print("LLM tests not tested : " + str(nt_ct))

if any(r[2] == FAIL for r in results):
    print("\nFAILED TESTS:")
    for r in results:
        if r[2] == FAIL:
            print("  " + r[0] + " -- " + r[1] + ": " + r[3])

if any(r[2] == WARN for r in results):
    print("\nWARNING TESTS:")
    for r in results:
        if r[2] == WARN:
            print("  " + r[0] + " -- " + r[1] + ": " + r[3])
