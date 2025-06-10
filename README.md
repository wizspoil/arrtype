# arrtype
A type dumper for pirate101

## install
`pip install arrtype`

## usage
an instance of pirate101 must be open for all commands

```shell
# generate a normal dump in the current directory named after the current revision
$ arrtype
# generate a dump with indent level 4 (for human reading)
$ arrtype --indent 4
# generate a version 1 dump (wizwalker)
$ arrtype --version 1 --indent 4
```

## support
discord: <https://discord.gg/wcftyYm6qe>

## json spec

```json5
{
  "version": 2,
  "classes": {
    "class hash (as string)": {
      "bases": ["class base classes"],
      "name": "class name",
      "singleton": true,
      "properties": {
        "property name": {
          "type": "property type",
          "id": 123,
          "offset": 123,
          "flags": 123,
          "container": "container name",
          "dynamic": true,
          "pointer": true,
          "hash": 123,
          "enum_options": {
            "option name": 123,
            // __DEFAULT is a string
            "__DEFAULT": "option name",
            // __BASECLASS is a string
            "__BASECLASS": "option name",
          }
        }
      }
    }
  }
}
```
