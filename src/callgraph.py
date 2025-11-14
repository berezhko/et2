import pycallgraph2
from functools import wraps
from typing import Callable, Any, List

def callgraph(exclude: List[str] = [], groups: List[str] = []) -> Callable[..., Any]:
    '''
    Декоратор формирующий граф вызовов декорируемой функции:
    
    @callgraph(exclude=['pandas.*', 'numpy.*'], groups=['src.station.*', 'src.elements.*'])
    def func():
        pass

    func()
    '''
    def callgraph_decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(function)
        def wrapped_function(*args: Any, **kwargs: Any) -> Any:
            config = pycallgraph2.Config()
            config.trace_filter = pycallgraph2.GlobbingFilter(exclude=exclude)
            config.trace_grouper = pycallgraph2.Grouper(groups=groups)
            output = pycallgraph2.output.GraphvizOutput()
            output.output_file = f'viz-{function.__name__}.png'
            
            with pycallgraph2.PyCallGraph(output=output, config=config):
                result = function(*args, **kwargs)
            return result
        return wrapped_function
    return callgraph_decorator