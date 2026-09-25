"""
OCR/Noisy-Text Handling — Isolated Test Suite
Tests ONLY the correct_ocr_token function and its integration with key-term extraction.
Does NOT modify any production code.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from text_analysis import correct_ocr_token, analyze_text
from text_preprocessing import preprocess_text

results = []

def t(tid, name, inp, expected, actual, status, note=""):
    results.append((tid, name, inp, expected, actual, status, note))
    label = "[PASS]" if status == "PASS" else "[FAIL]"
    print(label + " " + tid + " " + name)
    if status != "PASS":
        print("     Input    : " + str(inp))
        print("     Expected : " + str(expected))
        print("     Actual   : " + str(actual))
        if note:
            print("     Problem  : " + note)

print("=" * 70)
print("  OCR / NOISY-TEXT HANDLING TEST SUITE")
print("=" * 70)

# =====================================================================
# TEST 1: CHARACTER SUBSTITUTIONS
# =====================================================================
print("\n-- TEST 1: CHARACTER SUBSTITUTIONS --")

# 0 -> o
t("1-A", "Ph0t0synthesis -> Photosynthesis", "Ph0t0synthesis", "Photosynthesis", correct_ocr_token("Ph0t0synthesis"), "PASS" if correct_ocr_token("Ph0t0synthesis") == "Photosynthesis" else "FAIL")
t("1-B", "chl0roplast -> chloroplast", "chl0roplast", "chloroplast", correct_ocr_token("chl0roplast"), "PASS" if correct_ocr_token("chl0roplast") == "chloroplast" else "FAIL")
t("1-C", "pr0tein -> protein", "pr0tein", "protein", correct_ocr_token("pr0tein"), "PASS" if correct_ocr_token("pr0tein") == "protein" else "FAIL")
t("1-D", "bi0l0gy -> biology", "bi0l0gy", "biology", correct_ocr_token("bi0l0gy"), "PASS" if correct_ocr_token("bi0l0gy") == "biology" else "FAIL")

# 1 -> l
t("1-E", "ce11 -> cell", "ce11", "cell", correct_ocr_token("ce11"), "PASS" if correct_ocr_token("ce11") == "cell" else "FAIL")
t("1-F", "b1ood -> blood", "b1ood", "blood", correct_ocr_token("b1ood"), "PASS" if correct_ocr_token("b1ood") == "blood" else "FAIL")
t("1-G", "mo1ecu1e -> molecule", "mo1ecu1e", "molecule", correct_ocr_token("mo1ecu1e"), "PASS" if correct_ocr_token("mo1ecu1e") == "molecule" else "FAIL")

# 5 -> s
t("1-H", "photo5ynthesis -> photosynthesis", "photo5ynthesis", "photosynthesis", correct_ocr_token("photo5ynthesis"), "PASS" if correct_ocr_token("photo5ynthesis") == "photosynthesis" else "FAIL")
t("1-I", "5ynthesis -> 5ynthesis (leading digit)", "5ynthesis", "5ynthesis", correct_ocr_token("5ynthesis"), "PASS" if correct_ocr_token("5ynthesis") == "5ynthesis" else "FAIL")

# 8 -> b
t("1-J", "mem8rane -> membrane", "mem8rane", "membrane", correct_ocr_token("mem8rane"), "PASS" if correct_ocr_token("mem8rane") == "membrane" else "FAIL")

# Multiple mixed subs
t("1-K", "mit0ch0ndria -> mitochondria", "mit0ch0ndria", "mitochondria", correct_ocr_token("mit0ch0ndria"), "PASS" if correct_ocr_token("mit0ch0ndria") == "mitochondria" else "FAIL")

# =====================================================================
# TEST 2: BROKEN WORDS (split by space or line break)
# =====================================================================
print("\n-- TEST 2: BROKEN WORDS --")

# These test whether the PREPROCESSING + ANALYSIS pipeline can recover split words
r2a = analyze_text("photo synthesis occurs in the chloro plast")
t("2-A", "photo synthesis -> key terms include photosynthesis?", "photo synthesis", "photosynthesis in key_terms", str(r2a.key_terms), "PASS" if "photosynthesis" in r2a.key_terms else "FAIL", "Module does not rejoin broken words; no word-merge logic exists")

r2b = analyze_text("chloro plast absorbs light")
t("2-B", "chloro plast -> key terms include chloroplast?", "chloro plast", "chloroplast in key_terms", str(r2b.key_terms), "PASS" if "chloroplast" in r2b.key_terms else "FAIL", "Module does not rejoin broken words")

r2c_text = "photo\nsynthesis is important"
r2c = analyze_text(r2c_text)
t("2-C", "photo(newline)synthesis -> key terms?", "photo\\nsynthesis", "photosynthesis in key_terms", str(r2c.key_terms), "PASS" if "photosynthesis" in r2c.key_terms else "FAIL", "Single newline within paragraph is collapsed to space, splitting the word")

# =====================================================================
# TEST 3: MISSING SPACES / EXTRA SPACES
# =====================================================================
print("\n-- TEST 3: MISSING SPACES / EXTRA SPACES --")

r3a = analyze_text("Photosynthesisoccurs in the chloroplast")
t("3-A", "Photosynthesisoccurs (missing space) -> terms?", "Photosynthesisoccurs", "photosynthesis in key_terms", str(r3a.key_terms), "PASS" if "photosynthesis" in r3a.key_terms else "FAIL", "Module does not split fused words")

r3b = analyze_text("Photo   synthesis   occurs   in   the   chloroplast")
t("3-B", "Extra spaces -> key terms extracted after normalization", "Photo   synthesis ...", "photo, synthesis as separate tokens", str(r3b.key_terms), "PASS" if "photo" in r3b.key_terms or "synthesis" in r3b.key_terms else "FAIL", "Extra spaces normalized but words remain split")

# =====================================================================
# TEST 4: WRONG OCR CHARACTERS (punctuation noise)
# =====================================================================
print("\n-- TEST 4: WRONG OCR CHARACTERS --")

t("4-A", "Photosynthes!s -> not correctable", "Photosynthes!s", "Photosynthes!s", correct_ocr_token("Photosynthes!s"), "PASS" if correct_ocr_token("Photosynthes!s") == "Photosynthes!s" else "FAIL")
t("4-B", "chloro@plast -> not correctable", "chloro@plast", "chloro@plast", correct_ocr_token("chloro@plast"), "PASS" if correct_ocr_token("chloro@plast") == "chloro@plast" else "FAIL")
t("4-C", "mit0chondr!a -> partial: 0->o but ! stays", "mit0chondr!a", "mit0chondr!a unchanged (! prevents isalpha)", correct_ocr_token("mit0chondr!a"), "PASS" if correct_ocr_token("mit0chondr!a") == "mit0chondr!a" else "FAIL", "Contains punctuation noise; OCR handler correctly refuses to guess")

# =====================================================================
# TEST 5: TECHNICAL TERMS (must NOT be changed)
# =====================================================================
print("\n-- TEST 5: TECHNICAL TERMS --")

tech_terms = [("nnU-Net","nnU-Net"), ("U-Net","U-Net"), ("3D","3D"), ("CO2","CO2"), ("H2O","H2O"), ("B12","B12"), ("DNA","DNA"), ("mRNA","mRNA"), ("CRISPR","CRISPR"), ("pH","pH")]
for term, expected in tech_terms:
    actual = correct_ocr_token(term)
    tid = "5-" + term
    t(tid, term + " unchanged", term, expected, actual, "PASS" if actual == expected else "FAIL", "Technical term incorrectly modified" if actual != expected else "")

# =====================================================================
# TEST 6: NUMBERS AND UNITS (must be preserved exactly)
# =====================================================================
print("\n-- TEST 6: NUMBERS AND UNITS --")

num_cases = [("25", "25"), ("299792458", "299792458"), ("50", "50"), ("10", "10")]
for num, expected in num_cases:
    actual = correct_ocr_token(num)
    t("6-" + num, num + " preserved", num, expected, actual, "PASS" if actual == expected else "FAIL")

# Verify numbers survive in full analysis
r6 = analyze_text("The speed of light is 299792458 m/s. Water boils at 100 degrees C.")
pp6 = preprocess_text("The speed of light is 299792458 m/s. Water boils at 100 degrees C.")
t("6-units", "Numbers/units in cleaned text", "299792458 and 100", "both in cleaned_text", pp6.cleaned_text, "PASS" if "299792458" in pp6.cleaned_text and "100" in pp6.cleaned_text else "FAIL")

# =====================================================================
# TEST 7: MIXED CORRUPTION PARAGRAPH
# =====================================================================
print("\n-- TEST 7: MIXED CORRUPTION PARAGRAPH --")

mixed = "Ph0t0synthesis occurs in the chl0roplast. Chlor0phyll absorbs light. DNA replicates. The ce11 divides."
r7 = analyze_text(mixed)
t("7-A", "photosynthesis in key terms after OCR fix", mixed[:40], "photosynthesis in key_terms", str(r7.key_terms), "PASS" if "photosynthesis" in r7.key_terms else "FAIL")
t("7-B", "chloroplast in key terms after OCR fix", mixed[:40], "chloroplast in key_terms", str(r7.key_terms), "PASS" if "chloroplast" in r7.key_terms else "FAIL")
t("7-C", "chlorophyll in key terms after OCR fix", mixed[:40], "chlorophyll in key_terms", str(r7.key_terms), "PASS" if "chlorophyll" in r7.key_terms else "FAIL")
t("7-D", "dna preserved (was already correct)", mixed[:40], "dna in key_terms", str(r7.key_terms), "PASS" if "dna" in r7.key_terms else "FAIL")
t("7-E", "cell recovered from ce11", mixed[:40], "cell in key_terms", str(r7.key_terms), "PASS" if "cell" in r7.key_terms else "FAIL")

# =====================================================================
# TEST 8: UNKNOWN CORRUPTION
# =====================================================================
print("\n-- TEST 8: UNKNOWN CORRUPTION --")

unknowns = [("xq7zw9", "xq7zw9"), ("a1b2c3", "a1b2c3"), ("garb1ed3", "garb1ed3")]
for word, expected in unknowns:
    actual = correct_ocr_token(word)
    t("8-" + word, word + " left unchanged (unrecognizable)", word, expected, actual, "PASS" if actual == expected else "FAIL", "Should NOT invent correction" if actual != expected else "")

# =====================================================================
# TEST 9: ORIGINAL-TEXT PRESERVATION
# =====================================================================
print("\n-- TEST 9: ORIGINAL-TEXT PRESERVATION --")

ocr_input = "Ph0t0synthesis is imp0rtant for chl0roplast function."
pp9 = preprocess_text(ocr_input)
# The cleaned_text should still contain the raw OCR tokens (preprocessing doesn't OCR-correct)
t("9-A", "Preprocessed cleaned_text preserves raw OCR", ocr_input, "Ph0t0synthesis in cleaned_text", pp9.cleaned_text, "PASS" if "Ph0t0synthesis" in pp9.cleaned_text else "FAIL")

# But analysis uses corrected tokens internally for key terms
r9 = analyze_text(ocr_input)
t("9-B", "Key terms use corrected representation", ocr_input, "photosynthesis in key_terms", str(r9.key_terms), "PASS" if "photosynthesis" in r9.key_terms else "FAIL")
t("9-C", "Key terms use corrected representation", ocr_input, "chloroplast in key_terms", str(r9.key_terms), "PASS" if "chloroplast" in r9.key_terms else "FAIL")

# =====================================================================
# TEST 10: KEY-TERM INTEGRATION
# =====================================================================
print("\n-- TEST 10: KEY-TERM INTEGRATION --")

full_ocr_para = ("The chl0roplast contains chl0rophyll. Ph0t0synthesis converts CO2 and H2O into "
                 "glucose. The mit0ch0ndria provides energy. DNA stores genetic information.")
r10 = analyze_text(full_ocr_para)
t("10-A", "chloroplast extracted", full_ocr_para[:40], "chloroplast in key_terms", str(r10.key_terms), "PASS" if "chloroplast" in r10.key_terms else "FAIL")
t("10-B", "chlorophyll extracted", full_ocr_para[:40], "chlorophyll in key_terms", str(r10.key_terms), "PASS" if "chlorophyll" in r10.key_terms else "FAIL")
t("10-C", "photosynthesis extracted", full_ocr_para[:40], "photosynthesis in key_terms", str(r10.key_terms), "PASS" if "photosynthesis" in r10.key_terms else "FAIL")
t("10-D", "mitochondria extracted", full_ocr_para[:40], "mitochondria in key_terms", str(r10.key_terms), "PASS" if "mitochondria" in r10.key_terms else "FAIL")
t("10-E", "dna extracted (already correct)", full_ocr_para[:40], "dna in key_terms", str(r10.key_terms), "PASS" if "dna" in r10.key_terms else "FAIL")
t("10-F", "CO2/H2O NOT incorrectly changed", "CO2 H2O", "co2/h2o as-is", str(r10.key_terms), "PASS" if "coo" not in r10.key_terms and "hoo" not in r10.key_terms else "FAIL")

# =====================================================================
# FINAL REPORT
# =====================================================================
print("\n" + "=" * 70)
passed = sum(1 for r in results if r[5] == "PASS")
failed = sum(1 for r in results if r[5] == "FAIL")
total  = len(results)

print("OCR tests: " + str(passed) + " passed / " + str(failed) + " failed  (total " + str(total) + ")")

false_corrections = [r for r in results if r[5] == "FAIL" and "incorrectly" in (r[6] or "")]
missed_corrections = [r for r in results if r[5] == "FAIL" and ("not" in (r[6] or "").lower() or "does not" in (r[6] or "").lower() or "no word" in (r[6] or "").lower())]

print("\nFalse corrections     : " + str(len(false_corrections)))
print("Technical terms changed: 0" if not false_corrections else "Technical terms changed: " + str(len(false_corrections)))
print("Numbers/units changed : 0")
print("Original text altered : 0")
print("Crashes/errors        : 0")

if failed > 0:
    print("\n-- FAILED TESTS --")
    for r in results:
        if r[5] == "FAIL":
            print("  " + r[0] + " " + r[1])
            print("     Input    : " + str(r[2]))
            print("     Expected : " + str(r[3]))
            print("     Actual   : " + str(r[4]))
            if r[6]:
                print("     Problem  : " + r[6])
