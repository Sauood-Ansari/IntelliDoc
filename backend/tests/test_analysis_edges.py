import ast
from app.core.parser import ASTCodebaseParser
from app.core.drift_detector import DriftDetector
from app.core.docstring_parser import GoogleDocstringParser
from app.services.scoring_service import ScoringService

def parse(source):
    return ASTCodebaseParser._extract_functions_from_tree(ast.parse(source), source)

def test_nested_return_not_counted_for_outer():
    functions=parse('def outer():\n    """Outer."""\n    def inner():\n        return 1\n')
    assert not functions[0].has_return_value
    assert functions[1].has_return_value
    assert functions[1].qualified_name=="outer.inner"
    assert DriftDetector.analyze_function(functions[0])==[]

def test_signature_and_receiver_scope():
    f=parse('class A:\n    @staticmethod\n    def f(self, /, x: int=1, *, option=True, **kw):\n        """Summary."""\n        pass\n    def g(this):\n        def h(self): pass\n')[0]
    assert f.parameters==["self","x","option","**kw"]
    assert f.receiver is None
    assert "/" in f.signature and "x: int=1" in f.signature
    methods=parse('class A:\n    def g(this):\n        def h(self): pass\n')
    assert methods[0].receiver=="this"
    assert methods[1].receiver is None

def test_generator_yields_not_returns():
    f=parse('def values():\n    """Values.\n\n    Yields:\n        int: Each value.\n    """\n    yield 1\n')[0]
    assert f.is_generator
    assert DriftDetector.analyze_function(f)==[]

def test_no_false_positive_for_returns_none():
    f=parse('def run():\n    """Run.\n\n    Returns:\n        None: No result.\n    """\n    return None')[0]
    assert DriftDetector.analyze_function(f)==[]

def test_docstring_unknown_section_and_nested_colon():
    doc=GoogleDocstringParser.parse('Summary.\n\nArgs:\n    x: Input.\n        Note: this is a continuation.\n    y: Other.\nExamples:\n    fake: not a parameter\nReturns:\n    int: result\nNotes:\n    other text')
    assert set(doc.args)=={"x","y"}
    assert doc.returns=="int: result"

def test_empty_and_missing_scoring():
    assert ScoringService.calculate_drs(0,0)["documentation_score"] is None
    missing=DriftDetector.analyze_function(parse("def f(): pass")[0])
    score=ScoringService.calculate_drs(2,1,findings=missing)
    assert score["documentation_score"]==50
    assert score["breakdown"]["parameter_consistency"]==20

def test_parameter_penalties_cannot_erase_return_component():
    from app.core.drift_detector import DriftFinding
    findings=[DriftFinding("Missing Parameter Documentation","Medium","x")]*100
    score=ScoringService.calculate_drs(1,1,findings=findings)
    assert score["documentation_score"]==60

