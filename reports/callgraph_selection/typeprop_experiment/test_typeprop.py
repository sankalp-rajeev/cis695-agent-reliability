"""All snippets are AST data: never imported or executed."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[2] / 'src')]
from typeprop_graph import TypeGraph, TypeAmendedGraph, MAX_ROUNDS

ORDER = 'class Order:\n def save(self): pass\n'
USER = 'class User:\n def save(self): pass\n'


def graph(tmp_path, source, files=None, cls=TypeGraph):
    for path, text in {'a.py': source, **(files or {})}.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    g = cls().build(tmp_path)
    assert g.status == 'complete'
    assert len(g.calls) == len(g.call_details) == len(g.edges) == g.counts['call_sites']
    for before, after in zip(g.baseline_edges, g.edges):
        if before['status'] == 'resolved':
            assert after['status'] == 'resolved' and after['targets'] == before['targets']
    return g


def saves(g, expression='obj.save'):
    return [e for e in g.edges if e['expression'] == expression]


def test_local_constructor(tmp_path):
    g = graph(tmp_path, ORDER + 'def f():\n x = Order()\n x.save()\n')
    e, = saves(g, 'x.save')
    assert e['status'] == 'resolved' and e['provenance'] == 'local_constructor'
    assert g.nodes[e['targets'][0]]['qualname'] == 'Order.save'


@pytest.mark.parametrize('argument', ['x', 'Order()'])
def test_caller_and_direct_constructor(tmp_path, argument):
    g = graph(tmp_path, ORDER + f'def process(obj):\n obj.save()\ndef caller():\n x = Order()\n process({argument})\n')
    e, = saves(g)
    assert e['status'] == 'resolved' and e['provenance'] == 'caller_parameter'
    assert any(r['evidence'].get('incoming') for r in g.fact_records() if r['name'] == 'obj')


def test_multiple_types_and_same_named_methods(tmp_path):
    g = graph(tmp_path, ORDER + USER + 'def process(obj):\n obj.save()\ndef caller():\n process(Order())\n process(User())\n')
    e, = saves(g)
    assert e['status'] == 'ambiguous' and len(e['targets']) == len(e['receiver_types']) == 2


def test_duplicate_type_is_one(tmp_path):
    g = graph(tmp_path, ORDER + 'def process(obj):\n obj.save()\ndef caller():\n process(Order())\n process(Order())\n')
    e, = saves(g)
    assert e['status'] == 'resolved' and len(e['receiver_types']) == 1


@pytest.mark.parametrize('known', ['', ' process(Order())\n'])
def test_unknown_argument_taints_known_evidence(tmp_path, known):
    g = graph(tmp_path, ORDER + 'def process(obj):\n obj.save()\ndef outer(x):\n process(x)\n' + known)
    assert saves(g)[0]['status'] == 'unresolved'


@pytest.mark.parametrize('body', [
    ' x = Order()\n x = unknown\n x.save()\n',
    ' if condition:\n  x = Order()\n else:\n  x = User()\n x.save()\n',
    ' x.save()\n x = Order()\n',
    ' x = factory()\n x.save()\n',
    ' x = Order()\n del x\n x.save()\n',
    ' x = y = Order()\n x.save()\n',
    ' x, y = Order(), Order()\n x.save()\n',
    ' x = Order()\n x += unknown\n x.save()\n',
    ' x = Order(); x.save()\n',
])
def test_unsafe_local_stays_unknown(tmp_path, body):
    g = graph(tmp_path, ORDER + USER + 'def f():\n' + body)
    assert saves(g, 'x.save')[0]['status'] != 'resolved'


@pytest.mark.parametrize('import_line, constructor', [
    ('from pkg.api import Order', 'Order'),
    ('from pkg.api import Order as O', 'O'),
    ('import pkg.api as api', 'api.Order'),
])
def test_imported_alias_constructor(tmp_path, import_line, constructor):
    g = graph(tmp_path, import_line + f'\ndef f():\n x = {constructor}()\n x.save()\n', {'pkg/api.py': ORDER})
    assert saves(g, 'x.save')[0]['status'] == 'resolved'


def test_existing_direct_and_self_preserved(tmp_path):
    g = graph(tmp_path, 'def work(): pass\nclass A:\n def m(self): pass\n def f(self):\n  self.m()\n  work()\n')
    assert [e['status'] for e in g.edges] == ['resolved', 'resolved']
    assert all(e['provenance'] == 'existing_static_resolution' for e in g.edges)


def test_transitive(tmp_path):
    g = graph(tmp_path, ORDER + 'def a(x):\n b(x)\ndef b(obj):\n obj.save()\ndef caller():\n a(Order())\n')
    assert saves(g)[0]['status'] == 'resolved'
    assert saves(g)[0]['provenance'] == 'caller_parameter_transitive'


@pytest.mark.parametrize('functions', [
    'def a(obj):\n a(obj)\n obj.save()\n',
    'def a(obj):\n b(obj)\n obj.save()\ndef b(y):\n a(y)\n',
])
def test_recursion_terminates(tmp_path, functions):
    g = graph(tmp_path, ORDER + functions + 'def caller():\n a(Order())\n')
    assert g.type_metrics['converged'] and g.type_metrics['rounds'] <= MAX_ROUNDS
    assert saves(g)[0]['status'] == 'resolved'


def test_sourceless_cycle_cannot_invent_type(tmp_path):
    g = graph(tmp_path, 'def a(obj):\n b(obj)\n obj.save()\ndef b(x):\n a(x)\n')
    assert saves(g)[0]['status'] == 'unresolved'


@pytest.mark.parametrize('decl', [
    'class Order(Base):\n def save(self): pass\n',
    'class Order:\n def __getattr__(self, name): pass\n def save(self): pass\n',
    'class Order:\n def __getattribute__(self, name): pass\n def save(self): pass\n',
    'class Order:\n def __new__(cls): return unknown\n def save(self): pass\n',
    '@decorator\nclass Order:\n def save(self): pass\n',
    'class Order(metaclass=Meta):\n def save(self): pass\n',
    'class Order:\n @decorator\n def save(self): pass\n',
    'class Base:\n def save(self): pass\nclass Order(Base): pass\n',
])
def test_dynamic_inherited_decorated_classes(tmp_path, decl):
    g = graph(tmp_path, decl + 'def f():\n x = Order()\n x.save()\n')
    assert saves(g, 'x.save')[0]['status'] != 'resolved'


@pytest.mark.parametrize('call', ['process(obj=Order())', 'process(Order())'])
def test_keyword_mapping(tmp_path, call):
    g = graph(tmp_path, ORDER + f'def process(obj):\n obj.save()\ndef caller():\n {call}\n')
    assert saves(g)[0]['status'] == 'resolved'


@pytest.mark.parametrize('signature, call', [
    ('obj=None', 'process(Order())'), ('obj, *args', 'process(Order())'),
    ('obj, **kwargs', 'process(Order())'), ('obj', 'process(*values)'),
    ('obj', 'process(**values)'), ('obj', 'process()'),
    ('obj, /', 'process(obj=Order())'),
])
def test_defaults_and_variadics_stay_unknown(tmp_path, signature, call):
    g = graph(tmp_path, ORDER + f'def process({signature}):\n obj.save()\ndef caller():\n {call}\n')
    assert saves(g)[0]['status'] == 'unresolved'


def test_keyword_only(tmp_path):
    g = graph(tmp_path, ORDER + 'def process(*, obj):\n obj.save()\ndef caller():\n process(obj=Order())\n')
    assert saves(g)[0]['status'] == 'resolved'


def test_bound_self_mapping(tmp_path):
    g = graph(tmp_path, ORDER + 'class Helper:\n def process(self, obj):\n  obj.save()\n def caller(self):\n  self.process(Order())\n')
    assert saves(g)[0]['status'] == 'resolved'


def test_parameter_reassignment(tmp_path):
    g = graph(tmp_path, ORDER + 'def process(obj):\n obj = other\n obj.save()\ndef caller():\n process(Order())\n')
    assert saves(g)[0]['status'] == 'unresolved'


@pytest.mark.parametrize('extra', ['callback = process\n', 'def escape():\n return process\n'])
def test_escaped_function_blocks_confident_parameters(tmp_path, extra):
    g = graph(tmp_path, ORDER + 'def process(obj):\n obj.save()\ndef caller():\n process(Order())\n' + extra)
    assert saves(g)[0]['status'] == 'unresolved'


@pytest.mark.parametrize('extra', [
    ' x.save = callback\n', ' setattr(x, "save", callback)\n',
    ' x.__class__ = User\n', ' exec(code)\n',
])
def test_mutation_and_reflection(tmp_path, extra):
    g = graph(tmp_path, ORDER + 'def f():\n x = Order()\n' + extra + ' x.save()\n')
    assert saves(g, 'x.save')[0]['status'] == 'unresolved'


def test_unsupported_caller_taints_parameter(tmp_path):
    g = graph(tmp_path, ORDER + 'def process(obj):\n obj.save()\ndef caller():\n process(Order())\n [process(x) for x in values]\n')
    assert saves(g)[0]['status'] == 'unresolved'


def test_global_and_star_import(tmp_path):
    g = graph(tmp_path, ORDER + 'from unknown import *\ndef f():\n global x\n x = Order()\n x.save()\n')
    assert saves(g, 'x.save')[0]['status'] == 'unresolved'


def test_amended_wrapper_and_resource_stop(tmp_path):
    g = graph(tmp_path, ORDER + 'def f():\n x = Order()\n x.save()\n', cls=TypeAmendedGraph)
    assert saves(g, 'x.save')[0]['status'] == 'resolved'
    limited = TypeAmendedGraph(preflight_limit=3).build(tmp_path)
    assert limited.status == 'resource_limited' and not limited.edges


def test_type_bound_preserves_unknown_not_subset(tmp_path):
    from typeprop_graph import Fact, merge, MAX_TYPES
    assert merge([Fact(frozenset(str(i) for i in range(MAX_TYPES + 1)))]) .unknown


def test_round_bound_fails_closed(tmp_path, monkeypatch):
    import typeprop_graph
    monkeypatch.setattr(typeprop_graph, 'MAX_ROUNDS', 1)
    g = graph(tmp_path, ORDER + 'def a(x):\n b(x)\ndef b(obj):\n obj.save()\ndef caller():\n a(Order())\n')
    assert not g.type_metrics['converged'] and saves(g)[0]['status'] == 'unresolved'


def test_self_is_not_exact_constructor_evidence(tmp_path):
    g = graph(tmp_path, 'class A:\n def save(self): pass\n def caller(self):\n  process(self)\nclass B(A):\n def save(self): pass\ndef process(obj):\n obj.save()\n')
    assert saves(g)[0]['status'] == 'unresolved'


def test_module_star_import_blocks_constructor_evidence(tmp_path):
    g = graph(tmp_path, ORDER + 'from unknown import *\ndef f():\n x = Order()\n x.save()\n')
    assert saves(g, 'x.save')[0]['status'] == 'unresolved'


def test_class_method_reflection_blocks_exact_type(tmp_path):
    g = graph(tmp_path, ORDER + ' def change(self):\n  self.__class__ = other\ndef f():\n x = Order()\n x.save()\n')
    assert saves(g, 'x.save')[0]['status'] == 'unresolved'


def test_duplicate_constructor_stores_remain_unknown(tmp_path):
    g = graph(tmp_path, ORDER + 'def f():\n x = Order()\n x = Order()\n x.save()\n')
    assert saves(g, 'x.save')[0]['status'] == 'unresolved'


def test_lambda_callable_escape_is_unknown(tmp_path):
    g = graph(tmp_path, ORDER + 'def process(obj):\n obj.save()\ndef caller():\n process(Order())\nescape = lambda: process\n')
    assert saves(g)[0]['status'] == 'unresolved'


def test_nonlocal_parameter_mutation(tmp_path):
    g = graph(tmp_path, ORDER + USER + 'def process(obj):\n def mutate():\n  nonlocal obj\n  obj = User()\n mutate()\n obj.save()\ndef caller():\n process(Order())\n')
    assert saves(g)[0]['status'] == 'unresolved'


def test_nonlocal_local_mutation(tmp_path):
    g = graph(tmp_path, ORDER + USER + 'def caller():\n x = Order()\n def mutate():\n  nonlocal x\n  x = User()\n mutate()\n x.save()\n')
    assert saves(g, 'x.save')[0]['status'] == 'unresolved'


def test_global_constructor_mutation(tmp_path):
    g = graph(tmp_path, ORDER + USER + 'def mutate():\n global Order\n Order = User\ndef caller():\n x = Order()\n x.save()\n')
    assert saves(g, 'x.save')[0]['status'] == 'unresolved'


def test_comprehension_walrus_rebinding(tmp_path):
    g = graph(tmp_path, ORDER + USER + 'def f():\n x = Order()\n [(x := User()) for _ in values]\n x.save()\n')
    assert saves(g, 'x.save')[0]['status'] == 'unresolved'


def test_private_method_name_mangling_is_not_guessed(tmp_path):
    g = graph(tmp_path, 'class A:\n def __test(self): pass\nclass B:\n def caller(self):\n  x = A()\n  x.__test()\n')
    assert saves(g, 'x.__test')[0]['status'] == 'unresolved'
