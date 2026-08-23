from evaluation.gpu_run5_structure import classify_formula


def test_variable_denominator_and_rational_are_distinct():
    sigmoid = classify_formula("1/(1+exp(x_0))")
    assert sigmoid["variable_denominator_form"]
    assert not sigmoid["algebraically_rational"]
    assert sigmoid["sigmoid_saturating_form"]

    polynomial = classify_formula("x_0**2 + 1")
    assert polynomial["algebraically_rational"]
    assert not polynomial["rational_with_variable_denominator"]


def test_strict_hill_and_exponent_aware_skeleton():
    n2 = classify_formula("2*x_0**2/(1+x_0**2) - 0.5*x_0")
    n4 = classify_formula("2*x_0**4/(1+x_0**4) - 0.5*x_0")
    assert n2["hill_form"] and n4["hill_form"]
    assert n2["exponent_aware_skeleton"] != n4["exponent_aware_skeleton"]
    assert not classify_formula("sin(x_0)/(1+x_0**2)")["hill_form"]
    modulated = classify_formula("x_1*x_0**2/(1+x_0**2)")
    assert not modulated["hill_form"]
    assert modulated["modulated_hill_form"]


def test_sigmoid_requires_constant_numerator_and_affine_exponent():
    assert classify_formula("2/(1+exp(3*x_0+1))")["sigmoid_saturating_form"]
    assert not classify_formula("x_0/(1+exp(x_0)+sin(x_0))")["sigmoid_saturating_form"]


def test_cot_counts_as_variable_denominator_after_canonicalization():
    flags = classify_formula("cot(x_0)")
    assert flags["variable_denominator_form"]
    assert not flags["algebraically_rational"]
