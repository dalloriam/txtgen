# TxtGen
Blazing-fast text generation DSL.

## Description
TxtGen introduces a lightweight-yet-powerful DSL for dynamically generating text. The syntax is based on lisp 
(because - let's be honest - it's much easier to parse).

## Using the library
Parsing a TxtGen grammar and generating entities (with or without context) is extremely simple. Let's assume the
grammar defining the `greeting` entity is located in `/home/my_user/grammar.txtg`:

```python
from txtgen.interpreter import make

with open('/home/my_user/grammar.txtg') as infile:
    src = infile.read()
    
grammar = make(src)
print(grammar.generate('greeting'))
```

To bind a context at parse-time:
```python
from txtgen.interpreter import make

with open('/home/my_user/grammar.txtg') as infile:
    src = infile.read()

grammar = make(src, bind_ctx={'hello': 'world'})
```

And to use a dynamic context when generating entities:
```python
from txtgen.interpreter import make

with open('/home/my_user/grammar.txtg') as infile:
    src = infile.read()

grammar = make(src)
print(grammar.generate('greeting', ctx={'hello': 'world'}))
```

## Language Documentation

### Grammars and Entities
Since the TxtGen language is basically syntactic sugar for defining context-free grammars, the root object of any
TxtGen program is the `Grammar`. Grammars are composed of entities, which are blocks of top-level rules. 

For example, a simple grammar with two entities - `greeting` and `goodbye` - could be defined as follows:

```
(grammar
    (entity greeting "Hello, World")
    (entity goodbye "Goodbye, World")
)
```

Entities can also be composed to create more complex entities:
```
(grammar
    (entity sentence hello ".")
    (entity hello "Hello, World")
)
```

In this grammar, generating the `sentence` entity would generate "Hello, World."

### Context Placeholders
The previous examples are not super exciting however, because both entities are composed uniquely of constants,
meaning that multiple calls to generate will always yield the same output. Let's try to introduce some variety
in our generated text by using a *generation context*.

Let's suppose we define the following context in a JSON file:
```json
{
    "name": ["John", "Mary", "Jack", "Alice", "Paul", "Eric", "Mark", "Eve"]
}
```

and bind it at parse-time (see section above on how to do that) to the following grammar:
```
(grammar
    (entity greeting "Hello" "," $name "!")
)
```

Prefixing body items with `$` indicates to the interpreter that the token should be substituted by a value from context, 
which means that generating the `greeting` entity will substitute the `$name` token by a value chosen at random from 
the `name` key defined in the context, which will in turn generate sentences like "Hello, John!" or "Hello, Alice!".


### Optional Branches
The language also allows for _optional_ branches. When a body item is defined as optional, the interpreter will randomly
decide whether to include it in the output on every call to `generate()`.

For example, consider this variation on the previous example:
```
(grammar
    (entity greeting "Hello" ["there"] "," $name "!")
)
```

which would generate sentences such as "Hello there, Mary!" or "Hello, Paul!"

### Functions
Txtgen defines some functions to simplify the generation of more complex grammars. To invoke a function, simply 
create a body item that starts with the name of the function, followed by its arguments:
`(entity "some string" (function_name arg1 arg2))`. The function will be evaluated at runtime and the output
will be present in the generated sentences. The following functions are defined by the language at the moment:

* `(any *args)` => Returns at random one of the arguments on every call to `generate()`.
* `(if left=right arg_true arg_false)` => Conditional. Returns `arg_true` if the generated value of `left` 
    equals `right`, `arg_false` otherwise.
* `(repeat i arg)` => Repeat `arg` _i_ times.

### Macros
Finally, the language also supports simple macros. Macros are a way to define a pattern and apply it to multiple
entities. For instance, you could have a `sentence` macro that adds a period at the end of your entities:

```
(grammar
    (macro sentence (body) body ".")
    (entity hello<sentence> ("hello", "," "world"))
)
```

In this example, generating `hello` would apply the `sentence` macro and generate the string "hello, world."
