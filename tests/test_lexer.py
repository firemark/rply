from pytest import raises

from rply import LexerGenerator


class TestLexer(object):

    def test_simple(self):
        lg = LexerGenerator()
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")

        l = lg.build()

        stream = l.lex("2+3")
        t = stream.next()
        assert t.name == "NUMBER"
        assert t.value == "2"
        t = stream.next()
        assert t.name == "PLUS"
        assert t.value == "+"
        t = stream.next()
        assert t.name == "NUMBER"
        assert t.value == "3"
        assert t.source_pos.idx == 2

        with raises(StopIteration):
            stream.next()

    def test_ignore(self):
        lg = LexerGenerator()
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")
        lg.ignore(r"\s+")

        l = lg.build()

        stream = l.lex("2 + 3")
        t = stream.next()
        assert t.name == "NUMBER"
        assert t.value == "2"
        t = stream.next()
        assert t.name == "PLUS"
        assert t.value == "+"
        t = stream.next()
        assert t.name == "NUMBER"
        assert t.value == "3"
        assert t.source_pos.idx == 4

        with raises(StopIteration):
            stream.next()

    def test_states(self):
        lg = LexerGenerator(initial_state="scalar")
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")
        lg.ignore(r"\s+")

        lg.add("OPEN_BRACKET", r"\[", to_state="vector")
        lg.add("PLUS", r"\+", state="vector")
        lg.add("NUMBER", r"\d+", state="vector")
        lg.add("NEW_LINE", r"\n+", state="vector")
        lg.add("CLOSE_BRACKET", r"\]", state="vector", to_state="scalar")
        lg.ignore(r" +", state="vector")

        l = lg.build()

        stream = l.lex("2 + [ 3 + 4 \n\n 5 + 6 ] + 7")
        tokens = [
            ("NUMBER", "2", "scalar"),
            ("PLUS", "+", "scalar"),
            ("OPEN_BRACKET", "[", "scalar"),
            ("NUMBER", "3", "vector"),
            ("PLUS", "+", "vector"),
            ("NUMBER", "4", "vector"),
            ("NEW_LINE", "\n\n", "vector"),
            ("NUMBER", "5", "vector"),
            ("PLUS", "+", "vector"),
            ("NUMBER", "6", "vector"),
            ("CLOSE_BRACKET", "]", "vector"),
            ("PLUS", "+", "scalar"),
            ("NUMBER", "7", "scalar"),
        ]

        for compare_token, token in zip(tokens, stream):
            name, value, state = compare_token
            assert token.name == name
            assert token.value == value
            assert token.state == state

    def test_position(self):
        lg = LexerGenerator()
        lg.add("NUMBER", r"\d+")
        lg.add("PLUS", r"\+")
        lg.ignore(r"\s+")

        l = lg.build()

        stream = l.lex("2 + 3")
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 1
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 3
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 5
        with raises(StopIteration):
            stream.next()

        stream = l.lex("2 +\n    37")
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 1
        t = stream.next()
        assert t.source_pos.lineno == 1
        assert t.source_pos.colno == 3
        t = stream.next()
        assert t.source_pos.lineno == 2
        assert t.source_pos.colno == 5
        with raises(StopIteration):
            stream.next()
