from __future__ import annotations

import logging
from typing import TypeVar, Generic, Type, Annotated, Optional

from pydantic import BaseModel, model_validator, Field

from eidos.agent_os import AgentOS
from eidos.util.class_utils import for_name, fqn

T = TypeVar('T', bound=BaseModel)


class Specable(Generic[T]):
    """
    A generic type which can be used to describe a specable type. Specable types are expected to accept "spec" in kwarg.
    If Specable is not used, There will be no spec validation and the spec will be passed through as-is.
    """
    spec: T

    def __init__(self, spec: T, **kwargs: object):
        self.spec = spec


B = TypeVar('B')
D = TypeVar('D')


class Reference(BaseModel):
    """
    Used to create references to other classes. t is designed to be used with two type variables, `B` and `D` which are
    the type bound and default type respectively. Neither are required, and if only one type is provided it is assumed
    to be the bound. Bound is used as the default if no default is provided.

    Examples:
        Reference(implementation=fqn(Foo)                           # Returns an instance of Foo
        Reference[FooBase](implementation=fqn(Foo).instantiate()    # Returns an instance of Foo
        Reference[FooBase](implementation=fqn(Bar)                  # Raises ValueError
        Reference[FooBase, Foo]().instantiate()                     # Returns an instance of Foo
        Reference[FooBase]().instantiate()                          # Returns an instance of FooBase

    Attributes:
        _bound: This is a type variable `B` that represents the bound type of the reference. It defaults to `object`.
        _default: This is a type variable `D` that represents the default type of the reference. It defaults to `None`.
        implementation: This is a string that represents the fully qualified name of the class that the reference points to. It is optional and can be set to `None`.
        spec: This is a dictionary that can hold any additional specifications for the reference. It is optional and can be set to `None`.

    Methods:
        instantiate: This method is used to create an instance of the class that the reference points to.
    """
    _bound: Type[B] = object
    _default: Type[D] = None
    implementation: str = None
    spec: Optional[dict] = None

    def __class_getitem__(cls, params):
        if not isinstance(params, tuple):
            params = (params, params)

        class _Reference(Reference):
            _bound = params[0]
            _default = params[1]
            @model_validator(mode='before')
            def _dump_ref(cls, value):
                return value.model_dump(exclude_defaults=True) if isinstance(value, Reference) else value

        return _Reference

    @model_validator(mode='before')
    def _transform(cls, value):
        if isinstance(value, str):
            split = list(value.split("."))
            bucket = split.pop(0)
            name = ".".join(split) if split else "DEFAULT"
            found = AgentOS.get_resource(bucket, name)
            return found.model_dump(exclude={'apiVersion', 'kind', 'metadata'})
        else:
            if 'spec' in value and isinstance(value['spec'], BaseModel):
                value['spec'] = value['spec'].model_dump(exclude_defaults=True)
            return value

    @model_validator(mode='after')
    def _validate(self):
        if not self.implementation and self._default:
            self.implementation = fqn(self._default)
        if not self.implementation:
            raise ValueError(f'Unable to determine implementation for "{self}"')

        self._build_reference_spec()
        return self

    def _build_reference_spec(self):
        reference_class = self._get_reference_class()
        if issubclass(reference_class, Specable):
            bases = getattr(reference_class, '__orig_bases__', [])
            specable = next((base for base in bases if getattr(base, '__origin__', None) is Specable), None)
            if specable:
                spec_type, = specable.__args__
                return spec_type.model_validate(self.spec or {})
            else:
                logging.warning(f'Unable to find Specable definition on "{reference_class}", skipping validation')
                return self.spec
        else:
            return self.spec

    def _get_reference_class(self):
        return for_name(self.implementation, self._bound or object)

    def instantiate(self, *args, **kwargs):
        spec = self._build_reference_spec()
        if spec is not None:
            kwargs['spec'] = spec
        return self._get_reference_class()(*args, **kwargs)


class AnnotatedReference(Reference):
    """
    Helper class to manage References with defaults so that they do not need to be declared.
    Wraps the returned type in Annotated so that the default can be defined in the type annotation.

    This is important since defaults should be partially defined so that partial references can be defined.
    Ie, providing only the spec and accepting the default implementation or defining the implementation only, but
    accepting that implementation's default spec.

    One may be tempted to leave the Default off of the type annotation since it is declared later, but this would
    prevent users from overriding just the spec

    Example:
        class MySpec(BaseModel):
            ref1: AnnotatedReference[MyBound, MyDefaultImpl)] = Field(description="My description")

    Note:
        The description can still be added via a Field annotation without affecting default behavior
    """
    def __class_getitem__(cls, params) -> Type[Reference]:
        return Annotated[Reference[params], Field(default=Reference[params]())]