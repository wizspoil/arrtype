from typing import Any, Union

from iced_x86 import Code, Decoder, Instruction, Register
from memobj import MemoryObject, MemoryProperty, Pointer, Void
from memobj.process import Process, WindowsProcess


class SharedPointerToType(MemoryProperty):
    def from_memory(self) -> Any:
        from arrtype.memory.types import Type
        
        print(f"{hex(self.offset)=} {hex(self.memory_object.base_address)=}")
        
        sub_pointer = self.process.read_formatted(
            self.memory_object.base_address + self.offset,
            self.pointer_format_string
        )
        
        print(f"{hex(sub_pointer)=}")
        
        type_pointer = self.process.read_formatted(
            sub_pointer + 0x4,
            self.pointer_format_string
        )
        
        print(f"{hex(type_pointer)=}")
        
        return Type(address=type_pointer, process=self.process)


class CppString(MemoryProperty):
    def __init__(self, offset: int | None, encoding: str = "utf-8", sso_size: int = 16):
        super().__init__(offset)
        self.encoding = encoding
        self.sso_size = sso_size

    def from_memory(self) -> Any:
        length = self.memory_object.memobj_process.read_formatted(
            self.memory_object.base_address + self.offset + 16,
            self.pointer_format_string,
        )
        capacity = self.memory_object.memobj_process.read_formatted(
            self.memory_object.base_address + self.offset + 20,
            self.pointer_format_string,
        )

        if capacity >= self.sso_size:
            address = self.read_formatted_from_offset(self.pointer_format_string)
        else:
            address = self.memory_object.base_address + self.offset

        try:
            return self.memory_object.memobj_process.read_memory(address, length).decode(self.encoding)
        except UnicodeDecodeError:
            raise
            return ""

    def to_memory(self, value: Any):
        raise NotImplementedError()

    def memory_size(self) -> int:
        return 32


# TODO rework this into a MemoryObject
class SharedVector(MemoryProperty):
    def __init__(
            self,
            offset: int | None,
            max_size: int = 500,
            object_type: type[MemoryObject] | str | None = None,
    ):
        super().__init__(offset)
        self.max_size = max_size
        self.object_type = object_type

    def from_memory(self) -> Any:
        head = self.read_formatted_from_offset(self.pointer_format_string)
        tail = self.memory_object.memobj_process.read_formatted(
            self.memory_object.base_address + self.offset + 4,
            self.pointer_format_string
        )

        size = tail - head
        element_number = size // 8

        # less than 0 on dealloc
        if size <= 0:
            return []

        if element_number > self.max_size:
            raise ValueError(f"Size was {element_number} and the max was {self.max_size}")

        element_data = self.memory_object.memobj_process.read_memory(head, size)

        pointers = []
        data_position = 0
        for _ in range(element_number):
            pointers.append(int.from_bytes(element_data[data_position:data_position+4], "little", signed=False))
            # 8 byte pointer, 8 byte ref data*
            data_position += 8

        if self.object_type is None:
            return pointers

        if isinstance(self.object_type, str):
            typed_object_type = MemoryObject.__memory_object_instances__.get(self.object_type)

            if typed_object_type is None:
                raise ValueError(f"No MemoryObject type named {self.object_type}")

            self.object_type = typed_object_type

        objects = []
        for pointer in pointers:
            objects.append(self.object_type(
                address=pointer,
                process=self.memory_object.memobj_process,
            ))

        return objects

    def to_memory(self, value: Any):
        pass

    def memory_size(self) -> int:
        return self.pointer_size * 3


# TODO: must be updated
class PropertyEnumOptions(MemoryProperty):
    def read_cpp_string(self, address: int, *, sso_size: int = 16, encoding: str = "utf-8"):
        length = self.memory_object.memobj_process.read_formatted(
            address + 16,
            self.pointer_format_string,
        )
        
        capacity = self.memory_object.memobj_process.read_formatted(
            address + 20,
            self.pointer_format_string,
        )
        
        assert length <= capacity, f"{length=} {capacity=}"

        if length >= sso_size:
            address = self.memory_object.memobj_process.read_formatted(address, self.pointer_format_string)
        else:
            address = address

        try:
            return self.memory_object.memobj_process.read_memory(address, length).decode(encoding)
        except UnicodeDecodeError:
            return ""

    def from_memory(self) -> Any:
        start = self.read_formatted_from_offset(self.pointer_format_string)

        if start == 0:
            return None

        end = self.memory_object.memobj_process.read_formatted(
            self.memory_object.base_address + self.offset + self.pointer_size,
            self.pointer_format_string
        )

        total_size = end - start

        current = start
        enum_opts = {}
        for entry in range(total_size // 0x3C):
            name = self.read_cpp_string(current + 0x24)

            # TODO: int variants are always returned as string
            if string_value := self.read_cpp_string(current + 4):
                enum_opts[name] = string_value
            else:
                raise NotImplementedError("sus")
                # TODO: check if this is correct
                enum_opts[name] = self.memory_object.memobj_process.read_formatted(
                    current + 0x1C, "I"
                )

            current += 0x3C

        return enum_opts

    def to_memory(self, value: Any):
        raise NotImplementedError()

    def memory_size(self) -> int:
        return self.pointer_size * 2


class ContainerName(MemoryProperty):
    def from_memory(self) -> Any:
        # noinspection PyUnresolvedReferences
        vtable = self.memory_object.vtable
        lea_func_addr = self.memory_object.memobj_process.read_formatted(vtable + 0x4, self.pointer_format_string)
        name_offset = self.memory_object.memobj_process.read_formatted(lea_func_addr + 1, "i")
        # I need to read a null terminated string, but I can't use my MemoryProperty
        # this is an oversight
        string_bytes = self.memory_object.memobj_process.read_memory(
            name_offset,
            20,
        )

        end = string_bytes.find(b"\x00")

        if end == 0:
            return ""

        if end == -1:
            raise ValueError("No null end")

        return string_bytes[:end].decode()

    def to_memory(self, value: Any):
        raise NotImplementedError()

    # TODO: same as below
    def memory_size(self) -> int:
        return 0


class ContainerIsDynamic(MemoryProperty):
    def from_memory(self) -> Any:
        # noinspection PyUnresolvedReferences
        vtable = self.memory_object.vtable
        get_dynamic_func_addr = self.memory_object.memobj_process.read_formatted(
            vtable + 0x10, self.pointer_format_string
        )

        get_dynamic_bytes = self.memory_object.memobj_process.read_memory(get_dynamic_func_addr, 3)

        decoder = Decoder(32, get_dynamic_bytes)

        xor_al_al = Instruction.create_reg_reg(
            Code.XOR_R8_RM8,
            Register.AL,
            Register.AL
        )
        mov_al_1 = Instruction.create_reg_i32(
            Code.MOV_R8_IMM8,
            Register.AL,
            1
        )

        for instruction in decoder:
            if instruction == xor_al_al:
                return False
            elif instruction == mov_al_1:
                return True
            # Note: ret should never enter here
            else:
                raise RuntimeError(f"Invalid dynamic container instruction: {instruction=}")

    def to_memory(self, value: Any):
        raise NotImplementedError()

    # TODO: this should be a Pointer
    def memory_size(self) -> int:
        return 8
