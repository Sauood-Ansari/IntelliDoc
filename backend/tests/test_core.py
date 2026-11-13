import ast
from app.core.docstring_parser import GoogleDocstringParser
from app.core.parser import ASTCodebaseParser, ExtractedFunction
from app.core.drift_detector import DriftDetector


def test_google_docstring_parser():
    doc = """
    Calculate the total price.

    Args:
        price (float): Base price.
        tax (float): Tax percentage.

    Returns:
        float: Total price including tax.
    """
    parsed = GoogleDocstringParser.parse(doc)
    assert parsed is not None
    assert "Calculate the total price" in parsed.summary
    assert "price" in parsed.args
    assert "tax" in parsed.args
    assert "Total price" in parsed.returns


def test_ast_parser_extract_function():
    code = """
def add_numbers(a, b=10):
    '''Add two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Sum of a and b.
    '''
    return a + b
"""
    tree = ast.parse(code)
    funcs = ASTCodebaseParser._extract_functions_from_tree(tree)
    assert len(funcs) == 1
    f = funcs[0]
    assert f.name == "add_numbers"
    assert f.parameters == ["a", "b"]
    assert f.has_return_value is True
    assert f.docstring is not None


def test_drift_detector_clean_function():
    # T-07: All parameters documented properly
    f = ExtractedFunction(
        name="calc",
        line_number=1,
        signature="def calc(x, y)",
        parameters=["x", "y"],
        docstring="""Compute values.
        Args:
            x: First arg.
            y: Second arg.
        Returns:
            Result.
        """,
        has_return_value=True
    )
    findings = DriftDetector.analyze_function(f)
    assert len(findings) == 0


def test_drift_detector_missing_parameter():
    # T-08 & Appendix D Example 1: Function has 'tax', docstring omits it
    f = ExtractedFunction(
        name="calculate_total",
        line_number=1,
        signature="def calculate_total(price, tax)",
        parameters=["price", "tax"],
        docstring="""Calculate the total price.
        Args:
            price: Base price.
        Returns:
            Total price including tax.
        """,
        has_return_value=True
    )
    findings = DriftDetector.analyze_function(f)
    assert len(findings) == 1
    assert findings[0].type == "Missing Parameter Documentation"
    assert "tax" in findings[0].explanation


def test_drift_detector_obsolete_parameter():
    # T-09 & Appendix D Example 2: Docstring documents 'discount' which is absent
    f = ExtractedFunction(
        name="calculate_total",
        line_number=1,
        signature="def calculate_total(price, tax)",
        parameters=["price", "tax"],
        docstring="""Calculate the total price.
        Args:
            price: Base price.
            tax: Tax rate.
            discount: Obsolete discount.
        Returns:
            Total.
        """,
        has_return_value=True
    )
    findings = DriftDetector.analyze_function(f)
    assert len(findings) == 1
    assert findings[0].type == "Obsolete Parameter Documentation"
    assert "discount" in findings[0].explanation


def test_drift_detector_missing_documentation():
    # T-11 & Appendix D Example 3: Function has no docstring
    f = ExtractedFunction(
        name="undocumented_fn",
        line_number=10,
        signature="def undocumented_fn(val)",
        parameters=["val"],
        docstring=None,
        has_return_value=False
    )
    findings = DriftDetector.analyze_function(f)
    assert len(findings) == 1
    assert findings[0].type == "Missing Documentation"
    assert findings[0].severity == "High"

