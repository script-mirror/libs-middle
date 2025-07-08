# Raizen Power Trading Libraries - Middle Layer

Libs Raizen Power Middle

## Installation

Instalação HTTPS

```bash
pip install git+https://github.com/raizen-energy/raizen-power-trading-libs-middle.git
```

Instalação branch especifica:

```bash
pip install git+https://github.com/raizen-energy/raizen-power-trading-libs-middle.git@main
```



## Usage

```python
from middle import sanitize_string

# Basic usage
text = "Héllo Wörld! @#$"
sanitized = sanitize_string(text)
print(sanitized)  # Output: "HELLO WORLD"

# With custom characters
text = "test-string_with-dashes"
sanitized = sanitize_string(text, custom_chars="-_")
print(sanitized)  # Output: "TEST-STRING_WITH-DASHES"
```

## Functions

### `sanitize_string(text, custom_chars="")`

Sanitizes a string by removing special characters and normalizing the text.

**Parameters:**
- `text` (str): Text to be sanitized
- `custom_chars` (str): Additional characters to allow in the output

**Returns:**
- `str`: Sanitized string in uppercase

## Development

To install in development mode:

```bash
git clone https://github.com/your-username/raizen-power-trading-libs-middle.git
cd raizen-power-trading-libs-middle
pip install -e .[dev]
```

## License

MIT License