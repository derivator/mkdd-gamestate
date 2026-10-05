import struct

import dolphin_memory_engine as dme


def hex_(o):
    if isinstance(o, int):
        return hex(o)
    if isinstance(o, tuple):
        return tuple(map(hex_, o))
    if isinstance(o, list):
        return list(map(hex_, o))
    if isinstance(o, dict):
        return {hex_(key): hex_(o[key]) for key in o}

    return o


def dbg(x):
    print(hex_(x))
    return x


class Value:
    """Used in symbol definitions to mark a struct (i.e. non-fundamental type) field as embedded instead of pointer"""

    def __init__(self, ty):
        self.ty = ty
        self.size = ty.get("__size")


def tresolve(ty: dict, spec: list[str | tuple | list[str]]):
    result = []
    array_stride = 4  # assuming field is a pointer to ty
    is_value = False
    for field in spec:
        if isinstance(field, str):
            ty, offset = ty[field]
            if is_value:
                result[-1] += offset
            else:
                result.append(offset)

            if isinstance(ty, Value):
                array_stride = ty.size
                ty = ty.ty
                is_value = True
            else:
                if isinstance(ty, str):
                    array_stride = struct.calcsize(ty)
                else:
                    array_stride = 4

                is_value = False

        elif isinstance(field, tuple):  # probably a fundamental type leaf node
            assert len(field) == 2
            ty, offset = field
            result.append(offset)

        elif isinstance(field, list):
            assert len(field) == 1
            result[-1] = result[-1] + array_stride * field[0]
        else:
            raise TypeError(f"bad address spec: {spec!r}")

    if is_value:
        ty = Value(ty)
    try:
        return (ty, dme.follow_pointers(result[0], result[1:]))
    except RuntimeError:
        return None


def resolve(spec):
    if isinstance(spec, int):
        return spec
    elif isinstance(spec, list):
        if len(spec) == 1:
            return spec[0]
        else:
            try:
                return dme.follow_pointers(spec[0], spec[1:])
            except RuntimeError:
                return None
    else:
        raise TypeError(f"bad address spec: {spec!r}")


def r_byte(spec):
    addr = resolve(spec)
    if addr is None:
        return None
    try:
        return dme.read_byte(addr)
    except RuntimeError:
        return None


def r_word(spec) -> int | None:
    addr = resolve(spec)
    if addr is None:
        return None
    try:
        return dme.read_word(addr)
    except RuntimeError:
        return None


def r_float(spec):
    addr = resolve(spec)
    if addr is None:
        return None
    try:
        return dme.read_float(addr)
    except RuntimeError:
        return None


def r_vector(spec):
    addr = resolve(spec)
    if addr is None:
        return None
    try:
        return [
            dme.read_float(addr),
            dme.read_float(addr + 4),
            dme.read_float(addr + 8),
        ]
    except RuntimeError:
        return None


def r_mtx(spec):
    addr = resolve(spec)
    if addr is None:
        return None
    try:
        return struct.unpack(">12f", dme.read_bytes(addr, 12 * 4))
    except RuntimeError:
        return None


def round_floats(o):
    if isinstance(o, float):
        return round(o, 2)
    if isinstance(o, dict):
        return {k: round_floats(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [round_floats(x) for x in o]
    return o


def r_struct(globals, spec, default=None):
    res = tresolve(globals, spec)
    if not res:
        return default

    ty, addr = res
    # read a pointer if the chain ends before a fundamental type is reached
    if isinstance(ty, dict):
        ty = "I"
    elif isinstance(ty, Value):
        return addr

    size = struct.calcsize(ty)
    if addr is None:
        return default
    try:
        res = struct.unpack(f">{ty}", dme.read_bytes(addr, size))
        if len(res) == 1:
            res = res[0]
        return res
    except RuntimeError:
        return default
