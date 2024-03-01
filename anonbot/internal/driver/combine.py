from typing import TYPE_CHECKING, Type, Union, TypeVar, overload

from .abstract import Mixin, Driver

D = TypeVar('D', bound='Driver')

if TYPE_CHECKING:
    class CombinedDriver(Driver, Mixin):
        ...

@overload
def combine_driver(driver: Type[D]) -> Type[D]:
    ...

@overload
def combine_driver(driver: Type[D], *mixins: Type[Mixin]) -> Type['CombinedDriver']:
    ...

def combine_driver(
    driver: Type[D], *mixins: Type[Mixin]
) -> Union[Type[D], Type['CombinedDriver']]:
    '''将一个驱动器与多个混合类组合成一个新的驱动器'''
    if not issubclass(driver, Driver):
        raise TypeError('driver must be a subclass of Driver')
    if not all(issubclass(mixin, Mixin) for mixin in mixins):
        raise TypeError('all mixins must be subclasses of Mixin')
    
    if not mixins:
        return driver

    def type_(self: 'CombinedDriver') -> str:
        return (
            driver.type.__get__(self) # type: ignore
            + '+'
            + '+'.join(mixin.type.__get__(self) for mixin in mixins) # type: ignore
        )
    
    return type(
        'CombinedDriver', (*mixins, driver), {'type': property(type_), '__init__': driver.__init__}
    ) # type: ignore
