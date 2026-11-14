"""Synthetic AST/diff fixtures only; fixture source is never executed."""
import difflib
import sys
from pathlib import Path

import pytest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent.parent),str(HERE.parents[3]/'src')]
from mapper import map_file
from static_graph import Graph


def patch(old,new,path='a.py',context=3):
    return f'diff --git a/{path} b/{path}\n'+''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+path,tofile='b/'+path,n=context))


def run(tmp_path,old,new,*,nodes=None,section=None):
    (tmp_path/'a.py').write_text(old)
    graph=Graph().build(tmp_path)
    before=[dict(e) for e in graph.edges]
    actual=map_file('a.py','a.py',old.encode(),section or patch(old,new),graph.nodes.values() if nodes is None else nodes)
    assert graph.edges==before
    return actual


def names(result):
    return [(r['qualname'],r['status']) for r in result['records']]


def test_body_edit_missing_from_hunk_heading_still_maps_qualified_owner(tmp_path):
    old='class A:\n def run(self):\n  value=1\n  return value\nclass B:\n def run(self): return 0\n'
    actual=run(tmp_path,old,old.replace('value=1','value=2'))
    assert names(actual)==[('A.run','resolved')]


def test_same_method_name_in_multiple_classes_maps_all_actually_changed_owners(tmp_path):
    old='class A:\n def run(self): return 1\nclass B:\n def run(self): return 1\nclass C:\n def run(self): return 0\n'
    assert names(run(tmp_path,old,old.replace('return 1','return 2')))==[('A.run','resolved'),('B.run','resolved')]


def test_stale_header_and_unchanged_neighbor_are_not_seeds(tmp_path):
    old='def previous(): pass\ndef edited():\n return 1\ndef following(): pass\n'
    section=patch(old,old.replace('return 1','return 2')).replace('@@\n','@@ def previous():\n',1)
    assert names(run(tmp_path,old,old.replace('return 1','return 2'),section=section))==[('edited','resolved')]


def test_docstring_false_declaration_does_not_create_class_labels(tmp_path):
    old='class C:\n """Old doc."""\n def method(self): pass\n'
    new=old.replace('Old doc.','class labels for each estimator in the chain.')
    assert names(run(tmp_path,old,new))==[('C','resolved')]


def test_added_override_never_maps_to_ancestor_same_name(tmp_path):
    old='class Base:\n def fit(self): pass\nclass Child(Base):\n pass\n'
    new='class Base:\n def fit(self): pass\nclass Child(Base):\n def fit(self):\n  return super().fit()\n'
    assert names(run(tmp_path,old,new))==[('Child.fit','new_definition')]


def test_new_method_does_not_invent_enclosing_class_seed(tmp_path):
    old='class A:\n def existing(self): pass\n'
    new=old+' def added(self): pass\n'
    assert names(run(tmp_path,old,new))==[('A.added','new_definition')]


def test_nested_helper_and_direct_parent_call_edit_are_separate(tmp_path):
    old='def outer():\n return 1\n'
    new='def outer():\n def inner():\n  return 2\n return inner()\n'
    assert names(run(tmp_path,old,new))==[('outer','resolved'),('outer.inner','new_definition')]


def test_nested_only_body_edit_does_not_mark_parent(tmp_path):
    old='def outer():\n def inner():\n  return 1\n return inner()\n'
    assert names(run(tmp_path,old,old.replace('return 1','return 2')))==[('outer.inner','resolved')]


def test_async_and_nested_class_qualified_names(tmp_path):
    old='class A:\n class B:\n  async def f(self):\n   return 1\n'
    assert names(run(tmp_path,old,old.replace('return 1','return 2')))==[('A.B.f','resolved')]


def test_decorator_edit_maps_definition_identity_not_runtime_target(tmp_path):
    old='@decorator_a\ndef f(): return 1\n'
    assert names(run(tmp_path,old,old.replace('decorator_a','decorator_b')))==[('f','resolved')]


def test_class_base_edit_maps_class_only(tmp_path):
    old='class A(B):\n def f(self): pass\n'
    assert names(run(tmp_path,old,old.replace('A(B)','A(C)')))==[('A','resolved')]


def test_class_attribute_edit_maps_class(tmp_path):
    old='class A:\n value=1\n def f(self): pass\n'
    assert names(run(tmp_path,old,old.replace('value=1','value=2')))==[('A','resolved')]


def test_duplicate_full_qualified_definition_preserves_ambiguity(tmp_path):
    old='if flag:\n def f(): return 1\nelse:\n def f(): return 2\n'
    actual=run(tmp_path,old,old.replace('return 1','return 3'))
    assert names(actual)==[('f','ambiguous')]
    assert len(actual['records'][0]['targets'])==2


def test_deleted_definition_uses_base_node(tmp_path):
    old='def gone():\n return 1\ndef kept(): pass\n'
    actual=run(tmp_path,old,'def kept(): pass\n')
    assert names(actual)==[('gone','resolved')]
    assert actual['records'][0]['change_kind']=='deleted'


def test_rename_is_explicit_deleted_old_and_added_new_not_a_guess(tmp_path):
    old='def old(): return 1\n'
    assert names(run(tmp_path,old,'def new(): return 1\n'))==[('new','new_definition'),('old','resolved')]


def test_whitespace_and_comment_only_edits_do_not_add_seeds(tmp_path):
    old='def f():\n return 1 # old\n'
    actual=run(tmp_path,old,old.replace('# old','# revised'))
    assert not actual['records']
    assert actual['diagnostics'][0]['reason']=='owned_ast_structure_unchanged'


def test_comments_in_parent_do_not_leak_nested_structure_edits(tmp_path):
    old='def outer():\n # comment\n def inner(): return 1\n return inner()\n'
    new=old.replace('# comment','# different').replace('return 1','return 2')
    assert names(run(tmp_path,old,new))==[('outer.inner','resolved')]


def test_import_or_module_assignment_edit_is_explicit_without_module_seed(tmp_path):
    old='import a\nVALUE=1\ndef f(): return VALUE\n'
    actual=run(tmp_path,old,old.replace('VALUE=1','VALUE=2'))
    assert not actual['records']
    assert actual['diagnostics'][0]['reason']=='edits_outside_named_definitions'


def test_graph_omission_is_unresolved_without_class_fallback(tmp_path):
    old='class A:\n def f(self): return 1\n'
    actual=run(tmp_path,old,old.replace('return 1','return 2'),nodes=[])
    assert names(actual)==[('A.f','unresolved')]
    assert actual['records'][0]['reason']=='base_definition_not_indexed_at_expected_location'


def test_inconsistent_graph_location_does_not_fall_back_by_name(tmp_path):
    old='def f(): return 1\n'
    nodes=[dict(id='wrong',path='a.py',qualname='f',kind='function',line=99,column=0)]
    assert names(run(tmp_path,old,old.replace('return 1','return 2'),nodes=nodes))==[('f','unresolved')]


def test_new_file_definitions_are_separate(tmp_path):
    new='class A:\n def f(self): pass\n'
    actual=map_file('a.py','a.py',None,patch('',new),[],added_file=True)
    assert names(actual)==[('A','new_definition'),('A.f','new_definition')]


def test_missing_base_file_is_not_claimed_new(tmp_path):
    actual=map_file('a.py','a.py',None,patch('def f(): pass\n','def f(): return 1\n'),[])
    assert actual['records'][0]['status']=='unresolved'
    assert actual['records'][0]['reason']=='base_source_missing'


@pytest.mark.parametrize('broken', ['def f(:\n pass\n','def f():\nreturn 2\n'])
def test_candidate_parse_failure_is_explicit(tmp_path,broken):
    old='def f(): return 1\n'
    actual=run(tmp_path,old,broken)
    assert actual['records'][0]['record_kind']=='file_analysis_error'
    assert actual['records'][0]['status']=='unresolved'


def test_context_mismatch_fails_closed(tmp_path):
    old='def f(): return 1\n'
    actual=run(tmp_path,old,old.replace('1','2'),section=patch(old.replace('1','9'),old.replace('1','2')))
    assert actual['records'][0]['reason']=='old_context_or_removal_mismatch'


def test_wrong_hunk_count_fails_closed(tmp_path):
    old='def f(): return 1\n'
    section=patch(old,old.replace('1','2')).replace('@@ -1 +1 @@','@@ -1,2 +1 @@')
    assert run(tmp_path,old,old.replace('1','2'),section=section)['records'][0]['reason']=='hunk_line_count_mismatch'


def test_wrong_new_coordinates_fail_closed(tmp_path):
    old='def f(): return 1\n'
    section=patch(old,old.replace('1','2')).replace('@@ -1 +1 @@','@@ -1 +3 @@')
    assert run(tmp_path,old,old.replace('1','2'),section=section)['records'][0]['reason']=='new_hunk_coordinate_mismatch'


def test_multiple_hunks_with_line_shifts(tmp_path):
    old='def a():\n return 1\n'+'\n'*20+'def b():\n return 2\n'
    new=old.replace('return 1','x=1\n return x').replace('return 2','return 3')
    assert names(run(tmp_path,old,new,section=patch(old,new,context=1)))==[('a','resolved'),('b','resolved')]


def test_no_newline_marker(tmp_path):
    old='def f(): return 1'
    section='diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-def f(): return 1\n\\ No newline at end of file\n+def f(): return 2\n\\ No newline at end of file\n'
    assert names(run(tmp_path,old,'def f(): return 2',section=section))==[('f','resolved')]


def test_crlf_source(tmp_path):
    old='def f():\n return 1\n'
    (tmp_path/'a.py').write_text(old)
    graph=Graph().build(tmp_path)
    actual=map_file('a.py','a.py',old.replace('\n','\r\n').encode(),patch(old,old.replace('1','2')),graph.nodes.values())
    assert names(actual)==[('f','resolved')]


def test_non_utf8_source_cookie(tmp_path):
    text='# coding: latin-1\ndef f(): return "café"\n'
    (tmp_path/'a.py').write_bytes(text.encode('latin-1'))
    graph=Graph().build(tmp_path)
    actual=map_file('a.py','a.py',text.encode('latin-1'),patch(text,text.replace('café','été')),graph.nodes.values())
    assert names(actual)==[('f','resolved')]


def test_blob_cap_is_mapper_uncertainty_not_new_graph_policy(tmp_path,monkeypatch):
    import mapper
    monkeypatch.setattr(mapper,'MAX_SOURCE_BYTES',4)
    actual=map_file('a.py','a.py',b'def f(): pass\n','',[])
    assert actual['records'][0]['reason']=='source_blob_limit'


def test_keyword_only_default_positions_are_semantic_edits(tmp_path):
    old='def f(*, a, b=1): return a+b\n'
    new='def f(*, a=1, b): return a+b\n'
    assert names(run(tmp_path,old,new))==[('f','resolved')]


def test_pure_body_insertion_maps_existing_definition_without_old_removed_lines(tmp_path):
    old='def f():\n return 1\n'
    new='def f():\n value=2\n return 1\n'
    assert names(run(tmp_path,old,new))==[('f','resolved')]


def test_one_simple_name_can_have_both_existing_edit_and_new_scope(tmp_path):
    old='class A:\n def clear(self): return 1\nclass B:\n pass\n'
    new='class A:\n def clear(self): return 2\nclass B:\n def clear(self): return 3\n'
    assert names(run(tmp_path,old,new))==[('A.clear','resolved'),('B.clear','new_definition')]
