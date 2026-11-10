# accim - Adaptive-Comfort-Control-Implemented Model
# Copyright (C) 2021-2026 Daniel Sánchez-García
# Distributed under the GNU General Public License v3 or later.

"""Compiler of the EnergyPlus Runtime Language (Erl) to Python functions.

The EnergyPlus Python API backend of accim runs the EMS programs of the model in Python with this
module, and the tests use it to check the EMS programs that accim writes. The compiled programs
behave as in the EMS of EnergyPlus (``RuntimeLanguageProcessor.cc``):

- The operators are grouped in the order of precedence of EnergyPlus: ``/``, ``*``, ``-``, ``+``,
  ``==``, ``<>``, ``<=``, ``>=``, ``<``, ``>``, ``^``, ``&&``, ``||``, and then the built-in
  functions. The operators of each kind are grouped from left to right, so ``a + b - c`` is
  ``a + (b - c)`` and ``a * b / c`` is ``a * (b / c)``. The results are those of EnergyPlus, also in
  the last digit.
- A ``-`` at the beginning of an expression, or after an operator or ``(``, subtracts from 0.
- ``IF``, ``ELSEIF`` and ``WHILE`` are false when the value is 0; ``&&`` and ``||`` are true when
  their operands are 1. ``@Round`` rounds half away from zero.
- The names are case-insensitive. The variables that are not global (global variables, sensors,
  actuators, internal variables and built-in variables) are local to each program or subroutine.
- The values are numbers or Null, and the variables that have never been set are uninitialised.
  As in EnergyPlus, an operator whose operands are not both numbers (for instance, with Null) gives
  the number 0 without setting it (:data:`UNINITIALISED_NUMBER`): inside an expression it is 0, and
  reading the variable set to it is an error. ``==`` is true for two Nulls, and the functions take
  the values that are not numbers as 0. Reading an uninitialised variable, dividing by zero and the
  other serious errors stop the simulation (:class:`ErlRuntimeError`), except while EnergyPlus sizes
  the systems, when the expression just gives an error value (:attr:`ErlProgramSet.strict`).

Each statement runs as Python code on floats; when that fails (a variable that has not been set, a
Null value, a division by zero...), the statement is evaluated again with the exact rules of
EnergyPlus, so the usual case is fast and the unusual ones are exact.
"""

from __future__ import annotations

import math
import re
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

import numpy as np

__all__ = [
    'BUILT_IN_VARIABLES',
    'ErlError',
    'ErlProgramSet',
    'ErlRuntimeError',
    'ErlSyntaxError',
    'NULL',
    'UNINITIALISED_ERROR',
    'UNINITIALISED_NULL',
    'UNINITIALISED_NUMBER',
    'erl_round',
    'format_number',
    'is_number',
    'parse_expression',
]


class _ErlSpecialValue:
    """A value of Erl that is not a number. Python operations with it raise TypeError, so that the
    statements that use it are evaluated with the exact rules of EnergyPlus."""

    __slots__ = ('name', 'initialised', 'type')

    def __init__(self, name: str, initialised: bool, value_type: str):
        self.name = name
        self.initialised = initialised
        self.type = value_type

    def __repr__(self) -> str:
        return self.name

    def _fail(self, *args):
        raise TypeError(f'Erl value {self.name} in a Python operation')

    __hash__ = object.__hash__
    __eq__ = __ne__ = __lt__ = __le__ = __gt__ = __ge__ = _fail
    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = _fail
    __truediv__ = __rtruediv__ = __pow__ = __rpow__ = __mod__ = __rmod__ = _fail
    __neg__ = __pos__ = __abs__ = __float__ = __int__ = __index__ = __bool__ = _fail


#: The value Null (the built-in variable NULL, and the actuators that do not actuate)
NULL = _ErlSpecialValue('NULL', True, 'Null')
#: A Null value that has not been set (reading it is an error): an actuator that had not been set when a new
#: environment began
UNINITIALISED_NULL = _ErlSpecialValue('UNINITIALISED_NULL', False, 'Null')
#: The result of an operator whose operands are not both numbers (for instance, Null + 1): the number 0, which has
#: not been set. Inside an expression it is 0; reading the variable set to it is an error.
UNINITIALISED_NUMBER = _ErlSpecialValue('UNINITIALISED_NUMBER', False, 'Number')
#: The result of an expression that failed (for instance, with an uninitialised variable while sizing)
UNINITIALISED_ERROR = _ErlSpecialValue('UNINITIALISED_ERROR', False, 'Error')

_float = float


def is_number(value) -> bool:
    """True if an Erl value is a number."""
    return value.__class__ is _float


def format_number(value: float, keep_decimal: bool = False) -> str:
    """A number as accim writes it in the lines of the EMS programs: positional, without exponent, with the shortest
    digits that give the same float (:func:`numpy.format_float_positional`), and without the decimal point if it is
    an integer (with ``keep_decimal``, with ``.0``, as the programs of the outdoor metric write their numbers). All
    the modules that write numbers in the programs use it (finding B1-2 of the review of accim 1.2.0).

    :raises ValueError: If the number is not finite: ``nan`` or ``inf`` would be the names of variables in Erl.
    """
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'The EMS programs cannot have the number {value!r}: it is not finite.')
    return np.format_float_positional(number, trim='0' if keep_decimal else '-')


# Built-in variables of EnergyPlus; the constants keep their values at a new environment
CONSTANT_BUILT_IN_VARIABLES = {
    'NULL': NULL, 'FALSE': 0.0, 'TRUE': 1.0, 'OFF': 0.0, 'ON': 1.0, 'PI': math.pi,
}
DYNAMIC_BUILT_IN_VARIABLES = (
    'TIMESTEPSPERHOUR', 'YEAR', 'CALENDARYEAR', 'MONTH', 'DAYOFMONTH', 'DAYOFWEEK', 'DAYOFYEAR', 'HOUR',
    'TIMESTEPNUM', 'MINUTE', 'HOLIDAY', 'DAYLIGHTSAVINGS', 'CURRENTTIME', 'SUNISUP', 'ISRAINING',
    'SYSTEMTIMESTEP', 'ZONETIMESTEP', 'CURRENTENVIRONMENT', 'ACTUALDATEANDTIME', 'ACTUALTIME', 'WARMUPFLAG',
)
BUILT_IN_VARIABLES = frozenset(CONSTANT_BUILT_IN_VARIABLES) | frozenset(DYNAMIC_BUILT_IN_VARIABLES)
# Variables that EnergyPlus does not reset at a new environment
_NOT_RESET = frozenset(CONSTANT_BUILT_IN_VARIABLES) | {'ZONETIMESTEP', 'ACTUALDATEANDTIME', 'ACTUALTIME'}

# Binary operators, in the order in which EnergyPlus groups them
_BINARY_OPERATORS = ('/', '*', '-', '+', '==', '<>', '<=', '>=', '<', '>', '^', '&&', '||')
_TWO_CHARACTER_OPERATORS = ('==', '<>', '<=', '>=', '||', '&&')
_COMPARISONS = {'==': '==', '<>': '!=', '<=': '<=', '>=': '>=', '<': '<', '>': '>'}
# EnergyPlus leaves a WHILE loop after this number of iterations
_MAX_WHILE_ITERATIONS = 1_000_000
_NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
_FUNCTION = re.compile(r'@[A-Za-z][A-Za-z0-9]*')
# The exceptions after which a statement is evaluated with the exact rules
_FALLBACK = (KeyError, TypeError, ZeroDivisionError, ValueError, OverflowError)


class ErlError(Exception):
    """Base class of the errors of the Erl programs."""


class ErlSyntaxError(ErlError, ValueError):
    """The text of an Erl program is not valid, or uses a feature that is not supported."""


class ErlRuntimeError(ErlError, RuntimeError):
    """An Erl program failed while running, as EnergyPlus would (for instance, an uninitialised variable)."""


def erl_round(value: float) -> float:
    """``@Round`` of Erl: the nearest integer, with the halves rounded away from zero."""
    return float(int(value + (0.5 if value >= 0.0 else -0.5)))


# --------------------------------------------------------------------------------------------------
# Functions of the fast path: they work on floats and raise an exception in any other case, so that
# the statement is evaluated with the exact rules.
# --------------------------------------------------------------------------------------------------

def _is_odd_integer(value: float) -> bool:
    return math.isfinite(value) and value == math.floor(value) and math.fmod(value, 2.0) != 0.0


def _c_pow(a: float, b: float) -> float:
    """``std::pow`` of C, which EnergyPlus uses for ``^``: the poles (0 raised to a negative number) and the overflows
    give infinities, where ``math.pow`` raises an exception, and the domain errors give NaN."""
    try:
        return math.pow(a, b)
    except ValueError:
        if a == 0.0 and b < 0.0:
            return math.copysign(math.inf, a) if _is_odd_integer(b) else math.inf
        return math.nan
    except OverflowError:
        return -math.inf if a < 0.0 and _is_odd_integer(b) else math.inf


def _f_pow(a, b):
    result = _c_pow(a, b)
    if result != result:
        raise ValueError
    return result


def _f_and(a, b):
    if a.__class__ is _float and b.__class__ is _float:
        return 1.0 if (a == 1.0 and b == 1.0) else 0.0
    raise TypeError


def _f_or(a, b):
    if a.__class__ is _float and b.__class__ is _float:
        return 1.0 if (a == 1.0 or b == 1.0) else 0.0
    raise TypeError


def _f_lit(value):
    if value.__class__ is _float or value is NULL:
        return value
    raise TypeError


def _f_mod(a, b):
    return math.fmod(a, b) if b != 0.0 else 0.0


def _f_exp(a):
    if -20.0 < a < 700.0:
        return math.exp(a)
    if a <= -20.0:
        return 0.0
    raise OverflowError


def _f_ln(a):
    if a > 0.0:
        return math.log(a)
    raise ValueError


def _f_max(a, b):
    return b if a < b else a


def _f_min(a, b):
    return a if a < b else b


_DEG_TO_RADIANS = math.pi / 180.0

#: Built-in functions that report an error code in the error file of EnergyPlus and return it; @FatalHaltEP also
#: stops the simulation. The programs that use them are evaluated with the exact rules, so that a message is
#: never reported twice
_MESSAGE_FUNCTIONS = frozenset({'@WARNEP', '@SEVEREWARNEP', '@FATALHALTEP'})

# Built-in functions: name -> (number of operands, name of the function of the fast path)
_FUNCTIONS = {
    '@ROUND': (1, '_f_round'),
    '@MOD': (2, '_f_mod'),
    '@SIN': (1, '_f_sin'),
    '@COS': (1, '_f_cos'),
    '@ARCSIN': (1, '_f_asin'),
    '@ARCCOS': (1, '_f_acos'),
    '@DEGTORAD': (1, '_f_degtorad'),
    '@RADTODEG': (1, '_f_radtodeg'),
    '@EXP': (1, '_f_exp'),
    '@LN': (1, '_f_ln'),
    '@MAX': (2, '_f_max'),
    '@MIN': (2, '_f_min'),
    '@ABS': (1, '_f_abs'),
    '@WARNEP': (1, None),
    '@SEVEREWARNEP': (1, None),
    '@FATALHALTEP': (1, None),
}

_FAST_NAMESPACE = {
    '_f_pow': _f_pow,
    '_f_and': _f_and,
    '_f_or': _f_or,
    '_f_lit': _f_lit,
    '_f_round': erl_round,
    '_f_mod': _f_mod,
    '_f_sin': math.sin,
    '_f_cos': math.cos,
    '_f_asin': math.asin,
    '_f_acos': math.acos,
    '_f_degtorad': lambda a: a * _DEG_TO_RADIANS,
    '_f_radtodeg': lambda a: a / _DEG_TO_RADIANS,
    '_f_exp': _f_exp,
    '_f_ln': _f_ln,
    '_f_max': _f_max,
    '_f_min': _f_min,
    '_f_abs': abs,
    '_FALLBACK': _FALLBACK,
}

# Expression trees: ('num', value), ('var', NAME), ('bin', op, left, right), ('func', NAME, [args]) and
# ('lit', operand), the literal expressions of EnergyPlus (a variable or a number alone, at the top of a
# statement or in parentheses)
Tree = tuple


def _tokenize(expression: str) -> list:
    """Split an expression into tokens as EnergyPlus does, including its handling of the minus sign."""
    text = expression.strip()
    if not text:
        raise ErlSyntaxError('Empty expression.')
    if text[0] in '-+':
        text = '0' + text
    tokens = []
    pos = 0
    operator_processing = mult_found = div_found = False
    while pos < len(text):
        char = text[pos]
        if char == ' ':
            pos += 1
            continue
        if char in '0123456789.':
            end = pos + 1
            last_exponent = char in 'eEdD'
            while end < len(text):
                nxt = text[end]
                if nxt in '0123456789.eEdD':
                    if nxt in 'eEdD':
                        if last_exponent:
                            raise ErlSyntaxError(f'Two D/E in numeric string "{expression}".')
                        last_exponent = True
                    end += 1
                elif nxt in '+-' and last_exponent:
                    last_exponent = False
                    end += 1
                elif nxt in ' +-*/^=<>)':
                    break
                else:
                    raise ErlSyntaxError(f'Invalid number in "{expression}".')
            literal = text[pos:end]
            try:
                value = float(literal.replace('d', 'e').replace('D', 'e'))
            except ValueError:
                raise ErlSyntaxError(f'Invalid number "{literal}" in "{expression}".') from None
            tokens.append(('num', value))
            pos = end
            operator_processing = mult_found = div_found = False
        elif char.isascii() and char.isalpha():
            match = _NAME.match(text, pos)
            end = match.end()
            if end < len(text) and text[end] not in ' +-*/^=<>()&|@':
                raise ErlSyntaxError(f'Invalid character "{text[end]}" in "{expression}".')
            tokens.append(('var', match.group().upper()))
            pos = end
            operator_processing = mult_found = div_found = False
        elif char in '+-*/^=<>@|&':
            if char == '-':
                if mult_found:
                    raise ErlSyntaxError(
                        f'Minus sign used on the right side of multiplication sign in "{expression}".')
                if div_found:
                    raise ErlSyntaxError(f'Minus sign used on the right side of division sign in "{expression}".')
                if operator_processing:
                    # EnergyPlus changes "X == -1" into "X == 0-1"
                    tokens.append(('num', 0.0))
                    operator_processing = mult_found = div_found = False
                    continue
            two = text[pos:pos + 2]
            if two in _TWO_CHARACTER_OPERATORS:
                tokens.append(('op', two))
                pos += 2
                operator_processing = True
            elif char == '@':
                match = _FUNCTION.match(text, pos)
                name = match.group().upper() if match else text[pos:]
                if name not in _FUNCTIONS:
                    raise ErlSyntaxError(f'Built-in function "{name}" is not supported (in "{expression}").')
                tokens.append(('func', name))
                pos = match.end()
            else:
                mult_found = div_found = False
                if char == '+':
                    if operator_processing:
                        raise ErlSyntaxError(f'Plus sign after an operator is not supported (in "{expression}").')
                    tokens.append(('op', '+'))
                    operator_processing = True
                elif char == '-':
                    tokens.append(('op', '-'))
                    operator_processing = True
                elif char == '*':
                    tokens.append(('op', '*'))
                    mult_found = operator_processing = True
                elif char == '/':
                    tokens.append(('op', '/'))
                    div_found = operator_processing = True
                elif char in '<>^':
                    tokens.append(('op', char))
                    operator_processing = True
                else:
                    raise ErlSyntaxError(f'Invalid operator "{char}" in "{expression}".')
                pos += 1
        elif char == '(':
            tokens.append(('(',))
            operator_processing = True
            pos += 1
        elif char == ')':
            tokens.append((')',))
            pos += 1
        else:
            raise ErlSyntaxError(f'Invalid character "{char}" in "{expression}".')
    return tokens


def _operand(token, expression):
    if token[0] in ('num', 'var'):
        return token
    if token[0] == 'expr':
        return token[1]
    raise ErlSyntaxError(f'An operator is missing an operand in "{expression}".')


def _group(tokens: list, expression: str) -> Tree:
    """Group the tokens of an expression without parentheses, in the order of precedence of EnergyPlus."""
    tokens = list(tokens)
    for operator in _BINARY_OPERATORS:
        while True:
            pos = next((i for i, t in enumerate(tokens) if t[0] == 'op' and t[1] == operator), None)
            if pos is None:
                break
            if pos == 0:
                raise ErlSyntaxError(f'The operator "{operator}" is missing the left-hand operand in "{expression}".')
            if pos == len(tokens) - 1:
                raise ErlSyntaxError(f'The operator "{operator}" is missing the right-hand operand in "{expression}".')
            left = _operand(tokens[pos - 1], expression)
            right = _operand(tokens[pos + 1], expression)
            tokens[pos - 1:pos + 2] = [('expr', ('bin', operator, left, right))]
    if tokens and tokens[0][0] == 'func':
        name = tokens[0][1]
        n_operands = _FUNCTIONS[name][0]
        operands = tokens[1:]
        if len(operands) != n_operands:
            raise ErlSyntaxError(f'{name} needs {n_operands} operand(s) in "{expression}".')
        return ('func', name, [_operand(t, expression) for t in operands])
    if len(tokens) != 1:
        raise ErlSyntaxError(f'Invalid expression "{expression}" (functions must be at the beginning of an '
                             f'expression or in parentheses).')
    return _operand(tokens[0], expression)


def _as_expression(tree: Tree) -> Tree:
    """A variable or a number alone is a literal expression in EnergyPlus."""
    return ('lit', tree) if tree[0] in ('num', 'var') else tree


def parse_expression(expression: str) -> Tree:
    """Parse an Erl expression into a tree, grouped as EnergyPlus groups it."""
    tokens = _tokenize(expression)

    def parse(start: int) -> Tuple[Tree, int]:
        # Parse the tokens from start to the matching ')' (or the end), returning the tree and the end
        flat = []
        pos = start
        while pos < len(tokens):
            token = tokens[pos]
            if token[0] == '(':
                tree, pos = parse(pos + 1)
                if pos >= len(tokens) or tokens[pos][0] != ')':
                    raise ErlSyntaxError(f'Unbalanced parentheses in "{expression}".')
                flat.append(('expr', _as_expression(tree)))
                pos += 1
            elif token[0] == ')':
                break
            else:
                flat.append(token)
                pos += 1
        if not flat:
            raise ErlSyntaxError(f'Empty parentheses in "{expression}".')
        return _group(flat, expression), pos

    tree, end = parse(0)
    if end != len(tokens):
        raise ErlSyntaxError(f'Unbalanced parentheses in "{expression}".')
    return _as_expression(tree)


# --------------------------------------------------------------------------------------------------
# Exact evaluation (EvaluateExpression of RuntimeLanguageProcessor.cc)
# --------------------------------------------------------------------------------------------------

def _number(value) -> float:
    """The number of a value (the values that are not numbers have the number 0 in EnergyPlus)."""
    return value if value.__class__ is _float else 0.0


def _value_type(value) -> str:
    return 'Number' if value.__class__ is _float else value.type


class _ExactEvaluator:
    """Evaluates the expressions with the rules of EnergyPlus, raising ErlRuntimeError for the serious errors
    when ``owner.strict`` is True."""

    def __init__(self, owner: 'ErlProgramSet'):
        self.owner = owner

    def serious(self, message: str, program: str):
        if self.owner.strict:
            raise ErlRuntimeError(f'{message} (program {program})')

    def expression(self, tree: Tree, G: dict, L: dict, program: str):
        kind = tree[0]
        operands = (tree[1],) if kind == 'lit' else (tree[2], tree[3]) if kind == 'bin' else tuple(tree[2])
        values = []
        error = False
        for operand in operands:
            if operand[0] == 'num':
                values.append(operand[1])
            elif operand[0] == 'var':
                name = operand[1]
                value = (G if name in self.owner.global_names else L).get(name, UNINITIALISED_NULL)
                if value.__class__ is not _float and not value.initialised:
                    error = True
                    self.serious(f"Variable = '{name}' used in expression has not been initialized!", program)
                values.append(value)
            else:
                values.append(self.expression(operand, G, L, program))
        if error:
            return UNINITIALISED_ERROR
        if kind == 'lit':
            return values[0]
        if kind == 'func':
            return self.function(tree[1], [_number(v) for v in values], program)
        op = tree[1]
        a, b = values
        if op == '==':
            type_a, type_b = _value_type(a), _value_type(b)
            if type_a == type_b and (type_a == 'Null' or (type_a == 'Number' and _number(a) == _number(b))):
                return 1.0
            return 0.0
        if _value_type(a) != 'Number' or _value_type(b) != 'Number':
            # EnergyPlus leaves its result, the number 0, without setting it
            return UNINITIALISED_NUMBER
        a, b = _number(a), _number(b)
        if op == '+':
            return a + b
        if op == '-':
            return a - b
        if op == '*':
            return a * b
        if op == '/':
            if b == 0.0:
                self.serious('Divide By Zero in EMS Program!', program)
                return UNINITIALISED_ERROR
            return a / b
        if op == '^':
            result = _c_pow(a, b)
            if result != result:
                self.serious(f'Attempted to raise to power with incompatible numbers: {a} raised to {b}', program)
                return UNINITIALISED_ERROR
            return result
        if op == '&&':
            return 1.0 if (a == 1.0 and b == 1.0) else 0.0
        if op == '||':
            return 1.0 if (a == 1.0 or b == 1.0) else 0.0
        if op == '<>':
            return 1.0 if a != b else 0.0
        if op == '<=':
            return 1.0 if a <= b else 0.0
        if op == '>=':
            return 1.0 if a >= b else 0.0
        if op == '<':
            return 1.0 if a < b else 0.0
        return 1.0 if a > b else 0.0

    def function(self, name: str, args: List[float], program: str):
        a = args[0]
        if name == '@ROUND':
            return erl_round(a)
        if name == '@MOD':
            return _f_mod(a, args[1])
        if name == '@SIN':
            return math.sin(a)
        if name == '@COS':
            return math.cos(a)
        if name in ('@ARCSIN', '@ARCCOS'):
            try:
                return math.asin(a) if name == '@ARCSIN' else math.acos(a)
            except ValueError:
                return math.nan
        if name == '@DEGTORAD':
            return a * _DEG_TO_RADIANS
        if name == '@RADTODEG':
            return a / _DEG_TO_RADIANS
        if name == '@EXP':
            if -20.0 < a < 700.0:
                return math.exp(a)
            if a <= -20.0:
                return 0.0
            self.serious(f'Attempted to calculate exponential value of too large a number: {a}', program)
            return UNINITIALISED_ERROR
        if name == '@LN':
            if a > 0.0:
                return math.log(a)
            self.serious(f'Natural Log of zero or less! ln of value = {a}', program)
            return UNINITIALISED_ERROR
        if name == '@MAX':
            return _f_max(a, args[1])
        if name == '@MIN':
            return _f_min(a, args[1])
        if name in _MESSAGE_FUNCTIONS:
            return self.owner.message_function(name, a)
        return abs(a)

    def is_true(self, tree: Tree, G: dict, L: dict, program: str) -> bool:
        """The condition of IF, ELSEIF and WHILE: false if the number of the value is 0."""
        return _number(self.expression(tree, G, L, program)) != 0.0


# --------------------------------------------------------------------------------------------------
# Statements
# --------------------------------------------------------------------------------------------------

def _parse_statements(name: str, lines: Sequence[str]) -> list:
    """Parse the lines of a program into nested statements."""
    root: list = []
    stack: list = []  # open blocks: ['if', branches, else_body] or ['while', cond, body]
    current = root
    for raw in lines:
        line = (raw or '').strip()
        if not line or line.startswith('!'):
            continue
        keyword, _, remainder = line.partition(' ')
        keyword = keyword.upper()
        remainder = remainder.strip()
        where = f'program {name}, line "{line}"'
        try:
            if keyword == 'SET':
                target, equal, expression = remainder.partition('=')
                target = target.strip()
                if not equal or not target:
                    raise ErlSyntaxError('SET needs a variable, "=" and an expression.')
                if not _NAME.fullmatch(target):
                    raise ErlSyntaxError(f'Invalid variable name "{target}".')
                current.append(('set', target.upper(), parse_expression(expression)))
            elif keyword == 'RUN':
                if not remainder:
                    raise ErlSyntaxError('RUN needs a program or subroutine name.')
                current.append(('run', remainder.split(' ')[0].upper()))
            elif keyword == 'RETURN':
                current.append(('return',))
            elif keyword == 'IF':
                block = ['if', [(parse_expression(remainder), [])], None]
                current.append(block)
                stack.append(block)
                current = block[1][-1][1]
            elif keyword == 'ELSEIF':
                if not stack or stack[-1][0] != 'if' or stack[-1][2] is not None:
                    raise ErlSyntaxError('ELSEIF without IF.')
                stack[-1][1].append((parse_expression(remainder), []))
                current = stack[-1][1][-1][1]
            elif keyword == 'ELSE':
                if not stack or stack[-1][0] != 'if' or stack[-1][2] is not None:
                    raise ErlSyntaxError('ELSE without IF.')
                if remainder:
                    raise ErlSyntaxError('Nothing is allowed to follow the ELSE instruction.')
                stack[-1][2] = []
                current = stack[-1][2]
            elif keyword == 'ENDIF':
                if not stack or stack[-1][0] != 'if':
                    raise ErlSyntaxError('ENDIF without IF.')
                stack.pop()
                current = _innermost_body(stack, root)
            elif keyword == 'WHILE':
                block = ['while', parse_expression(remainder), []]
                current.append(block)
                stack.append(block)
                current = block[2]
            elif keyword == 'ENDWHILE':
                if not stack or stack[-1][0] != 'while':
                    raise ErlSyntaxError('ENDWHILE without WHILE.')
                stack.pop()
                current = _innermost_body(stack, root)
            else:
                raise ErlSyntaxError(f'Unknown instruction "{keyword}".')
        except ErlSyntaxError as error:
            raise ErlSyntaxError(f'{error} ({where})') from None
    if stack:
        raise ErlSyntaxError(f'Missing ENDIF or ENDWHILE in program {name}.')
    return [_freeze(s) for s in root]


def _innermost_body(stack: list, root: list) -> list:
    if not stack:
        return root
    block = stack[-1]
    if block[0] == 'while':
        return block[2]
    return block[2] if block[2] is not None else block[1][-1][1]


def _freeze(statement):
    if isinstance(statement, list):
        if statement[0] == 'if':
            branches = [(c, [_freeze(s) for s in body]) for c, body in statement[1]]
            else_body = None if statement[2] is None else [_freeze(s) for s in statement[2]]
            return ('if', branches, else_body)
        return ('while', statement[1], [_freeze(s) for s in statement[2]])
    return statement


def _visit_tree(tree: Tree, found: set) -> None:
    if tree[0] == 'var':
        found.add(tree[1])
    elif tree[0] == 'lit':
        _visit_tree(tree[1], found)
    elif tree[0] == 'bin':
        _visit_tree(tree[2], found)
        _visit_tree(tree[3], found)
    elif tree[0] == 'func':
        for argument in tree[2]:
            _visit_tree(argument, found)


def _visit_functions(tree: Tree, found: set) -> None:
    if tree[0] == 'func':
        found.add(tree[1])
        for argument in tree[2]:
            _visit_functions(argument, found)
    elif tree[0] == 'lit':
        _visit_functions(tree[1], found)
    elif tree[0] == 'bin':
        _visit_functions(tree[2], found)
        _visit_functions(tree[3], found)


def _functions_used(statements: list, found: set) -> set:
    """Names of the built-in functions that the statements use."""
    for statement in statements:
        if statement[0] == 'set':
            _visit_functions(statement[2], found)
        elif statement[0] == 'if':
            for condition, body in statement[1]:
                _visit_functions(condition, found)
                _functions_used(body, found)
            if statement[2] is not None:
                _functions_used(statement[2], found)
        elif statement[0] == 'while':
            _visit_functions(statement[1], found)
            _functions_used(statement[2], found)
    return found


def _read_variables(statements: list, found: set) -> set:
    """Names of the variables that the statements read or set."""
    for statement in statements:
        if statement[0] == 'set':
            found.add(statement[1])
            _visit_tree(statement[2], found)
        elif statement[0] == 'if':
            for condition, body in statement[1]:
                _visit_tree(condition, found)
                _read_variables(body, found)
            if statement[2] is not None:
                _read_variables(statement[2], found)
        elif statement[0] == 'while':
            _visit_tree(statement[1], found)
            _read_variables(statement[2], found)
    return found


def _set_variables(statements: list, found: set) -> set:
    """Names of the variables that the statements set."""
    for statement in statements:
        if statement[0] == 'set':
            found.add(statement[1])
        elif statement[0] == 'if':
            for _, body in statement[1]:
                _set_variables(body, found)
            if statement[2] is not None:
                _set_variables(statement[2], found)
        elif statement[0] == 'while':
            _set_variables(statement[2], found)
    return found


def _number_code(value: float) -> str:
    """The Python code of a number (the literals too large for a float, such as 1e999, are infinite)."""
    return repr(value) if math.isfinite(value) else f"float('{value!r}')"


class _CodeWriter:
    """Writes the Python code of a program: each expression runs on floats, and is evaluated again with the
    exact rules if that fails."""

    def __init__(self, program: str, global_names: frozenset, exact: bool = False):
        self.program = program
        self.global_names = global_names
        # True to evaluate every expression with the exact rules (for the expressions too long for Python code)
        self.exact = exact
        self.lines: List[str] = []
        self.trees: Dict[str, Tree] = {}
        self.counter = 0

    def ref(self, name: str) -> str:
        return f"G[{name!r}]" if name in self.global_names else f"L[{name!r}]"

    def tree_constant(self, tree: Tree) -> str:
        self.counter += 1
        name = f'_T{self.counter}'
        self.trees[name] = tree
        return name

    def expr(self, tree: Tree) -> str:
        kind = tree[0]
        if kind == 'num':
            return _number_code(tree[1])
        if kind == 'var':
            return self.ref(tree[1])
        if kind == 'lit':
            if tree[1][0] == 'num':
                return _number_code(tree[1][1])
            return f'_f_lit({self.ref(tree[1][1])})'
        if kind == 'func':
            function = _FUNCTIONS[tree[1]][1]
            return f"{function}({', '.join(self.expr(a) for a in tree[2])})"
        _, op, left, right = tree
        if op in ('+', '-', '*', '/'):
            return f'({self.chain(tree)})'
        a, b = self.expr(left), self.expr(right)
        if op == '^':
            return f'_f_pow({a}, {b})'
        if op == '&&':
            return f'_f_and({a}, {b})'
        if op == '||':
            return f'_f_or({a}, {b})'
        return f'(1.0 if {a} {_COMPARISONS[op]} {b} else 0.0)'

    def chain(self, tree: Tree) -> str:
        """The code of an arithmetic operator and of the same operator in its left operand, without nested
        parentheses: EnergyPlus groups ``a + b + c`` as ``(a + b) + c``, as Python does, and the parentheses of long
        sums (such as the building averages) would exceed the limit of nested parentheses of Python."""
        op = tree[1]
        operands = []
        while tree[0] == 'bin' and tree[1] == op:
            operands.append(self.expr(tree[3]))
            tree = tree[2]
        operands.append(self.expr(tree))
        return f' {op} '.join(reversed(operands))

    def condition(self, tree: Tree) -> str:
        """Python condition that is true when the number of the Erl expression is not 0."""
        if tree[0] == 'bin' and tree[1] in _COMPARISONS:
            return f'({self.expr(tree[2])} {_COMPARISONS[tree[1]]} {self.expr(tree[3])})'
        return f'({self.expr(tree)} != 0.0)'

    def emit_test(self, tree: Tree, variable: str, indent: str) -> None:
        constant = self.tree_constant(tree)
        if self.exact:
            self.lines.append(f'{indent}{variable} = _is_true({constant}, G, L, {self.program!r})')
            return
        self.lines.append(f'{indent}try:')
        self.lines.append(f'{indent}    {variable} = {self.condition(tree)}')
        self.lines.append(f'{indent}except _FALLBACK:')
        self.lines.append(f'{indent}    {variable} = _is_true({constant}, G, L, {self.program!r})')

    def emit(self, statements: list, indent: str) -> None:
        if not statements:
            self.lines.append(f'{indent}pass')
            return
        for statement in statements:
            kind = statement[0]
            if kind == 'set':
                _, target, tree = statement
                constant = self.tree_constant(tree)
                if self.exact:
                    self.lines.append(f'{indent}{self.ref(target)} = _expression({constant}, G, L, {self.program!r})')
                    continue
                self.lines.append(f'{indent}try:')
                self.lines.append(f'{indent}    {self.ref(target)} = {self.expr(tree)}')
                self.lines.append(f'{indent}except _FALLBACK:')
                self.lines.append(f'{indent}    {self.ref(target)} = _expression({constant}, G, L, {self.program!r})')
            elif kind == 'run':
                self.lines.append(f'{indent}run({statement[1]!r})')
            elif kind == 'return':
                self.lines.append(f'{indent}return')
            elif kind == 'if':
                # The branch is chosen first, without nesting the conditions (Python limits the nested blocks)
                _, branches, else_body = statement
                self.counter += 1
                branch = f'_b{self.counter}'
                self.lines.append(f'{indent}{branch} = 0')
                for n, (condition, _) in enumerate(branches, start=1):
                    if n == 1:
                        self.emit_test(condition, '_t', indent)
                        self.lines.append(f'{indent}if _t:')
                        self.lines.append(f'{indent}    {branch} = 1')
                    else:
                        self.lines.append(f'{indent}if {branch} == 0:')
                        self.emit_test(condition, '_t', indent + '    ')
                        self.lines.append(f'{indent}    if _t:')
                        self.lines.append(f'{indent}        {branch} = {n}')
                for n, (_, body) in enumerate(branches, start=1):
                    self.lines.append(f'{indent}{"if" if n == 1 else "elif"} {branch} == {n}:')
                    self.emit(body, indent + '    ')
                if else_body is not None:
                    self.lines.append(f'{indent}else:')
                    self.emit(else_body, indent + '    ')
            elif kind == 'while':
                _, condition, body = statement
                self.counter += 1
                counter = f'_n{self.counter}'
                self.lines.append(f'{indent}{counter} = 0')
                self.lines.append(f'{indent}while True:')
                self.emit_test(condition, '_t', indent + '    ')
                self.lines.append(f'{indent}    if not _t or {counter} > {_MAX_WHILE_ITERATIONS}:')
                self.lines.append(f'{indent}        break')
                self.emit(body, indent + '    ')
                self.lines.append(f'{indent}    {counter} += 1')


class ErlProgramSet:
    """EMS programs and subroutines compiled to Python, with their variables.

    :param programs: The lines of each program and subroutine, by name.
    :param global_variables: The names of the global variables (EMS global variables, sensors,
        actuators and internal variables). The built-in variables of EnergyPlus are always global.
    :param actuators: The names of the actuator variables, which are reset to Null (not actuated)
        at a new environment, as in EnergyPlus.
    :ivar strict: True to raise :class:`ErlRuntimeError` for the serious errors (an uninitialised
        variable, a division by zero...), as EnergyPlus does except while sizing.
    :ivar variables: The values of the global variables that have been set.
    :ivar local_variables: The values of the local variables of each program that have been set.
    :ivar source: The Python code of each program.
    :ivar messages: The messages of @WarnEP, @SevereWarnEP and @FatalHaltEP, as ``(level, text)``, with the level
        'warning' or 'severe'.
    :ivar on_message: Called with each message, as ``on_message(level, text)``; the Python API backend writes
        them in the error file of EnergyPlus, as the EMS does.
    """

    def __init__(
        self,
        programs: Mapping[str, Sequence[str]],
        global_variables: Iterable[str] = (),
        actuators: Iterable[str] = (),
    ):
        self.strict = True
        self.actuators = frozenset(name.upper() for name in actuators)
        self.global_names = frozenset(name.upper() for name in global_variables) | BUILT_IN_VARIABLES | self.actuators
        self.variables: Dict[str, object] = dict(CONSTANT_BUILT_IN_VARIABLES)
        # EnergyPlus initialises the variables of the actuators to Null (not actuated)
        self.variables.update(dict.fromkeys(self.actuators, NULL))
        self.local_variables: Dict[str, Dict[str, object]] = {}
        self.source: Dict[str, str] = {}
        self.messages: List[Tuple[str, str]] = []
        self.on_message: Optional[Callable[[str, str], None]] = None
        self._functions: Dict[str, Callable] = {}
        self._set_names: Dict[str, Set[str]] = {}
        evaluator = _ExactEvaluator(self)
        program_lines = {name.upper(): list(lines) for name, lines in programs.items()}
        program_names = frozenset(program_lines)
        for name, lines in program_lines.items():
            statements = _parse_statements(name, lines)
            self._check_runs(name, statements, program_names)
            self._set_names[name] = _set_variables(statements, set())
            exact = bool(_functions_used(statements, set()) & _MESSAGE_FUNCTIONS)
            try:
                function, code = self._compile(name, statements, evaluator, exact=exact)
            except (SyntaxError, RecursionError, MemoryError):
                # Python cannot compile some expressions (too deeply nested): they are evaluated with the exact rules
                function, code = self._compile(name, statements, evaluator, exact=True)
            self.source[name] = code
            self._functions[name] = function
            self.local_variables[name] = {}

    def _compile(self, name: str, statements: list, evaluator: '_ExactEvaluator', exact: bool) -> Tuple[Callable, str]:
        writer = _CodeWriter(name, self.global_names, exact=exact)
        writer.lines.append('def _program(G, L, run):')
        writer.emit(statements, '    ')
        code = '\n'.join(writer.lines)
        namespace = dict(_FAST_NAMESPACE)
        namespace.update(writer.trees)
        namespace['_expression'] = evaluator.expression
        namespace['_is_true'] = evaluator.is_true
        exec(compile(code, f'<Erl program {name}>', 'exec'), namespace)
        return namespace['_program'], code

    @staticmethod
    def _check_runs(name: str, statements: list, program_names: frozenset) -> None:
        for statement in statements:
            if statement[0] == 'run' and statement[1] not in program_names:
                raise ErlSyntaxError(f'Program or subroutine [{statement[1]}] not found for the RUN instruction '
                                     f'(program {name}).')
            if statement[0] == 'if':
                for _, body in statement[1]:
                    ErlProgramSet._check_runs(name, body, program_names)
                if statement[2] is not None:
                    ErlProgramSet._check_runs(name, statement[2], program_names)
            if statement[0] == 'while':
                ErlProgramSet._check_runs(name, statement[2], program_names)

    @property
    def program_names(self) -> List[str]:
        """Names (in upper case) of the compiled programs and subroutines."""
        return list(self._functions)

    def message_function(self, name: str, number: float) -> float:
        """Run @WarnEP, @SevereWarnEP or @FatalHaltEP: report the error code and return it.

        As in EnergyPlus (``RuntimeLanguageProcessor.cc``), @FatalHaltEP stops the simulation, also while sizing.
        """
        code = f'{number:.2f}'
        if name == '@WARNEP':
            self._message('warning', f'EMS user program issued warning with error code = {code}')
        elif name == '@SEVEREWARNEP':
            self._message('severe', f'EMS user program issued severe warning with error code = {code}')
        else:
            self._message('severe', 'EMS user program found serious problem and is halting simulation')
            raise ErlRuntimeError(f'EMS user program halted simulation with error code = {code}')
        return number

    def _message(self, level: str, text: str) -> None:
        self.messages.append((level, text))
        if self.on_message is not None:
            self.on_message(level, text)

    def run(self, name: str) -> None:
        """Run a program (or subroutine), as an EMS program calling manager or a RUN instruction does."""
        key = name.upper()
        try:
            function = self._functions[key]
        except KeyError:
            raise ErlRuntimeError(f'Program or subroutine "{name}" not found.') from None
        function(self.variables, self.local_variables[key], self.run)

    def reset(self) -> None:
        """Reset the variables as EnergyPlus does at the beginning of each environment.

        The variables that have been set become 0, except the built-in constants, and the actuators
        become Null (not actuated).
        """
        for store in [self.variables, *self.local_variables.values()]:
            for name, value in store.items():
                if (value.__class__ is _float or value.initialised) and name not in _NOT_RESET:
                    store[name] = 0.0
        for name in self.actuators:
            value = self.variables.get(name)
            initialised = value is not None and (value.__class__ is _float or value.initialised)
            self.variables[name] = NULL if initialised else UNINITIALISED_NULL

    def initialise_set_variables(self) -> None:
        """Set to 0 the variables that the programs set and have not been set yet.

        EnergyPlus runs the programs once before the first environment (to start the simulation, without
        the callbacks of its API), and then sets to 0 the variables that they set. With this method, the
        programs that read a variable before setting it at the beginning of an environment work as in
        EnergyPlus.
        """
        for program, names in self._set_names.items():
            for name in names:
                store = self.variables if name in self.global_names else self.local_variables[program]
                value = store.get(name, UNINITIALISED_NULL)
                if name not in self.actuators and value.__class__ is not _float and not value.initialised:
                    store[name] = 0.0

    def get(self, name: str, program: Optional[str] = None) -> Optional[float]:
        """The number of a global variable, or of a local variable of a program (None if it is not a number)."""
        store = self.variables if program is None else self.local_variables[program.upper()]
        value = store.get(name.upper())
        return value if value.__class__ is _float else None

    def value(self, name: str, program: Optional[str] = None):
        """The value of a variable: a float, NULL, UNINITIALISED_NULL, UNINITIALISED_NUMBER or UNINITIALISED_ERROR, or
        None if it has never been set."""
        store = self.variables if program is None else self.local_variables[program.upper()]
        return store.get(name.upper())

    def set(self, name: str, value: Optional[float]) -> None:
        """Set a global variable (for instance, a sensor or a built-in variable); None sets Null."""
        self.variables[name.upper()] = NULL if value is None else float(value)


def variables_in_programs(programs: Mapping[str, Sequence[str]]) -> Dict[str, set]:
    """The names of the variables that each program reads or sets (for checks and tests)."""
    return {name.upper(): _read_variables(_parse_statements(name, lines), set()) for name, lines in programs.items()}
