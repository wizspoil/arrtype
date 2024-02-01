from memobj.property import *

from .properties import *


# NOTE: fixed
class HashNode(MemoryObject):
    left: "HashNode" = DereffedPointer(0x0, "HashNode")
    parent: "HashNode" = DereffedPointer(0x4, "HashNode")
    right: "HashNode" = DereffedPointer(0x8, "HashNode")
    hash: int = Signed4(0xC)
    is_leaf: bool = Bool(0x15)
    node_data: "Type" = DereffedPointer(0x10, "Type")


class Type(MemoryObject):
    name: str = CppString(0x20) # fixed
    hash: int = Signed4(0x38) # fixed
    size: int = Signed4(0x40) # fixed
    name_2: str = CppString(0x48) # fixed
    is_pointer: bool = Bool(0x60) # fixed
    if_ref: bool = Bool(0x61) # fixed
    property_list: "PropertyList" = DereffedPointer(0x64, "PropertyList") # fixed

    def get_bases(self) -> list["PropertyList"]:
        if (fields := self.property_list) is None:
            return []

        bases = []
        current_base = fields
        while (base_type := current_base.base_class_list) is not None:
            bases.append(base_type)
            current_base = base_type

        return bases


class PropertyList(MemoryObject):
    is_singleton: bool = Bool(0x5) # fixed
    offset: int = Signed4(0x8) # fixed
    base_class_list: "PropertyList" = DereffedPointer(0xC, "PropertyList") # fixed
    type: "Type" = DereffedPointer(0x10, "Type") # fixed
    pointer_version: "Type" = DereffedPointer(0x18, "Type") # fixed
    properties: list["Property"] = SharedVector(0x34, object_type="Property") # fixed
    functions: list["Function"] = SharedVector(0x44, object_type="Function") # fixed
    name: str = CppString(0x74, sso_size=16) # fixed


class Property(MemoryObject):
    list: "PropertyList" = DereffedPointer(0x1C, "PropertyList") # likely fixed
    container: "Container" = DereffedPointer(0x20, "Container") # likely fixed
    index: int = Signed4(0x28) # likely fixed
    name: str = DereffedPointer(0x2C, NullTerminatedString(None, search_size=100)) # fixed
    name_hash: int = Signed4(0x30) # likely fixed
    full_hash: int = Signed4(0x34) # likely fixed
    offset: int = Signed4(0x38) # fixed
    type: "Type" = DereffedPointer(0x3C, "Type") # fixed
    flags: int = Signed4(0x44) # fixed
    note: str = CppString(0x48) # fixed
    ps_info: str = CppString(0x4C) # likely fixed 
    enum_options = PropertyEnumOptions(0x54) # fixed 


# class Function(MemoryObject):
#     list: "PropertyList" = DereffedPointer(0x18, "PropertyList") # likely fixed
#     name: str = CppString(0x20) # maybe fixed 
#     details: "FunctionDetails" = DereffedPointer(0x58, "FunctionDetails")


class Container(MemoryObject):
    vtable: int = Unsigned4(0x0) # fixed
    name: str = ContainerName(None) # fixed
    is_dynamic: bool = ContainerIsDynamic(None) # fixed


# class FunctionDetails(MemoryObject):
#     called_function: int = Unsigned8(0x30)
#     something: int = Unsigned4(0x3C)
