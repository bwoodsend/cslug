from pathlib import Path
import collections
import warnings
import io

from cslug import exceptions, _stdlib, c_parse, Types

warnings.filterwarnings("error", category=exceptions.TypeParseWarning)

source = Path(__file__).with_name("stdlib.md").read_text().split("\n")

for (i, line) in enumerate(source):
    if "------" in line:
        break
table_source = source[i + 1:]
table = [[j.strip() for j in i.split("|")] for i in table_source if i]

functions = collections.defaultdict(list)

Function = collections.namedtuple("Function",
                                  ["name", "prototype", "description", "index"])

unparsable = []
unavailable = []

for (_, name, headers, prototype, description, _) in table:
    for (index, header) in enumerate(headers.split()):
        try:
            name = c_parse.parse_function(prototype.rstrip(";"))[0]
        except (exceptions.TypeParseWarning, ValueError) as ex:
            # Ignore anything that cslug doesn't understand.
            continue
        function = Function(name, prototype, description, not index)
        functions[header].append(function)

stdlib_json = Path(__file__, "..", "..", "cslug", "stdlib.json").resolve()
stdlib_h = io.StringIO("".join(
    j.prototype + "\n" for i in functions.values() for j in i))

types = Types(stdlib_json, headers=stdlib_h, compact=False)
types.init_from_source()
types.write(stdlib_json)

functions = {
    key: [
        function for function in functions[key]
        if function.name in types.functions
    ] for key in functions
}
