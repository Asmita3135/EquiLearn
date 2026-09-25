from text_analysis import correct_ocr_token, analyze_text
import re

def test_ocr(input_str):
    normalized = correct_ocr_token(input_str)
    return f"{input_str} -> {normalized}"

# 1
print("--- Test 1 ---")
print(test_ocr("Ph0t0synthesis"))
print(test_ocr("chl0roplast"))
print(test_ocr("ph0t0synthesis"))

# 2
print("\n--- Test 2 ---")
res2 = analyze_text("Ph0t0synthesis occurs in the chl0roplast. Chlor0phyll absorbs light.")
print("Original:", res2.total_words, "words") # Just to show it parsed
print("Key Terms:", res2.key_terms)
print("Original text preserved:", "Ph0t0synthesis" in res2.key_terms) # should be False

# 3
print("\n--- Test 3 ---")
res3 = analyze_text("Photosynthesis occurs in the chloroplast.")
print("Key Terms:", res3.key_terms)

# 4
print("\n--- Test 4 ---")
for t in ["nnU-Net", "U-Net", "3D", "CO2", "H2O", "B12"]:
    print(test_ocr(t))

# 5
print("\n--- Test 5 ---")
print(test_ocr("garb1ed3"))

# 6 & 7 can be inferred from the output of Test 2.
