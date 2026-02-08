from nicegui.ssr import _fix_anchor_nesting, _postprocess


class TestPostprocessNumberInputs:

    def test_strips_value_from_number_input(self):
        html = '<input type="number" value="42" id="c1">'
        assert _postprocess(html) == '<input type="number" id="c1">'

    def test_preserves_value_on_text_input(self):
        html = '<input type="text" value="hello" id="c1">'
        assert _postprocess(html) == html

    def test_preserves_input_without_type(self):
        html = '<input value="hello" id="c1">'
        assert _postprocess(html) == html

    def test_multiple_inputs_mixed_types(self):
        html = '<input type="number" value="1"><input type="text" value="a"><input type="number" value="2">'
        assert _postprocess(html) == '<input type="number"><input type="text" value="a"><input type="number">'


class TestFixAnchorNesting:

    def test_replaces_link_target_with_div(self):
        html = '<a id="c5" name="line0"><a href="#line0">Line 0</a></a>'
        expected = '<div id="c5" name="line0"><a href="#line0">Line 0</a></div>'
        assert _fix_anchor_nesting(html) == expected

    def test_preserves_regular_anchors(self):
        html = '<a href="#line0">Line 0</a>'
        assert _fix_anchor_nesting(html) == html

    def test_preserves_anchors_without_name(self):
        html = '<a id="c5" href="/page">Link</a>'
        assert _fix_anchor_nesting(html) == html

    def test_multiple_link_targets(self):
        html = '<a name="a"><a href="#a">A</a></a><a name="b"><a href="#b">B</a></a>'
        expected = '<div name="a"><a href="#a">A</a></div><div name="b"><a href="#b">B</a></div>'
        assert _fix_anchor_nesting(html) == expected

    def test_link_target_with_non_anchor_children(self):
        html = '<a name="x"><span>text</span></a>'
        expected = '<div name="x"><span>text</span></div>'
        assert _fix_anchor_nesting(html) == expected

    def test_no_anchors(self):
        html = '<div>Hello</div><span>World</span>'
        assert _fix_anchor_nesting(html) == html

    def test_empty_string(self):
        assert _fix_anchor_nesting('') == ''

    def test_mixed_content(self):
        html = '<div><a name="x"><a href="#x">X</a></a><p>text</p><a href="/y">Y</a></div>'
        expected = '<div><div name="x"><a href="#x">X</a></div><p>text</p><a href="/y">Y</a></div>'
        assert _fix_anchor_nesting(html) == expected


class TestPostprocessIntegration:

    def test_both_fixes_applied(self):
        html = '<a name="n"><a href="#n">N</a></a><input type="number" value="5">'
        result = _postprocess(html)
        assert '<div name="n">' in result
        assert '</div>' in result
        assert 'value="5"' not in result
