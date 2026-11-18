from abc import ABC, abstractmethod
import inspect
import sys

class ParseContext:
    def __init__(self, args: list, start=0):
        self.args = args
        self.index = start
        self.capture = {}

    @property
    def current_arg(self):
        if self.index >= len(self.args):
            #I probably will want to make this a custom error later
            raise IndexError(f"Invalid arguments given. Only {len(self.args)} {"was" if len(self.args) == 1 else "were"} given.")
        return self.args[self.index]

class MatchError(Exception):
    """Raised when Node doesn't match the current argument"""

class ConversionError(Exception):
    """Raised when a captured argument cannot be converted to the specified type"""

class StructureError(Exception):
    """Raised when the instantiated command tree is an invalid structure"""
    
class Node(ABC):
    def __init__(self):
        self.parent: 'Node' = None
        self.next: list['Node'] = []

    @abstractmethod
    def parse(self, context: ParseContext):
        pass
    def parse_next(self, context: ParseContext, *, increment_index=True):
        if increment_index:
            context.index += 1
        for branch in self.next:
            try:
                return branch.parse(context)
            except MatchError:
                continue
        raise MatchError(f"Invalid arguments: No valid branches found. Ended on '{context.current_arg}'")

    def add_child(self, node: 'Node'):
        self.next.append(node)
        node.parent = self

    def add_children(self, nodes: list['Node']):
        self.next.extend(nodes)
        for node in nodes:
            node.parent = self

    def with_child(self, node: 'Node'):
        self.add_child(node)
        return self
    
    def with_children(self, nodes: list['Node']):
        self.add_children(nodes)
        return self

class RootNode(Node):
    def parse(self, context):
        self.parse_next(context, increment_index=False)

class LiteralNode(Node):
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def parse(self, context):
        if self.value == context.current_arg:
            self.parse_next(context)
        else:
            raise MatchError

class CaptureNode(Node):
    def __init__(self, key: str, datatype: type = str):
        super().__init__()
        self.key = key
        self.datatype = datatype

    def parse(self, context):
        coerced_arg = self.datatype(context.current_arg)
        context.capture[self.key] = coerced_arg
        self.parse_next(context)

class RemainderNode(Node):
    #TODO?: Type coercion
    def __init__(self, key: str):
        super().__init__()
        self.key = key

    def parse(self, context):
        remaining_args = context.args[context.index:]
        context.capture[self.key] = remaining_args
        context.index = len(context.args)-1
        self.parse_next(context)

    def parse_next(self, context, *, is_root=False):
        if len(self.next) != 1 or not isinstance(self.next[0], FunctionNode):
            raise StructureError(f"The only child of a RemainderNode must be a FunctionNode.")
        return super().parse_next(context)

class FunctionNode(Node):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def parse(self, context):
        #TODO?: I might want to raise an error if there are extra arguments still at this point.
        sig = inspect.signature(self.func)
        parameters = list(sig.parameters.keys())
        capture = {key: value for key, value in context.capture.items() if key in parameters}
        #print(f"Running {self.func.__name__}() with this capture: {capture}")
        return self.func(**capture)

def print_rest(rem):
    print(f"{rem=}")

if __name__ == "__main__":
    context = ParseContext(sys.argv, 1)

    root = RootNode().with_child(
        LiteralNode("-p").with_child(
            RemainderNode("rem").with_child(
                LiteralNode("fail").with_child(
                    FunctionNode(print_rest)
                )
            )
        )
    )

    root.parse(context)