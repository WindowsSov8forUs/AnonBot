import re
from enum import IntEnum
from dataclasses import field, dataclass
from typing import Any, Union, Literal, TypeVar, Callable, Iterable, Optional, TypeAlias, TypedDict, cast

T = TypeVar('T')

def escape(text: str, inline: bool = False) -> str:
    '''转义字符串'''
    result = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return result.replace('"', '&quot;') if inline else result

def unescape(text: str) -> str:
    '''反转义字符串'''
    result = text.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    result = re.sub(r'&#(\d+);', lambda m: m[0] if m[1] == '38' else chr(int(m[1])), result)
    result = re.sub(r'&#x([0-9a-f]+);', lambda m: m[0] if m[1] == '26' else chr(int(m[1], 16)), result)
    return re.sub('&(amp|#38|#x26);', '&', result)

def uncapitalize(text: str) -> str:
    '''首字母小写'''
    return text[:1].lower() + text[1:]

def camel_case(text: str) -> str:
    '''转换为驼峰命名'''
    return re.sub('[_-]([a-z])', lambda m: m[0][1:].upper(), text)

def param_case(text: str) -> str:
    return re.sub(
        '.[A-Z]+', lambda m: m[0][0] + '-' + m[0][1:].lower(), uncapitalize(text).replace('_', '-')
    )

def snake_case(text: str) -> str:
    '''转换为蛇形命名'''
    return re.sub(
        '.[A-Z]', lambda m: m[0][0] + '_' + m[0][1].lower(), uncapitalize(text).replace('-', '_')
    )

def ensure_list(value: Union[T, list[T], None]) -> list[T]:
    return value if isinstance(value, list) else [value] if value is not None else []

S = TypeVar('S')
Fragment: TypeAlias = Union[str, 'Element', list[Union[str, 'Element']]]
Render: TypeAlias = Callable[[dict, list['Element'], S], T]
Visitor: TypeAlias = Callable[['Element', S], T]

def make_element(content: Union[str, bool, int, float, 'Element']) -> Optional['Element']:
    if isinstance(content, Element):
        return content
    if isinstance(content, (bool, int, float)):
        return Element(type='text', attrs={'text': str(content)})
    if isinstance(content, str) and content:
        return Element(type='text', attrs={'text': content})
    if content is not None:
        raise ValueError(f'Invalid content: {content}')

def make_elements(content: Fragment) -> list['Element']:
    if isinstance(content, list):
        result = [make_element(item) for item in content]
    else:
        result = [make_element(content)]
    return [item for item in result if item]

class Element:
    type: str
    attrs: dict[str, Any]
    children: list['Element']
    source: Optional[str]
    
    def __init__(
        self,
        type: Union[str, Render[Fragment, Any]],
        attrs: Optional[dict[str, Any]] = None,
        *children: Fragment
    ) -> None:
        self.attrs = {}
        self.children = []
        if attrs:
            for k, v in attrs.items():
                if v is None:
                    continue
                if k == 'children':
                    self.children.extend(ensure_list(v))
                else:
                    self.attrs[camel_case(k)] = v
        for child in children:
            self.children.extend(make_elements(child))
        if not isinstance(type, str):
            self.type = 'component'
            self.attrs['is'] = type
        else:
            self.type = type
    
    def tag(self) -> str:
        if self.type == 'component':
            if is_ := self.attrs.get('is'):
                return is_.__name__
            return 'component'
        return self.type
    
    def attributes(self) -> str:
        def _attr(key: str, value: Any) -> str:
            if value is None:
                return ''
            key = param_case(key)
            if value is True:
                return f' {key}'
            if value is False:
                return f' no-{key}'
            return f' {key}="{escape(str(value), True)}"'
        return ''.join(_attr(k, v) for k, v in self.attrs.items())
    
    def dumps(self, strip: bool = False) -> str:
        if self.type == 'text' and 'text' in self.attrs:
            return self.attrs['text'] if strip else escape(self.attrs['text'])
        inner = ''.join(item.dumps(strip) for item in self.children)
        if strip:
            return inner
        attrs = self.attributes()
        tag = self.tag()
        if not self.children:
            return f'<{tag}{attrs}/>'
        return f'<{tag}{attrs}>{inner}</{tag}>'
    
    def __str__(self) -> str:
        return self.dumps()
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.type!r}, {self.attrs!r}, {self.children!r})'

Combinator: TypeAlias = Literal[' ', '>', '+', '~']

@dataclass
class Selector:
    type: str
    combinator: Combinator

comb_pat = re.compile(' *([ >+~]) *')

def parse_selector(input: str) -> list[list[Selector]]:
    def _quert(query: str) -> list[Selector]:
        selectors = []
        combinator = ' '
        while mat := comb_pat.search(query):
            selectors.append(
                Selector(
                    query[:mat.start()],
                    combinator
                )
            )
            combinator = cast(Combinator, mat.group(1))
            query = query[mat.end():]
        selectors.append(Selector(query, combinator))
        return selectors
    return [_quert(query) for query in input.split(',')]

def select(source: Union[str, list[Element]], query: Union[str, list[list[Selector]]]) ->list[Element]:
    if not source or not query:
        return []
    if isinstance(source, str):
        source = parse(source)
    if isinstance(query, str):
        query = parse_selector(query)
    if not query:
        return []
    adjacent: list[list[Selector]] = []
    results = []
    for index, element in enumerate(source):
        inner: list[list[Selector]] = []
        local = [*query, *adjacent]
        adjacent = []
        matched = False
        for group in local:
            type_ = group[0].type
            combinator = group[0].combinator
            if type_ == element.type or type_ == '*':
                if len(group) == 1:
                    matched = True
                elif group[1].combinator in (' ', '>'):
                    inner.append(group[1:])
                elif group[1].combinator == '+':
                    adjacent.append(group[1:])
                else:
                    query.append(group[1:])
            if combinator == ' ':
                inner.append(group)
        if matched:
            results.append(source[index])
        results.extend(select(element.children, inner))
    return results

def evaluate(expression: str, context: dict[str, Any]) -> Any:
    try:
        return eval(expression, None, context)
    except Exception:
        return ''

def interpolate(expression: str, context: dict[str, Any]) -> Any:
    expression = expression.strip()
    if not re.fullmatch(r'[\w.]+', expression):
        answer = evaluate(expression, context)
        return '' if answer is None else answer
    value = context
    for part in expression.split('.'):
        if part not in value:
            return ''
        value = value[part]
        if value is None:
            return ''
    return '' if value is None else value

tag_pat_1 = re.compile(r'(?P<comment><!--[\s\S]*?-->)|(?P<tag><(/?)([^!\s>/]*)([^>]*?)\s*(/?)>)')
tag_pat_2 = re.compile(r'(?P<comment><!--[\s\S]*?-->)|(?P<tag><(/?)([^!\s>/]*)([^>]*?)\s*(/?)>)|(?P<curly>\{(?P<derivative>[@:/#][^\s\}]*)?[\s\S]*?\})')
attr_pat_1 = re.compile(r'([^\s=]+)(?:="(?P<value1>[^"]*)"|=\'(?P<value2>[^\']*)\')?', re.S)
attr_pat_2 = re.compile(r'([^\s=]+)(?:="(?P<value1>[^"]*)"|=\'(?P<value2>[^\']*)\'|=\{(?P<value3>[^\}]+)\})?', re.S)

class Position(IntEnum):
    OPEN = 0
    CLOSE = 1
    EMPTY = 2
    CONTINUE = 3

@dataclass
class Token:
    type: Literal['angle', 'curly']
    name: str
    position: Position
    source: str
    extra: str
    children: dict[str, list[Union[str, 'Token']]] = field(default_factory=dict)

class StackItem(TypedDict):
    token: Token
    slot: str

def fold_tokens(tokens: list[Union[str, Token]]) -> list[Union[str, Token]]:
    stack: list[StackItem] = [
        {
            'token': Token(
                type='angle',
                name='template',
                position=Position.OPEN,
                source='',
                extra='',
                children={'default': []}
            ),
            'slot': 'default'
        }
    ]
    
    def push_token(*tokens: Union[str, Token]) -> None:
        token = stack[0]['token']
        token.children[stack[0]['slot']].extend(tokens)
    
    for token in tokens:
        if isinstance(token, str):
            push_token(token)
            continue
        if token.position == Position.CLOSE:
            if stack[0]['token'].name == token.name:
                stack.pop(0)
        elif token.position == Position.CONTINUE:
            stack[0]['token'].children[token.name] = []
            stack[0]['slot'] = token.name
        elif token.position == Position.OPEN:
            push_token(token)
            token.children = {'default': []}
            stack.insert(0, {'token': token, 'slot': 'default'})
        else:
            push_token(token)
    return stack[-1]['token'].children['default']

def parse_tokens(tokens: list[Union[str, Token]], context: Optional[dict[str, Any]] = None) -> list[Element]:
    result: list[Element] = []
    for token in tokens:
        if isinstance(token, str):
            result.append(Element(type='text', attrs={'text': token}))
        elif token.type == 'angle':
            attrs = {}
            attr_pat = attr_pat_2 if context is not None else attr_pat_1
            while mat := attr_pat.search(token.extra):
                key = mat.group(1)
                groupdict = mat.groupdict()
                value = groupdict.get('value1') or groupdict.get('value2')
                value3 = groupdict.get('value3')
                if value3 and context is not None:
                    attrs[key] = interpolate(value3, context)
                elif value is not None:
                    attrs[key] = unescape(value)
                elif key.startswith('no-'):
                    attrs[key[3:]] = False
                else:
                    attrs[key] = True
                token.extra = token.extra[mat.end():]
            result.append(
                Element(
                    token.name,
                    attrs,
                    *parse_tokens(token.children['default'], context) if token.children else []
                )
            )
        elif not token.name:
            result.extend(make_elements(interpolate(token.extra, context or {})))
        elif token.name == 'if':
            if evaluate(token.extra, context or {}):
                result.extend(parse_tokens(token.children['default'], context))
            else:
                result.extend(parse_tokens(token.children.get('else', []), context))
        elif token.name == 'each':
            expression, ident = re.split(r'\s+as\s+', token.extra)
            items = interpolate(expression, context or {})
            if not items or not isinstance(items, Iterable):
                continue
            for item in items:
                result.extend(parse_tokens(token.children['default'], {**(context or {}), ident: item}))
    return result

def parse(src: str, context: Optional[dict[str, Any]] = None):
    tokens: list[Union[str, Token]] = []
    
    def push_text(text: str) -> None:
        if text:
            tokens.append(text)
    
    def parse_content(source: str, _start: bool, _end: bool) -> None:
        source = unescape(source)
        if _start:
            source = re.sub(r'^\s*\n\s*', '', source, re.MULTILINE)
        if _end:
            source = re.sub(r'\s*\n\s*$', '', source, re.MULTILINE)
        push_text(source)
    
    tag_pat = tag_pat_2 if context is not None else tag_pat_1
    strip_start = True
    
    while tag_mat := tag_pat.search(src):
        groupdict = tag_mat.groupdict()
        strip_end = not bool(groupdict.get('curly'))
        parse_content(src[:tag_mat.start()], strip_start, strip_end)
        strip_start = strip_end
        src = src[tag_mat.end():]
        groups = tag_mat.groups()
        close, type_, extra, empty = groups[2], groups[3], groups[4], groups[5]
        if groupdict.get('comment'):
            continue
        if groupdict.get('curly'):
            name = ''
            position = Position.EMPTY
            if groupdict.get('derivative'):
                name = groupdict['derivative'][1:]
                position = {
                    '@': Position.EMPTY,
                    '#': Position.OPEN,
                    '/': Position.CLOSE,
                    ':': Position.CONTINUE
                }[groupdict['derivative'][0]]
            tokens.append(
                Token(
                    type='curly',
                    name=name,
                    position=position,
                    source=groupdict['curly'],
                    extra=groupdict['curly'][
                        1 + (len(groupdict['derivative']) if groupdict.get('derivative') else 0):-1
                    ]
                )
            )
            continue
        tokens.append(
            Token(
                type='angle',
                name=type_ or 'template',
                position=Position.CLOSE if close else Position.EMPTY if empty else Position.OPEN,
                source=tag_mat[0],
                extra=extra
            )
        )
    parse_content(src, strip_start, True)
    return parse_tokens(fold_tokens(tokens), context)
